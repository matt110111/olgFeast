from decimal import Decimal
from app.models.event import OrderConsumption, StationCheck
from app.models.order import Order


def setup(client, headers, foods):
    event = client.post('/api/v1/events', headers=headers, json={'name': 'Four kitchens', 'event_date': '2026-09-26'}).json()
    rooms = []
    for index, name in enumerate(['Fried', 'Grilled', 'Cooked 1', 'Cooked 2']):
        room = client.post(f"/api/v1/events/{event['id']}/rooms", headers=headers, json={'name': name}).json()
        rooms.append(room)
        if index < len(foods):
            client.put(f"/api/v1/events/{event['id']}/rooms/{room['id']}/menu", headers=headers, json={'food_item_ids': [foods[index].id]})
    ingredient = client.post('/api/v1/events/setup/consumables', headers=headers, json={'name': 'Demo plate', 'unit': 'each'}).json()
    for food in foods:
        client.put(f'/api/v1/events/setup/recipes/{food.id}', headers=headers, json=[{'consumable_id': ingredient['id'], 'quantity': 1}])
    return event, rooms


def payload(foods):
    return {'customer_name': 'Table 8', 'checkout_key': 'mixed-check-123', 'station_number': 6,
            'tickets_collected': sum(f.ticket * 2 for f in foods),
            'items': [{'food_item_id': f.id, 'quantity': 2} for f in foods]}


def test_routing_and_retry_preserve_snapshot(client, staff_auth_headers, test_food_items, db_session):
    h = staff_auth_headers
    event, rooms = setup(client, h, test_food_items)
    url = f"/api/v1/events/{event['id']}/station-checkout"
    data = payload(test_food_items)
    response = client.post(url, headers=h, json=data)
    assert response.status_code == 200, response.text
    receipt = response.json()
    assert len(receipt['orders']) == 3
    assert sum(o['tickets_collected'] for o in receipt['orders']) == data['tickets_collected']
    for index, order in enumerate(receipt['orders']):
        assert order['room_id'] == rooms[index]['id']
        assert order['check_id'] == receipt['id'] and order['station_number'] == 6
        assert order['awaiting_tickets'] is False
        assert len(order['order_items']) == 1
        assert order['order_items'][0]['food_item_id'] == test_food_items[index].id
    assert sum(r.quantity for r in db_session.query(OrderConsumption)) == Decimal(6)
    client.put(f"/api/v1/events/{event['id']}/rooms/{rooms[0]['id']}/menu", headers=h, json={'food_item_ids': []})
    again = client.post(url, headers=h, json=data)
    assert again.status_code == 200
    assert [o['id'] for o in again.json()['orders']] == [o['id'] for o in receipt['orders']]
    assert db_session.query(Order).count() == 3
    assert db_session.query(StationCheck).count() == 1
    report = client.get(f"/api/v1/events/{event['id']}/report", headers=h).json()
    assert report['tickets_collected'] == data['tickets_collected']
    assert client.post(url, headers=h, json={**data, 'station_number': 1}).status_code == 409


def test_invalid_total_route_and_guest_cannot_send(client, staff_auth_headers, auth_headers, test_food_items, db_session):
    h = staff_auth_headers
    event, rooms = setup(client, h, test_food_items)
    url = f"/api/v1/events/{event['id']}/station-checkout"
    data = payload(test_food_items)
    assert client.post(url, headers=auth_headers, json=data).status_code == 403
    assert client.post(url, headers=h, json={**data, 'tickets_collected': 0}).status_code == 409
    assert client.post(url, headers=h, json={**data, 'station_number': 7}).status_code == 422
    client.put(f"/api/v1/events/{event['id']}/rooms/{rooms[-1]['id']}/menu", headers=h, json={'food_item_ids': [test_food_items[-1].id]})
    assert client.post(url, headers=h, json=data).status_code == 409
    assert db_session.query(Order).count() == db_session.query(StationCheck).count() == db_session.query(OrderConsumption).count() == 0


def test_later_kitchen_failure_rolls_back_every_order(client, staff_auth_headers, test_food_items, db_session, monkeypatch):
    from app.services import station_checkout as service
    h = staff_auth_headers
    event, _ = setup(client, h, test_food_items)
    real_checkout = service.checkout
    calls = []
    def fail_second(*args, **kwargs):
        from fastapi import HTTPException
        calls.append(1)
        if len(calls) == 2:
            raise HTTPException(409, 'Kitchen changed')
        return real_checkout(*args, **kwargs)
    monkeypatch.setattr(service, 'checkout', fail_second)
    response = client.post(f"/api/v1/events/{event['id']}/station-checkout", headers=h, json=payload(test_food_items))
    assert response.status_code == 409
    assert len(calls) == 2
    assert db_session.query(Order).count() == db_session.query(StationCheck).count() == db_session.query(OrderConsumption).count() == 0
