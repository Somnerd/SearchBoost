import React from 'react';

export default function SystemHealth({ health, loading }) {
  if (loading || !health) return (
     <div className="glass-card" style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
       <HealthCard label="Warden Service" />
       <HealthCard label="Database (sb_db)" />
     </div>
  );

  const warden = health.warden;
  const db = health.database;

  return (
    <div className="glass-card" style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
      <HealthCard 
        label="Warden Service" 
        status={warden.status === 'healthy' ? 'OK' : 'DOWN'} 
        color={warden.status === 'healthy' ? '#4caf50' : '#f44336'} 
        details={warden.circuit_breaker ? `Circuit: ${warden.circuit_breaker}` : `Status: ${warden.status}`}
      />
      <HealthCard 
        label="Database (sb_db)" 
        status={db.status === 'healthy' ? 'CONNECTED' : 'DOWN'} 
        color={db.status === 'healthy' ? '#4caf50' : '#f44336'} 
        details={db.status === 'healthy' ? 'Pool active' : 'Check logs'}
      />
      <div style={{ marginLeft: 'auto', textAlign: 'right', flex: '1 0 100%' }}>
         <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: '0.5rem 0' }}>
            Last Checked: {new Date(health.timestamp).toLocaleTimeString()}
         </p>
      </div>
    </div>
  );
}

function HealthCard({ label, status = '...', color = 'var(--text-muted)', details = '...' }) {
  return (
    <div style={{ flex: '1 1 200px', padding: '1.5rem', background: 'rgba(0,0,0,0.1)', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
      <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: color }}></div>
        <span style={{ fontSize: '1.4rem', fontWeight: 700, color: '#fff' }}>{status}</span>
      </div>
      <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: '0.5rem', opacity: 0.8 }}>{details}</div>
    </div>
  );
}
