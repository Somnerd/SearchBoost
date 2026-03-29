import React, { useRef, useEffect } from 'react';

export default function SearchBar({ onSubmit, loading }) {
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, []);

  const handleInput = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = e.target.scrollHeight + 'px';
  };

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (loading) return;
    const query = textareaRef.current.value.trim();
    if (query) {
      onSubmit(query);
      textareaRef.current.value = '';
      textareaRef.current.style.height = 'auto'; // reset height
    }
  };

  return (
    <div className="glass-card" style={{ 
      width: '100%', 
      maxWidth: '800px', 
      margin: '0 auto', 
      padding: '1rem',
      display: 'flex',
      alignItems: 'flex-end',
      gap: '1rem',
      transition: 'box-shadow 0.2s',
      position: 'relative'
    }}
    onFocus={(e) => e.currentTarget.style.boxShadow = '0 0 0 2px var(--accent), 0 0 24px rgba(79, 142, 247, 0.3)'}
    onBlur={(e) => e.currentTarget.style.boxShadow = 'none'}
    >
      <textarea
        id="search-input"
        ref={textareaRef}
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        disabled={loading}
        placeholder="Ask anything... (Ctrl+Enter to submit)"
        style={{
          flex: 1,
          background: 'transparent',
          border: 'none',
          boxShadow: 'none',
          resize: 'none',
          outline: 'none',
          fontSize: '1.1rem',
          maxHeight: '200px',
          minHeight: '44px',
          overflow: 'auto',
          padding: '0.5rem',
          display: 'block'
        }}
      />
      <button 
        onClick={handleSubmit} 
        disabled={loading}
        title="Submit"
        style={{
          background: 'var(--accent)',
          border: 'none',
          borderRadius: '50%',
          width: '44px',
          height: '44px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: loading ? 'not-allowed' : 'pointer',
          opacity: loading ? 0.7 : 1,
          transition: 'transform 0.1s',
          flexShrink: 0
        }}
        onMouseEnter={(e) => { if (!loading) e.currentTarget.style.transform = 'scale(1.05)' }}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
      >
        {loading ? (
          <div style={{
            width: '20px', height: '20px', 
            border: '2px solid rgba(255,255,255,0.3)', 
            borderTop: '2px solid white', 
            borderRadius: '50%', 
            animation: 'spin 1s linear infinite'
          }}></div>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        )}
      </button>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes spin { 100% { transform: rotate(360deg); } }
      `}} />
    </div>
  );
}
