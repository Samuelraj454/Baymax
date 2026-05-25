import { useState, useCallback, useRef, useEffect } from 'react';
import { API_BASE_URL } from '../config';

const AUDIO_CONSTRAINTS = {
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    channelCount: 1,
  },
};

const WAKE_WORDS = [
  'hey baymax', 'okay baymax', 'hi baymax',
  'baymax', 'hey bay max', 'hey bamax',
  'a baymax', 'hey be max',
];

function matchesWakePhrase(text) {
  const heard = text.toLowerCase().trim();
  return WAKE_WORDS.some((w) => heard.includes(w));
}

function bestTranscript(result) {
  const alts = result[result.length - 1];
  if (!alts || alts.length === 0) return '';
  let best = alts[0];
  for (let i = 1; i < alts.length; i++) {
    if (alts[i].confidence > best.confidence) best = alts[i];
  }
  return best.transcript.trim();
}

export const useVoice = (onWakeWord, setOrbState, setStatus, addMessage, sessionIdRef, setLiveTranscript, setInterimTranscript, setCurrentSpeech, setShowActivationFlash) => {
  const [isListening,    setIsListening]    = useState(false)
  const [isSpeaking,     setIsSpeaking]     = useState(false)
  const [isProcessing,   setIsProcessing]   = useState(false)
  const [micError,       setMicError]       = useState('')
  const [wakeActive,     setWakeActive]     = useState(false)
  const [micReady,       setMicReady]       = useState(false)

  const [voiceSettings, setVoiceSettings] = useState({ language: 'en-IN', rate: 1.05, pitch: 0.85, volume: 1.0 });
  const [availableVoices, setAvailableVoices] = useState({});

  const refreshVoiceSettings = useCallback(async () => {
    try {
      const [voiceRes, voicesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/profile/voice`),
        fetch(`${API_BASE_URL}/voices`)
      ]);
      if (voiceRes.ok && voicesRes.ok) {
        const vs = await voiceRes.json();
        const vc = await voicesRes.json();
        setVoiceSettings(vs);
        setAvailableVoices(vc.voices || {});
        console.log("[BAYMAX] Speech synthesis settings updated:", vs);
      }
    } catch (e) {
      console.error("[BAYMAX] Failed to refresh speech settings:", e);
    }
  }, []);

  useEffect(() => {
    refreshVoiceSettings();
  }, [refreshVoiceSettings]);

  const wakeRecRef       = useRef(null)
  const cmdRecRef        = useRef(null)
  const isSpeakingRef    = useRef(false)
  const isActiveRef      = useRef(false)
  const audioCtxRef      = useRef(null)
  const micStreamRef     = useRef(null)
  const activateRef      = useRef(() => {})

  const getSpeechRecognition = () =>
    window.SpeechRecognition || window.webkitSpeechRecognition

  const ensureAudioContext = useCallback(async () => {
    if (!audioCtxRef.current) {
      const Ctx = window.AudioContext || window.webkitAudioContext
      if (Ctx) audioCtxRef.current = new Ctx()
    }
    if (audioCtxRef.current?.state === 'suspended') {
      await audioCtxRef.current.resume()
    }
  }, [])

  const requestMicAccess = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setMicError('Microphone API not available in this browser.')
      setMicReady(false)
      return false
    }
    try {
      if (micStreamRef.current) {
        micStreamRef.current.getTracks().forEach((t) => t.stop())
        micStreamRef.current = null
      }
      const stream = await navigator.mediaDevices.getUserMedia(AUDIO_CONSTRAINTS)
      micStreamRef.current = stream
      setMicError('')
      setMicReady(true)
      await ensureAudioContext()
      return true
    } catch (err) {
      console.error('[BAYMAX] Mic denied:', err)
      setMicReady(false)
      if (err.name === 'NotFoundError') {
        setMicError('No microphone found. Plug in a mic and refresh.')
      } else if (err.name === 'NotReadableError') {
        setMicError('Microphone is in use by another app. Close it and retry.')
      } else {
        setMicError(
          'Microphone access denied. Click the lock icon in the address bar → Allow microphone.'
        )
      }
      return false
    }
  }, [ensureAudioContext])

  const resetToIdle = useCallback(() => {
    setIsListening(false)
    setIsSpeaking(false)
    setIsProcessing(false)
    if (setOrbState) setOrbState('idle')
    if (setStatus) setStatus('READY')
    if (setLiveTranscript) setLiveTranscript('')
    if (setInterimTranscript) setInterimTranscript('')
    isSpeakingRef.current = false
    isActiveRef.current   = false
    setTimeout(restartWakeWord, 500)
  }, [setOrbState, setStatus, setLiveTranscript, setInterimTranscript])

  const speak = useCallback((text, onDone = null) => {
    if (!text || !text.trim()) {
      if (onDone) onDone()
      return
    }

    if (cmdRecRef.current) {
      try { cmdRecRef.current.abort() } catch (_) {}
      cmdRecRef.current = null
    }

    window.speechSynthesis.cancel()
    isSpeakingRef.current = true
    setIsSpeaking(true)
    if (setOrbState) setOrbState('speaking')
    if (setStatus) setStatus('SPEAKING')
    if (setCurrentSpeech) setCurrentSpeech(text)

    const clean = text
      .replace(/\{[^}]*\}/gs, '')
      .replace(/[*_#`~]/g, '')
      .replace(/[✓✗⏳⚠═─█◆▸→]/g, '')
      .replace(/\s+/g, ' ')
      .trim()

    if (!clean) {
      isSpeakingRef.current = false
      setIsSpeaking(false)
      if (setOrbState) setOrbState('idle')
      if (setStatus) setStatus('READY')
      if (setCurrentSpeech) setCurrentSpeech('')
      if (onDone) onDone()
      return
    }

    const utterance = new SpeechSynthesisUtterance(clean)
    utterance.rate   = voiceSettings.rate   || 1.05
    utterance.pitch  = voiceSettings.pitch  || 0.85
    utterance.volume = voiceSettings.volume || 1.0
    utterance.lang   = voiceSettings.language || 'en-IN'

    const voices = window.speechSynthesis.getVoices()
    let preferred = null
    const catalog = availableVoices[voiceSettings.voiceId]
    if (catalog) {
      preferred = voices.find((v) => v.name === catalog.name)
               || voices.find((v) => v.lang === voiceSettings.language)
    }
    if (!preferred) {
      preferred = voices.find((v) => v.name === 'Google UK English Male')
               || voices.find((v) => v.name.includes('Google') && v.lang.startsWith('en'))
               || voices.find((v) => v.lang.startsWith('en'))
    }
    if (preferred) utterance.voice = preferred

    const finish = () => {
      isSpeakingRef.current = false
      setIsSpeaking(false)
      if (setOrbState) setOrbState('idle')
      if (setStatus) setStatus('READY')
      if (setCurrentSpeech) setCurrentSpeech('')
      if (onDone) onDone()
    }

    const safetyTimer = setTimeout(() => {
      if (isSpeakingRef.current) {
        console.warn('TTS safety timeout triggered')
        window.speechSynthesis.cancel()
        finish()
      }
    }, (clean.split(' ').length / 2.5 * 1000) + 4000)

    utterance.onend = () => {
      clearTimeout(safetyTimer)
      finish()
    }

    utterance.onerror = (e) => {
      clearTimeout(safetyTimer)
      console.error('TTS error:', e.error)
      finish()
    }

    window.speechSynthesis.speak(utterance)
  }, [voiceSettings, availableVoices, setOrbState, setStatus, setCurrentSpeech])

  const startWakeWordListener = useCallback((lang = 'en-IN') => {
    const WS = getSpeechRecognition()
    if (!WS) {
      setMicError('Speech recognition not supported. Use Chrome or Edge.')
      return
    }
    if (!micReady) return

    if (wakeRecRef.current) {
      try { wakeRecRef.current.abort() } catch (_) {}
      wakeRecRef.current = null
    }

    const rec = new WS()
    rec.continuous      = true
    rec.interimResults    = true
    rec.lang              = lang
    rec.maxAlternatives   = 2

    rec.onstart = () => {
      setWakeActive(true)
      setMicError('')
      console.log('[BAYMAX] Wake word listener active, lang:', lang)
    }

    rec.onresult = (event) => {
      if (isActiveRef.current || isSpeakingRef.current) return

      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const chunk = bestTranscript(event.results[i])
        if (event.results[i].isFinal) final += chunk + ' '
        else interim += chunk
      }

      const heard = (final || interim).toLowerCase().trim()
      if (!heard) return

      if (matchesWakePhrase(heard)) {
        console.log('[BAYMAX] Wake word triggered:', heard)
        isActiveRef.current = true
        activateRef.current()
      }
    }

    rec.onerror = (event) => {
      console.warn('[BAYMAX WAKE] Error:', event.error)

      if (event.error === 'not-allowed') {
        setMicError('Microphone blocked. Allow mic in browser site settings.')
        setWakeActive(false)
        setMicReady(false)
        return
      }

      if (event.error === 'audio-capture') {
        setMicError('No audio captured. Check your microphone connection.')
        setWakeActive(false)
        requestMicAccess().then((ok) => ok && startWakeWordListener(lang))
        return
      }

      if (event.error === 'no-speech') return

      setWakeActive(false)
      setTimeout(() => {
        if (!isActiveRef.current && micReady) startWakeWordListener(lang)
      }, 1500)
    }

    rec.onend = () => {
      setWakeActive(false)
      setTimeout(() => {
        if (!isActiveRef.current && micReady) startWakeWordListener(lang)
      }, 400)
    }

    try {
      rec.start()
      wakeRecRef.current = rec
    } catch (e) {
      console.error('[BAYMAX WAKE] Could not start:', e)
      setTimeout(() => startWakeWordListener(lang), 2000)
    }
  }, [micReady, requestMicAccess])

  const restartWakeWord = useCallback(() => {
    isActiveRef.current = false
    setTimeout(() => startWakeWordListener(voiceSettings.language || 'en-IN'), 500)
  }, [voiceSettings.language, startWakeWordListener])

  const playActivationSound = useCallback(async () => {
    try {
      await ensureAudioContext()
      const ctx = audioCtxRef.current
      if (!ctx) return
      const osc  = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.type = 'sine'
      osc.frequency.setValueAtTime(520, ctx.currentTime)
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12)
      gain.gain.setValueAtTime(0.18, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3)
      osc.start(ctx.currentTime)
      osc.stop(ctx.currentTime + 0.3)
    } catch (_) {}
  }, [ensureAudioContext])

  const listenForCommand = useCallback(() => {
    return new Promise((resolve) => {
      const WS = getSpeechRecognition()
      if (!WS) { resolve(''); return }

      const rec = new WS()
      rec.continuous      = true
      rec.interimResults  = true
      rec.lang            = voiceSettings.language || 'en-IN'
      rec.maxAlternatives = 3

      let finalResult = ''
      let silenceTimer = null

      cmdRecRef.current = rec

      if (setOrbState) setOrbState('listening')
      if (setStatus) setStatus('LISTENING')

      const startSilenceTimer = (durationMs) => {
        if (silenceTimer) clearTimeout(silenceTimer)
        silenceTimer = setTimeout(() => {
          console.log(`[BAYMAX CMD] Silence timeout (${durationMs}ms)`)
          try { rec.stop() } catch (_) {}
        }, durationMs)
      }

      startSilenceTimer(6000)

      rec.onresult = (event) => {
        let interim = ''
        let hasNewFinal = false

        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            const chunk = bestTranscript(event.results[i])
            if (chunk) {
              finalResult += chunk + ' '
              hasNewFinal = true
            }
          } else {
            interim += bestTranscript(event.results[i])
          }
        }

        if (hasNewFinal) {
          if (setLiveTranscript) setLiveTranscript(finalResult.trim())
          startSilenceTimer(2200)
        } else if (interim) {
          startSilenceTimer(3200)
        }

        if (setInterimTranscript) setInterimTranscript(interim)
      }

      rec.onerror = (e) => {
        console.error('[BAYMAX CMD] Error:', e.error)
        if (silenceTimer) clearTimeout(silenceTimer)
        cmdRecRef.current = null
        if (e.error === 'no-speech') resolve('')
        else resolve(finalResult.trim())
      }

      rec.onend = () => {
        if (silenceTimer) clearTimeout(silenceTimer)
        cmdRecRef.current = null
        resolve(finalResult.trim())
      }

      try {
        rec.start()
      } catch (e) {
        console.error('[BAYMAX CMD] Cannot start:', e)
        if (silenceTimer) clearTimeout(silenceTimer)
        resolve('')
      }
    })
  }, [voiceSettings.language, setOrbState, setStatus, setLiveTranscript, setInterimTranscript])

  const processCommand = async (transcript, source = 'voice') => {
    if (setOrbState) setOrbState('processing')
    if (setStatus) setStatus('THINKING')
    setIsProcessing(true)

    addMessage({ role: 'user', content: transcript, timestamp: Date.now() })

    try {
      const controller = new AbortController()
      const timeout    = setTimeout(() => controller.abort(), 120000)

      const actualSessionId = typeof sessionIdRef === 'string' ? sessionIdRef : sessionIdRef?.current || 'session_' + Date.now();
      const res = await fetch(`${API_BASE_URL}/query`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        signal:  controller.signal,
        body: JSON.stringify({
          message:    transcript,
          session_id: actualSessionId,
          source:     source
        })
      })

      clearTimeout(timeout)

      if (!res.ok) {
        throw new Error(`Backend returned ${res.status}`)
      }

      const data = await res.json()
      const responseText = data.speak_text || data.response || "Done."

      addMessage({
        role:      'baymax',
        content:   data.response || responseText,
        tool_used: data.tool_used || '',
        open_url:  data.open_url || '',
        timestamp: Date.now()
      })

      if (data.open_url) {
        if (/Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)) {
          window.location.href = data.open_url;
        } else {
          window.open(data.open_url, '_blank');
        }
      }

      if (data.voice_change || data.language_change) {
        await refreshVoiceSettings();
      }

      setIsProcessing(false)
      await new Promise((resolve) => speak(responseText, resolve))

    } catch (err) {
      console.error('[BAYMAX] processCommand error:', err)
      setIsProcessing(false)

      let errMsg = "Something went wrong. Try again."
      if (err.name === 'AbortError') errMsg = "Took too long. Try again."
      else if (!navigator.onLine)    errMsg = "No internet connection."

      addMessage({ role: 'baymax', content: errMsg, timestamp: Date.now() })
      await new Promise((resolve) => speak(errMsg, resolve))

    } finally {
      setIsListening(false)
      setIsProcessing(false)
      if (setLiveTranscript) setLiveTranscript('')
      if (setInterimTranscript) setInterimTranscript('')
      isActiveRef.current = false
      setTimeout(restartWakeWord, 700)
    }
  }

  const activateBaymax = useCallback(async () => {
    if (wakeRecRef.current) {
      try { wakeRecRef.current.abort() } catch (_) {}
      wakeRecRef.current = null
    }

    if (setShowActivationFlash) {
      setShowActivationFlash(true)
      setTimeout(() => setShowActivationFlash(false), 200)
    }
    if (setOrbState) setOrbState('activated')
    if (setStatus) setStatus('LISTENING')
    setIsListening(true)
    await playActivationSound()

    const acks = ["Yeah?", "Go ahead.", "I'm here.", "Listening.", "Mm?"]
    const ack  = acks[Math.floor(Math.random() * acks.length)]

    await new Promise((resolve) => speak(ack, resolve))
    await new Promise((r) => setTimeout(r, 650))

    const command = await listenForCommand()

    if (!command || command.trim().length < 2) {
      console.warn("[BAYMAX] No command detected, resetting.");
      resetToIdle()
      return
    }

    if (setLiveTranscript) setLiveTranscript(command)
    await processCommand(command)
  }, [speak, listenForCommand, resetToIdle, playActivationSound, setOrbState, setStatus, setLiveTranscript, setShowActivationFlash])

  activateRef.current = activateBaymax

  const toggleConversationMode = () => {
     console.log("Conversation mode toggled");
  }

  useEffect(() => {
    const preload = () => window.speechSynthesis.getVoices()
    preload()
    window.speechSynthesis.onvoiceschanged = preload
    return () => { window.speechSynthesis.onvoiceschanged = null }
  }, [])

  useEffect(() => {
    let cancelled = false

    const boot = async () => {
      const ok = await requestMicAccess()
      if (cancelled || !ok) return
      startWakeWordListener(voiceSettings.language || 'en-IN')
    }

    boot()

    return () => {
      cancelled = true
      if (wakeRecRef.current) {
        try { wakeRecRef.current.abort() } catch (_) {}
      }
      if (cmdRecRef.current) {
        try { cmdRecRef.current.abort() } catch (_) {}
      }
      if (micStreamRef.current) {
        micStreamRef.current.getTracks().forEach((t) => t.stop())
        micStreamRef.current = null
      }
      window.speechSynthesis.cancel()
    }
  }, [requestMicAccess, startWakeWordListener, voiceSettings.language])

  return {
    isListening,
    isSpeaking,
    unsupported: micError.includes('not supported'),
    speechError: micError,
    wakeListenerActive: wakeActive,
    micReady,
    isConversationMode: false,
    startWakeWordListener,
    toggleConversationMode,
    activateBaymax,
    processCommand,
    refreshVoiceSettings,
    requestMicAccess,
  }
}
