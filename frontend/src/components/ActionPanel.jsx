import React, { useEffect, useState } from 'react';
import { Sun, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function ActionPanel({ sessionId }) {
  const [briefing, setBriefing] = useState(null);
  const [suggestions, setSuggestions] = useState([
    { id: 1, type: 'reminder', text: 'Set follow-up for meeting?' },
    { id: 2, type: 'calendar', text: 'Schedule prep time for tomorrow?' }
  ]);

  useEffect(() => {
    const fetchBriefing = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/briefing/${sessionId}`);
        const data = await res.json();
        if (data.briefing) setBriefing(data.briefing);
      } catch (err) {
        console.error('Failed to fetch briefing', err);
      }
    };
    fetchBriefing();
  }, [sessionId]);

  return (
    <div className="glass-panel flex-col h-full" style={{ padding: '24px', overflowY: 'auto' }}>
      <div className="flex items-center" style={{ marginBottom: '24px' }}>
        <Sun className="text-cyan" style={{ marginRight: '12px' }} size={20} />
        <h3 style={{ letterSpacing: '2px', fontSize: '14px', textTransform: 'uppercase' }}>Intelligence Hub</h3>
      </div>

      {briefing && (
        <div style={{ marginBottom: '32px', animation: 'slideUp 0.5s ease' }}>
          <h4 className="text-cyan" style={{ fontSize: '12px', marginBottom: '12px', opacity: 0.8 }}>MORNING BRIEFING</h4>
          <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text-primary)' }}>
            {briefing}
          </p>
        </div>
      )}

      <div style={{ marginBottom: '32px' }}>
        <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px', letterSpacing: '1px' }}>PROACTIVE SUGGESTIONS</h4>
        <div className="flex-col" style={{ gap: '12px' }}>
          {suggestions.map(s => (
            <div key={s.id} className="glass-panel" style={{ padding: '12px', cursor: 'pointer', background: 'rgba(255,255,255,0.03)' }}>
              <div className="flex items-center justify-between">
                <span style={{ fontSize: '13px' }}>{s.text}</span>
                <ArrowRight size={14} className="text-cyan" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 'auto' }}>
        <div className="glass-panel" style={{ padding: '16px', background: 'linear-gradient(135deg, rgba(0,240,255,0.05) 0%, transparent 100%)' }}>
          <div className="flex items-center" style={{ marginBottom: '8px' }}>
            <CheckCircle size={14} className="text-cyan" style={{ marginRight: '8px' }} />
            <span style={{ fontSize: '12px', fontWeight: 'bold' }}>SYSTEM HEALTH</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            Precision Mode: Active<br />
            Latent Memory: 1.2GB<br />
            Uptime: 14h 22m
          </div>
        </div>
      </div>
    </div>
  );
}
