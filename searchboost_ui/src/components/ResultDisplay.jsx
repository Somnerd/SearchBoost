import React from 'react';

export default function ResultDisplay({ result, loading, error }) {
  if (!result && !loading && !error) return null;

  return (
    <div className="page-enter" style={{ width: '100%', maxWidth: '800px', margin: '2rem auto 0' }}>
      {error && (
        <div className="glass-card" style={{ borderColor: 'var(--bg-warning)', borderLeft: '4px solid var(--bg-warning)' }}>
          <h3 style={{ color: 'var(--bg-warning)', marginTop: 0 }}>Error</h3>
          <p style={{ margin: 0, color: 'var(--text-primary)' }}>{error}</p>
        </div>
      )}

      {loading && !result && !error && (
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>Thinking</span>
          <span className="dot-pulse"></span>
        </div>
      )}

      {result && (
        <div className="glass-card page-enter">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '1rem' }}>
            AI Response
          </div>
          <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: 'var(--text-primary)' }}>
            {result}
          </div>
        </div>
      )}

      <style dangerouslySetInnerHTML={{__html: `
        .dot-pulse {
          position: relative;
          color: var(--accent);
          width: 6px;
          height: 6px;
          border-radius: 3px;
          background-color: var(--accent);
          animation: dotPulse 1.5s infinite linear;
          margin-left: 10px;
        }
        .dot-pulse::before, .dot-pulse::after {
          content: '';
          display: inline-block;
          position: absolute;
          top: 0;
          width: 6px;
          height: 6px;
          border-radius: 3px;
          background-color: var(--accent);
        }
        .dot-pulse::before {
          left: -12px;
          animation: dotPulseBefore 1.5s infinite linear;
        }
        .dot-pulse::after {
          left: 12px;
          animation: dotPulseAfter 1.5s infinite linear;
        }
        @keyframes dotPulseBefore {
          0% { box-shadow: 0 -10px 0 0 rgba(79,142,247,0); }
          25% { box-shadow: 0 -10px 0 0 rgba(79,142,247,0.8); }
          50% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
          100% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
        }
        @keyframes dotPulse {
          0% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
          25% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
          50% { box-shadow: 0 -10px 0 0 rgba(79,142,247,0.8); }
          75% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
          100% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
        }
        @keyframes dotPulseAfter {
          0% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
          25% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
          50% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
          75% { box-shadow: 0 -10px 0 0 rgba(79,142,247,0.8); }
          100% { box-shadow: 0 0 0 0 rgba(79,142,247,0); }
        }
      `}} />
    </div>
  );
}
