import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Checkout, DinnerEvent, EventOrder, EventRoom, StationReceipt, FoodItem, errorMessage, eventApi, newKey } from './eventApi';

type Receipt = EventOrder | StationReceipt;
interface Draft { quantities: Record<number, number>; name: string; pending: Checkout | null; receipt?: Receipt | null }
export function EventStation({ event, foods, connected, guest = false, roomId, roomName, rooms = [], stationNumber, allowNewOrders = true }: {
  event: DinnerEvent; foods: FoodItem[]; connected: boolean; guest?: boolean; roomId?: number; roomName?: string;
  rooms?: EventRoom[]; stationNumber?: number; allowNewOrders?: boolean;
}) {
  const { user } = useAuth();
  const routed = stationNumber !== undefined && !guest;
  const collectHere = !guest && (routed || event.collect_tickets);
  const storage = `event-draft:${user?.id}:${event.id}${routed ? `:input:${stationNumber}` : roomId ? `:room:${roomId}` : ''}`;
  const [draft, setDraft] = useState<Draft>(() => {
    try { return JSON.parse(localStorage.getItem(storage) || '') as Draft; }
    catch { return { quantities: {}, name: '', pending: null }; }
  });
  const [checking, setChecking] = useState(!!draft.pending);
  const [category, setCategory] = useState('All');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(4);
  const [collected, setCollected] = useState(false);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const frame = useRef<HTMLDivElement>(null);
  const [error, setError] = useState('');
  const [storageError, setStorageError] = useState(false);
  useEffect(() => {
    try { localStorage.setItem(storage, JSON.stringify(draft)); setStorageError(false); }
    catch { setStorageError(true); }
  }, [draft, storage]);
  // Use the visible viewport, including Safari's browser controls and keyboard.
  useLayoutEffect(() => {
    const resize = () => {
      if (frame.current) {
        const height = Math.max(320, (window.visualViewport?.height || window.innerHeight) - frame.current.getBoundingClientRect().top - 12);
        frame.current.style.setProperty('--station-height', `${height}px`);
        setPageSize(height < 440 ? 2 : 4);
      }
    };
    resize(); window.addEventListener('resize', resize); window.visualViewport?.addEventListener('resize', resize);
    return () => { window.removeEventListener('resize', resize); window.visualViewport?.removeEventListener('resize', resize); };
  });
  const lines = foods.filter(f => draft.quantities[f.id] > 0);
  const total = lines.reduce((sum, f) => sum + f.ticket * draft.quantities[f.id], 0);
  const portions = lines.reduce((sum, f) => sum + draft.quantities[f.id], 0);
  const locked = busy || !!draft.pending || !allowNewOrders;
  const kitchenFor = (id: number) => rooms.filter(r => r.food_item_ids.includes(id));
  const invalidRouting = routed && lines.some(f => kitchenFor(f.id).length !== 1);
  const filtered = foods.filter(f => category === 'All' || (routed ? kitchenFor(f.id).some(r => r.name === category) : f.food_group === category));
  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, pages - 1);
  function quantity(id: number, delta: number) {
    if (locked) return;
    setCollected(false);
    setDraft(d => ({ ...d, receipt: null, quantities: { ...d.quantities, [id]: Math.max(0, Math.min(999, (d.quantities[id] || 0) + delta)) } }));
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busyRef.current || !connected || storageError || (!draft.pending && (!checking || !allowNewOrders || !lines.length || invalidRouting || (collectHere && !collected)))) return;
    busyRef.current = true; setBusy(true); setError('');
    const payload: Checkout = draft.pending || { ...(routed ? { station_number: stationNumber } : roomId ? { room_id: roomId } : {}), customer_name: draft.name.trim() || 'Walk-up', checkout_key: newKey(),
      items: lines.map(f => ({ food_item_id: f.id, quantity: draft.quantities[f.id] })), tickets_collected: collectHere ? total : 0 };
    const pending = { ...draft, pending: payload };
    try {
      localStorage.setItem(storage, JSON.stringify(pending)); setDraft(pending);
      const receipt = payload.station_number ? await eventApi.stationCheckout(event.id, payload) : await eventApi.checkout(event.id, payload);
      const empty = { quantities: {}, name: '', pending: null, receipt };
      localStorage.setItem(storage, JSON.stringify(empty)); setDraft(empty);
      setCollected(false); setChecking(false);
    } catch (e) {
      const status = (e as { response?: { status: number } })?.response?.status;
      if (status && [400, 409, 422].includes(status)) { setDraft(d => ({ ...d, pending: null })); setCollected(false); }
      setError(errorMessage(e));
    } finally { busyRef.current = false; setBusy(false); }
  }
  if (event.closed) return <div className="panel"><h2>This event is closed</h2><p>Reopen the event in Setup to take more orders.</p></div>;
  const receipt = draft.receipt;
  if (receipt) {
    const orders = 'orders' in receipt ? receipt.orders : [receipt];
    const awaiting = orders.some(o => o.awaiting_tickets);
    return <div className="receipt" role="status"><div><p>{awaiting ? 'Bring this number to the ticket desk' : 'Sent to kitchen'}</p><strong>{'orders' in receipt ? `Check #${receipt.id}` : `#${receipt.display_id}`}</strong>
      <p>{orders[0]?.customer_name} · {orders.reduce((n, o) => n + o.order_items.reduce((s, i) => s + i.quantity * i.unit_tickets, 0), 0)} tickets{awaiting ? ' to give the volunteer' : collectHere ? ' collected' : ' owed'}</p>
      {orders.map(o => <p key={o.id}>{rooms.find(r => r.id === o.room_id)?.name || roomName || 'Kitchen'} · order #{o.display_id}</p>)}
    </div><button onClick={() => { setDraft(d => ({ ...d, receipt: null })); setPage(0); }}>Next guest</button></div>;
  }
  return <div className="order-workflow" ref={frame}>
    {!allowNewOrders && <p className="notice">Choose a kitchen to start a new order.</p>}
    <nav className="order-steps" aria-label="Order steps"><button aria-current={!checking ? 'step' : undefined} disabled={!!draft.pending || busy} onClick={() => { setChecking(false); setCollected(false); }}>1. Menu</button><button aria-current={checking ? 'step' : undefined} disabled={!lines.length || busy} onClick={() => setChecking(true)}>2. Check & collect</button><span>3. Kitchen</span></nav>
    <div className={checking ? 'station-grid checking' : 'station-grid'}>
      {!checking && <section className={`menu-panel ${pageSize === 2 ? 'short-menu' : ''}`} aria-label="Food menu">
        <div className="menu-heading"><h2>Menu</h2><label className="menu-filter"><span className="sr-only">Filter menu</span><select aria-label="Filter menu" value={category} onChange={e => { setCategory(e.target.value); setPage(0); }}>
          {['All', ...(routed ? rooms.map(r => r.name) : Array.from(new Set(foods.map(f => f.food_group))))].map(c => <option key={c} value={c}>{c === 'All' ? 'All kitchens / full menu' : c}</option>)}
        </select></label></div>
        <div className="food-grid">{filtered.slice(currentPage * pageSize, currentPage * pageSize + pageSize).map(f => {
          const kitchens = kitchenFor(f.id); const assigned = !routed || kitchens.length === 1;
          return <button key={f.id} className="food-tile" disabled={!f.is_available || locked || !assigned} onClick={() => quantity(f.id, 1)} aria-label={`Add ${f.name}`}>
            <span className="food-category">{routed ? kitchens.map(r => r.name).join(' / ') || 'Needs kitchen assignment' : f.food_group}</span><strong>{f.name}</strong><span>{f.ticket} ticket{f.ticket === 1 ? '' : 's'}</span><span className="tile-count">{!f.is_available ? 'Unavailable' : !assigned ? 'Assign one kitchen in setup' : draft.quantities[f.id] ? `${draft.quantities[f.id]} in order · Add one` : '+ Add portion'}</span>
          </button>;
        })}</div>
        {!foods.length && <p>Add your dinner menu in Menu & kitchens.</p>}
        <div className="menu-pages"><button disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous</button><span role="status">{currentPage + 1} / {pages} · {filtered.length} items</span><button disabled={currentPage >= pages - 1} onClick={() => setPage(currentPage + 1)}>Next</button></div>
      </section>}
      <form className="panel checkout-panel" onSubmit={submit}>
        <div className="section-heading"><h2>{checking ? 'Check order' : 'Current order'}</h2><span>{portions} portions</span></div>
        {!checking && <label className="guest-name"><span className="sr-only">Guest name or table (optional)</span><input aria-label="Guest name or table (optional)" value={draft.name} disabled={locked} maxLength={100} placeholder="Walk-up" onChange={e => setDraft(d => ({ ...d, name: e.target.value }))} /></label>}
        {checking && <p className="check-guest">{draft.name || 'Walk-up'}{routed ? ` · Input ${stationNumber}` : ''}</p>}
        <div className="order-lines" aria-label="Order items">
          {!lines.length && <p className="muted">Tap a menu item to begin.</p>}
          {lines.map(f => <div className="order-line" key={f.id}><div><strong>{f.name}</strong><p>{f.ticket * draft.quantities[f.id]} tickets{routed ? ` · ${kitchenFor(f.id).map(r => r.name).join(', ')}` : ''}</p></div><div className="stepper"><button type="button" disabled={locked} aria-label={`Remove one ${f.name}`} onClick={() => quantity(f.id, -1)}>−</button><output aria-label={`${f.name} quantity`}>{draft.quantities[f.id]}</output><button type="button" disabled={locked} aria-label={`Add one ${f.name}`} onClick={() => quantity(f.id, 1)}>+</button></div></div>)}
        </div>
        <div className="checkout-footer">
          <div className="ticket-total"><span>{checking && collectHere ? 'Collect tickets here' : 'Tickets owed'}</span><strong>{draft.pending ? draft.pending.tickets_collected || total : total}</strong></div>
          {checking && collectHere && !draft.pending && <label className="check-row"><input type="checkbox" checked={collected} onChange={e => setCollected(e.target.checked)} disabled={busy || !lines.length} />I collected {total} tickets</label>}
          {checking && guest && event.collect_tickets && <p className="muted">For ticket collection here, sign in with a volunteer account.</p>}
          {storageError && <p role="alert" className="notice error">Enable browser storage before checkout.</p>}
          {error && <p role="alert" className="notice error">{error}</p>}
          {invalidRouting && <p role="alert" className="notice error">Assign each item to one kitchen in Menu & kitchens.</p>}
          {draft.pending && <p className="notice">Retry to recover this order. Do not collect tickets again.</p>}
          {!checking && !draft.pending ? <button key="review" type="button" className="primary full" disabled={!allowNewOrders || !lines.length || invalidRouting} onClick={e => { e.preventDefault(); setChecking(true); }}>Check order · {total} tickets</button> : <button key="send" type="submit" className="primary full" disabled={busy || !connected || storageError || (!draft.pending && (!allowNewOrders || !lines.length || invalidRouting || (collectHere && !collected)))}>{busy ? 'Sending…' : draft.pending ? 'Retry same order' : guest && event.collect_tickets ? 'Send to ticket desk' : 'Send to kitchen'}</button>}
          <div className="checkout-actions">{checking && !locked && <button type="button" onClick={() => { setChecking(false); setCollected(false); }}>Back to menu</button>}
          {!!lines.length && !locked && <button type="button" onClick={() => { if (window.confirm('Clear this unsubmitted order?')) { setDraft({ quantities: {}, name: '', pending: null }); setCollected(false); setChecking(false); } }}>Clear order</button>}</div>
        </div>
      </form>
    </div>
  </div>;
}
