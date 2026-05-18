import React, { useState, useEffect, useRef } from 'react';
import { X, Settings, User, Globe, Volume2, Save, Info, Music, Shield } from 'lucide-react';
import { API_BASE_URL } from '../config';

const useDebounce = (value, delay = 800) => {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

const COUNTRIES = [
  { code: "IN",  name: "India 🇮🇳" },
  { code: "US",  name: "United States 🇺🇸" },
  { code: "GB",  name: "United Kingdom 🇬🇧" },
  { code: "AU",  name: "Australia 🇦🇺" },
  { code: "CA",  name: "Canada 🇨🇦" },
  { code: "SG",  name: "Singapore 🇸🇬" },
  { code: "AE",  name: "UAE 🇦🇪" },
]

export default function SettingsModal({ isOpen, onClose, sessionId, onVoiceSettingsChange }) {
  const [profile, setProfile] = useState({});
  const [voiceSettings, setVoiceSettings] = useState({});
  const [availableVoices, setAvailableVoices] = useState({});
  const [availableLanguages, setAvailableLanguages] = useState([]);
  
  const [cityInput, setCityInput] = useState('');
  const [countryInput, setCountryInput] = useState('');
  const [nameInput, setNameInput] = useState('');

  const debouncedCity = useDebounce(cityInput, 800);
  const debouncedCountry = useDebounce(countryInput, 800);
  const debouncedName = useDebounce(nameInput, 800);

  const voiceSaveTimer = useRef(null);

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    try {
      const [profRes, voiceRes, voicesRes, langRes] = await Promise.all([
        fetch(`${API_BASE_URL}/profile`),
        fetch(`${API_BASE_URL}/profile/voice`),
        fetch(`${API_BASE_URL}/voices`),
        fetch(`${API_BASE_URL}/languages`)
      ]);
      
      const p = await profRes.json();
      const vs = await voiceRes.json();
      const vc = await voicesRes.json();
      const lg = await langRes.json();

      setProfile(p);
      setVoiceSettings(vs);
      setAvailableVoices(vc.voices || {});
      setAvailableLanguages(lg.languages || []);
      
      setCityInput(p.user_city || '');
      setCountryInput(p.user_country || 'IN');
      setNameInput(p.user_name || '');
    } catch (err) {
      console.error("Failed to load settings data", err);
    }
  };

  useEffect(() => {
    if (debouncedCity && debouncedCity !== profile.user_city) {
      saveProfileField('user_city', debouncedCity);
      setProfile(p => ({...p, user_city: debouncedCity}));
    }
  }, [debouncedCity]);

  useEffect(() => {
    if (debouncedName && debouncedName !== profile.user_name) {
      saveProfileField('user_name', debouncedName);
      setProfile(p => ({...p, user_name: debouncedName}));
    }
  }, [debouncedName]);

  useEffect(() => {
    if (debouncedCountry && debouncedCountry !== profile.user_country) {
      saveProfileField('user_country', debouncedCountry);
      setProfile(p => ({...p, user_country: debouncedCountry}));
    }
  }, [debouncedCountry]);

  const handleProfileChange = (key, value) => {
    setProfile(prev => ({ ...prev, [key]: value }));
    saveProfileField(key, value);
  };

  const handleVoiceChange = async (key, value) => {
    const updated = { ...voiceSettings, [key]: value }
    setVoiceSettings(updated)

    // Save with 500ms debounce
    clearTimeout(voiceSaveTimer.current)
    voiceSaveTimer.current = setTimeout(async () => {
      try {
        await fetch(`${API_BASE_URL}/profile/voice`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(updated)
        });
        if (onVoiceSettingsChange) {
          onVoiceSettingsChange();
        }
      } catch (e) {
        console.error("Error saving voice settings", e);
      }
    }, 500)
  }

  const saveProfileField = async (key, value) => {
    try {
      await fetch(`${API_BASE_URL}/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value })
      });
    } catch (e) { console.error("Error saving profile", e); }
  };

  const testVoice = () => {
    const text = "Hello! This is BAYMAX. How does this voice sound?";
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = voiceSettings.rate;
    utterance.pitch = voiceSettings.pitch;
    utterance.volume = voiceSettings.volume;
    utterance.lang = voiceSettings.language;

    const voices = window.speechSynthesis.getVoices();
    const catalog = availableVoices[voiceSettings.voiceId];
    if (catalog) {
      const v = voices.find(v => v.name === catalog.name) || voices.find(v => v.lang === voiceSettings.language);
      if (v) utterance.voice = v;
    }
    window.speechSynthesis.speak(utterance);
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '20px'
    }}>
      <div className="glass-panel" style={{ 
        width: '100%', maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto',
        padding: '32px', border: '1px solid var(--accent-cyan)', 
        boxShadow: '0 0 40px rgba(0,240,255,0.15)', borderRadius: '16px'
      }}>
        <div className="flex justify-between items-center" style={{ marginBottom: '32px', borderBottom: '1px solid rgba(0,255,255,0.2)', paddingBottom: '16px' }}>
          <div className="flex items-center" style={{ gap: '12px' }}>
            <Settings className="text-cyan" size={28} />
            <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: 'white', margin: 0 }}>BAYMAX Settings</h2>
          </div>
          <button onClick={() => { onClose(); }} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', padding: '8px' }}>
            <X size={24} />
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
          
          {/* Left Column */}
          <div className="flex-col" style={{ gap: '24px' }}>
            
            {/* Voice Settings */}
            <div className="flex-col" style={{ gap: '16px', background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px' }}>
              <h3 className="flex items-center text-cyan" style={{ gap: '8px', margin: 0, fontSize: '16px' }}><Volume2 size={18}/> Voice Settings</h3>
              
              <div className="flex-col" style={{ gap: '8px' }}>
                <label style={{ fontSize: '12px', opacity: 0.8 }}>Voice Style</label>
                <select 
                  className="glass-panel"
                  value={voiceSettings.voiceId || ''}
                  onChange={e => handleVoiceChange('voiceId', e.target.value)}
                  style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', color: 'white', borderRadius: '6px' }}
                >
                  {Object.entries(availableVoices).map(([id, info]) => (
                    <option key={id} value={id}>{info.label}</option>
                  ))}
                </select>
              </div>

              <div className="flex-col" style={{ gap: '8px' }}>
                <div className="flex justify-between" style={{ fontSize: '12px', opacity: 0.8 }}>
                  <span>Speaking Speed</span>
                  <span>{voiceSettings.rate}x</span>
                </div>
                <input type="range" min="0.5" max="2.0" step="0.1" 
                  value={voiceSettings.rate || 1.05} 
                  onChange={e => handleVoiceChange('rate', parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
                />
              </div>

              <div className="flex-col" style={{ gap: '8px' }}>
                <div className="flex justify-between" style={{ fontSize: '12px', opacity: 0.8 }}>
                  <span>Pitch (Deep ←→ High)</span>
                  <span>{voiceSettings.pitch}</span>
                </div>
                <input type="range" min="0.5" max="1.5" step="0.1" 
                  value={voiceSettings.pitch || 0.85} 
                  onChange={e => handleVoiceChange('pitch', parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
                />
              </div>

              <div className="flex-col" style={{ gap: '8px' }}>
                <div className="flex justify-between" style={{ fontSize: '12px', opacity: 0.8 }}>
                  <span>Volume</span>
                  <span>{Math.round((voiceSettings.volume || 1.0) * 100)}%</span>
                </div>
                <input type="range" min="0.0" max="1.0" step="0.1" 
                  value={voiceSettings.volume || 1.0} 
                  onChange={e => handleVoiceChange('volume', parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
                />
              </div>

              <button 
                onClick={testVoice}
                style={{ padding: '8px', background: 'rgba(0,255,255,0.1)', border: '1px solid var(--accent-cyan)', color: 'var(--accent-cyan)', borderRadius: '6px', cursor: 'pointer', marginTop: '8px' }}
              >
                Test Voice
              </button>
            </div>

            {/* Language Settings */}
            <div className="flex-col" style={{ gap: '16px', background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px' }}>
              <h3 className="flex items-center text-cyan" style={{ gap: '8px', margin: 0, fontSize: '16px' }}><Globe size={18}/> Language Settings</h3>
              
              <div className="flex-col" style={{ gap: '8px' }}>
                <label style={{ fontSize: '12px', opacity: 0.8 }}>Interface Language</label>
                <select 
                  className="glass-panel"
                  value={voiceSettings.language || 'en-IN'}
                  onChange={e => handleVoiceChange('language', e.target.value)}
                  style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', color: 'white', borderRadius: '6px' }}
                >
                  {availableLanguages.map((lg) => (
                    <option key={lg.code} value={lg.code}>{lg.flag} {lg.name}</option>
                  ))}
                </select>
              </div>
            </div>

          </div>

          {/* Right Column */}
          <div className="flex-col" style={{ gap: '24px' }}>
            
            {/* Personal Profile */}
            <div className="flex-col" style={{ gap: '16px', background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px' }}>
              <h3 className="flex items-center text-cyan" style={{ gap: '8px', margin: 0, fontSize: '16px' }}><User size={18}/> Personal Profile</h3>
              
              <div className="flex-col" style={{ gap: '8px' }}>
                <div className="flex justify-between">
                  <label style={{ fontSize: '12px', opacity: 0.8 }}>Your Name</label>
                  {debouncedName !== nameInput && <span style={{color:'grey', fontSize:'11px'}}>typing...</span>}
                  {debouncedName === nameInput && nameInput && <span style={{color:'teal', fontSize:'11px'}}>✓ saved</span>}
                </div>
                <input 
                  className="glass-panel"
                  value={nameInput}
                  onChange={e => setNameInput(e.target.value)}
                  style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', color: 'white', borderRadius: '6px' }}
                />
              </div>

              <div className="flex-col" style={{ gap: '8px' }}>
                <div className="flex justify-between">
                  <label style={{ fontSize: '12px', opacity: 0.8 }}>Your City</label>
                  {debouncedCity !== cityInput && <span style={{color:'grey', fontSize:'11px'}}>typing...</span>}
                  {debouncedCity === cityInput && cityInput && <span style={{color:'teal', fontSize:'11px'}}>✓ saved</span>}
                </div>
                <input 
                  className="glass-panel"
                  value={cityInput}
                  onChange={e => setCityInput(e.target.value)}
                  placeholder="Your city"
                  style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', color: 'white', borderRadius: '6px' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '16px' }}>
                <div className="flex-col" style={{ gap: '8px', flex: 1 }}>
                  <div className="flex justify-between">
                    <label style={{ fontSize: '12px', opacity: 0.8 }}>Country Code</label>
                    {debouncedCountry !== countryInput && <span style={{color:'grey', fontSize:'11px'}}>...</span>}
                  </div>
                  <select 
                    className="glass-panel"
                    value={countryInput}
                    onChange={e => setCountryInput(e.target.value)}
                    style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', color: 'white', borderRadius: '6px' }}
                  >
                    {COUNTRIES.map(c => (
                      <option key={c.code} value={c.code}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div className="flex-col" style={{ gap: '8px', flex: 1 }}>
                  <label style={{ fontSize: '12px', opacity: 0.8 }}>Timezone</label>
                  <input 
                    className="glass-panel"
                    value={profile.user_timezone || ''}
                    onChange={e => handleProfileChange('user_timezone', e.target.value)}
                    style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', color: 'white', borderRadius: '6px' }}
                  />
                </div>
              </div>
            </div>

            {/* Preferences */}
            <div className="flex-col" style={{ gap: '16px', background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px' }}>
              <h3 className="flex items-center text-cyan" style={{ gap: '8px', margin: 0, fontSize: '16px' }}><Music size={18}/> Preferences</h3>
              
              <div className="flex-col" style={{ gap: '8px' }}>
                <label style={{ fontSize: '12px', opacity: 0.8 }}>Preferred Music Genre</label>
                <input 
                  className="glass-panel"
                  value={profile.preferred_music_genre || ''}
                  onChange={e => handleProfileChange('preferred_music_genre', e.target.value)}
                  style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', color: 'white', borderRadius: '6px' }}
                />
              </div>

              <div className="flex-col" style={{ gap: '8px' }}>
                <label style={{ fontSize: '12px', opacity: 0.8 }}>Preferred News Category</label>
                <select 
                  className="glass-panel"
                  value={profile.preferred_news_category || 'technology'}
                  onChange={e => handleProfileChange('preferred_news_category', e.target.value)}
                  style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', color: 'white', borderRadius: '6px' }}
                >
                  <option value="technology">Technology</option>
                  <option value="business">Business</option>
                  <option value="general">General</option>
                  <option value="science">Science</option>
                  <option value="sports">Sports</option>
                </select>
              </div>

            </div>

            {/* System Info */}
            <div className="flex-col" style={{ gap: '8px', background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px', fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}>
              <h3 className="flex items-center text-cyan" style={{ gap: '8px', margin: 0, fontSize: '14px', marginBottom: '8px' }}><Info size={16}/> System Info</h3>
              <div className="flex justify-between"><span>BAYMAX Version:</span> <span>10.0</span></div>
              <div className="flex justify-between"><span>Last Active:</span> <span>{profile.last_active || 'Never'}</span></div>
              <div className="flex justify-between"><span>Most Used Tool:</span> <span>{profile.most_used_tool || 'None'}</span></div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
