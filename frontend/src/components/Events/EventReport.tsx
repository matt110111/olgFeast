import React, { useCallback, useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { DinnerEvent, EventReportData, errorMessage, eventApi, roomQuery } from './eventApi';

export function EventReport({ event, roomId, roomName }: { event: DinnerEvent; roomId?: number; roomName?: string }) {
  const [report, setReport] = useState<EventReportData | null>(null);
  const [error, setError] = useState('');
  const load = useCallback(async () => { try { setReport(await eventApi.report(event.id, roomId)); setError(''); } catch (e) { setError(errorMessage(e)); } }, [event.id, roomId]);
  useEffect(() => { void load(); }, [load]);
  async function download() {
    try {
      const blob = await apiService.download(`/events/${event.id}/report.csv${roomQuery(roomId)}`);
      const url = URL.createObjectURL(blob); const link = document.createElement('a');
      link.href = url; link.download = `event-${event.id}${roomId === undefined ? '' : `-room-${roomId}`}-report.csv`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) { setError(errorMessage(e)); }
  }
  return <><div className="section-heading"><div><h2>{event.name} report</h2><p className="muted">{roomName || 'Whole event'} · Tickets, portions, and consumables.</p></div><div className="actions"><button onClick={load}>Refresh</button><button className="primary" onClick={download}>Download CSV</button></div></div>
    {error && <p className="notice error" role="alert">{error}</p>}
    {report && <><div className="metrics">{[['Kitchen orders',report.order_count],['Tickets owed',report.tickets_owed],['Tickets collected',report.tickets_collected],['Portions served',report.portions.reduce((n,p)=>n+p.served,0)]].map(([name,value]) => <div className="panel metric" key={name}><span>{name}</span><strong>{value}</strong></div>)}</div>
      {!!report.awaiting_ticket_count && <p className="notice">{report.awaiting_ticket_count} guest orders await collection of {report.awaiting_ticket_total} tickets. They are excluded from accepted order totals and depletion until a volunteer confirms collection.</p>}
      {!!report.voided_count && <p className="notice">{report.voided_count} voided orders are excluded. {report.voided_tickets_to_return} tickets were collected on those orders; reconcile their return separately.</p>}
      <div className="panel"><h3>Portions</h3><div className="table-scroll"><table><thead><tr><th>Menu item</th><th>Ordered</th><th>Served</th><th>Tickets owed</th></tr></thead><tbody>{report.portions.map(p=><tr key={p.name}><td>{p.name}</td><td>{p.ordered}</td><td>{p.served}</td><td>{p.tickets}</td></tr>)}</tbody></table></div>{!report.portions.length && <p>No orders recorded yet.</p>}</div>
      <div className="panel"><h3>Estimated consumable depletion</h3><p className="muted">Recipe quantities × accepted portions, excluding voids and orders awaiting tickets. Includes food still being prepared. Actual use can differ because of waste and portion sizes. Stock adjustments account for replenishment, waste, and counts.</p>
        {!!report.items_without_recipes.length && <p className="notice">Missing recipe snapshots: {report.items_without_recipes.join(', ')}. Their ingredients and supplies are not included. Configure recipes before taking further orders.</p>}
        <div className="table-scroll"><table><thead><tr><th>Ingredient / supply</th><th>Unit</th><th>Net stock added</th><th>Estimated used</th><th>Estimated remaining</th></tr></thead><tbody>{report.consumables.map(c=><tr key={c.id}><td>{c.name}</td><td>{c.unit}</td><td>{Number(c.stock_added).toLocaleString()}</td><td>{Number(c.estimated_used).toLocaleString()}</td><td className={Number(c.estimated_remaining)<0?'negative':''}>{Number(c.estimated_remaining).toLocaleString()}</td></tr>)}</tbody></table></div>
        {!report.consumables.length && <p>Add consumables, recipes, and starting stock in Setup to see estimates.</p>}
      </div></>}
  </>;
}
