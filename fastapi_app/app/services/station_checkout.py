"""A single ticket collection, with atomic and retry-safe kitchen routing."""
from collections import defaultdict
import hashlib
import json
from fastapi import HTTPException
from ..models.event import DinnerEvent, EventRoom, RoomMenuItem, OrderCounter, StationCheck
from ..models.order import Order
from ..models.menu import FoodItem
from .checkout import checkout


def station_checkout(db, user_id, event_id, data):
    combined = defaultdict(int)
    for item in data.items:
        combined[item.food_item_id] += item.quantity
    fingerprint = hashlib.sha256(json.dumps([
        event_id, data.station_number, data.customer_name.strip(),
        sorted(combined.items()), data.tickets_collected,
    ], separators=(',', ':')).encode()).hexdigest()
    counter = db.query(OrderCounter).filter_by(id=1).with_for_update().first()
    if not counter:
        raise HTTPException(503, 'Database migration is required')
    existing = db.query(StationCheck).filter_by(user_id=user_id, checkout_key=data.checkout_key).first()
    if existing:
        if existing.fingerprint != fingerprint:
            raise HTTPException(409, 'This checkout reference belongs to a different check')
        return existing, db.query(Order).filter_by(check_id=existing.id).order_by(Order.id).all()
    event = db.query(DinnerEvent).filter_by(id=event_id).with_for_update().first()
    if not event or event.closed:
        raise HTTPException(409, 'This event is closed or unavailable')
    if not data.customer_name.strip():
        raise HTTPException(422, 'Enter a guest name or table number')
    foods = {f.id: f for f in db.query(FoodItem).filter(FoodItem.id.in_(combined)).all()}
    assignments = defaultdict(list)
    for row in db.query(RoomMenuItem).join(EventRoom).filter(EventRoom.event_id == event_id).all():
        assignments[row.food_item_id].append(row.room_id)
    grouped = defaultdict(list)
    for food_id, quantity in combined.items():
        food = foods.get(food_id)
        if not food or str(food.is_available).lower() not in ('true', '1'):
            raise HTTPException(409, 'An item is no longer available. Review the menu.')
        if not 1 <= quantity <= 999:
            raise HTTPException(422, 'Quantity must be between 1 and 999')
        if len(assignments[food_id]) != 1:
            raise HTTPException(409, f'Assign {food.name} to exactly one kitchen in Menu & kitchens before ordering')
        grouped[assignments[food_id][0]].append({'food_item_id': food_id, 'quantity': quantity})
    owed = sum(foods[id].ticket * qty for id, qty in combined.items())
    # Input stations always collect on the check screen, even for legacy events
    # whose separate guest ticket desk was disabled.
    if data.tickets_collected != owed:
        raise HTTPException(409, f'Collect exactly {owed} tickets before sending to kitchens')
    check = StationCheck(user_id=user_id, event_id=event_id, checkout_key=data.checkout_key,
                         fingerprint=fingerprint, station_number=data.station_number)
    db.add(check)
    db.flush()
    orders = []
    for room_id, items in sorted(grouped.items()):
        tickets = sum(foods[i['food_item_id']].ticket * i['quantity'] for i in items)
        order = checkout(db, user_id, data.customer_name, items, None, event_id,
                         tickets, room_id=room_id, commit=False)
        order.check_id = check.id
        order.station_number = data.station_number
        orders.append(order)
    db.commit()
    return check, orders
