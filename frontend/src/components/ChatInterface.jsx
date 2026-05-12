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
            <div className="flex" style={{ maxWidth: '85%', gap: '12px', flexDirection: m.role === 'user' ? 'row-reverse' : 'row' }}>
              <div className="flex items-center justify-center" style={{ 
                width: '32px', height: '32px', borderRadius: '50%', 
                background: m.role === 'user' ? 'rgba(255,255,255,0.1)' : 'var(--accent-cyan)',
                flexShrink: 0
              }}>
                {m.role === 'user' ? <User size={16} /> : <Cpu size={16} color="#000" />}
              </div>
              <div className="glass-panel" style={{ 
                padding: '12px 16px', 
                background: m.role === 'user' ? 'rgba(255,255,255,0.05)' : 'rgba(0,240,255,0.05)',
                borderBottomLeftRadius: m.role === 'assistant' ? '4px' : '20px',
                borderBottomRightRadius: m.role === 'user' ? '4px' : '20px',
              }}>
                <p style={{ fontSize: '14px', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>{m.content}</p>
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center" style={{ gap: '8px', color: 'var(--accent-cyan)', fontSize: '12px', opacity: 0.8 }}>
              <Loader2 size={14} className="animate-spin" />
              <span>BAYMAX is processing...</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center justify-center" style={{ color: 'var(--accent-red)', fontSize: '12px', gap: '8px' }}>
          <AlertCircle size={14} />
          <span>{error}</span>
        </div>
      )}

      {/* Input Area */}
      <div className="glass-panel flex items-center" style={{ padding: '8px 12px', gap: '12px' }}>
        <input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
          style={{ 
            flex: 1, background: 'transparent', border: 'none', color: 'white', 
            outline: 'none', fontSize: '14px' 
          }}
        />
        
        {status === 'SPEAKING' && <Volume2 size={18} className="text-cyan animate-pulse" />}

        <button 
          onClick={handleSend}
          disabled={loading}
          style={{ 
            background: 'transparent', border: 'none', cursor: 'pointer', 
            color: 'var(--accent-cyan)', display: 'flex' 
          }}
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}

