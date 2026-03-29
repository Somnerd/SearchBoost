import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import AdminUserTable from '../components/AdminUserTable';
import SystemHealth from '../components/SystemHealth';

export default function Admin() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchHealth, 10000); // refresh health every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [usersRes, healthRes] = await Promise.all([
        client.get('/admin/users'),
        client.get('/admin/health')
      ]);
      setUsers(usersRes.data);
      setHealthData(healthRes.data);
    } catch (err) {
      console.error('Failed to fetch admin data:', err);
      setError('Failed to load administrative data. Some services may be unreachable.');
    } finally {
      setLoading(false);
    }
  };

  const fetchHealth = async () => {
    try {
      const res = await client.get('/admin/health');
      setHealthData(res.data);
    } catch (err) {
      // silently fail health poll
    }
  };

  const handleRoleChange = async (targetId, newRole) => {
    try {
      await client.patch(`/admin/users/${targetId}/role`, { role: newRole });
      setUsers(users.map(u => u.id === targetId ? { ...u, role: newRole } : u));
    } catch (err) {
       alert('Operation failed: ' + (err.response?.data?.error || 'Unknown error'));
    }
  };

  const handleDelete = async (targetId) => {
    try {
      await client.delete(`/admin/users/${targetId}`);
      setUsers(users.filter(u => u.id !== targetId));
    } catch (err) {
       alert('Operation failed: ' + (err.response?.data?.error || 'Unknown error'));
    }
  };

  return (
    <div className="page-enter" style={{ padding: '2rem 1rem', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 600, margin: '0 0 0.5rem' }}>Admin Dashboard</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>Manage users and monitor system health across the SearchBoost ecosystem.</p>
      </header>

      {error && (
        <div style={{ background: 'rgba(224, 90, 90, 0.1)', color: 'var(--bg-warning)', padding: '1rem', borderRadius: '8px', marginBottom: '2rem', border: '1px solid var(--bg-warning)' }}>
          {error}
        </div>
      )}

      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '1.5rem' }}>
          System Health Monitoring
        </h2>
        <SystemHealth health={healthData} loading={loading} />
      </section>

      <section>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '1.5rem' }}>
          Registered Users
        </h2>
        <AdminUserTable 
          users={users} 
          currentUser={user} 
          onRoleChange={handleRoleChange} 
          onDelete={handleDelete} 
          loading={loading}
        />
      </section>
    </div>
  );
}
