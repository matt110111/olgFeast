"""Dinner events, ticket checkout, and estimated consumable usage."""
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from ...api.deps import get_current_user, get_current_staff_user, get_current_admin_user
from ...core.database import get_db
from ...models.event import DinnerEvent, Consumable, RecipeLine, StockAdjustment, OrderConsumption, OrderCounter, EventRoom, RoomMenuItem
from ...models.order import Order, OrderItem, OrderStatus
from ...models.menu import FoodItem
from ...models.user import User
from ...schemas.order import Order as OrderSchema
from ...services.checkout import checkout
from ...services.rooms import require_room, room_filter, check_order_room

router = APIRouter(dependencies=[Depends(get_current_user)])


class EventInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    event_date: date
    collect_tickets: bool = True


@router.get('')
def events(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(DinnerEvent)
    if not user.is_staff:
        query = query.filter_by(closed=False)
    return query.order_by(DinnerEvent.id.desc()).all()


@router.post('', dependencies=[Depends(get_current_admin_user)])
def create_event(data: EventInput, db: Session = Depends(get_db)):
    event = DinnerEvent(name=data.name.strip(), event_date=data.event_date.isoformat(), collect_tickets=data.collect_tickets)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def require_event(db, event_id, writable=False, lock=False):
    query = db.query(DinnerEvent).filter_by(id=event_id)
    if writable or lock:
        query = query.with_for_update()
    event = query.first()
    if not event:
        raise HTTPException(404, 'Event not found')
    if writable and event.closed:
        raise HTTPException(409, 'Event is closed')
    return event


class EventState(BaseModel):
    closed: bool


@router.patch('/{event_id}/state', dependencies=[Depends(get_current_admin_user)])
def event_state(event_id: int, data: EventState, db: Session = Depends(get_db)):
    event = require_event(db, event_id, lock=True)
    if data.closed and db.query(Order).filter(Order.event_id == event_id, Order.voided_at.is_(None), Order.status != OrderStatus.COMPLETE).count():
        raise HTTPException(409, 'Serve or void outstanding orders before closing the event')
    event.closed = data.closed
    db.commit()
    return {'closed': event.closed}


class ConsumableInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    unit: str = Field(pattern='^(g|ml|each)$')


@router.get('/setup/consumables', dependencies=[Depends(get_current_admin_user)])
def consumables(db: Session = Depends(get_db)):
    return db.query(Consumable).order_by(Consumable.name).all()


@router.post('/setup/consumables', dependencies=[Depends(get_current_admin_user)])
def create_consumable(data: ConsumableInput, db: Session = Depends(get_db)):
    if db.query(Consumable).filter(func.lower(Consumable.name) == data.name.strip().lower()).first():
        raise HTTPException(409, 'A consumable with that name already exists')
    item = Consumable(name=data.name.strip(), unit=data.unit)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


class RecipeInput(BaseModel):
    consumable_id: int
    quantity: Decimal = Field(gt=0, le=1000000, decimal_places=3)


@router.get('/setup/recipes', dependencies=[Depends(get_current_admin_user)])
def recipes(db: Session = Depends(get_db)):
    return db.query(RecipeLine).all()


@router.put('/setup/recipes/{food_id}', dependencies=[Depends(get_current_admin_user)])
def set_recipe(food_id: int, data: list[RecipeInput], db: Session = Depends(get_db)):
    # Use checkout's lock so the whole recipe is snapshotted before or after edits.
    db.query(OrderCounter).filter_by(id=1).with_for_update().first()
    if not db.get(FoodItem, food_id):
        raise HTTPException(404, 'Menu item not found')
    if len({line.consumable_id for line in data}) != len(data):
        raise HTTPException(422, 'Each consumable may appear once per recipe')
    for line in data:
        if not db.get(Consumable, line.consumable_id):
            raise HTTPException(404, 'Consumable not found')
    db.query(RecipeLine).filter_by(food_item_id=food_id).delete()
    for line in data:
        db.add(RecipeLine(food_item_id=food_id, **line.model_dump()))
    db.commit()
    return {'message': 'Recipe saved. Applies to new orders only.'}


class StockInput(BaseModel):
    room_id: int | None = Field(default=None, gt=0)
    consumable_id: int
    quantity: Decimal = Field(ge=-1000000000, le=1000000000, decimal_places=3)
    reason: str = Field(min_length=3, max_length=200)


@router.post('/{event_id}/stock', dependencies=[Depends(get_current_admin_user)])
def adjust_stock(event_id: int, data: StockInput, user: User = Depends(get_current_staff_user), db: Session = Depends(get_db)):
    require_event(db, event_id, writable=True)
    require_room(db, event_id, data.room_id)
    if not db.get(Consumable, data.consumable_id):
        raise HTTPException(404, 'Consumable not found')
    if data.quantity == 0:
        raise HTTPException(422, 'Enter a nonzero adjustment')
    adjustment = StockAdjustment(event_id=event_id, user_id=user.id, **data.model_dump())
    db.add(adjustment)
    db.commit()
    return {'message': 'Stock adjustment recorded'}


@router.get('/{event_id}/stock', dependencies=[Depends(get_current_admin_user)])
def stock_history(event_id: int, room_id: int | None = None, db: Session = Depends(get_db)):
    require_event(db, event_id)
    require_room(db, event_id, room_id)
    return room_filter(db.query(StockAdjustment).filter_by(event_id=event_id), StockAdjustment, room_id).order_by(StockAdjustment.id.desc()).limit(200).all()


class CheckoutItem(BaseModel):
    food_item_id: int
    quantity: int = Field(ge=1, le=999)


class EventCheckout(BaseModel):
    room_id: int | None = Field(default=None, gt=0)
    customer_name: str = Field(min_length=1, max_length=100)
    items: list[CheckoutItem] = Field(min_length=1, max_length=100)
    checkout_key: str = Field(min_length=8, max_length=80)
    tickets_collected: int = Field(default=0, ge=0)


class StationCheckout(EventCheckout):
    station_number: int = Field(ge=1, le=6)


class StationReceipt(BaseModel):
    id: int
    station_number: int
    orders: list[OrderSchema]


@router.post('/{event_id}/station-checkout', response_model=StationReceipt)
def checkout_station(event_id: int, data: StationCheckout, tasks: BackgroundTasks,
                     user: User = Depends(get_current_staff_user), db: Session = Depends(get_db)):
    from ...services.station_checkout import station_checkout
    from ...websocket.notifications import notify_order
    check, orders = station_checkout(db, user.id, event_id, data)
    for order in orders:
        tasks.add_task(notify_order, order.id)
    return {'id': check.id, 'station_number': check.station_number, 'orders': orders}


@router.post('/{event_id}/checkout', response_model=OrderSchema)
def event_checkout(event_id: int, data: EventCheckout, tasks: BackgroundTasks,
                   user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not data.customer_name.strip():
        raise HTTPException(422, 'Enter a guest name or table number')
    order = checkout(db, user.id, data.customer_name, [item.model_dump() for item in data.items],
                     data.checkout_key, event_id, data.tickets_collected, guest=not user.is_staff, room_id=data.room_id)
    from ...websocket.notifications import notify_order
    tasks.add_task(notify_order, order.id)
    return order


@router.get('/{event_id}/orders', response_model=list[OrderSchema], dependencies=[Depends(get_current_staff_user)])
def event_orders(event_id: int, room_id: int | None = None, db: Session = Depends(get_db)):
    require_event(db, event_id)
    require_room(db, event_id, room_id)
    query = db.query(Order).options(selectinload(Order.order_items).selectinload(OrderItem.food_item)).filter(Order.event_id == event_id, Order.voided_at.is_(None), Order.status != OrderStatus.COMPLETE)
    return room_filter(query, Order, room_id).order_by(Order.id.desc()).all()


class TicketConfirmation(BaseModel):
    tickets_collected: int = Field(ge=0)


@router.post('/{event_id}/orders/{order_id}/tickets', response_model=OrderSchema)
def confirm_tickets(event_id: int, order_id: int, data: TicketConfirmation, tasks: BackgroundTasks, room_id: int | None = None,
                    user: User = Depends(get_current_staff_user), db: Session = Depends(get_db)):
    require_event(db, event_id, writable=True)
    order = db.query(Order).filter_by(id=order_id, event_id=event_id).with_for_update().first()
    if not order:
        raise HTTPException(404, 'Order not found')
    check_order_room(order, room_id)
    if order.voided_at:
        raise HTTPException(409, 'This order was voided')
    owed = sum(item.unit_tickets * item.quantity for item in order.order_items)
    if data.tickets_collected != owed:
        raise HTTPException(409, f'Collect exactly {owed} tickets before confirming')
    if not order.awaiting_tickets:
        if order.tickets_confirmed_at and order.tickets_collected == owed:
            return order  # Safe retry after a lost confirmation response.
        raise HTTPException(409, 'This order is not awaiting ticket collection')
    if any(str(item.food_item.is_available).lower() not in ('true', '1') for item in order.order_items):
        raise HTTPException(409, 'An item is now unavailable. Void this order and return any tickets.')
    order.tickets_collected = owed
    order.awaiting_tickets = False
    order.tickets_confirmed_by = user.id
    order.tickets_confirmed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    from ...websocket.notifications import notify_order
    tasks.add_task(notify_order, order.id)
    return order


class VoidInput(BaseModel):
    reason: str = Field(min_length=3, max_length=200)


@router.post('/{event_id}/orders/{order_id}/void', dependencies=[Depends(get_current_staff_user)])
def void_order(event_id: int, order_id: int, data: VoidInput, tasks: BackgroundTasks, room_id: int | None = None, db: Session = Depends(get_db)):
    require_event(db, event_id, writable=True)
    order = db.query(Order).filter_by(id=order_id, event_id=event_id).with_for_update().first()
    if not order:
        raise HTTPException(404, 'Order not found')
    check_order_room(order, room_id)
    if order.voided_at:
        return {'message': 'Order already voided'}
    if order.status != OrderStatus.PENDING:
        raise HTTPException(409, 'Only unprepared orders can be voided; record waste separately for prepared food')
    order.voided_at = datetime.now(timezone.utc)
    order.void_reason = data.reason
    db.commit()
    from ...websocket.notifications import notify_order
    tasks.add_task(notify_order, order.id)
    return {'message': 'Order voided. Return any collected tickets to the guest.'}


def event_report(db, event_id, room_id=None):
    event = require_event(db, event_id)
    room = require_room(db, event_id, room_id)
    orders = room_filter(db.query(Order).options(selectinload(Order.order_items)).filter_by(event_id=event_id), Order, room_id).all()
    waiting = [order for order in orders if order.voided_at is None and order.awaiting_tickets]
    active = [order for order in orders if order.voided_at is None and not order.awaiting_tickets]
    portions = defaultdict(lambda: {'ordered': 0, 'served': 0, 'tickets': 0})
    missing = set()
    for order in active:
        for item in order.order_items:
            row = portions[item.item_name]
            row['ordered'] += item.quantity
            row['served'] += item.quantity if order.status == OrderStatus.COMPLETE else 0
            row['tickets'] += item.unit_tickets * item.quantity
            if not item.recipe_recorded:
                missing.add(item.item_name)
    use = defaultdict(Decimal)
    for row in room_filter(db.query(OrderConsumption).join(Order).filter(Order.event_id == event_id, Order.voided_at.is_(None), Order.awaiting_tickets.is_(False)), Order, room_id).all():
        use[row.consumable_id] += row.quantity
    stock = defaultdict(Decimal)
    for row in room_filter(db.query(StockAdjustment).filter_by(event_id=event_id), StockAdjustment, room_id).all():
        stock[row.consumable_id] += row.quantity
    inventory = []
    for item in db.query(Consumable).order_by(Consumable.name).all():
        if item.id in stock or item.id in use:
            inventory.append({'id': item.id, 'name': item.name, 'unit': item.unit,
                'stock_added': stock[item.id], 'estimated_used': use[item.id],
                'estimated_remaining': stock[item.id] - use[item.id]})
    return {'room_name': room.name if room else ('Unassigned / shared' if room_id == 0 else 'Whole event'),
        'event': {'id': event.id, 'name': event.name, 'event_date': event.event_date, 'closed': event.closed},
        'order_count': len(active), 'voided_count': sum(order.voided_at is not None for order in orders),
        'awaiting_ticket_count': len(waiting),
        'awaiting_ticket_total': sum(item.quantity * item.unit_tickets for order in waiting for item in order.order_items),
        'tickets_owed': sum(row['tickets'] for row in portions.values()),
        'tickets_collected': sum(order.tickets_collected for order in active),
        'voided_tickets_to_return': sum(order.tickets_collected for order in orders if order.voided_at),
        'portions': [{'name': name, **row} for name, row in sorted(portions.items())],
        'consumables': inventory, 'items_without_recipes': sorted(missing)}


@router.get('/{event_id}/report', dependencies=[Depends(get_current_admin_user)])
def report(event_id: int, room_id: int | None = None, db: Session = Depends(get_db)):
    return event_report(db, event_id, room_id)


@router.get('/{event_id}/report.csv', dependencies=[Depends(get_current_admin_user)])
def report_csv(event_id: int, room_id: int | None = None, db: Session = Depends(get_db)):
    report = event_report(db, event_id, room_id)
    output = io.StringIO()
    writer = csv.writer(output)
    def safe(value):
        text = str(value)
        return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text
    writer.writerow(['Event', safe(report['event']['name']), report['event']['event_date']])
    writer.writerow(['Room', safe(report['room_name'])])
    writer.writerow(['Orders', report['order_count'], 'Voided orders', report['voided_count']])
    writer.writerow(['Tickets owed', report['tickets_owed'], 'Tickets collected', report['tickets_collected']])
    writer.writerow(['Orders awaiting tickets', report['awaiting_ticket_count'], 'Tickets awaiting collection', report['awaiting_ticket_total']])
    writer.writerow(['Voided tickets to return', report['voided_tickets_to_return']])
    writer.writerow([])
    writer.writerow(['Menu item', 'Portions ordered', 'Portions served', 'Tickets owed'])
    for row in report['portions']:
        writer.writerow([safe(row['name']), row['ordered'], row['served'], row['tickets']])
    writer.writerow([])
    writer.writerow(['Consumable', 'Unit', 'Net stock added', 'Estimated use', 'Estimated remaining'])
    for row in report['consumables']:
        writer.writerow([safe(row['name']), row['unit'], row['stock_added'], row['estimated_used'], row['estimated_remaining']])
    writer.writerow([])
    writer.writerow(['Items missing recipes', *[safe(name) for name in report['items_without_recipes']]])
    return Response(output.getvalue(), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename="event-{event_id}-report.csv"'})


class RoomInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.get('/{event_id}/rooms')
def rooms(event_id: int, db: Session = Depends(get_db)):
    require_event(db, event_id)
    rows = db.query(EventRoom).filter_by(event_id=event_id).order_by(EventRoom.id).all()
    assignments = db.query(RoomMenuItem).join(EventRoom).filter(EventRoom.event_id == event_id).all()
    return [{'id': room.id, 'event_id': room.event_id, 'name': room.name,
             'food_item_ids': [item.food_item_id for item in assignments if item.room_id == room.id]} for room in rows]


@router.post('/{event_id}/rooms', dependencies=[Depends(get_current_admin_user)])
def create_room(event_id: int, data: RoomInput, db: Session = Depends(get_db)):
    # Match checkout lock order to avoid deadlocks with menu/room edits.
    db.query(OrderCounter).filter_by(id=1).with_for_update().first()
    require_event(db, event_id, writable=True)
    name = data.name.strip()
    if not name:
        raise HTTPException(422, 'Enter a room name')
    if db.query(EventRoom).filter(EventRoom.event_id == event_id, func.lower(EventRoom.name) == name.lower()).first():
        raise HTTPException(409, 'A room with this name already exists in the event')
    room = EventRoom(event_id=event_id, name=name)
    db.add(room); db.commit(); db.refresh(room)
    return {'id': room.id, 'event_id': room.event_id, 'name': room.name, 'food_item_ids': []}


class RoomMenuInput(BaseModel):
    food_item_ids: list[int] = Field(max_length=100)


@router.put('/{event_id}/rooms/{room_id}/menu', dependencies=[Depends(get_current_admin_user)])
def set_room_menu(event_id: int, room_id: int, data: RoomMenuInput, db: Session = Depends(get_db)):
    db.query(OrderCounter).filter_by(id=1).with_for_update().first()
    require_event(db, event_id, writable=True)
    if not room_id or room_id < 0:
        raise HTTPException(404, 'Room not found')
    require_room(db, event_id, room_id)
    ids = set(data.food_item_ids)
    if db.query(FoodItem).filter(FoodItem.id.in_(ids)).count() != len(ids):
        raise HTTPException(404, 'Menu item not found')
    db.query(RoomMenuItem).filter_by(room_id=room_id).delete()
    db.add_all([RoomMenuItem(room_id=room_id, food_item_id=food_id) for food_id in ids])
    db.commit()
    return {'message': 'Room menu saved. Existing orders retain their items.'}
