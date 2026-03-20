import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Username and password are required');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const res = await client.post('/auth/login', { username, password });
      login(res.data);
      navigate('/search');
    } catch (err) {
      if (err.response && err.response.status === 401) {
        setError('Invalid username or password');
      } else {
        setError('Something went wrong. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-enter" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 80px)' }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '400px' }}>
        <div style={{ color: 'var(--accent)', fontWeight: 700, fontSize: '1.8rem', textAlign: 'center', marginBottom: '1rem' }}>SearchBoost</div>
        <h1 style={{ fontSize: '1.4rem', textAlign: 'center', marginBottom: '0.5rem' }}>Welcome back</h1>
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginBottom: '2rem' }}>Sign in to your account</p>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label htmlFor="login-username" style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Username</label>
            <input 
              id="login-username" 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              disabled={loading}
              placeholder="Enter your username"
            />
          </div>
          <div>
            <label htmlFor="login-password" style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Password</label>
            <input 
              id="login-password" 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              disabled={loading}
              placeholder="••••••••"
            />
          </div>
          
          {error && <div style={{ color: 'var(--bg-warning)', fontSize: '0.9rem', marginTop: '0.5rem' }}>{error}</div>}
          
          <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: '1rem', width: '100%' }}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>Don't have an account? </span>
          <Link to="/register" style={{ color: 'var(--accent)', textDecoration: 'none' }}>Register</Link>
        </div>
      </div>
    </div>
  );
}
