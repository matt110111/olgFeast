import React, { useCallback, useEffect, useState } from 'react';
import { DinnerEvent, EventOrder, errorMessage, eventApi, request, roomQuery } from './eventApi';

export function EventTickets({ event, roomId }: { event: DinnerEvent; roomId?: number }) {
  const [orders, setOrders] = useState<EventOrder[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmed, setConfirmed] = useState<number[]>([]);
  const [message, setMessage] = useState('');
  const load = useCallback(async () => {
    try { setOrders((await eventApi.orders(event.id, roomId)).filter(o => o.awaiting_tickets)); setError(''); }
    catch (e) { setError(errorMessage(e)); }
  }, [event.id, roomId]);
  useEffect(() => { void load(); const timer = setInterval(load, 5000); return () => clearInterval(timer); }, [load]);
  async function collect(order: EventOrder) {
    if (busy) return;
    setBusy(true); setMessage('');
    try {
      await request('POST', `/events/${event.id}/orders/${order.id}/tickets${roomQuery(roomId)}`, {
        tickets_collected: order.order_items.reduce((n, i) => n + i.quantity * i.unit_tickets, 0),
      });
      setMessage(`Order #${order.display_id}: tickets confirmed and sent to the kitchen.`);
      setConfirmed(c => c.filter(id => id !== order.id)); await load();
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  async function cancel(order: EventOrder) {
    const reason = window.prompt(`Cancel order #${order.display_id}? Return any tickets you physically collected. Enter a reason:`);
    if (!reason) return;
    setBusy(true);
    try { await request('POST', `/events/${event.id}/orders/${order.id}/void${roomQuery(roomId)}`, { reason }); await load(); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return <>
    <div className="section-heading"><div><h2>Collect guest tickets</h2><p>Match the guest’s order number, collect the physical tickets, then release the order to the kitchen.</p></div><button onClick={load}>Refresh</button></div>
    <p className="muted">If a confirmation response is lost, refresh first. Confirmed orders leave this list. Retrying confirmation is safe; do not collect tickets twice.</p>
    {error && <p className="notice error" role="alert">{error}</p>}
    {message && <p className="notice success" role="status">{message}</p>}
    {!orders.length && !error && <div className="panel">No guest orders awaiting tickets.</div>}
    <div className="food-grid">{orders.slice().reverse().map(o => {
      const total = o.order_items.reduce((n, i) => n + i.quantity * i.unit_tickets, 0);
      return <article className="panel" key={o.id}>
        <strong className="order-number">#{o.display_id}</strong><h3>{o.customer_name}</h3>
        <ul>{o.order_items.map(i => <li key={i.id}>{i.quantity}× {i.item_name}</li>)}</ul>
        <div className="ticket-total"><span>Tickets owed</span><strong>{total}</strong></div>
        <label className="check-row"><input type="checkbox" checked={confirmed.includes(o.id)} disabled={busy} onChange={e => setConfirmed(c => e.target.checked ? [...c, o.id] : c.filter(id => id !== o.id))} />I collected {total} tickets for #{o.display_id}</label>
        <button className="primary full" disabled={busy || !!error || !confirmed.includes(o.id)} onClick={() => collect(o)}>Confirm tickets and send to kitchen</button>
        <button className="full" disabled={busy || !!error} onClick={() => cancel(o)}>Cancel uncollected order</button>
      </article>;
    })}</div>
  </>;
}
