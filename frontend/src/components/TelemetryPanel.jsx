import React, { useState, useEffect } from 'react';
import { Terminal, ShieldCheck, Activity, Globe } from 'lucide-react';

export default function TelemetryPanel({ sessionId }) {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch(`http://localhost:8000/logs/${sessionId}`);
        const data = await res.json();
        if (data.tool_logs) setLogs(data.tool_logs.slice(0, 10));
      } catch (err) {
        console.error('Failed to fetch logs', err);
      }
    };
    
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [sessionId]);

  return (
    <div className="glass-panel flex-col h-full" style={{ padding: '24px', overflowY: 'auto' }}>
      <div className="flex items-center" style={{ marginBottom: '24px' }}>
        <Terminal className="text-cyan" style={{ marginRight: '12px' }} size={20} />
        <h3 style={{ letterSpacing: '2px', fontSize: '14px', textTransform: 'uppercase' }}>System Telemetry</h3>
      </div>

      <div className="flex-col" style={{ gap: '20px' }}>
        <div className="flex justify-between items-center">
            <div className="flex items-center" style={{ gap: '8px' }}>
                <ShieldCheck size={14} className="text-cyan" />
                <span style={{ fontSize: '12px', opacity: 0.8 }}>SECURITY STATUS</span>
            </div>
            <span style={{ fontSize: '10px', color: 'var(--accent-cyan)' }}>OPTIMAL</span>
        </div>

        <div className="flex-col" style={{ gap: '12px' }}>
            <h4 style={{ fontSize: '11px', color: 'var(--text-secondary)', letterSpacing: '1px' }}>RECENT TOOL EXECUTION</h4>
            {logs.length === 0 ? (
                <p style={{ fontSize: '11px', opacity: 0.4, fontStyle: 'italic' }}>No active tool sequences...</p>
            ) : (
                logs.map((log, i) => (
                    <div key={i} className="flex-col" style={{ 
                        padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.02)',
                        borderLeft: `2px solid ${log.success ? 'var(--accent-cyan)' : 'var(--accent-red)'}`
                    }}>
                        <div className="flex justify-between items-center" style={{ marginBottom: '4px' }}>
                            <span style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-primary)' }}>{log.tool.toUpperCase()}</span>
                            <span style={{ fontSize: '10px', opacity: 0.6 }}>{new Date(log.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                        </div>
                        <p style={{ fontSize: '11px', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {log.args || 'No arguments'}
                        </p>
                    </div>
                ))
            )}
        </div>

        <div style={{ marginTop: '20px' }}>
            <h4 style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '12px' }}>NETWORK NODES</h4>
            <div className="flex items-center" style={{ gap: '12px', opacity: 0.6 }}>
                <Globe size={14} />
                <div style={{ flex: 1, height: '2px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', position: 'relative' }}>
                    <div style={{ position: 'absolute', width: '60%', height: '100%', background: 'var(--accent-cyan)', borderRadius: '2px' }} />
                </div>
                <span style={{ fontSize: '10px' }}>60%</span>
            </div>
        </div>
      </div>
    </div>
  );
}
