import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { errorMessage, request } from './eventApi';
import './events.css';
export default function Account() {
  const { user, logout } = useAuth();
  const [error, setError] = useState(''); const [busy,setBusy]=useState(false);
  return <section className="event-app"><form className="panel" style={{maxWidth:500,margin:'auto'}} onSubmit={async e=>{e.preventDefault();const data=new FormData(e.currentTarget);setBusy(true);setError('');try{await request('POST','/auth/password',{current_password:data.get('current'),new_password:data.get('password')});logout();window.location.href='/login';}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}}>
    <h1>Account</h1><p>Signed in as {user?.username}</p><h2>Change password</h2><label>Current password<input type="password" name="current" autoComplete="current-password" required /></label><label>New password<input type="password" name="password" autoComplete="new-password" minLength={10} maxLength={128} required /></label><p className="muted">Use at least 10 characters. Changing your password signs out all sessions for this account.</p>{error&&<p role="alert" className="notice error">{error}</p>}<button className="primary" disabled={busy}>{busy?'Saving…':'Change password'}</button>
  </form></section>;
}
