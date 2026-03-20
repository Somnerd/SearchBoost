import React, { useState } from 'react';

export default function AdminUserTable({ users, currentUser, onRoleChange, onDelete, loading }) {
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  if (loading) {
    return (
      <div className="glass-card">
        <div style={{ height: '40px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', marginBottom: '1rem', animation: 'pulse 1.5s infinite' }}></div>
        <div style={{ height: '200px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px', animation: 'pulse 1.5s infinite' }}></div>
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 0.8; } 100% { opacity: 0.5; } }
        `}} />
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ overflowX: 'auto', padding: '1rem' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-glass)' }}>
            <th style={{ padding: '1rem', color: 'var(--text-muted)' }}>Username</th>
            <th style={{ padding: '1rem', color: 'var(--text-muted)' }}>Role</th>
            <th style={{ padding: '1rem', color: 'var(--text-muted)' }}>Joined</th>
            <th style={{ padding: '1rem', color: 'var(--text-muted)', textAlign: 'right' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => {
            const isSelf = u.id === currentUser?.id;
            return (
              <tr key={u.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <td style={{ padding: '1rem', fontWeight: 500 }}>{u.username} {isSelf && '(You)'}</td>
                <td style={{ padding: '1rem' }}>
                  <span style={{ 
                    padding: '0.2rem 0.6rem', 
                    borderRadius: '4px', 
                    fontSize: '0.8rem',
                    background: u.role === 'admin' ? 'var(--accent)' : 'rgba(255,255,255,0.1)',
                    color: '#fff'
                  }}>
                    {u.role}
                  </span>
                </td>
                <td style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  {new Date(u.created_at).toLocaleDateString()}
                </td>
                <td style={{ padding: '1rem', textAlign: 'right' }}>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                    {isSelf ? (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>System Admin</span>
                    ) : (
                      <>
                        <button 
                          onClick={() => onRoleChange(u.id, u.role === 'admin' ? 'user' : 'admin')}
                          style={{
                            background: u.role === 'admin' ? 'rgba(255,165,0,0.2)' : 'rgba(79,142,247,0.2)',
                            color: u.role === 'admin' ? '#ffa500' : 'var(--accent)',
                            border: `1px solid ${u.role === 'admin' ? 'rgba(255,165,0,0.3)' : 'var(--accent)'}`,
                            padding: '0.3rem 0.6rem',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.8rem'
                          }}
                        >
                          {u.role === 'admin' ? 'Demote to User' : 'Make Admin'}
                        </button>
                        
                        {confirmDeleteId === u.id ? (
                          <div style={{ display: 'flex', gap: '0.4rem' }}>
                            <button 
                              onClick={() => onDelete(u.id)}
                              className="btn-danger"
                              style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
                            >
                              Confirm
                            </button>
                            <button 
                              onClick={() => setConfirmDeleteId(null)}
                              style={{ 
                                background: 'transparent', 
                                border: '1px solid var(--border-glass)', 
                                color: 'var(--text-primary)',
                                padding: '0.3rem 0.6rem',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '0.8rem'
                              }}
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button 
                            onClick={() => setConfirmDeleteId(u.id)}
                            className="btn-danger"
                            style={{ 
                              background: 'rgba(224, 90, 90, 0.1)',
                              color: 'var(--bg-warning)',
                              border: '1px solid rgba(224, 90, 90, 0.2)',
                              padding: '0.3rem 0.6rem', 
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '0.8rem'
                            }}
                          >
                            Delete
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
