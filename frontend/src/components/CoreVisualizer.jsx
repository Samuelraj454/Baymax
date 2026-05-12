import React from 'react';
import { Shield, Zap, Activity } from 'lucide-react';

export default function CoreVisualizer({ status }) {
  const isThinking = status === 'thinking';
  const color = isThinking ? 'var(--accent-red)' : 'var(--accent-cyan)';
  
  return (
    <div className="glass-panel flex-col items-center justify-center h-full" style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Background Scanning Line */}
      <div style={{ 
        position: 'absolute', top: 0, left: 0, right: 0, height: '2px', 
        background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
        opacity: 0.3, animation: 'scanline 4s linear infinite'
      }} />

      <div style={{ position: 'relative', width: '240px', height: '240px', display: 'flex', alignItems: 'center', justifyCenter: 'center' }}>
        
        {/* Outer Rotating Ring */}
        <div style={{
          position: 'absolute', width: '100%', height: '100%',
          border: `2px dashed ${color}`, borderRadius: '50%',
          opacity: 0.2, animation: 'rotate-slow 10s linear infinite'
        }} />

        {/* Middle Pulse Ring */}
        <div style={{
          position: 'absolute', width: '80%', height: '80%', left: '10%', top: '10%',
          border: `1px solid ${color}`, borderRadius: '50%',
          opacity: 0.4, animation: isThinking ? 'pulse-red 1s infinite' : 'pulse-cyan 3s infinite'
        }} />

        {/* Inner Core */}
        <div className="flex items-center justify-center" style={{
          position: 'absolute', width: '60%', height: '60%', left: '20%', top: '20%',
          background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
          borderRadius: '50%', transition: 'all 0.5s ease',
          boxShadow: `0 0 40px ${color}`
        }}>
          <Activity size={40} className={isThinking ? 'glow-red' : 'glow-cyan'} />
        </div>
      </div>

      <div className="flex-col items-center" style={{ marginTop: '40px', gap: '8px' }}>
        <h2 style={{ letterSpacing: '8px', fontSize: '18px', color: 'var(--text-primary)' }}>{isThinking ? 'PROCESSING' : 'BAYMAX'}</h2>
        <div className="flex items-center" style={{ gap: '12px', opacity: 0.6 }}>
            <Shield size={14} />
            <span style={{ fontSize: '10px', letterSpacing: '2px' }}>CORE ENCRYPTED</span>
            <Zap size={14} />
        </div>
      </div>

      {/* Voice Visualizer Mockup */}
      <div className="flex items-center" style={{ position: 'absolute', bottom: '24px', gap: '4px', height: '20px' }}>
        {[...Array(12)].map((_, i) => (
          <div key={i} style={{ 
            width: '3px', 
            height: isThinking ? `${Math.random() * 100}%` : '4px',
            background: color,
            borderRadius: '2px',
            transition: 'height 0.1s ease',
            opacity: 0.5
          }} />
        ))}
      </div>
    </div>
  );
}
