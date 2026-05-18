import React, { useState, useEffect } from 'react';
import { Terminal, ShieldCheck, Activity, Globe } from 'lucide-react';

export default function TelemetryPanel({ sessionId }) {
  const [logs, setLogs] = useState([]);
  const [telemetry, setTelemetry] = useState({ cpu: 0, memory: 0, status: 'UNKNOWN', active_tools: 0, network: 'WAITING' });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const logRes = await fetch(`http://localhost:8000/logs/${sessionId}`);
        const logData = await logRes.json();
        if (logData.logs) setLogs(logData.logs.reverse().slice(0, 10));

        const telRes = await fetch(`http://localhost:8000/telemetry`);
        const telData = await telRes.json();
        setTelemetry(telData);
      } catch (err) {
        console.error('Failed to fetch telemetry', err);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  return (
    <div className="glass-panel flex-col h-full" style={{ padding: '24px', overflowY: 'auto' }}>
      <div className="flex items-center" style={{ marginBottom: '24px' }}>
        <Terminal className="text-primary" style={{ marginRight: '12px' }} size={20} />
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>System Telemetry</h3>
      </div>

      <div className="flex-col" style={{ gap: '20px' }}>
        <div className="flex justify-between items-center" style={{ padding: '12px 16px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--panel-border)', borderLeft: telemetry.status === 'OPTIMAL' ? '4px solid var(--accent-primary)' : '4px solid var(--accent-error)' }}>
            <div className="flex items-center" style={{ gap: '10px' }}>
                <ShieldCheck size={16} style={{ color: 'var(--text-secondary)' }} />
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>Core Status</span>
            </div>
            <span style={{ fontSize: '13px', fontWeight: 600, color: telemetry.status === 'OPTIMAL' ? 'var(--accent-primary)' : 'var(--accent-error)' }}>
                {telemetry.status}
            </span>
        </div>

        {/* Real-time Hardware Metrics */}
        <div className="flex-col" style={{ gap: '16px', padding: '16px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--panel-border)' }}>
            <div>
                <div className="flex justify-between" style={{ marginBottom: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)' }}>CPU Load</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{telemetry.cpu.toFixed(1)}%</span>
                </div>
                <div style={{ height: '6px', background: '#e5e7eb', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${telemetry.cpu}%`, height: '100%', background: 'var(--accent-primary)', transition: 'width 1s ease-in-out', borderRadius: '3px' }} />
                </div>
            </div>
            <div>
                <div className="flex justify-between" style={{ marginBottom: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)' }}>Memory</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{telemetry.memory.toFixed(1)}%</span>
                </div>
                <div style={{ height: '6px', background: '#e5e7eb', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${telemetry.memory}%`, height: '100%', background: 'var(--accent-primary)', transition: 'width 1s ease-in-out', borderRadius: '3px' }} />
                </div>
            </div>
        </div>

        <div className="flex-col" style={{ gap: '12px', flex: 1 }}>
            <div className="flex items-center gap-2 mb-2">
                <Activity size={16} style={{ color: 'var(--text-secondary)' }} />
                <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>Runtime Logs</h4>
            </div>
            
            {logs.length === 0 ? (
                <div className="flex items-center justify-center h-full" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                    Awaiting input...
                </div>
            ) : (
                <div className="flex-col gap-2" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {logs.map((log, i) => (
                        <div key={i} className="flex-col" style={{ 
                            padding: '12px', borderRadius: '8px', background: 'var(--bg-secondary)',
                            border: '1px solid var(--panel-border)',
                            borderLeft: log.level === 'ERROR' ? '3px solid var(--accent-error)' : '3px solid var(--panel-border)'
                        }}>
                            <div className="flex justify-between items-center" style={{ marginBottom: '6px' }}>
                                <span style={{ fontSize: '11px', fontWeight: 600, color: log.level === 'ERROR' ? 'var(--accent-error)' : 'var(--text-secondary)' }}>{log.level}</span>
                                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{log.timestamp.split('T')[1].substring(0,8)}</span>
                            </div>
                            <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                                {log.message}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
      </div>
    </div>
  );
}
