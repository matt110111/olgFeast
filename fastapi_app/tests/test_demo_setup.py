from demo_setup import populate_demo
from app.models.event import DinnerEvent, Consumable, RecipeLine, StockAdjustment, EventRoom, RoomMenuItem
from app.models.user import User


def test_demo_is_repeatable(db_session, test_staff_user, test_food_items):
    db = db_session
    event = DinnerEvent(name='Demo', event_date='2026-09-26')
    db.add(event)
    for food, name in zip(test_food_items, ['Wings', 'Beef Steak', 'Vegetarian Pasta']):
        food.name = name
    db.commit()
    first = populate_demo(db, 'test-demo-station-password', event.id)
    models = [Consumable, RecipeLine, StockAdjustment, EventRoom, RoomMenuItem, User]
    counts = [db.query(model).count() for model in models]
    again = populate_demo(db, 'another-password-not-applied', event.id)
    assert first['menu_items_with_recipes'] == 3
    assert len(first['created_accounts']) == 10
    assert again['created_accounts'] == []
    assert counts == [db.query(model).count() for model in models]
    assert {r.name for r in db.query(EventRoom)} == {'Fried', 'Grilled', 'Cooked 1', 'Cooked 2'}
    for line in db.query(RecipeLine):
        room = db.query(RoomMenuItem).filter_by(food_item_id=line.food_item_id).one()
        stock = db.query(StockAdjustment).filter_by(room_id=room.room_id, consumable_id=line.consumable_id).one()
        assert stock.quantity == line.quantity * 100
