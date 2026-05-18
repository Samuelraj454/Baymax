import React, { useState, useEffect, useRef } from 'react';
import { Send, User, Cpu, Loader2, Volume2, AlertCircle } from 'lucide-react';

export default function ChatInterface({ messages, onSendMessage, loading, status, error }) {
  const [input, setInput] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <div className="flex-col h-full" style={{ gap: '20px' }}>
      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="glass-panel flex-col" 
        style={{ flex: 1, padding: '24px', overflowY: 'auto', gap: '20px', position: 'relative' }}
      >
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`} style={{ animation: 'slideUp 0.3s ease' }}>
            <div className="flex" style={{ maxWidth: '80%', gap: '14px', flexDirection: m.role === 'user' ? 'row-reverse' : 'row' }}>
              <div className="flex items-center justify-center" style={{ 
                width: '36px', height: '36px', borderRadius: '50%', 
                background: m.role === 'user' ? 'var(--bg-secondary)' : 'var(--accent-primary)',
                border: m.role === 'user' ? '1px solid var(--panel-border)' : 'none',
                flexShrink: 0
              }}>
                {m.role === 'user' ? <User size={18} style={{ color: 'var(--text-secondary)' }} /> : <Cpu size={18} color="#ffffff" />}
              </div>
              <div className="glass-panel" style={{ 
                padding: '14px 20px', 
                background: m.role === 'user' ? '#ffffff' : 'var(--bg-secondary)',
                borderBottomLeftRadius: m.role === 'assistant' ? '4px' : '20px',
                borderBottomRightRadius: m.role === 'user' ? '4px' : '20px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)'
              }}>
                <p style={{ fontSize: '16px', lineHeight: '1.6', whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>{m.content}</p>
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center" style={{ gap: '8px', color: 'var(--text-secondary)', fontSize: '13px' }}>
              <Loader2 size={16} className="animate-spin" style={{ color: 'var(--accent-primary)' }} />
              <span>Processing...</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center justify-center glass-panel" style={{ color: 'var(--accent-error)', fontSize: '13px', gap: '8px', padding: '12px' }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Input Area */}
      <div className="glass-panel flex items-center" style={{ padding: '12px 16px', gap: '12px', background: '#ffffff' }}>
        <input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Type a message..."
          style={{ 
            flex: 1, background: 'transparent', border: 'none', color: 'var(--text-primary)', 
            outline: 'none', fontSize: '15px' 
          }}
        />
        
        {status === 'SPEAKING' && <Volume2 size={20} style={{ color: 'var(--accent-primary)' }} className="animate-pulse" />}

        <button 
          onClick={handleSend}
          disabled={loading}
          style={{ 
            background: 'var(--accent-primary)', border: 'none', cursor: 'pointer', 
            color: '#ffffff', display: 'flex', padding: '10px', borderRadius: '8px',
            opacity: input.trim() && !loading ? 1 : 0.5,
            transition: 'opacity 0.2s'
          }}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}

