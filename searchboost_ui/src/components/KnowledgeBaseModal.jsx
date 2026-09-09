import React, { useState, useEffect } from 'react';
import client from '../api/client';

export default function KnowledgeBaseModal({ isOpen, onClose }) {
  const [docsData, setDocsData] = useState({ totalChunks: 0, totalSources: 0, sources: [] });
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [ingesting, setIngesting] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchDocs();
      setStatusMessage(null);
      setErrorMessage(null);
    }
  }, [isOpen]);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const res = await client.get('/search/docs');
      setDocsData(res.data);
    } catch (err) {
      setErrorMessage('Failed to fetch knowledge base documents.');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const res = await client.post('/search/docs/sync');
      setDocsData({
        totalChunks: res.data.totalChunks,
        totalSources: res.data.totalSources,
        sources: res.data.sources || []
      });
      setStatusMessage('Knowledge base synchronized successfully.');
    } catch (err) {
      setErrorMessage('Sync operation failed.');
    } finally {
      setSyncing(false);
    }
  };

  const handleDelete = async (sourceFile) => {
    try {
      await client.delete('/search/docs', { params: { source: sourceFile } });
      setDocsData(prev => ({
        ...prev,
        sources: prev.sources.filter(s => s !== sourceFile),
        totalSources: Math.max(0, (prev.totalSources || prev.sources.length) - 1)
      }));
      setStatusMessage(`Deleted document source: ${sourceFile}`);
      // Refresh count from backend
      fetchDocs();
    } catch (err) {
      setErrorMessage(`Failed to delete '${sourceFile}'.`);
    }
  };

  const handleIngestRaw = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;

    setIngesting(true);
    setStatusMessage(null);
    setErrorMessage(null);

    try {
      const res = await client.post('/search/docs/raw', {
        title: title.trim(),
        content: content.trim()
      });
      setStatusMessage(res.data.message || 'Document indexed successfully.');
      setTitle('');
      setContent('');
      fetchDocs();
    } catch (err) {
      setErrorMessage(err.response?.data?.error || 'Failed to ingest document.');
    } finally {
      setIngesting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="kb-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Knowledge Base Manager"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="kb-modal-content"
        style={{
          background: '#12131a',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '780px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)'
        }}
      >
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>📚</span> Knowledge Base Manager
            </h2>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              PGVector HNSW Indexing & Hybrid BM25 / Vector RRF Grounding
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close Knowledge Base"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '1.5rem',
              cursor: 'pointer',
              lineHeight: 1
            }}
          >
            &times;
          </button>
        </div>

        {/* Scrollable Body */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Notifications */}
          {statusMessage && (
            <div style={{
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(34, 197, 94, 0.15)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              color: '#4ade80',
              fontSize: '0.85rem'
            }}>
              ✓ {statusMessage}
            </div>
          )}
          {errorMessage && (
            <div style={{
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              fontSize: '0.85rem'
            }}>
              ⚠ {errorMessage}
            </div>
          )}

          {/* Stats Bar */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '0.75rem'
          }}>
            <div style={{
              padding: '0.9rem',
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '10px',
              border: '1px solid rgba(255, 255, 255, 0.06)'
            }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Sources</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--text-primary)', marginTop: '2px' }}>
                {docsData.totalSources ?? (docsData.sources ? docsData.sources.length : 0)}
              </div>
            </div>

            <div style={{
              padding: '0.9rem',
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '10px',
              border: '1px solid rgba(255, 255, 255, 0.06)'
            }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Indexed Chunks</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--accent)', marginTop: '2px' }}>
                {docsData.totalChunks || 0}
              </div>
            </div>

            <div style={{
              padding: '0.9rem',
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '10px',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center'
            }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Index Acceleration</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#10b981', marginTop: '4px' }}>
                ⚡ HNSW + BM25 RRF
              </div>
            </div>
          </div>

          {/* Action Row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              Document Sources ({docsData.sources ? docsData.sources.length : 0})
            </h3>
            <button
              onClick={handleSync}
              disabled={syncing}
              style={{
                padding: '0.4rem 0.8rem',
                background: 'rgba(123, 97, 255, 0.15)',
                color: 'var(--accent)',
                border: '1px solid var(--accent)',
                borderRadius: '6px',
                fontSize: '0.8rem',
                cursor: syncing ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <span>{syncing ? '🔄 Syncing...' : '🔄 Sync Files'}</span>
            </button>
          </div>

          {/* Document Sources List */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.25)',
            borderRadius: '10px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            maxHeight: '200px',
            overflowY: 'auto'
          }}>
            {loading ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Loading knowledge documents...
              </div>
            ) : (!docsData.sources || docsData.sources.length === 0) ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No documents indexed yet. Ingest documents below or place files in <code>./docs</code>.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {docsData.sources.map((source, i) => (
                  <div
                    key={source || i}
                    style={{
                      padding: '0.75rem 1rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      borderBottom: i < docsData.sources.length - 1 ? '1px solid rgba(255, 255, 255, 0.04)' : 'none',
                      fontSize: '0.85rem'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                      <span>📄</span>
                      <span style={{ color: 'var(--text-primary)', wordBreak: 'break-all' }}>{source}</span>
                    </div>
                    <button
                      onClick={() => handleDelete(source)}
                      aria-label={`Delete ${source}`}
                      style={{
                        background: 'rgba(239, 68, 68, 0.1)',
                        color: '#f87171',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        borderRadius: '4px',
                        padding: '3px 8px',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        marginLeft: '10px',
                        flexShrink: 0
                      }}
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Ingest Form */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            borderRadius: '10px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            padding: '1.25rem'
          }}>
            <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              Quick Ingest / Add Document Note
            </h3>
            <form onSubmit={handleIngestRaw} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <input
                type="text"
                placeholder="Document Title (e.g. project-specification)"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{
                  padding: '0.6rem 0.8rem',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  color: 'white',
                  fontSize: '0.85rem'
                }}
              />
              <textarea
                placeholder="Paste Markdown notes, technical guidelines, or documentation text here..."
                rows={4}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
                style={{
                  padding: '0.6rem 0.8rem',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  color: 'white',
                  fontSize: '0.85rem',
                  resize: 'vertical',
                  fontFamily: 'inherit'
                }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  type="submit"
                  disabled={ingesting || !content.trim()}
                  style={{
                    padding: '0.6rem 1.2rem',
                    background: 'var(--accent)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: 'bold',
                    cursor: ingesting || !content.trim() ? 'not-allowed' : 'pointer',
                    opacity: ingesting || !content.trim() ? 0.6 : 1
                  }}
                >
                  {ingesting ? 'Indexing Chunks...' : '📥 Ingest Document'}
                </button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
}
