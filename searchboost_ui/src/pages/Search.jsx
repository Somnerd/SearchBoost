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
  const pollIntervalRef = useRef(null);

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const handleSearch = async (query) => {
    setLoading(true);
    setError(null);
    setResult(null);
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    try {
      const res = await client.post('/search/enqueue', { query });
      const jobId = res.data.id || res.data.job_id || res.data.job_id_used;
      
      let pollCount = 0;
      pollIntervalRef.current = setInterval(async () => {
        pollCount++;
        if (pollCount > 120) { // 240 seconds max
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
            setLoading(false);
          } else if (resultRes.data.status === 'failed') {
            clearInterval(pollIntervalRef.current);
            setError('Search job failed: ' + (resultRes.data.error || 'Unknown error'));
            setLoading(false);
          }
        } catch (pollErr) {
          // If 404, might just mean still processing or not found, we keep polling? Wait, Warden result 500 etc
           // If it is 503, warden is down
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
    setConversationHistory([]);
    setResult(null);
    setError(null);
  };

  return (
    <div className="page-enter" style={{ padding: '2rem 1rem', maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column' }}>
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.5rem', margin: '0 0 0.5rem', fontWeight: '600' }}>Hello, {user?.username}</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', margin: 0 }}>What do you want to know today?</p>
      </div>

      {conversationHistory.length > 0 && (
        <div style={{ maxWidth: '800px', margin: '0 auto 1.5rem', width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-muted)' }}>Session History</h3>
            <button 
              onClick={clearHistory}
              style={{ background: 'transparent', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '0.9rem' }}
            >
              Start New Conversation
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {conversationHistory.map((item, idx) => (
              <div key={idx} className="glass-card" style={{ padding: '1rem' }}>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--accent)', fontWeight: 'bold' }}>Q:</span>
                  <span style={{ color: 'var(--text-primary)' }}>{item.query}</span>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <span style={{ color: 'var(--text-muted)', fontWeight: 'bold' }}>A:</span>
                  <span style={{ color: 'var(--text-muted)' }}>
                    {typeof item.result === 'string' ? item.result.substring(0, 100) + (item.result.length > 100 ? '...' : '') : '...'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <SearchBar onSubmit={handleSearch} loading={loading} />
      
      <ResultDisplay result={result} loading={loading} error={error} />
    </div>
  );
}
