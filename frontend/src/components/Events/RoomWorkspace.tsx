import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DinnerEvent, EventRoom, FoodItem, eventApi, errorMessage, request } from './eventApi';
import { EventStation } from './EventStation';
import { EventTickets } from './EventTickets';
import { EventKitchen } from './EventKitchen';
import { EventReport } from './EventReport';
import { EventSetup } from './EventSetup';

export function RoomWorkspace({ event, foods, connected, tab, onRefresh, onCreated }: {
  event: DinnerEvent; foods: FoodItem[]; connected: boolean; tab: string;
  onRefresh: () => Promise<void>; onCreated: (id: number) => void;
}) {
  const { user } = useAuth();
  const storage = `event-room:${user?.id}:${event.id}`;
  const [rooms, setRooms] = useState<EventRoom[]>([]);
  const [stationNumber, setStationNumber] = useState(() => Math.max(1, Math.min(6, Number(localStorage.getItem(`input-station:${user?.id}`)) || Number(user?.username?.match(/^input([1-6])$/)?.[1]) || 1)));
  useEffect(() => { localStorage.setItem(`input-station:${user?.id}`, String(stationNumber)); }, [stationNumber, user?.id]);
  const [selected, setSelected] = useState<number | null>(() => {
    const saved = localStorage.getItem(storage); return saved === null ? null : Number(saved);
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [wholeEvent, setWholeEvent] = useState(false);
  const refresh = useCallback(async () => {
    try {
      const next = await eventApi.rooms(event.id); setRooms(next); setError('');
      setSelected(current => next.some(r => r.id === current) || (current === 0 && user?.is_staff) ? current : next[(Number(user?.username?.match(/^kitchen([1-4])$/)?.[1]) || 1) - 1]?.id ?? next[0]?.id ?? 0);
    } catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  }, [event.id, user?.is_staff, user?.username]);
  useEffect(() => { void refresh(); const timer = setInterval(refresh, 15000); return () => clearInterval(timer); }, [refresh]);
  useEffect(() => { if (selected !== null) localStorage.setItem(storage, String(selected)); }, [storage, selected]);
  const room = rooms.find(r => r.id === selected);
  const roomId = rooms.length ? selected ?? 0 : undefined;
  const roomName = room?.name || (rooms.length ? 'Unassigned / shared' : undefined);
  const scope = `${event.id}:${roomId}`;
  if (loading) return <p role="status">Loading rooms…</p>;
  return <>
    {error && <p className="notice error" role="alert">{error} Room data may be out of date. <button onClick={refresh}>Refresh rooms</button></p>}
    {!!rooms.length && !(tab === 'order' && user?.is_staff) && <div className="room-bar"><label>Kitchen<select aria-label="Kitchen" value={selected ?? 0} onChange={e => { setSelected(Number(e.target.value)); setWholeEvent(false); }}>
      {user?.is_staff && <option value={0}>Unassigned orders / shared stock</option>}
      {rooms.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
    </select></label><div><h2>{roomName}</h2><p className="muted">This kitchen shows only its assigned food, orders, and stock.</p></div></div>}
    {tab === 'order' && <>
      {user?.is_staff && !!rooms.length && <div className="input-bar"><label>Input station<select aria-label="Input station" value={stationNumber} onChange={e => setStationNumber(Number(e.target.value))}>{[1,2,3,4,5,6].map(n => <option key={n} value={n}>Input {n}</option>)}</select></label><p>Full menu · {rooms.length} kitchens · collect tickets here</p></div>}
      <EventStation key={user?.is_staff && rooms.length ? `input:${stationNumber}` : scope} event={event} foods={user?.is_staff ? rooms.length ? foods.filter(f => rooms.some(r => r.food_item_ids.includes(f.id))) : foods : room ? foods.filter(f => room.food_item_ids.includes(f.id)) : foods} connected={connected && !error} guest={!user?.is_staff} rooms={rooms} stationNumber={user?.is_staff && rooms.length ? stationNumber : undefined} roomId={user?.is_staff && rooms.length ? undefined : roomId} roomName={roomName} allowNewOrders={!!user?.is_staff || !rooms.length || !!room} />
    </>}
    {tab === 'tickets' && user?.is_staff && <EventTickets key={scope} event={event} roomId={roomId} />}
    {tab === 'kitchen' && user?.is_staff && <EventKitchen key={scope} event={event} roomId={roomId} />}
    {tab === 'report' && user?.is_admin && <>
      {!!rooms.length && <label className="check-row"><input type="checkbox" checked={wholeEvent} onChange={e => setWholeEvent(e.target.checked)} />Show whole-event totals across all rooms and shared stock</label>}
      <EventReport key={`${scope}:${wholeEvent}`} event={event} roomId={wholeEvent ? undefined : roomId} roomName={wholeEvent ? 'Whole event' : roomName} />
    </>}
    {tab === 'setup' && user?.is_admin && <>
      <RoomSetup event={event} rooms={rooms} room={room} foods={foods} onRefresh={refresh} onCreated={setSelected} />
      <EventSetup key={scope} event={event} foods={foods} roomId={roomId} roomName={roomName} onRefresh={onRefresh} onCreated={onCreated} />
    </>}
  </>;
}

function RoomSetup({ event, rooms, room, foods, onRefresh, onCreated }: {
  event: DinnerEvent; rooms: EventRoom[]; room?: EventRoom; foods: FoodItem[];
  onRefresh: () => Promise<void>; onCreated: (id: number) => void;
}) {
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  async function action(fn: () => Promise<void>) {
    setBusy(true); setError(''); setMessage('');
    try { await fn(); await onRefresh(); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return <div className="panel">
    <h2>Menu & kitchens</h2><p>Assign each menu item to exactly one kitchen: Fried, Grilled, Cooked 1, or Cooked 2. All six input stations share the full menu. One ticket collection sends each item to its kitchen.</p>
    {error && <p className="notice error" role="alert">{error}</p>}{message && <p className="notice success" role="status">{message}</p>}
    <form onSubmit={e => {
      e.preventDefault(); const form = e.currentTarget; const data = new FormData(form);
      void action(async () => { const created = await request<EventRoom>('POST', `/events/${event.id}/rooms`, { name: data.get('name') }); onCreated(created.id); form.reset(); setMessage('Kitchen created. Assign its menu below.'); });
    }}><label>New kitchen name<input name="name" required maxLength={100} placeholder="Fried / Grilled / Cooked 1 / Cooked 2" /></label><button className="primary" disabled={busy || event.closed}>Create kitchen</button></form>
    {room && <form key={`${room.id}:${room.food_item_ids.join(',')}`} onSubmit={e => {
      e.preventDefault(); const data = new FormData(e.currentTarget);
      void action(async () => { await request('PUT', `/events/${event.id}/rooms/${room.id}/menu`, { food_item_ids: data.getAll('food').map(Number) }); setMessage('Kitchen menu saved.'); });
    }}><h3>Menu for {room.name}</h3><p className="muted">Ticket values, availability, and recipes are edited below. Assign each food to one kitchen so input stations can route it automatically.</p>
      <div className="room-menu-list">{foods.map(f => <label className="check-row" key={f.id}><input name="food" type="checkbox" value={f.id} defaultChecked={room.food_item_ids.includes(f.id)} />{f.name} · {f.ticket} tickets{f.is_available ? '' : ' · unavailable'}</label>)}</div>
      <button className="primary" disabled={busy || event.closed}>Save kitchen menu</button>
    </form>}
    {!rooms.length && <p className="muted">Until rooms are added, this event uses one shared menu and kitchen.</p>}
  </div>;
}
