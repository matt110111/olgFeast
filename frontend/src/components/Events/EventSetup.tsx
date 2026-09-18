import React, { useEffect, useState } from 'react';
import { Consumable, DinnerEvent, FoodItem, Recipe, errorMessage, eventApi, request, roomQuery } from './eventApi';

export function EventSetup({ event, foods, onRefresh, onCreated, roomId, roomName }: { event?: DinnerEvent; roomId?: number; roomName?: string; foods: FoodItem[]; onRefresh: () => Promise<void>; onCreated: (id: number) => void }) {
  const [consumables, setConsumables] = useState<Consumable[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [recipeFood, setRecipeFood] = useState(0);
  const [recipe, setRecipe] = useState<{ consumable_id: number; quantity: number }[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [menuId, setMenuId] = useState(0);
  const [history, setHistory] = useState<{ id: number; consumable_id: number; quantity: number; reason: string; created_at: string }[]>([]);
  async function load() {
    const [c, r] = await Promise.all([eventApi.consumables(), eventApi.recipes()]); setConsumables(c); setRecipes(r);
    if (event) setHistory(await request('GET', `/events/${event.id}/stock${roomQuery(roomId)}`));
  }
  useEffect(() => { void load().catch(e => setError(errorMessage(e))); }, [event?.id, roomId]);
  useEffect(() => { setRecipe(recipes.filter(r => r.food_item_id === recipeFood).map(r => ({ consumable_id: r.consumable_id, quantity: Number(r.quantity) }))); }, [recipes, recipeFood]);
  async function action(fn: () => Promise<void>, success: string) {
    setBusy(true); setError(''); setMessage('');
    try { await fn(); await load(); await onRefresh(); setMessage(success); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  function form(e: React.FormEvent<HTMLFormElement>) { e.preventDefault(); return new FormData(e.currentTarget); }
  const menu = foods.find(f => f.id === menuId);
  return <div className="setup-grid">
    <div className="setup-feedback">{error && <p className="notice error" role="alert">{error}</p>}{message && <p className="notice success" role="status">{message}</p>}</div>
    <form className="panel" onSubmit={e => { const data=form(e); void action(async () => { const result=await request<DinnerEvent>('POST','/events',{ name:data.get('name'),event_date:data.get('date'),collect_tickets:data.get('collect')==='on' }); onCreated(result.id); },'Event created'); }}>
      <h2>Create a dinner event</h2><label>Event name<input name="name" required maxLength={100} placeholder="Friday community dinner" /></label>
      <label>Date<input name="date" type="date" required defaultValue={new Date().toLocaleDateString('en-CA')} /></label>
      <label className="check-row"><input name="collect" type="checkbox" defaultChecked />Require ticket collection confirmation at checkout</label>
      <button disabled={busy} className="primary">Create event</button>
      {event && <div className="event-state"><p>Selected: <strong>{event.name}</strong> · {event.closed ? 'Closed' : 'Open'}</p><button type="button" disabled={busy} onClick={() => { if(window.confirm(`${event.closed?'Reopen':'Close'} ${event.name}?`)) void action(async () => { await request('PATCH',`/events/${event.id}/state`,{closed:!event.closed}); }, 'Event updated'); }}>{event.closed?'Reopen event':'Close event'}</button></div>}
    </form>
    <div className="panel"><h2>Menu and ticket values</h2><label>Menu item<select value={menuId} onChange={e=>setMenuId(Number(e.target.value))}><option value={0}>Add a new menu item</option>{foods.map(f=><option key={f.id} value={f.id}>{f.name}</option>)}</select></label>
      <form key={menuId} onSubmit={e=>{const data=form(e); void action(async()=>{await request(menu?'PUT':'POST',menu?`/menu/items/${menu.id}`:'/menu/items',{name:data.get('name'),food_group:data.get('group'),description:data.get('description'),ticket:Number(data.get('tickets')),value:menu?.value||0,is_available:data.get('available')==='on'});},'Menu saved. Existing orders retain their ticket values.');}}>
        <label>Item name<input name="name" required maxLength={40} defaultValue={menu?.name||''} /></label><label>Category<input name="group" required maxLength={40} defaultValue={menu?.food_group||'Dinner'} /></label>
        <label>Tickets per portion<input name="tickets" type="number" min={0} max={10000} step={1} required defaultValue={menu?.ticket??1} inputMode="numeric" /></label>
        <label>Description<input name="description" maxLength={500} defaultValue={menu?.description||''} /></label><label className="check-row"><input name="available" type="checkbox" defaultChecked={menu?.is_available??true} />Available to order</label><button className="primary" disabled={busy}>Save menu item</button>
      </form><p className="muted">Menu and recipes are shared across events. Changes apply only to future orders.</p>
    </div>
    <form className="panel" onSubmit={e=>{const data=form(e);const target=e.currentTarget;void action(async()=>{await request('POST','/events/setup/consumables',{name:data.get('name'),unit:data.get('unit')});target.reset();},'Consumable added');}}>
      <h2>Ingredients and supplies</h2><p className="muted">Use one base unit consistently: grams, milliliters, or individual pieces. For example, 2 kg of pasta is 2,000 g.</p>
      <label>Name<input name="name" required maxLength={100} placeholder="Dry pasta, sauce, dinner plate…" /></label><label>Unit<select name="unit"><option value="g">Grams (g)</option><option value="ml">Milliliters (ml)</option><option value="each">Each / pieces</option></select></label><button className="primary" disabled={busy}>Add consumable</button>
      <ul className="compact-list">{consumables.map(c=><li key={c.id}>{c.name} <span>{c.unit}</span></li>)}</ul>
    </form>
    <form className="panel" onSubmit={e=>{e.preventDefault();void action(async()=>{await request('PUT',`/events/setup/recipes/${recipeFood}`,recipe);},'Recipe saved for future orders');}}>
      <h2>Recipe per portion</h2><label>Menu item<select required value={recipeFood} onChange={e=>setRecipeFood(Number(e.target.value))}><option value={0}>Choose a menu item</option>{foods.map(f=><option key={f.id} value={f.id}>{f.name}</option>)}</select></label>
      <p className="muted">Include food and supplies. Example: one dinner uses 100 g dry pasta, 150 ml sauce, and 1 plate. These are your estimates; the app does not assume a recipe.</p>
      {recipe.map((line,index)=><div className="recipe-line" key={index}><label>Consumable<select aria-label={`Recipe consumable ${index+1}`} value={line.consumable_id} onChange={e=>setRecipe(r=>r.map((v,i)=>i===index?{...v,consumable_id:Number(e.target.value)}:v))}>{consumables.map(c=><option key={c.id} value={c.id}>{c.name} ({c.unit})</option>)}</select></label><label>Per portion<input aria-label={`Recipe quantity ${index+1}`} type="number" min="0.001" max="1000000" step="0.001" required value={line.quantity} onChange={e=>setRecipe(r=>r.map((v,i)=>i===index?{...v,quantity:Number(e.target.value)}:v))} /></label><button type="button" aria-label={`Remove recipe line ${index+1}`} onClick={()=>setRecipe(r=>r.filter((_,i)=>i!==index))}>Remove</button></div>)}
      <div className="actions"><button type="button" disabled={!consumables.length||!recipeFood} onClick={()=>setRecipe(r=>[...r,{consumable_id:consumables[0].id,quantity:1}])}>Add recipe line</button><button className="primary" disabled={busy||!recipeFood}>Save recipe</button></div>
    </form>
    <form className="panel" onSubmit={e=>{const data=form(e); const target=e.currentTarget; void action(async()=>{await request('POST',`/events/${event?.id}/stock`,{room_id:roomId || null,consumable_id:Number(data.get('consumable')),quantity:Number(data.get('quantity')),reason:data.get('reason')});target.reset();},'Stock adjustment recorded');}}>
      <h2>Event stock adjustments</h2><p><strong>{roomName || 'Whole event / shared stock'}</strong></p><p className="muted">Add starting stock and replenishment as positive quantities. Enter waste or count corrections as signed adjustments. Estimated usage is already deducted automatically.</p>
      <label>Consumable<select name="consumable" required>{consumables.map(c=><option key={c.id} value={c.id}>{c.name} ({c.unit})</option>)}</select></label><label>Quantity added or removed<input name="quantity" type="number" step="0.001" min="-1000000000" max="1000000000" required placeholder="2000 or -250" /></label><label>Reason<input name="reason" required minLength={3} maxLength={200} placeholder="Starting stock / replenishment / waste / physical count" /></label><button className="primary" disabled={busy||!event||event.closed||!consumables.length}>Record adjustment</button>
      <details><summary>Recent adjustments</summary><ul className="compact-list">{history.map(h=><li key={h.id}><span>{consumables.find(c=>c.id===h.consumable_id)?.name}: {Number(h.quantity)}<br/>{h.reason}</span><small>{new Date(h.created_at).toLocaleString()}</small></li>)}</ul></details>
    </form>
    <form className="panel" onSubmit={e=>{const data=form(e);const target=e.currentTarget;void action(async()=>{await request('POST',data.get('role')==='guest'?'/auth/guest-stations':'/auth/volunteers',{username:data.get('username'),password:data.get('password')});target.reset();},'Station account created. Use these credentials on the matching tablet.');}}>
      <h2>Tablet and volunteer accounts</h2><p className="muted">Use a guest account on guest tablets. Guests choose food; volunteers confirm tickets and operate the kitchen. Use table numbers on shared guest tablets.</p><label>Account type<select name="role"><option value="volunteer">Volunteer</option><option value="guest">Guest tablet</option></select></label><label>Username<input name="username" required minLength={3} maxLength={40} pattern="[a-zA-Z0-9_.\-]+" autoComplete="off" /></label><label>Temporary password<input name="password" type="password" required minLength={10} maxLength={128} autoComplete="new-password" /></label><button className="primary" disabled={busy}>Create station account</button>
    </form>
  </div>;
}
