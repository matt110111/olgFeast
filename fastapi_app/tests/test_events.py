from decimal import Decimal
import pytest
from starlette.websockets import WebSocketDisconnect
from app.core.security import hash_password
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.event import OrderCounter, OrderConsumption


def setup_event(client, headers, foods):
    event = client.post('/api/v1/events', headers=headers, json={'name':'Church dinner','event_date':'2026-09-17'}).json()
    c = client.post('/api/v1/events/setup/consumables', headers=headers, json={'name':'Dry pasta','unit':'g'}).json()
    response = client.put(f'/api/v1/events/setup/recipes/{foods[0].id}', headers=headers,
        json=[{'consumable_id':c['id'],'quantity':'125.5'}])
    assert response.status_code == 200, response.text
    assert client.post(f"/api/v1/events/{event['id']}/stock", headers=headers,
        json={'consumable_id':c['id'],'quantity':1000,'reason':'Starting stock'}).status_code == 200
    return event, c


def payload(foods, key='checkout-one', quantity=2):
    return {'customer_name':'Table 4', 'checkout_key':key, 'tickets_collected':foods[0].ticket*quantity,
            'items':[{'food_item_id':foods[0].id,'quantity':quantity}]}


def test_ticket_checkout_snapshot_and_retry(client, staff_auth_headers, test_food_items, db_session):
    h=staff_auth_headers; event,c=setup_event(client,h,test_food_items)
    url=f"/api/v1/events/{event['id']}/checkout"; data=payload(test_food_items)
    first=client.post(url,headers=h,json=data)
    assert first.status_code == 200, first.text
    second=client.post(url,headers=h,json=data)
    assert second.json()['id'] == first.json()['id']
    assert db_session.query(Order).count() == 1
    assert db_session.query(OrderConsumption).one().quantity == Decimal('251.000')
    assert client.post(url,headers=h,json={**data,'customer_name':'Different'}).status_code == 409
    assert client.put(f'/api/v1/menu/items/{test_food_items[0].id}',headers=h,json={'ticket':20}).status_code == 200
    assert client.put(f'/api/v1/events/setup/recipes/{test_food_items[0].id}',headers=h,json=[{'consumable_id':c['id'],'quantity':900}]).status_code == 200
    report=client.get(f"/api/v1/events/{event['id']}/report",headers=h).json()
    assert report['tickets_owed'] == 2 and report['tickets_collected'] == 2
    assert Decimal(str(report['consumables'][0]['estimated_remaining'])) == Decimal('749')
    assert report['items_without_recipes'] == []
    assert 'Dry pasta,g,1000.000,251.000,749.000' in client.get(f"/api/v1/events/{event['id']}/report.csv",headers=h).text


def test_checkout_validation_and_event_isolation(client,staff_auth_headers,test_food_items,db_session):
    h=staff_auth_headers; event,c=setup_event(client,h,test_food_items)
    url=f"/api/v1/events/{event['id']}/checkout"; data=payload(test_food_items)
    assert client.post(url,headers=h,json={**data,'tickets_collected':1}).status_code == 409
    assert client.post(url,headers=h,json={**data,'items':[{'food_item_id':test_food_items[0].id,'quantity':-1}]}).status_code == 422
    assert db_session.query(Order).count() == 0 and db_session.query(OrderConsumption).count() == 0
    assert client.post(url,headers=h,json=data).status_code == 200
    other=client.post('/api/v1/events',headers=h,json={'name':'Other dinner','event_date':'2026-09-18','collect_tickets':False}).json()
    assert client.get(f"/api/v1/events/{other['id']}/report",headers=h).json()['order_count'] == 0
    assert client.patch(f"/api/v1/events/{event['id']}/state",headers=h,json={'closed':True}).status_code == 409
    assert client.patch(f"/api/v1/events/{other['id']}/state",headers=h,json={'closed':True}).status_code == 200
    assert client.post(f"/api/v1/events/{other['id']}/checkout",headers=h,json={**data,'checkout_key':'closed-event'}).status_code == 409


def test_void_reverses_estimates_but_preserves_history(client,staff_auth_headers,test_food_items,db_session):
    h=staff_auth_headers; event,c=setup_event(client,h,test_food_items)
    order=client.post(f"/api/v1/events/{event['id']}/checkout",headers=h,json=payload(test_food_items)).json()
    assert client.post(f"/api/v1/events/{event['id']}/orders/{order['id']}/void",headers=h,json={'reason':'Guest changed mind'}).status_code == 200
    report=client.get(f"/api/v1/events/{event['id']}/report",headers=h).json()
    assert report['order_count'] == 0 and report['voided_count'] == 1 and report['voided_tickets_to_return'] == 2
    assert Decimal(str(report['consumables'][0]['estimated_remaining'])) == Decimal('1000')
    assert db_session.query(OrderItem).count() == 1
    assert client.put(f"/api/v1/orders/{order['id']}/status",headers=h,json={'status':'preparing'}).status_code == 409


def test_order_numbers_beyond_999_and_workflow(client,staff_auth_headers,test_food_items,db_session):
    h=staff_auth_headers; event,c=setup_event(client,h,test_food_items)
    db_session.get(OrderCounter,1).value=999; db_session.commit()
    order=client.post(f"/api/v1/events/{event['id']}/checkout",headers=h,json=payload(test_food_items)).json()
    assert order['display_id']==1000
    url=f"/api/v1/orders/{order['id']}/status"
    assert client.put(url,headers=h,json={'status':'complete'}).status_code==409
    for status in ['preparing','ready','complete']:
        response=client.put(url,headers=h,json={'status':status})
        assert response.status_code==200,response.text
    assert client.get(f"/api/v1/events/{event['id']}/report",headers=h).json()['portions'][0]['served']==2
    assert client.patch(f"/api/v1/events/{event['id']}/state",headers=h,json={'closed':True}).status_code==200


def test_volunteer_permissions(client,staff_auth_headers,auth_headers,test_food_items):
    assert client.get('/api/v1/events',headers=auth_headers).status_code==200
    response=client.post('/api/v1/auth/volunteers',headers=staff_auth_headers,json={'username':'station1','password':'station-password'})
    assert response.status_code==200,response.text
    assert response.json()['is_admin'] is False
    login=client.post('/api/v1/auth/login',data={'username':'station1','password':'station-password'}).json()
    headers={'Authorization':'Bearer '+login['access_token']}
    assert client.get('/api/v1/events',headers=headers).status_code==200
    assert client.post('/api/v1/events',headers=headers,json={'name':'No','event_date':'2026-09-17'}).status_code==403
    assert client.post('/api/v1/auth/volunteers',headers=headers,json={'username':'station2','password':'station-password'}).status_code==403
    assert client.put(f'/api/v1/menu/items/{test_food_items[0].id}',headers=headers,json={'ticket':0}).status_code==403


def test_refresh_rotation_logout_and_password_upgrade(client,test_user,db_session):
    test_user.hashed_password=hash_password('testpass123','abc');db_session.commit()
    tokens=client.post('/api/v1/auth/login',data={'username':'testuser','password':'testpass123'}).json()
    assert db_session.get(User,test_user.id).hashed_password.startswith('$argon2id$')
    assert client.get('/api/v1/auth/me',headers={'Authorization':'Bearer '+tokens['refresh_token']}).status_code==401
    refreshed=client.post('/api/v1/auth/refresh',json={'refresh_token':tokens['refresh_token']})
    assert refreshed.status_code==200
    assert client.post('/api/v1/auth/refresh',json={'refresh_token':tokens['refresh_token']}).status_code==401
    headers={'Authorization':'Bearer '+refreshed.json()['access_token']}
    assert client.post('/api/v1/auth/logout',headers=headers).status_code==200
    assert client.get('/api/v1/auth/me',headers=headers).status_code==401


def test_password_change_revokes_sessions(client,auth_headers):
    assert client.post('/api/v1/auth/password',headers=auth_headers,json={'current_password':'wrong','new_password':'new-password-123'}).status_code==400
    assert client.post('/api/v1/auth/password',headers=auth_headers,json={'current_password':'testpass123','new_password':'new-password-123'}).status_code==200
    assert client.get('/api/v1/auth/me',headers=auth_headers).status_code==401
    assert client.post('/api/v1/auth/login',data={'username':'testuser','password':'new-password-123'}).status_code==200


def test_websocket_requires_auth_and_staff(client,auth_headers):
    with client.websocket_connect('/ws/kitchen/display') as ws:
        ws.send_json({'type':'authenticate','token':'invalid'})
        with pytest.raises(WebSocketDisconnect): ws.receive_json()
    with client.websocket_connect('/ws/admin/dashboard') as ws:
        ws.send_json({'type':'authenticate','token':auth_headers['Authorization'].split()[1]})
        with pytest.raises(WebSocketDisconnect): ws.receive_json()
    with client.websocket_connect('/ws/orders/updates') as ws:
        ws.send_json({'type':'authenticate','token':auth_headers['Authorization'].split()[1]})
        assert ws.receive_json()['type']=='authenticated'
        ws.send_json({'type':'ping'})
        assert ws.receive_json()['type']=='pong'


def test_checkout_rolls_back_partial_failure(client,staff_auth_headers,test_food_items,db_session):
    from sqlalchemy import event as sqlevent
    event,c=setup_event(client,staff_auth_headers,test_food_items)
    def fail(*args): raise RuntimeError('Simulated failed item insert')
    sqlevent.listen(OrderItem,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError,match='Simulated'):
            client.post(f"/api/v1/events/{event['id']}/checkout",headers=staff_auth_headers,json=payload(test_food_items))
    finally:
        sqlevent.remove(OrderItem,'before_insert',fail)
        db_session.rollback()
    assert db_session.query(Order).count()==0
    assert db_session.get(OrderCounter,1).value==0


def test_guest_handoff_permissions_and_inventory(client, staff_auth_headers, auth_headers, test_food_items):
    h=staff_auth_headers; event,c=setup_event(client,h,test_food_items)
    base=f"/api/v1/events/{event['id']}"
    data={**payload(test_food_items), 'tickets_collected':0}
    assert client.post(base+'/checkout',headers=auth_headers,json=payload(test_food_items)).status_code==403
    result=client.post(base+'/checkout',headers=auth_headers,json=data)
    assert result.status_code==200,result.text
    order=result.json(); assert order['awaiting_tickets'] and order['tickets_collected']==0
    assert client.post(base+'/checkout',headers=auth_headers,json=data).json()['id']==order['id']
    report=client.get(base+'/report',headers=h).json()
    assert report['order_count']==0 and report['voided_count']==0 and report['awaiting_ticket_count']==1
    assert Decimal(str(report['consumables'][0]['estimated_used']))==0
    assert client.get('/api/v1/operations/orders/pending',headers=h).json()==[]
    for path in ['/orders','/report','/stock']:
        assert client.get(base+path,headers=auth_headers).status_code==403
    confirm=base+f"/orders/{order['id']}/tickets"
    assert client.post(confirm,headers=auth_headers,json={'tickets_collected':2}).status_code==403
    assert client.post(base+f"/orders/{order['id']}/void",headers=auth_headers,json={'reason':'No thanks'}).status_code==403
    assert client.put(f"/api/v1/orders/{order['id']}/status",headers=h,json={'status':'preparing'}).status_code==409
    assert client.post('/api/v1/orders/checkout',headers=auth_headers,json={'customer_name':'Bypass'}).status_code==409
    assert client.post(confirm,headers=h,json={'tickets_collected':1}).status_code==409
    first=client.post(confirm,headers=h,json={'tickets_collected':2}).json()
    second=client.post(confirm,headers=h,json={'tickets_collected':2}).json()
    assert first['tickets_confirmed_at']==second['tickets_confirmed_at']
    assert first['tickets_confirmed_by'] and not first['awaiting_tickets']
    assert client.post(base+'/checkout',headers=auth_headers,json=data).json()['id']==order['id']
    report=client.get(base+'/report',headers=h).json()
    assert report['order_count']==1 and report['awaiting_ticket_count']==0 and report['tickets_collected']==2
    assert Decimal(str(report['consumables'][0]['estimated_used']))==Decimal('251')
    assert client.put(f"/api/v1/orders/{order['id']}/status",headers=h,json={'status':'preparing'}).status_code==200


def test_guest_void_and_closed_event(client, staff_auth_headers, auth_headers, test_food_items):
    h=staff_auth_headers; event,c=setup_event(client,h,test_food_items)
    base=f"/api/v1/events/{event['id']}"
    order=client.post(base+'/checkout',headers=auth_headers,json={**payload(test_food_items),'tickets_collected':0}).json()
    assert client.patch(base+'/state',headers=h,json={'closed':True}).status_code==409
    assert client.post(base+f"/orders/{order['id']}/void",headers=h,json={'reason':'Guest left'}).status_code==200
    assert client.post(base+f"/orders/{order['id']}/tickets",headers=h,json={'tickets_collected':2}).status_code==409
    report=client.get(base+'/report',headers=h).json()
    assert report['voided_count']==1 and report['awaiting_ticket_count']==0 and report['order_count']==0
    assert client.patch(base+'/state',headers=h,json={'closed':True}).status_code==200
    assert client.get('/api/v1/events',headers=auth_headers).json()==[]


def test_guest_tablet_account(client, staff_auth_headers, auth_headers):
    data={'username':'guest-tablet-1','password':'guest-tablet-password'}
    assert client.post('/api/v1/auth/guest-stations',headers=auth_headers,json=data).status_code==403
    result=client.post('/api/v1/auth/guest-stations',headers=staff_auth_headers,json=data)
    assert result.status_code==200,result.text
    assert not result.json()['is_staff'] and not result.json()['is_admin']


def make_room(client, headers, event, name, foods):
    base=f"/api/v1/events/{event['id']}"
    result=client.post(base+'/rooms',headers=headers,json={'name':name})
    assert result.status_code==200,result.text
    room=result.json()
    assert client.put(base+f"/rooms/{room['id']}/menu",headers=headers,json={'food_item_ids':[f.id for f in foods]}).status_code==200
    return room


def test_rooms_isolate_menu_checkout_queue_and_stock(client,staff_auth_headers,test_food_items):
    h=staff_auth_headers; event,c=setup_event(client,h,test_food_items)
    base=f"/api/v1/events/{event['id']}"
    wings=make_room(client,h,event,'Wings',test_food_items[:1])
    sandwiches=make_room(client,h,event,'Sandwiches',test_food_items[1:2])
    data={**payload(test_food_items),'room_id':wings['id']}
    assert client.post(base+'/checkout',headers=h,json=payload(test_food_items)).status_code==409
    assert client.post(base+'/checkout',headers=h,json={**data,'room_id':sandwiches['id']}).status_code==409
    first=client.post(base+'/checkout',headers=h,json=data)
    assert first.status_code==200,first.text
    order=first.json(); assert order['room_id']==wings['id']
    assert client.post(base+'/checkout',headers=h,json=data).json()['id']==order['id']
    assert client.get(base+f"/orders?room_id={wings['id']}",headers=h).json()[0]['id']==order['id']
    assert client.get(base+f"/orders?room_id={sandwiches['id']}",headers=h).json()==[]
    assert client.get(base+'/orders?room_id=0',headers=h).json()==[]
    assert client.put(f"/api/v1/orders/{order['id']}/status?room_id={sandwiches['id']}",headers=h,json={'status':'preparing'}).status_code==409
    assert client.post(base+f"/orders/{order['id']}/void?room_id={sandwiches['id']}",headers=h,json={'reason':'Wrong room'}).status_code==409
    assert client.post(base+'/stock',headers=h,json={'room_id':wings['id'],'consumable_id':c['id'],'quantity':500,'reason':'Room starting stock'}).status_code==200
    report=client.get(base+f"/report?room_id={wings['id']}",headers=h).json()
    assert report['room_name']=='Wings' and report['order_count']==1
    assert Decimal(str(report['consumables'][0]['estimated_remaining']))==Decimal('249')
    assert client.get(base+f"/report?room_id={sandwiches['id']}",headers=h).json()['consumables']==[]
    total=client.get(base+'/report',headers=h).json()
    assert Decimal(str(total['consumables'][0]['stock_added']))==1500
    shared=client.get(base+'/report?room_id=0',headers=h).json()
    assert shared['order_count']==0 and Decimal(str(shared['consumables'][0]['stock_added']))==1000
    assert 'Room,Wings' in client.get(base+f"/report.csv?room_id={wings['id']}",headers=h).text


def test_room_guest_collection_and_event_boundary(client,staff_auth_headers,auth_headers,test_food_items):
    h=staff_auth_headers; event,c=setup_event(client,h,test_food_items)
    a=make_room(client,h,event,'Wings',test_food_items[:1]);b=make_room(client,h,event,'Sandwiches',test_food_items[:1])
    other=client.post('/api/v1/events',headers=h,json={'name':'Other','event_date':'2026-09-26'}).json()
    base=f"/api/v1/events/{event['id']}"
    guest={**payload(test_food_items),'tickets_collected':0,'room_id':a['id']}
    order=client.post(base+'/checkout',headers=auth_headers,json=guest).json()
    assert client.post(f"/api/v1/events/{other['id']}/checkout",headers=h,json={**payload(test_food_items),'room_id':a['id']}).status_code==404
    assert client.get(f"/api/v1/events/{other['id']}/orders?room_id={a['id']}",headers=h).status_code==404
    url=base+f"/orders/{order['id']}/tickets"
    assert client.post(url+f"?room_id={b['id']}",headers=h,json={'tickets_collected':2}).status_code==409
    assert client.post(url+f"?room_id={a['id']}",headers=h,json={'tickets_collected':2}).status_code==200
    assert client.post(base+'/checkout',headers=auth_headers,json={**guest,'room_id':b['id']}).status_code==409
    assert client.put(f"/api/v1/orders/{order['id']}/status?room_id={a['id']}",headers=h,json={'status':'preparing'}).status_code==200
    assert client.post(base+'/rooms',headers=auth_headers,json={'name':'No'}).status_code==403
    assert client.put(base+f"/rooms/{a['id']}/menu",headers=auth_headers,json={'food_item_ids':[]}).status_code==403


def test_adding_rooms_preserves_old_order_retries_and_unassigned_queue(client,staff_auth_headers,test_food_items):
    h=staff_auth_headers;event,c=setup_event(client,h,test_food_items)
    base=f"/api/v1/events/{event['id']}";data=payload(test_food_items)
    old=client.post(base+'/checkout',headers=h,json=data).json()
    room=make_room(client,h,event,'Wings',test_food_items[:1])
    assert client.post(base+'/checkout',headers=h,json=data).json()['id']==old['id']
    assert client.get(base+'/orders?room_id=0',headers=h).json()[0]['id']==old['id']
    assert client.get(base+f"/orders?room_id={room['id']}",headers=h).json()==[]
    assert client.post(base+'/rooms',headers=h,json={'name':' wings '}).status_code==409
    assert client.post(base+'/rooms',headers=h,json={'name':'   '}).status_code==422
    assert client.put(base+f"/rooms/{room['id']}/menu",headers=h,json={'food_item_ids':[999999]}).status_code==404
    assert client.put(base+f"/rooms/{room['id']}/menu",headers=h,json={'food_item_ids':[]}).status_code==200
    assert client.post(base+'/checkout',headers=h,json={**data,'checkout_key':'fresh-order-key','room_id':room['id']}).status_code==409
