"""Integration check for an isolated rehearsal database, never production."""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
import httpx

base=os.environ.get('E2E_API_URL','http://127.0.0.1:8002')
if not os.environ.get('E2E_ALLOW_TEST_WRITES'):
    raise SystemExit('Set E2E_ALLOW_TEST_WRITES=1 only for an isolated test database')
with httpx.Client(base_url=base,timeout=30) as client:
    login=client.post('/api/v1/auth/login',data={'username':'admin','password':os.environ['E2E_ADMIN_PASSWORD']})
    login.raise_for_status(); headers={'Authorization':'Bearer '+login.json()['access_token']}
    client.headers.update(headers)
    def post(path,data):
        response=client.post('/api/v1'+path,json=data); response.raise_for_status(); return response.json()
    event=post('/events',{'name':'Concurrent tablets '+uuid.uuid4().hex[:8],'event_date':'2026-09-17'})
    food=post('/menu/items',{'name':'Concurrency dinner','food_group':'Checks','ticket':2,'value':0})
    consumable=post('/events/setup/consumables',{'name':'Concurrency plate '+uuid.uuid4().hex[:8],'unit':'each'})
    response=client.put(f"/api/v1/events/setup/recipes/{food['id']}",json=[{'consumable_id':consumable['id'],'quantity':1}]);response.raise_for_status()
    payload={'customer_name':'Concurrent guest','checkout_key':uuid.uuid4().hex,'tickets_collected':4,'items':[{'food_item_id':food['id'],'quantity':2}]}
    def send(data):
        response=httpx.post(base+f"/api/v1/events/{event['id']}/checkout",headers=headers,json=data,timeout=30)
        response.raise_for_status();return response.json()
    with ThreadPoolExecutor(max_workers=12) as pool:
        retried=list(pool.map(send,[payload]*12))
    assert len({r['id'] for r in retried})==1
    with ThreadPoolExecutor(max_workers=12) as pool:
        distinct=list(pool.map(send,[{**payload,'checkout_key':uuid.uuid4().hex} for _ in range(12)]))
    assert len({r['display_id'] for r in distinct})==12
    report=client.get(f"/api/v1/events/{event['id']}/report").json()
    assert report['order_count']==13 and report['tickets_owed']==52
    assert float(report['consumables'][0]['estimated_used'])==26
    print('PASS: 12 simultaneous retries create one order; 12 distinct submissions get unique numbers; tickets and consumption reconcile.')
    station=post('/auth/guest-stations',{'username':'guest-'+uuid.uuid4().hex[:12],'password':'isolated-guest-password'})
    guest_login=httpx.post(base+'/api/v1/auth/login',data={'username':station['username'],'password':'isolated-guest-password'})
    guest_login.raise_for_status()
    guest_headers={'Authorization':'Bearer '+guest_login.json()['access_token']}
    response=httpx.post(base+f"/api/v1/events/{event['id']}/checkout",headers=guest_headers,json={**payload,'tickets_collected':0,'checkout_key':uuid.uuid4().hex})
    response.raise_for_status();guest_order=response.json()
    def collect(_):
        response=httpx.post(base+f"/api/v1/events/{event['id']}/orders/{guest_order['id']}/tickets",headers=headers,json={'tickets_collected':4},timeout=30)
        response.raise_for_status();return response.json()
    with ThreadPoolExecutor(max_workers=12) as pool:
        confirmations=list(pool.map(collect,range(12)))
    assert len({order['tickets_confirmed_at'] for order in confirmations})==1
    report=client.get(f"/api/v1/events/{event['id']}/report").json()
    assert report['order_count']==14 and report['tickets_collected']==56 and report['awaiting_ticket_count']==0
    assert float(report['consumables'][0]['estimated_used'])==28
    print('PASS: 12 simultaneous volunteer confirmations collect guest tickets exactly once.')
