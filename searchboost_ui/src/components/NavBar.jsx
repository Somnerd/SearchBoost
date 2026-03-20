import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function NavBar() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <nav style={{
      position: 'sticky', top: 0, zIndex: 100,
      background: 'rgba(10, 15, 30, 0.8)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-glass)',
      padding: '1rem 2rem',
      display: 'flex', justifyContent: 'space-between', alignItems: 'center'
    }}>
      <div>
        <span style={{ color: 'var(--accent)', fontWeight: 700, fontSize: '1.2rem', marginRight: '2rem' }}>
          SearchBoost
        </span>
        <NavLink to="/search" style={({isActive}) => ({
          color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
          textDecoration: 'none', marginRight: '1rem', fontWeight: 500
        })}>
          Search
        </NavLink>
        {user.role === 'admin' && (
          <NavLink to="/admin" style={({isActive}) => ({
             color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
             textDecoration: 'none', fontWeight: 500
          })}>
            Admin Panel
          </NavLink>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ background: 'var(--bg-glass)', padding: '0.4rem 0.8rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>{user.username}</span>
          {user.role === 'admin' && (
            <span style={{ marginLeft: '0.5rem', background: 'var(--accent)', padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.7rem', color: '#fff' }}>Admin</span>
          )}
        </div>
        <button onClick={logout} className="btn-danger" style={{ padding: '0.4rem 0.8rem', fontSize: '0.9rem' }}>
          Logout
        </button>
      </div>
    </nav>
  );
}
