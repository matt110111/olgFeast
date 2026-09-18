import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ChefHat } from 'lucide-react';
import ThemeToggle from '../ThemeToggle';

export default function Header() {
  const { user, logout, isStaff } = useAuth();
  const navigate = useNavigate();
  const link = 'inline-flex items-center min-h-12 px-3 py-3 rounded-lg font-medium hover:bg-gray-100 dark:hover:bg-gray-700';
  return <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-100">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-3">
      <Link to={isStaff?'/event':'/'} className="flex items-center gap-2 font-bold text-xl"><ChefHat className="w-7 h-7 text-cyan-800 dark:text-cyan-300" />OLG Feast</Link>
      <nav className="flex flex-wrap items-center gap-1" aria-label="Main navigation">
        {isStaff ? <><Link className={link} to="/event">Event station</Link>{user?.is_admin && <Link className={link} to="/admin/orders">Order history</Link>}</> : <><Link className={link} to="/event">Order at an event</Link>{user ? <Link className={link} to="/orders">My orders</Link> : <Link className={link} to="/">Menu</Link>}</>}
        {user ? <><Link className={link} to="/account">Account</Link><span className="px-2 text-sm text-gray-500 dark:text-gray-300">{user.username} · {user.is_admin?'Organizer':isStaff?'Volunteer':'Guest'}</span><button className={link} onClick={()=>{logout();navigate('/login');}}>Sign out</button></> : <Link className={link} to="/login">Sign in</Link>}
        <ThemeToggle />
      </nav>
    </div>
  </header>;
}
