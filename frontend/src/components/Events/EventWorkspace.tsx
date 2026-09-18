import React, { useCallback, useEffect, useState } from 'react';
import { DinnerEvent, eventApi, FoodItem, errorMessage } from './eventApi';
import { RoomWorkspace } from './RoomWorkspace';
import { EventSetup } from './EventSetup';
import './events.css';
import { useAuth } from '../../contexts/AuthContext';

export default function EventWorkspace() {
  const { user } = useAuth();
  const [events, setEvents] = useState<DinnerEvent[]>([]);
  const [foods, setFoods] = useState<FoodItem[]>([]);
  const [selected, setSelected] = useState(Number(localStorage.getItem('event-id')) || 0);
  const [tab, setTab] = useState(/^kitchen[1-4]$/.test(user?.username || '') ? 'kitchen' : 'order');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState('');
  const refresh = useCallback(async () => {
    try {
      const [newEvents, newFoods] = await Promise.all([eventApi.events(), eventApi.foods()]);
      setEvents(newEvents); setFoods(newFoods); setError(''); setLastSync(new Date().toLocaleTimeString());
      setSelected(current => newEvents.some(e => e.id === current) ? current : (newEvents.find(e => !e.closed)?.id || newEvents[0]?.id || 0));
    } catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    void refresh(); const timer = setInterval(refresh, 15000);
    return () => clearInterval(timer);
  }, [refresh]);
  useEffect(() => { localStorage.setItem('event-id', String(selected)); }, [selected]);
  const event = events.find(e => e.id === selected);
  return <section className={`event-app ${tab === 'order' ? 'ordering' : ''}`}>
    <div className="event-heading"><div><p className="eyebrow">{event?.name || 'OLG Feast'}</p><h1>{user?.is_staff ? 'Event station' : 'Choose your dinner'}</h1></div>
      <span className={error ? 'connection offline' : 'connection'} role="status">{error ? 'Connection interrupted' : lastSync ? `Connected · ${lastSync}` : 'Connecting…'}</span></div>
    {error && <div className="notice error" role="alert">{error} Orders are confirmed only after the server responds. <button onClick={refresh}>Reconnect</button></div>}
    <div className="event-toolbar"><label>Current event<select aria-label="Current event" value={selected} onChange={e => setSelected(Number(e.target.value))}>
      {!events.length && <option value={0}>Create an event to begin</option>}
      {events.map(e => <option key={e.id} value={e.id}>{e.name} · {e.event_date}{e.closed ? ' (closed)' : ''}</option>)}
    </select></label><nav aria-label="Event tools">{[['order',user?.is_staff ? 'Menu / take orders' : 'Menu / order food'],...(user?.is_staff ? [['tickets','Collect tickets'],['kitchen','Kitchen']] : []),...(user?.is_admin ? [['report','Event report'],['setup','Menu & setup']] : [])].map(([id,label]) => <button key={id} className={tab === id ? 'active' : ''} aria-pressed={tab === id} onClick={() => setTab(id)}>{label}</button>)}</nav></div>
    {loading ? <p role="status">Loading event…</p> : <>
      {!event && tab !== 'setup' && <div className="panel empty"><h2>Ready for your first dinner?</h2><p>Create an event, set ticket values, and add the ingredients and supplies used by each portion.</p>{user?.is_admin ? <button className="primary" onClick={() => setTab('setup')}>Set up an event</button> : <p>Ask your organizer to create an event.</p>}</div>}
      {event ? <RoomWorkspace key={event.id} event={event} foods={foods} connected={!error} tab={tab} onRefresh={refresh} onCreated={id => { setSelected(id); setTab('order'); }} /> : tab === 'setup' && <EventSetup foods={foods} onRefresh={refresh} onCreated={id => { setSelected(id); setTab('order'); }} />}
    </>}
  </section>;
}
