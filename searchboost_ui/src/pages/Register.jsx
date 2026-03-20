import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password || !confirmPassword) {
      setError('All fields are required');
      return;
    }
    if (username.length < 3 || username.length > 32 || !/^[a-zA-Z0-9_]+$/.test(username)) {
      setError('Username must be 3-32 alphanumeric characters or underscores');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      await client.post('/auth/register', { username, password });
      const res = await client.post('/auth/login', { username, password });
      login(res.data);
      navigate('/search');
    } catch (err) {
      if (err.response && err.response.status === 409) {
        setError('Username already taken');
      } else if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
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
        <h1 style={{ fontSize: '1.4rem', textAlign: 'center', marginBottom: '2rem' }}>Create account</h1>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label htmlFor="register-username" style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Username</label>
            <input 
              id="register-username" 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              disabled={loading}
              placeholder="Choose a username"
            />
          </div>
          <div>
            <label htmlFor="register-password" style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Password</label>
            <input 
              id="register-password" 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              disabled={loading}
              placeholder="••••••••"
            />
          </div>
          <div>
            <label htmlFor="register-confirm" style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Confirm Password</label>
            <input 
              id="register-confirm" 
              type="password" 
              value={confirmPassword} 
              onChange={(e) => setConfirmPassword(e.target.value)} 
              disabled={loading}
              placeholder="••••••••"
            />
          </div>
          
          {error && <div style={{ color: 'var(--bg-warning)', fontSize: '0.9rem', marginTop: '0.5rem' }}>{error}</div>}
          
          <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: '1rem', width: '100%' }}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
        
        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>Already have an account? </span>
          <Link to="/login" style={{ color: 'var(--accent)', textDecoration: 'none' }}>Sign in</Link>
        </div>
      </div>
    </div>
  );
}
