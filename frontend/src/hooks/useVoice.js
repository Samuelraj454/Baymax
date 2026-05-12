import { useState, useCallback, useRef, useEffect } from 'react';

export const useVoice = (onWakeWord, setOrbState, setStatus, addMessage, sessionIdRef, setLiveTranscript, setInterimTranscript, setCurrentSpeech, setShowActivationFlash) => {
  // ── STATE VARIABLES ──────────────────────────────────────────
  const [isListening,    setIsListening]    = useState(false)
  const [isSpeaking,     setIsSpeaking]     = useState(false)
  const [isProcessing,   setIsProcessing]   = useState(false)
  const [micError,       setMicError]       = useState('')
  const [wakeActive,     setWakeActive]     = useState(false)

  const [voiceSettings, setVoiceSettings] = useState({ language: 'en-IN', rate: 1.05, pitch: 0.85, volume: 1.0 });

  // Refs — don't trigger re-renders
  const wakeRecRef    = useRef(null)
  const cmdRecRef     = useRef(null)
  const isSpeakingRef = useRef(false)   // ← ref for callbacks
  const isActiveRef   = useRef(false)   // ← ref for wake word check

  // ── SAFE STATE RESET ─────────────────────────────────────────
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
    // Restart wake word after 500ms
    setTimeout(restartWakeWord, 500)
  }, [setOrbState, setStatus, setLiveTranscript, setInterimTranscript])

  // ── SPEAK FUNCTION (FIXED) ───────────────────────────────────
  const speak = useCallback((text, onDone = null) => {
    if (!text || !text.trim()) {
      if (onDone) onDone()
      return
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

    const utterance     = new SpeechSynthesisUtterance(clean)
    utterance.rate      = voiceSettings.rate   || 1.05
    utterance.pitch     = voiceSettings.pitch  || 0.85
    utterance.volume    = voiceSettings.volume || 1.0
    utterance.lang      = voiceSettings.language || 'en-IN'

    // Voice selection
    const voices = window.speechSynthesis.getVoices()
    const preferred = voices.find(v => v.name === 'Google UK English Male')
                   || voices.find(v => v.name.includes('Google') && v.lang.startsWith('en'))
                   || voices.find(v => v.lang.startsWith('en'))
    if (preferred) utterance.voice = preferred

    // CRITICAL: Always reset on end or error
    utterance.onend = () => {
      isSpeakingRef.current = false
      setIsSpeaking(false)
      if (setOrbState) setOrbState('idle')
      if (setStatus) setStatus('READY')
      if (setCurrentSpeech) setCurrentSpeech('')
      if (onDone) onDone()
    }

    utterance.onerror = (e) => {
      console.error('TTS error:', e.error)
      isSpeakingRef.current = false
      setIsSpeaking(false)
      if (setOrbState) setOrbState('idle')
      if (setStatus) setStatus('READY')
      if (setCurrentSpeech) setCurrentSpeech('')
      if (onDone) onDone()
    }

    // Safety timeout — force reset if TTS hangs
    const safetyTimer = setTimeout(() => {
      if (isSpeakingRef.current) {
        console.warn('TTS safety timeout triggered')
        window.speechSynthesis.cancel()
        isSpeakingRef.current = false
        setIsSpeaking(false)
        if (setOrbState) setOrbState('idle')
        if (setStatus) setStatus('READY')
        if (setCurrentSpeech) setCurrentSpeech('')
        if (onDone) onDone()
      }
    }, (clean.split(' ').length / 2.5 * 1000) + 3000)

    utterance.onend = () => {
      clearTimeout(safetyTimer)
      isSpeakingRef.current = false
      setIsSpeaking(false)
      if (setOrbState) setOrbState('idle')
      if (setStatus) setStatus('READY')
      if (setCurrentSpeech) setCurrentSpeech('')
      if (onDone) onDone()
    }

    window.speechSynthesis.speak(utterance)
  }, [voiceSettings, setOrbState, setStatus, setCurrentSpeech])

  // ── WAKE WORD LISTENER (FIXED RESTART LOOP) ──────────────────
  const startWakeWordListener = useCallback((lang = 'en-IN') => {
    const WS = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!WS) {
      setMicError('Speech recognition not supported. Use Chrome or Edge.')
      return
    }

    // Stop existing listener first
    if (wakeRecRef.current) {
      try { wakeRecRef.current.abort() } catch(e) {}
      wakeRecRef.current = null
    }

    const rec = new WS()
    rec.continuous     = true
    rec.interimResults = false
    rec.lang           = lang
    rec.maxAlternatives = 1

    const WAKE_WORDS = [
      'hey baymax', 'okay baymax', 'hi baymax',
      'baymax', 'hey bay max', 'hey bamax',
      'a baymax', 'hey be max'   // common misheard variants
    ]

    rec.onstart = () => {
      setWakeActive(true)
      setMicError('')
      console.log('[BAYMAX] Wake word listener active, lang:', lang)
    }

    rec.onresult = (event) => {
      // Don't trigger if already active or speaking
      if (isActiveRef.current || isSpeakingRef.current) return

      const heard = event.results[event.results.length - 1][0]
                    .transcript.toLowerCase().trim()

      console.log('[BAYMAX WAKE] Heard:', heard)

      const triggered = WAKE_WORDS.some(w => heard.includes(w))
      if (triggered) {
        console.log('[BAYMAX] Wake word triggered!')
        isActiveRef.current = true
        activateBaymax()
      }
    }

    rec.onerror = (event) => {
      console.warn('[BAYMAX WAKE] Error:', event.error)

      if (event.error === 'not-allowed') {
        setMicError('Microphone blocked. Click the mic icon in Chrome address bar and allow.')
        setWakeActive(false)
        return
      }

      if (event.error === 'no-speech') {
        // Normal — just restart
        return
      }

      // For all other errors — restart after delay
      setWakeActive(false)
      setTimeout(() => {
        if (!isActiveRef.current) {
          startWakeWordListener(lang)
        }
      }, 1500)
    }

    rec.onend = () => {
      setWakeActive(false)
      console.log('[BAYMAX WAKE] Listener ended. Restarting...')
      // Always restart unless currently processing a command
      setTimeout(() => {
        if (!isActiveRef.current) {
          startWakeWordListener(lang)
        }
      }, 300)
    }

    try {
      rec.start()
      wakeRecRef.current = rec
    } catch (e) {
      console.error('[BAYMAX WAKE] Could not start:', e)
      setTimeout(() => startWakeWordListener(lang), 2000)
    }
  }, [])

  const restartWakeWord = useCallback(() => {
    isActiveRef.current = false
    setTimeout(() => startWakeWordListener(voiceSettings.language || 'en-IN'), 400)
  }, [voiceSettings.language, startWakeWordListener])

  // ── ACTIVATION SOUND ─────────────────────────────────────────
  const playActivationSound = () => {
    try {
      const ctx  = new (window.AudioContext || window.webkitAudioContext)()
      const osc  = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.type = 'sine'
      osc.frequency.setValueAtTime(600, ctx.currentTime)
      osc.frequency.exponentialRampToValueAtTime(900, ctx.currentTime + 0.1)
      gain.gain.setValueAtTime(0.2, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25)
      osc.start(ctx.currentTime)
      osc.stop(ctx.currentTime + 0.25)
    } catch(e) {}
  }

  // ── COMMAND LISTENER (FIXED) ─────────────────────────────────
  const listenForCommand = () => {
    return new Promise((resolve) => {
      const WS = window.SpeechRecognition || window.webkitSpeechRecognition
      if (!WS) { resolve(''); return }

      const rec = new WS()
      rec.continuous     = false
      rec.interimResults = true
      rec.lang           = voiceSettings.language || 'en-IN'
      rec.maxAlternatives = 3

      let finalResult = ''
      let hasResult   = false

      cmdRecRef.current = rec

      if (setOrbState) setOrbState('listening')
      if (setStatus) setStatus('LISTENING')

      rec.onresult = (event) => {
        let interim = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalResult += event.results[i][0].transcript + ' '
            hasResult   = true
            if (setLiveTranscript) setLiveTranscript(finalResult.trim())
          } else {
            interim += event.results[i][0].transcript
            if (setInterimTranscript) setInterimTranscript(interim)
          }
        }
      }

      rec.onend = () => {
        cmdRecRef.current = null
        resolve(finalResult.trim())
      }

      rec.onerror = (e) => {
        console.error('[BAYMAX CMD] Error:', e.error)
        cmdRecRef.current = null
        resolve(finalResult.trim())
      }

      // Timeout safety — max 12 seconds
      const timeout = setTimeout(() => {
        try { rec.stop() } catch(e) {}
      }, 12000)

      rec.onend = () => {
        clearTimeout(timeout)
        cmdRecRef.current = null
        resolve(finalResult.trim())
      }

      try {
        rec.start()
      } catch(e) {
        console.error('[BAYMAX CMD] Cannot start:', e)
        resolve('')
      }
    })
  }

  // ── ACTIVATION (FIXED) ───────────────────────────────────────
  const activateBaymax = useCallback(async () => {
    // Stop wake word listener while command is active
    if (wakeRecRef.current) {
      try { wakeRecRef.current.abort() } catch(e) {}
      wakeRecRef.current = null
    }

    if (setShowActivationFlash) {
      setShowActivationFlash(true)
      setTimeout(() => setShowActivationFlash(false), 200)
    }
    if (setOrbState) setOrbState('activated')
    if (setStatus) setStatus('LISTENING')
    setIsListening(true)
    playActivationSound()

    // Speak acknowledgment then immediately listen
    const acks = ["Yeah?", "Go ahead.", "I'm here.", "Listening.", "Mm?"]
    const ack  = acks[Math.floor(Math.random() * acks.length)]

    await new Promise(resolve => speak(ack, resolve))
    await new Promise(r => setTimeout(r, 200))

    // Listen for command
    const command = await listenForCommand()

    if (!command || command.trim().length < 2) {
      speak("Didn't catch that.", resetToIdle)
      return
    }

    if (setLiveTranscript) setLiveTranscript(command)
    await processCommand(command)
  }, [speak, resetToIdle, setOrbState, setStatus, setLiveTranscript, setShowActivationFlash])

  // ── PROCESS COMMAND (FIXED WITH ALWAYS-RESET) ────────────────
  const processCommand = async (transcript) => {
    if (setOrbState) setOrbState('processing')
    if (setStatus) setStatus('THINKING')
    setIsProcessing(true)

    // Ensure it uses content instead of text to match App.jsx interface
    addMessage({ role: 'user', content: transcript, timestamp: Date.now() })

    try {
      const controller = new AbortController()
      const timeout    = setTimeout(() => controller.abort(), 30000)

      const actualSessionId = typeof sessionIdRef === 'string' ? sessionIdRef : sessionIdRef?.current || 'session_' + Date.now();
      const res = await fetch('http://localhost:8000/query', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        signal:  controller.signal,
        body: JSON.stringify({
          message:    transcript,
          session_id: actualSessionId,
          source:     'voice'
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
        timestamp: Date.now()
      })

      setIsProcessing(false)

      // Speak response — reset to idle when done
      await new Promise(resolve => speak(responseText, resolve))

    } catch (err) {
      console.error('[BAYMAX] processCommand error:', err)
      setIsProcessing(false)

      let errMsg = "Something went wrong. Try again."
      if (err.name === 'AbortError') errMsg = "Took too long. Try again."
      else if (!navigator.onLine)    errMsg = "No internet connection."

      addMessage({ role: 'baymax', content: errMsg, timestamp: Date.now() })
      await new Promise(resolve => speak(errMsg, resolve))

    } finally {
      // ALWAYS reset — no matter what happened
      setIsListening(false)
      setIsProcessing(false)
      if (setLiveTranscript) setLiveTranscript('')
      if (setInterimTranscript) setInterimTranscript('')
      isActiveRef.current = false
      // Restart wake word listener
      setTimeout(restartWakeWord, 600)
    }
  }

  const toggleConversationMode = () => {
     console.log("Conversation mode toggled");
  }

  // ── STARTUP ──────────────────────────────────────────────────
  useEffect(() => {
    // Check mic permission first
    navigator.mediaDevices?.getUserMedia({ audio: true })
      .then(() => {
        console.log('[BAYMAX] Mic permission granted')
      })
      .catch((err) => {
        console.error('[BAYMAX] Mic denied:', err)
        setMicError(
          'Microphone access denied. ' +
          'Click the camera icon in Chrome address bar → Allow microphone.'
        )
      })

    return () => {
      // Cleanup on unmount
      if (wakeRecRef.current) {
        try { wakeRecRef.current.abort() } catch(e) {}
      }
      window.speechSynthesis.cancel()
    }
  }, [])

  return {
    isListening,
    isSpeaking,
    unsupported: micError.includes('not supported'),
    speechError: micError,
    wakeListenerActive: wakeActive,
    isConversationMode: false,
    startWakeWordListener,
    toggleConversationMode,
    activateBaymax,
    processCommand
  }
}
