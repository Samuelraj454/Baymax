import React, { useState, useEffect, useCallback } from 'react';
import Orb from './components/Orb';
import ChatInterface from './components/ChatInterface';
import TelemetryPanel from './components/TelemetryPanel';
import ActionPanel from './components/ActionPanel';
import SettingsModal from './components/SettingsModal';
import { useVoice } from './hooks/useVoice';
import { Settings, Mic, Activity } from 'lucide-react';
import { API_BASE_URL } from './config';

function App() {
  const [orbState, setOrbState] = useState('idle'); // idle, activated, listening, processing, speaking, error
  const [status, setStatus] = useState('READY'); // READY, LISTENING, THINKING, SPEAKING, ERROR
  const [systemHealth, setSystemHealth] = useState({ online: false, version: '7.0' });
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hello. I am BAYMAX v7.0. Say 'Hey Baymax' to begin." }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showActivationFlash, setShowActivationFlash] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [currentSpeech, setCurrentSpeech] = useState('');
  const sessionId = 'ui_session';

  const addMessage = (msg) => {
    setMessages(prev => [...prev, msg]);
  };

  const {
    isListening,
    isSpeaking,
    unsupported,
    speechError,
    wakeListenerActive,
    isConversationMode,
    startWakeWordListener,
    toggleConversationMode,
    activateBaymax,
    processCommand
  } = useVoice(
    null,
    setOrbState,
    setStatus,
    addMessage,
    sessionId,
    setLiveTranscript,
    setInterimTranscript,
    setCurrentSpeech,
    setShowActivationFlash
  );

  useEffect(() => {
    startWakeWordListener();
    const interval = setInterval(() => {
      if (!wakeListenerActive && !unsupported) {
        startWakeWordListener();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [startWakeWordListener, wakeListenerActive, unsupported]);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`);
        const data = await res.json();
        setSystemHealth({ online: data.status === 'online', ...data });
      } catch (err) {
        setSystemHealth({ online: false, version: '7.0' });
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={`app-container ${showActivationFlash ? 'activation-flash' : ''}`}>
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} sessionId={sessionId} />
      
      {/* Always Listening Indicator & Mic Support */}
      <div style={{ 
        position: 'fixed', top: '24px', left: '24px', zIndex: 100,
        display: 'flex', flexDirection: 'column', gap: '8px'
      }}>
        <div style={{ 
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '8px 12px', borderRadius: '20px', background: 'rgba(0,0,0,0.3)',
          border: '1px solid rgba(0,255,255,0.1)'
        }}>
          <div className={`listening-dot ${wakeListenerActive ? 'active' : ''}`} />
          <span style={{ fontSize: '10px', letterSpacing: '1px', color: 'rgba(0,255,255,0.7)' }}>
            {unsupported ? 'SPEECH UNSUPPORTED' : (wakeListenerActive ? 'ALWAYS LISTENING' : 'MIC STANDBY')}
          </span>
        </div>
        
        {unsupported && (
          <div style={{ color: '#ff4444', fontSize: '10px', padding: '4px 12px', background: 'rgba(255,0,0,0.1)', borderRadius: '4px' }}>
            Use Chrome/Edge for voice features.
          </div>
        )}

        {speechError && (
          <div style={{ color: '#ffcc00', fontSize: '10px', padding: '4px 12px', background: 'rgba(255,200,0,0.1)', borderRadius: '4px' }}>
            Mic Error: {speechError}
          </div>
        )}
      </div>

      {/* Floating Settings Button */}
      <button 
        onClick={() => setIsSettingsOpen(true)}
        className="glass-panel"
        style={{ 
          position: 'fixed', bottom: '24px', right: '24px', zIndex: 100,
          padding: '12px', borderRadius: '50%', cursor: 'pointer',
          color: 'var(--accent-cyan)', border: '1px solid rgba(0,240,255,0.2)'
        }}
      >
        <Settings size={20} />
      </button>

      {/* Left Panel: Monitoring & History */}
      <div className="flex-col h-screen-content" style={{ overflow: 'hidden' }}>
        <TelemetryPanel sessionId={sessionId} health={systemHealth} />
      </div>

      {/* Center Panel: Interaction & Core */}
      <div className="flex-col h-screen-content" style={{ gap: '24px', overflow: 'hidden', alignItems: 'center' }}>
        <div 
          onClick={() => { if (!isListening) activateBaymax(); }}
          style={{ 
            height: '350px', flexShrink: 0, display: 'flex', alignItems: 'center', 
            justifyContent: 'center', width: '100%', cursor: 'pointer' 
          }}
        >
            <Orb state={orbState} />
        </div>

        {/* Live Transcript */}
        <div style={{ height: '40px', textAlign: 'center', opacity: interimTranscript || liveTranscript ? 1 : 0, transition: 'opacity 0.3s' }}>
          <em style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>{interimTranscript || liveTranscript}</em>
        </div>

        {/* Status Bar */}
        <div style={{ 
          padding: '4px 20px', borderRadius: '10px', 
          background: 'rgba(0,255,255,0.05)', border: '1px solid rgba(0,255,255,0.1)',
          display: 'flex', alignItems: 'center', gap: '10px'
        }}>
          <Activity size={12} color={orbState === 'error' ? '#ff4444' : '#00ffff'} />
          <span style={{ fontSize: '10px', letterSpacing: '4px', fontWeight: 'bold', color: orbState === 'error' ? '#ff4444' : '#00ffff' }}>
            {status}
          </span>
        </div>

        {/* Conversation Mode Button */}
        <button 
          onClick={toggleConversationMode}
          style={{
            padding: '8px 16px', borderRadius: '20px',
            background: isConversationMode ? 'rgba(0, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.05)',
            border: `1px solid ${isConversationMode ? '#00ffff' : 'rgba(255, 255, 255, 0.1)'}`,
            color: isConversationMode ? '#00ffff' : 'white',
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px',
            fontSize: '12px', fontWeight: 'bold', letterSpacing: '1px'
          }}
        >
          <Mic size={14} color={isConversationMode ? '#00ffff' : 'white'} />
          {isConversationMode ? 'CONVERSATION ACTIVE' : 'START CONVERSATION'}
        </button>

        <div style={{ flex: 1, minHeight: 0, width: '100%' }}>
            <ChatInterface 
              messages={messages} 
              onSendMessage={(txt) => processCommand(txt, 'text')}
              loading={loading}
              status={status}
              error={error}
            />
        </div>
      </div>


      {/* Right Panel: Intelligence Hub */}
      <div className="flex-col h-screen-content" style={{ overflow: 'hidden' }}>
        <ActionPanel sessionId={sessionId} health={systemHealth} />
      </div>
    </div>
  );
}

export default App;

