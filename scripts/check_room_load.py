"""Run 48 authenticated clients against an explicitly isolated test server."""
import asyncio
import json
import os
import time
import uuid
import httpx

if os.environ.get('E2E_ALLOW_TEST_WRITES') != '1':
    raise SystemExit('Set E2E_ALLOW_TEST_WRITES=1 only for an isolated test database')
BASE = os.environ.get('E2E_API_URL', 'http://127.0.0.1:8002')
CLIENTS = 48


async def main():
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=100)
    async with httpx.AsyncClient(base_url=BASE, timeout=30, limits=limits) as client:
        async def call(method, path, headers=None, **kwargs):
            r = await client.request(method, '/api/v1' + path, headers=headers, **kwargs)
            r.raise_for_status()
            return r.json()
        login = await call('POST', '/auth/login', data={'username': 'admin', 'password': os.environ['E2E_ADMIN_PASSWORD']})
        admin = {'Authorization': 'Bearer ' + login['access_token']}
        async def post(path, data):
            return await call('POST', path, admin, json=data)
        tag = uuid.uuid4().hex[:10]
        event = await post('/events', {'name': '48 tablet check ' + tag, 'event_date': '2026-09-26'})
        rooms = []
        for name in ['Wings', 'Sandwiches']:
            food = await post('/menu/items', {'name': name + ' ' + tag, 'food_group': 'Load check', 'ticket': 3, 'value': 0, 'is_available': True})
            room = await post(f"/events/{event['id']}/rooms", {'name': name})
            await call('PUT', f"/events/{event['id']}/rooms/{room['id']}/menu", admin, json={'food_item_ids': [food['id']]})
            consumable = await post('/events/setup/consumables', {'name': name + ' plate ' + tag, 'unit': 'each'})
            await call('PUT', f"/events/setup/recipes/{food['id']}", admin, json=[{'consumable_id': consumable['id'], 'quantity': 1}])
            await post(f"/events/{event['id']}/stock", {'room_id': room['id'], 'consumable_id': consumable['id'], 'quantity': 1000, 'reason': 'Load check stock'})
            rooms.append((room, food))
        people = []
        # Deliberately outside the timed phases: normal users sign in before service.
        for i in range(CLIENTS):
            username = f'load-{tag}-{i}'
            await post('/auth/volunteers', {'username': username, 'password': 'isolated-load-password'})
            token = await call('POST', '/auth/login', data={'username': username, 'password': 'isolated-load-password'})
            people.append({'Authorization': 'Bearer ' + token['access_token']})
        results = {}
        async def phase(name, operation):
            latencies = []
            async def run(i):
                start = time.perf_counter()
                value = await operation(i)
                latencies.append(time.perf_counter() - start)
                return value
            start = time.perf_counter()
            values = await asyncio.gather(*(run(i) for i in range(CLIENTS)))
            latencies.sort()
            results[name] = {'requests': CLIENTS, 'elapsed_s': round(time.perf_counter() - start, 3),
                             'p95_s': round(latencies[int(len(latencies) * .95) - 1], 3), 'max_s': round(max(latencies), 3)}
            return values
        payloads = [{'customer_name': f'Table {i}', 'checkout_key': f'{tag}-{i}', 'room_id': rooms[i % 2][0]['id'],
                     'tickets_collected': 3, 'items': [{'food_item_id': rooms[i % 2][1]['id'], 'quantity': 1}]} for i in range(CLIENTS)]
        async def checkout(i):
            return await call('POST', f"/events/{event['id']}/checkout", people[i], json=payloads[i])
        orders = await phase('48_simultaneous_checkouts', checkout)
        assert len({o['id'] for o in orders}) == CLIENTS
        assert len({o['display_id'] for o in orders}) == CLIENTS
        retries = await phase('48_simultaneous_retries', checkout)
        assert [o['id'] for o in retries] == [o['id'] for o in orders]
        async def poll(i):
            room = rooms[i % 2][0]
            rows = await call('GET', f"/events/{event['id']}/orders?room_id={room['id']}", people[i])
            assert len(rows) == CLIENTS // 2 and all(o['room_id'] == room['id'] for o in rows)
            await call('GET', '/events', people[i])
            await call('GET', f"/events/{event['id']}/rooms", people[i])
            await call('GET', '/menu/items', people[i])
        for wave in range(3):
            await phase(f'48_tablets_refresh_wave_{wave + 1}', poll)
            if wave < 2:
                await asyncio.sleep(5)
        for status in ['preparing', 'ready', 'complete']:
            async def advance(i):
                return await call('PUT', f"/orders/{orders[i]['id']}/status?room_id={orders[i]['room_id']}", people[i], json={'status': status})
            await phase('48_' + status, advance)
        total = await call('GET', f"/events/{event['id']}/report", admin)
        assert total['order_count'] == CLIENTS and total['tickets_collected'] == CLIENTS * 3
        assert sum(p['served'] for p in total['portions']) == CLIENTS
        for room, food in rooms:
            report = await call('GET', f"/events/{event['id']}/report?room_id={room['id']}", admin)
            assert report['order_count'] == CLIENTS // 2 and report['tickets_collected'] == CLIENTS // 2 * 3
            assert float(report['consumables'][0]['estimated_used']) == CLIENTS // 2
            assert float(report['consumables'][0]['estimated_remaining']) == 1000 - CLIENTS // 2
        print(json.dumps({'clients': CLIENTS, 'rooms': 2, 'errors': 0, 'orders': CLIENTS, 'metrics': results}, indent=2))


asyncio.run(main())
