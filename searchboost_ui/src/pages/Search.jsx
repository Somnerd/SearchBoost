import React, { useState, useEffect, useRef } from 'react';
import SearchBar from '../components/SearchBar';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';

export default function Search() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentThreadId, setCurrentThreadId] = useState(() => Date.now().toString());
  const [selectedModel, setSelectedModel] = useState('llama3.2:latest');
  const [availableModels, setAvailableModels] = useState(['llama3.2:latest', 'nomic-embed-text:latest', 'mistral:latest']);
  const [historySearchQuery, setHistorySearchQuery] = useState('');
  const [historySearchResults, setHistorySearchResults] = useState(null);
  const pollIntervalRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    fetchHistory(currentThreadId);
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [currentThreadId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationHistory, loading]);

  const handleHistorySearch = async (e) => {
    e.preventDefault();
    if (!historySearchQuery.trim()) {
      setHistorySearchResults(null);
      return;
    }
    try {
      const res = await client.post('/search/history/search', { query: historySearchQuery });
      setHistorySearchResults(res.data);
    } catch (err) {
      console.error('History search failed:', err);
    }
  };

  const fetchSessions = async () => {
    try {
      const res = await client.get('/search/sessions');
      setSessions(res.data);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    }
  };

  const normalizeHistory = (rawItems, threadId) => {
    if (!Array.isArray(rawItems)) return [];

    // If already in { query, result } format (e.g. from tests or local state)
    if (rawItems.length > 0 && ('query' in rawItems[0] || 'result' in rawItems[0])) {
      return rawItems.map(item => ({ ...item, thread_id: item.thread_id || threadId }));
    }

    // Transform database turn sequence [{ role: 'user', content }, { role: 'assistant', content }]
    const paired = [];
    let currentPair = null;

    for (const turn of rawItems) {
      if (turn.role === 'user') {
        if (currentPair) paired.push(currentPair);
        currentPair = {
          query: turn.content,
          result: null,
          pending: false,
          thread_id: threadId,
          createdAt: turn.createdAt
        };
      } else if (turn.role === 'assistant') {
        if (currentPair) {
          currentPair.result = turn.content;
          paired.push(currentPair);
          currentPair = null;
        } else {
          paired.push({
            query: '',
            result: turn.content,
            pending: false,
            thread_id: threadId,
            createdAt: turn.createdAt
          });
        }
      }
    }
    if (currentPair) paired.push(currentPair);
    return paired;
  };

  const fetchHistory = async (threadId) => {
    try {
      const res = await client.get(`/search/history/${threadId}`);
      const normalized = normalizeHistory(res.data, threadId);
      // Preserve any pending messages that are currently in flight for this thread
      setConversationHistory(prev => {
        const pendingForThisThread = prev.filter(m => m.pending && m.thread_id === threadId);
        return [...normalized, ...pendingForThisThread];
      });
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const handleSearch = async (query) => {
    setLoading(true);
    setError(null);
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    const tempJobId = 'job-' + Date.now();
    const searchThreadId = currentThreadId; // Capture the thread where search started

    setConversationHistory(prev => [...prev, { 
      query, 
      result: null, 
      pending: true, 
      jobId: tempJobId,
      thread_id: searchThreadId 
    }]);

    setSessions(prev => {
      if (!prev.find(s => s.thread_id === searchThreadId)) {
        return [{ thread_id: searchThreadId, last_activity: new Date().toISOString() }, ...prev];
      }
      return prev;
    });

    try {
      const res = await client.post('/search/enqueue', { 
        query, 
        thread_id: searchThreadId,
        model: selectedModel 
      });
      const jobId = res.data.id || res.data.job_id || res.data.job_id_used;
      
      // Update state with actual jobId
      setConversationHistory(prev => prev.map(m => m.jobId === tempJobId ? { ...m, jobId } : m));

      let pollCount = 0;
      pollIntervalRef.current = setInterval(async () => {
        pollCount++;
        if (pollCount > 300) {
          clearInterval(pollIntervalRef.current);
          setConversationHistory(prev => prev.map(m => m.jobId === jobId ? { ...m, pending: false, result: 'Search timed out' } : m));
          setLoading(false);
          return;
        }

        if (pollCount % 30 === 0) {
          const minutesElapsed = pollCount / 30;
          setConversationHistory(prev => prev.map(m => 
            m.jobId === jobId ? { ...m, timeElapsed: minutesElapsed } : m
          ));
        }

        try {
          const resultRes = await client.get(`/search/result/${jobId}`);
          if (resultRes.data.status === 'complete') {
            clearInterval(pollIntervalRef.current);
            const answer = resultRes.data.result.answer || resultRes.data.result;
            
            // Critical update: only update the source message for this task
            setConversationHistory(prev => prev.map(m => 
              m.jobId === jobId ? { ...m, result: answer, pending: false } : m
            ));
            
            fetchSessions();
            setLoading(false);
          } else if (resultRes.data.status === 'failed') {
            clearInterval(pollIntervalRef.current);
            const errorMsg = resultRes.data.error || 'Worker reported failure';
            setConversationHistory(prev => prev.map(m => 
              m.jobId === jobId ? { ...m, result: errorMsg, pending: false } : m
            ));
            setError(errorMsg);
            setLoading(false);
          }
        } catch (pollErr) {
          if (pollErr?.response?.status === 429) {
            console.warn('API Rate limited (429), polling will continue on next tick...');
            return;
          }
          clearInterval(pollIntervalRef.current);
          setError('Communication error with Warden');
          setLoading(false);
        }
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start research task');
      setLoading(false);
    }
  };

  const clearHistory = () => {
    setCurrentThreadId(Date.now().toString());
    setConversationHistory([]);
    setError(null);
  };

  return (
    <div style={{ display: 'flex', width: '100%', maxWidth: '1400px', margin: '0 auto', height: 'calc(100vh - 120px)', gap: '1rem', padding: '1rem' }}>
      
      {/* Sidebar */}
      <div style={{ width: '280px', background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(10px)', borderRadius: '16px', padding: '1.5rem', display: 'flex', flexDirection: 'column', border: '1px solid rgba(255,255,255,0.05)' }}>
        <button 
          onClick={clearHistory}
          style={{ width: '100%', padding: '0.8rem', background: 'var(--accent)', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer', marginBottom: '1.5rem', fontWeight: 'bold', fontSize: '0.95rem', transition: 'all 0.2s', boxShadow: '0 4px 15px rgba(123, 97, 255, 0.3)' }}
        >
          + New Thread
        </button>
        
        <form onSubmit={handleHistorySearch} style={{ marginBottom: '1.5rem' }}>
          <input 
            type="text" 
            placeholder="Search history..."
            value={historySearchQuery}
            onChange={(e) => setHistorySearchQuery(e.target.value)}
            style={{ width: '100%', padding: '0.6rem 1rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', borderRadius: '8px', color: 'white', fontSize: '0.85rem' }}
          />
        </form>

        {historySearchResults && (
          <div style={{ marginBottom: '1.5rem', background: 'rgba(123, 97, 255, 0.05)', padding: '0.5rem', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
               <span style={{ fontSize: '0.75rem', color: 'var(--accent)', fontWeight: 'bold' }}>Matches</span>
               <button onClick={() => setHistorySearchResults(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.7rem' }}>Close</button>
            </div>
            {historySearchResults.map((res, i) => (
              <div key={i} onClick={() => { 
                const sessionParts = res.session_id.split(':');
                setCurrentThreadId(sessionParts[sessionParts.length - 1]); 
                setHistorySearchResults(null); 
              }} style={{ fontSize: '0.8rem', padding: '0.4rem', borderRadius: '4px', cursor: 'pointer', color: 'var(--text-primary)' }}>
                {res.content.substring(0, 40)}...
              </div>
            ))}
          </div>
        )}

        <div style={{ overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          {sessions.map(s => (
            <div key={s.thread_id} onClick={() => setCurrentThreadId(s.thread_id)} style={{ padding: '0.7rem 1rem', borderRadius: '8px', cursor: 'pointer', background: currentThreadId === s.thread_id ? 'rgba(123, 97, 255, 0.1)' : 'transparent', color: currentThreadId === s.thread_id ? 'var(--accent)' : 'var(--text-muted)', borderLeft: currentThreadId === s.thread_id ? '3px solid var(--accent)' : '3px solid transparent', fontSize: '0.85rem' }}>
               {s.thread_id === 'default' ? 'Global Sandbox' : `Thread-${s.thread_id.substring(s.thread_id.length - 4)}`}
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'rgba(255,255,255,0.01)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.03)', overflow: 'hidden' }}>
        <div className="chat-container" style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {conversationHistory.length === 0 && !loading && (
            <div style={{ textAlign: 'center', marginTop: '15%', opacity: 0.5 }}>
              <h1 style={{ fontWeight: '300', fontSize: '3rem', margin: '0' }}>SearchBoost</h1>
              <p style={{ fontSize: '1.2rem' }}>Sovereign AI Research Engine</p>
            </div>
          )}

          {conversationHistory.map((item, idx) => (
            <React.Fragment key={idx}>
              {/* User Message */}
              {item.query ? (
                <div className="chat-bubble-user">
                  {item.query}
                </div>
              ) : null}
              
              {/* Assistant Message */}
              {(item.result || item.pending) ? (
                <div className="chat-bubble-ai">
                   {item.pending ? (
                     <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                       <div className="dot-pulse"></div>
                       <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                         {item.timeElapsed ? `Still researching... (${item.timeElapsed} minutes elapsed)` : 'Researching...'}
                       </span>
                     </div>
                   ) : (
                     item.result || 'No response received'
                   )}
                </div>
              ) : null}
            </React.Fragment>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* Input & Options */}
        <div style={{ padding: '1.5rem', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Model:</label>
              <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} style={{ background: 'transparent', color: 'var(--text-primary)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', fontSize: '0.75rem', outline: 'none' }}>
                {availableModels.map(m => <option key={m} style={{background: '#1a1a1a'}} value={m}>{m}</option>)}
              </select>
            </div>
            <SearchBar onSubmit={handleSearch} loading={loading} />
            {error && <div style={{ color: '#ff6b6b', fontSize: '0.8rem', marginTop: '0.5rem', textAlign: 'center' }}>{error}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
