"""Populate the explicitly requested demo. Existing orders and passwords survive.

Run with DEMO_STATION_PASSWORD set. Quantities are illustrative, per portion.
The seeded starting stock covers 100 portions of each menu item per kitchen.
"""
import os
from collections import defaultdict
from decimal import Decimal
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models import cart, order  # Register the User relationship targets.
from app.models.menu import FoodItem
from app.models.event import DinnerEvent, EventRoom, RoomMenuItem, Consumable, RecipeLine, StockAdjustment, OrderCounter

# kitchen, ingredients (name, unit, quantity), serving supplies
DEMO_MENU = {
    'Wings': ('Fried', [('Chicken wings', 'g', 250), ('Frying oil', 'ml', 25), ('Wing sauce', 'ml', 40)], 'tray'),
    'Sausage & Peppers Sandwich': ('Grilled', [('Italian sausage', 'g', 150), ('Bell peppers', 'g', 80), ('Onions', 'g', 40), ('Sandwich roll', 'each', 1)], 'tray'),
    'Grilled Salmon': ('Grilled', [('Salmon fillet', 'g', 180), ('Lemon', 'g', 20), ('Cooking oil', 'ml', 10)], 'plate'),
    'Beef Steak': ('Grilled', [('Beef steak', 'g', 225), ('Seasoning', 'g', 5), ('Cooking oil', 'ml', 10)], 'plate'),
    'Chicken Alfredo': ('Cooked 1', [('Dry pasta', 'g', 100), ('Chicken breast', 'g', 120), ('Alfredo sauce', 'ml', 150), ('Parmesan', 'g', 15)], 'plate'),
    'Garlic Bread': ('Cooked 1', [('Bread', 'g', 80), ('Garlic butter', 'g', 20)], 'tray'),
    'Vegetarian Pasta': ('Cooked 2', [('Dry pasta', 'g', 100), ('Tomato sauce', 'ml', 150), ('Mixed vegetables', 'g', 100)], 'plate'),
    'Caesar Salad': ('Cooked 2', [('Romaine lettuce', 'g', 100), ('Caesar dressing', 'ml', 30), ('Croutons', 'g', 20), ('Parmesan', 'g', 10)], 'plate'),
    'Chocolate Cake': ('Cooked 2', [('Chocolate cake slice', 'each', 1)], 'dessert'),
    'Tiramisu': ('Cooked 2', [('Tiramisu portion', 'each', 1)], 'dessert'),
    'Ice Cream': ('Cooked 2', [('Ice cream', 'g', 120)], 'dessert'),
    'Coffee': ('Cooked 1', [('Ground coffee', 'g', 15), ('Drinking water', 'ml', 240), ('Sugar packet', 'each', 1)], 'hot drink'),
    'Fresh Juice': ('Cooked 2', [('Fruit juice', 'ml', 250)], 'cold drink'),
    'Soft Drinks': ('Cooked 2', [('Soft drink can', 'each', 1)], 'can'),
}
SUPPLIES = {
    'tray': [('Food tray', 'each', 1), ('Napkin', 'each', 2)],
    'plate': [('Dinner plate', 'each', 1), ('Fork', 'each', 1), ('Knife', 'each', 1), ('Napkin', 'each', 2)],
    'dessert': [('Dessert bowl', 'each', 1), ('Spoon', 'each', 1), ('Napkin', 'each', 1)],
    'hot drink': [('Hot cup', 'each', 1), ('Cup lid', 'each', 1), ('Stirrer', 'each', 1), ('Napkin', 'each', 1)],
    'cold drink': [('Cold cup', 'each', 1), ('Straw', 'each', 1), ('Napkin', 'each', 1)],
    'can': [('Napkin', 'each', 1)],
}


def populate_demo(db, password, event_id=1):
    if not password or len(password) < 10:
        raise ValueError('Set DEMO_STATION_PASSWORD to at least 10 characters')
    db.query(OrderCounter).filter_by(id=1).with_for_update().one()
    event = db.query(DinnerEvent).filter_by(id=event_id).with_for_update().one()
    if event.closed:
        raise ValueError('Choose an open demo event')
    organizer = db.query(User).filter_by(is_admin=True, is_active=True).first()
    if not organizer:
        raise ValueError('An organizer account is required')
    event.collect_tickets = True
    rooms = {}
    for name, old in [('Fried', 'Wings'), ('Grilled', 'Sausage & Peppers'), ('Cooked 1', None), ('Cooked 2', None)]:
        room = db.query(EventRoom).filter_by(event_id=event_id, name=name).first()
        if not room and old:
            room = db.query(EventRoom).filter_by(event_id=event_id, name=old).first()
        if not room:
            room = EventRoom(event_id=event_id, name=name); db.add(room)
        room.name = name
        db.flush(); rooms[name] = room
    stock = defaultdict(Decimal)
    seeded = 0
    for name, (kitchen, ingredients, serving) in DEMO_MENU.items():
        food = db.query(FoodItem).filter_by(name=name).first()
        if not food:
            continue
        room = rooms[kitchen]
        # Change assignments for these demo items only, in this event only.
        event_room_ids = [r.id for r in db.query(EventRoom).filter_by(event_id=event_id)]
        db.query(RoomMenuItem).filter(RoomMenuItem.room_id.in_(event_room_ids), RoomMenuItem.food_item_id == food.id).delete(synchronize_session=False)
        db.add(RoomMenuItem(room_id=room.id, food_item_id=food.id))
        existing_recipe = db.query(RecipeLine).filter_by(food_item_id=food.id).all()
        if not existing_recipe:
            for item_name, unit, qty in ingredients + SUPPLIES[serving]:
                consumable = db.query(Consumable).filter_by(name=item_name).first()
                if not consumable:
                    consumable = Consumable(name=item_name, unit=unit); db.add(consumable); db.flush()
                db.add(RecipeLine(food_item_id=food.id, consumable_id=consumable.id, quantity=qty))
            db.flush()
            existing_recipe = db.query(RecipeLine).filter_by(food_item_id=food.id).all()
        for line in existing_recipe:
            stock[(room.id, line.consumable_id)] += line.quantity * 100
        seeded += 1
    for (room_id, consumable_id), quantity in stock.items():
        reason = 'Demo starting stock: 100 portions per assigned menu item'
        if not db.query(StockAdjustment).filter_by(event_id=event_id, room_id=room_id, consumable_id=consumable_id, reason=reason).first():
            db.add(StockAdjustment(event_id=event_id, room_id=room_id, consumable_id=consumable_id, quantity=quantity, reason=reason, user_id=organizer.id))
    created = []
    for username in [f'input{i}' for i in range(1, 7)] + [f'kitchen{i}' for i in range(1, 5)]:
        if not db.query(User).filter_by(username=username).first():
            db.add(User(username=username, email=f'{username}@demo.olgfeast.local', hashed_password=get_password_hash(password), is_staff=True, is_admin=False, is_active=True))
            created.append(username)
    db.commit()
    return {'kitchens': {name: room.id for name, room in rooms.items()}, 'menu_items_with_recipes': seeded, 'consumables': db.query(Consumable).count(), 'stock_lines': len(stock), 'created_accounts': created}


if __name__ == '__main__':
    import json
    with SessionLocal() as db:
        print(json.dumps(populate_demo(db, os.environ.get('DEMO_STATION_PASSWORD'), int(os.environ.get('DEMO_EVENT_ID', '1')))))
