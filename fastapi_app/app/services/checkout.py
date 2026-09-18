"""One transaction records an order, its ticket values, and recipe usage."""
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
import secrets
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models.order import Order, OrderItem, OrderStatus
from ..models.event import DinnerEvent, RecipeLine, Consumable, OrderConsumption, OrderCounter, RoomMenuItem
from ..models.menu import FoodItem
from ..models.cart import Cart, CartItem
from .rooms import require_room


def checkout(db: Session, user_id: int, name: str, items: list[dict], key: str | None,
             event_id: int | None = None, tickets_collected: int = 0, cart: Cart | None = None, guest: bool = False, room_id: int | None = None, commit: bool = True):
    combined = defaultdict(int)
    for item in items:
        combined[item['food_item_id']] += item['quantity']
    identity = [name.strip(), sorted(combined.items()), event_id, tickets_collected]
    if room_id:
        identity.append(room_id)
    fingerprint = hashlib.sha256(json.dumps(identity, separators=(',', ':')).encode()).hexdigest()
    # Global row lock makes numbering and idempotent retries safe across workers.
    counter = db.query(OrderCounter).filter_by(id=1).with_for_update().first()
    if not counter:
        raise HTTPException(503, 'Database migration is required')
    if key:
        existing = db.query(Order).filter_by(user_id=user_id, checkout_key=key).first()
        if existing:
            if existing.checkout_fingerprint != fingerprint and cart is None:
                raise HTTPException(409, 'This checkout reference belongs to a different order')
            return existing
    if not combined:
        raise HTTPException(400, 'Add at least one item')
    if event_id is not None:
        event = db.query(DinnerEvent).filter_by(id=event_id).with_for_update().first()
        if not event or event.closed:
            raise HTTPException(409, 'This event is closed or unavailable')
    else:
        event = None
    room = require_room(db, event_id, room_id, required=True) if event else None
    if room:
        allowed = {row.food_item_id for row in db.query(RoomMenuItem).filter_by(room_id=room.id).all()}
        if not set(combined).issubset(allowed):
            raise HTTPException(409, 'An item is not on this room’s menu. Review the order.')
    foods = {food.id: food for food in db.query(FoodItem).filter(FoodItem.id.in_(combined)).all()}
    for food_id, quantity in combined.items():
        food = foods.get(food_id)
        if not food or str(food.is_available).lower() not in ('true', '1'):
            raise HTTPException(409, 'An item is no longer available. Review the menu.')
        if quantity < 1 or quantity > 999:
            raise HTTPException(422, 'Quantity must be between 1 and 999')
    owed = sum(foods[food_id].ticket * quantity for food_id, quantity in combined.items())
    if guest and tickets_collected:
        raise HTTPException(403, "Only a volunteer can confirm collected tickets")
    awaiting_tickets = bool(guest and event and event.collect_tickets)
    if event and event.collect_tickets and not guest and tickets_collected != owed:
        raise HTTPException(409, f'Collect exactly {owed} tickets before confirming')
    if tickets_collected < 0 or tickets_collected > owed:
        raise HTTPException(422, 'Collected tickets must be between zero and tickets owed')
    counter.value += 1
    order = Order(display_id=counter.value, ref_code=secrets.token_hex(16), user_id=user_id,
        customer_name=name.strip(), status=OrderStatus.PENDING, event_id=event_id, room_id=room.id if room else None,
        checkout_key=key, checkout_fingerprint=fingerprint, tickets_collected=tickets_collected,
        awaiting_tickets=awaiting_tickets,
        tickets_confirmed_by=user_id if event and event.collect_tickets and not guest else None,
        tickets_confirmed_at=datetime.now(timezone.utc) if event and event.collect_tickets and not guest else None)
    db.add(order)
    db.flush()
    recipe_food_ids = {r.food_item_id for r in db.query(RecipeLine).filter(RecipeLine.food_item_id.in_(combined)).all()}
    for food_id, quantity in combined.items():
        food = foods[food_id]
        db.add(OrderItem(order_id=order.id, food_item_id=food.id, quantity=quantity,
            item_name=food.name, recipe_recorded=food_id in recipe_food_ids, unit_tickets=food.ticket, unit_value=Decimal(str(food.value))))
    consumption = defaultdict(Decimal)
    recipes = db.query(RecipeLine).filter(RecipeLine.food_item_id.in_(combined)).all()
    for recipe in recipes:
        consumption[recipe.consumable_id] += recipe.quantity * combined[recipe.food_item_id]
    for consumable_id, quantity in consumption.items():
        consumable = db.get(Consumable, consumable_id)
        db.add(OrderConsumption(order_id=order.id, consumable_id=consumable_id,
            name=consumable.name, unit=consumable.unit, quantity=quantity))
    if cart:
        db.query(CartItem).filter_by(cart_id=cart.id).delete(synchronize_session=False)
    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(order)
    return order
