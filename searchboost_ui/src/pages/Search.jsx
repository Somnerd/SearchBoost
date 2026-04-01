import React, { useState, useEffect, useRef } from 'react';
import SearchBar from '../components/SearchBar';
import ResultDisplay from '../components/ResultDisplay';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';

export default function Search() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentThreadId, setCurrentThreadId] = useState(() => Date.now().toString());
  const [selectedModel, setSelectedModel] = useState('llama3.2:latest');
  const [availableModels, setAvailableModels] = useState(['llama3.2:latest']);
  const pollIntervalRef = useRef(null);

  useEffect(() => {
    fetchSessions();
    fetchAvailableModels();
  }, []);

  useEffect(() => {
    fetchHistory(currentThreadId);
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [currentThreadId]);

  const fetchSessions = async () => {
    try {
      const res = await client.get('/search/sessions');
      setSessions(res.data);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    }
  };

  const fetchAvailableModels = async () => {
    try {
      // In a real app, the API would proxy this. For now, we hardcode based on discovery or add a route later.
      // But we know llama3.2:latest is there.
      setAvailableModels(['llama3.2:latest', 'nomic-embed-text:latest']);
    } catch (err) {
      console.error('Failed to fetch models:', err);
    }
  };

  const fetchHistory = async (threadId) => {
    try {
      const res = await client.get(`/search/history/${threadId}`);
      setConversationHistory(res.data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const handleSearch = async (query) => {
    setLoading(true);
    setError(null);
    setResult(null);
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    // Optimistically push the chat into the sidebar instantly
    setSessions(prev => {
      if (!prev.find(s => s.thread_id === currentThreadId)) {
        return [{ thread_id: currentThreadId, last_activity: new Date().toISOString() }, ...prev];
      }
      return prev;
    });

    try {
      const res = await client.post('/search/enqueue', { 
        query, 
        thread_id: currentThreadId,
        model: selectedModel 
      });
      const jobId = res.data.id || res.data.job_id || res.data.job_id_used;
      
      let pollCount = 0;
      pollIntervalRef.current = setInterval(async () => {
        pollCount++;
        if (pollCount > 300) { // 600 seconds max
          clearInterval(pollIntervalRef.current);
          setError('Request timed out');
          setLoading(false);
          return;
        }

        try {
          const resultRes = await client.get(`/search/result/${jobId}`);
          if (resultRes.data.status === 'complete') {
            clearInterval(pollIntervalRef.current);
            const answer = resultRes.data.result.answer || resultRes.data.result;
            setResult(answer);
            setConversationHistory(prev => [...prev, { query, result: answer }]);
            fetchSessions();
            setLoading(false);
          } else if (resultRes.data.status === 'failed') {
            clearInterval(pollIntervalRef.current);
            setError('Search job failed: ' + (resultRes.data.error || 'Unknown error'));
            setLoading(false);
          }
        } catch (pollErr) {
          // If 429 (Rate Limited), Warden is throttling us. Don't stop polling!
          if (pollErr.response?.status === 429) {
            console.warn('Warden rate limit hit, retrying in next tick...');
            return;
          }

          // For all other errors (5xx, network, etc.), stop polling and show error
          clearInterval(pollIntervalRef.current);
          if (pollErr.response) {
             setError(pollErr.response.data.error || 'Could not fetch result');
          } else {
             setError('Could not reach Warden');
          }
          setLoading(false);
        }
      }, 2000);
    } catch (err) {
      if (err.response) {
         setError(err.response.data.error || err.response.data.message || 'Error executing search');
      } else {
         setError('Could not enqueue request (Warden unreachable)');
      }
      setLoading(false);
    }
  };

  const clearHistory = () => {
    setCurrentThreadId(Date.now().toString());
    setConversationHistory([]);
    setResult(null);
    setError(null);
  };

  return (
    <div style={{ display: 'flex', width: '100%', maxWidth: '1400px', margin: '0 auto', minHeight: '85vh', gap: '2rem' }}>
      
      {/* SIDEBAR */}
      <div style={{ width: '260px', borderRight: '1px solid rgba(255,255,255,0.05)', padding: '1rem 1rem 1rem 0', display: 'flex', flexDirection: 'column' }}>
        <button 
          onClick={clearHistory}
          style={{ width: '100%', padding: '0.8rem', background: 'var(--accent)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', marginBottom: '1.5rem', fontWeight: 'bold', fontSize: '1rem', transition: 'filter 0.2s', ':hover': {filter: 'brightness(1.1)'} }}
        >
          + New Chat
        </button>
        <h4 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '1rem' }}>Past Sessions</h4>
        <div style={{ overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {sessions.map(s => (
            <div 
              key={s.thread_id} 
              onClick={() => setCurrentThreadId(s.thread_id)}
              style={{
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                cursor: 'pointer',
                background: currentThreadId === s.thread_id ? 'rgba(123, 97, 255, 0.15)' : 'transparent',
                color: currentThreadId === s.thread_id ? 'var(--accent)' : 'var(--text-primary)',
                borderLeft: currentThreadId === s.thread_id ? '3px solid var(--accent)' : '3px solid transparent',
                transition: 'all 0.2s ease',
                fontSize: '0.9rem',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}
            >
               {s.thread_id === 'default' ? 'Legacy Sandbox' : `Chat-${s.thread_id.substring(s.thread_id.length - 6)}`}
            </div>
          ))}
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="page-enter" style={{ flex: 1, padding: '2rem 0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <h1 style={{ fontSize: '2.5rem', margin: '0 0 0.5rem', fontWeight: '600' }}>Hello, {user?.username}</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', margin: 0 }}>What do you want to know today?</p>
        </div>

        {conversationHistory.length > 0 && (
          <div style={{ maxWidth: '800px', margin: '0 auto 1.5rem', width: '100%' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {conversationHistory.map((item, idx) => (
                <div key={idx} className="glass-card" style={{ padding: '1.5rem', borderRadius: '12px' }}>
                  <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                    <span style={{ color: 'var(--accent)', fontWeight: 'bold' }}>Q:</span>
                    <span style={{ color: 'var(--text-primary)', lineHeight: '1.5' }}>{item.query}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <span style={{ color: 'var(--text-muted)', fontWeight: 'bold' }}>A:</span>
                    <span style={{ color: 'var(--text-muted)', lineHeight: '1.6' }}>
                      {typeof item.result === 'string' ? item.result : 'Response parsing error'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ maxWidth: '800px', margin: '0 auto 1rem', width: '100%', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Model:</label>
          <select 
            value={selectedModel} 
            onChange={(e) => setSelectedModel(e.target.value)}
            style={{
              background: 'var(--bg-glass)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-glass)',
              borderRadius: '6px',
              padding: '0.3rem 0.5rem',
              fontSize: '0.85rem',
              outline: 'none'
            }}
          >
            {availableModels.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>

        <SearchBar onSubmit={handleSearch} loading={loading} />
        
        {/* We clear the main result container if we have history flowing instead, or just keep it at bottom */}
        <ResultDisplay result={result} loading={loading} error={error} />
      </div>
    </div>
  );
}
