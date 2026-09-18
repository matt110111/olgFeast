import React, { useCallback, useEffect, useState } from 'react';
import { DinnerEvent, EventOrder, errorMessage, eventApi, request, roomQuery } from './eventApi';

export function EventKitchen({ event, roomId }: { event: DinnerEvent; roomId?: number }) {
  const [orders, setOrders] = useState<EventOrder[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState<number | null>(null);
  const [updated, setUpdated] = useState('');
  const load = useCallback(async () => {
    try { setOrders(await eventApi.orders(event.id, roomId)); setError(''); setUpdated(new Date().toLocaleTimeString()); }
    catch (e) { setError(errorMessage(e)); }
  }, [event.id, roomId]);
  useEffect(() => { void load(); const timer = setInterval(load, 5000); return () => clearInterval(timer); }, [load]);
  async function advance(order: EventOrder, status: string) {
    setBusy(order.id);
    try { await request('PUT', `/orders/${order.id}/status${roomQuery(roomId)}`, { status }); await load(); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(null); }
  }
  async function voidOrder(order: EventOrder) {
    const reason = window.prompt(`Void order #${order.display_id}? Return ${order.tickets_collected} collected tickets. Enter a reason:`);
    if (!reason) return;
    setBusy(order.id);
    try { await request('POST', `/events/${event.id}/orders/${order.id}/void${roomQuery(roomId)}`, { reason }); await load(); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(null); }
  }
  return <><div className="section-heading"><h2>Kitchen queue</h2><span role="status">{updated ? `Updated ${updated} · refreshes every 5 seconds` : 'Loading…'}</span><button onClick={load}>Refresh</button></div>
    {error && <p className="notice error" role="alert">{error} The queue may be out of date.</p>}
    <div className="kitchen-grid">{[['pending','New orders','preparing','Start preparing'],['preparing','Preparing','ready','Mark ready'],['ready','Ready for pickup','complete','Mark served']].map(([status,title,next,label]) => {
      const queue = orders.filter(o => o.status === status && !o.voided_at && !o.awaiting_tickets).reverse();
      return <section key={status} className={`kitchen-column ${status}`}><h3>{title} <span>{queue.length}</span></h3>{queue.length === 0 && <p className="muted">No orders here.</p>}
        {queue.map(o => <article className="panel kitchen-order" key={o.id}><div className="section-heading"><strong className="order-number">#{o.display_id}</strong><span>{Math.max(0, Math.floor((Date.now() - new Date(o.date_ordered).getTime()) / 60000))} min</span></div><h4>{o.customer_name}</h4>{o.check_id && <p className="muted">Check #{o.check_id} · Input {o.station_number}</p>}
          <ul>{o.order_items.map(i => <li key={i.id}><strong>{i.quantity}×</strong> {i.item_name || i.food_item.name}</li>)}</ul>
          <button className="primary full" disabled={busy !== null || !!error} onClick={() => advance(o, next)}>{busy === o.id ? 'Saving…' : label}</button>
          {status === 'pending' && <button className="full" disabled={busy !== null || !!error} onClick={() => voidOrder(o)}>Void unprepared order</button>}
        </article>)}
      </section>;
    })}</div></>;
}
