import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, BookOpen, Lightbulb, Code2, HelpCircle,
  ExternalLink, Bot, User, ChevronDown, ChevronUp,
  ThumbsUp, ThumbsDown, Sparkles, Mic, MicOff, Volume2,
} from 'lucide-react'

import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import { streamSSE } from '@/lib/sse'
import { useUIStore } from '@/store/uiStore'
import api from '@/lib/api'
import { voiceApi } from '@/lib/api'
import type { SourceItem } from '@/types'

// ── Types ─────────────────────────────────────────────────────────────────────
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceItem[]
  streaming?: boolean
}

type ExplainMode = 'eli5' | 'highschool' | 'college' | 'researcher' | 'exam' | 'interview'

const EXPLAIN_MODES: { id: ExplainMode; label: string; emoji: string }[] = [
  { id: 'eli5',        label: 'ELI5',        emoji: '🧒' },
  { id: 'highschool',  label: 'High School',  emoji: '📚' },
  { id: 'college',     label: 'College',      emoji: '🎓' },
  { id: 'researcher',  label: 'Researcher',   emoji: '🔬' },
  { id: 'exam',        label: 'Exam',         emoji: '📝' },
  { id: 'interview',   label: 'Interview',    emoji: '💼' },
]

// ── Section tabs ──────────────────────────────────────────────────────────────
const TABS = [
  { key: 'explanation',        label: 'Explanation', icon: BookOpen  },
  { key: 'analogy',            label: 'Analogy',     icon: Lightbulb },
  { key: 'example',            label: 'Example',     icon: Code2     },
  { key: 'practice_questions', label: 'Practice',    icon: HelpCircle },
]

function parseSection(content: string, key: string): string {
  const headers: Record<string, string[]> = {
    explanation:        ['## Explanation', '**Explanation**'],
    analogy:            ['## Analogy', '**Analogy**'],
    example:            ['## Worked Example', '**Worked Example**'],
    practice_questions: ['## Practice Questions', '**Practice Questions**'],
  }
  const markers    = headers[key] ?? []
  const allMarkers = Object.values(headers).flat()
  let start = -1, marker = ''
  for (const m of markers) {
    const i = content.indexOf(m)
    if (i !== -1 && (start === -1 || i < start)) { start = i; marker = m }
  }
  if (start === -1) return key === 'explanation' ? content : ''
  const contentStart = start + marker.length
  let end = content.length
  for (const m of allMarkers) {
    if (m === marker) continue
    const i = content.indexOf(m, contentStart)
    if (i !== -1 && i < end) end = i
  }
  return content.slice(contentStart, end).trim()
}

function StreamingCursor() {
  return (
    <span
      className="animate-blink"
      style={{ display: 'inline-block', width: 2, height: '1em', background: 'var(--primary)', verticalAlign: 'text-bottom', marginLeft: 2 }}
    />
  )
}

// ── Sources Panel ──────────────────────────────────────────────────────────────
function SourcesPanel({ sources }: { sources: SourceItem[] }) {
  const [open, setOpen] = useState(false)

  return (
    <div style={{ marginTop: 16, borderRadius: 12, border: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)', overflow: 'hidden' }}>
      <button
        onClick={() => setOpen(v => !v)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 16px', background: 'transparent',
          border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: 13, fontWeight: 500,
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ExternalLink size={14} />
          Sources ({sources.length})
        </span>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '0 16px 12px', display: 'flex', flexDirection: 'column', gap: 12 }}>
              {sources.map((s, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 8,
                    background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}>
                    <BookOpen size={12} color="var(--text-muted)" />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {s.source}
                      </span>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)', flexShrink: 0, marginLeft: 8 }}>p.{s.page}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ── Rating buttons ─────────────────────────────────────────────────────────────
function RatingButtons({ msgId, topic }: { msgId: string; topic: string }) {
  const [rated, setRated] = useState<1 | -1 | null>(null)

  const rate = async (rating: 1 | -1) => {
    if (rated !== null) return
    setRated(rating)
    try {
      await api.post('/api/v1/mentor/feedback', { rating, topic, message_id: msgId })
      toast.success('Thanks for the feedback!', { duration: 2000 })
    } catch {
      // non-critical: silently swallow
    }
  }

  return (
    <div className="msg-rating" style={{ display: 'flex', gap: 6, marginTop: 12, opacity: 0, transition: 'opacity 0.2s ease' }}>
      <button
        onClick={() => rate(1)}
        disabled={rated !== null}
        title="Helpful"
        style={{
          background: rated === 1 ? 'var(--bg-elevated)' : 'transparent',
          border: '1px solid', borderColor: rated === 1 ? 'var(--success)' : 'var(--border-subtle)',
          borderRadius: 8, padding: '4px 10px', cursor: rated !== null ? 'default' : 'pointer',
          color: rated === 1 ? 'var(--success)' : 'var(--text-muted)', fontSize: 12,
          display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.15s',
        }}
      >
        <ThumbsUp size={12} /> {rated === 1 ? 'Helpful' : ''}
      </button>
      <button
        onClick={() => rate(-1)}
        disabled={rated !== null}
        title="Not helpful"
        style={{
          background: rated === -1 ? 'var(--bg-elevated)' : 'transparent',
          border: '1px solid', borderColor: rated === -1 ? 'var(--danger)' : 'var(--border-subtle)',
          borderRadius: 8, padding: '4px 10px', cursor: rated !== null ? 'default' : 'pointer',
          color: rated === -1 ? 'var(--danger)' : 'var(--text-muted)', fontSize: 12,
          display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.15s',
        }}
      >
        <ThumbsDown size={12} />
      </button>
    </div>
  )
}

// ── Assistant message ──────────────────────────────────────────────────────────
function AssistantMessage({ msg, topic }: { msg: Message; topic: string }) {
  const [activeTab, setActiveTab] = useState('explanation')
  const tabContent = parseSection(msg.content, activeTab)

  return (
    <div
      className="assistant-msg"
      style={{ display: 'flex', gap: 16, alignItems: 'flex-start', maxWidth: '85%' }}
    >
      <div style={{
        width: 32, height: 32, borderRadius: 10,
        background: 'var(--primary)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        boxShadow: 'var(--shadow-sm)',
      }}>
        <Bot size={16} color="#fff" />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Tabs */}
        {!msg.streaming && (
          <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
            {TABS.map(({ key, label, icon: Icon }) => {
              const has = parseSection(msg.content, key).length > 10
              if (!has && key !== 'explanation') return null
              return (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: 99,
                    fontSize: 13, fontWeight: 500, cursor: 'pointer',
                    background: activeTab === key ? 'var(--primary)' : 'transparent',
                    border: '1px solid',
                    borderColor: activeTab === key ? 'var(--primary)' : 'var(--border-subtle)',
                    color: activeTab === key ? '#fff' : 'var(--text-secondary)',
                    transition: 'all 0.15s',
                  }}
                >
                  <Icon size={12} /> {label}
                </button>
              )
            })}
          </div>
        )}

        {/* Content */}
        <div style={{ fontSize: 15, lineHeight: 1.6, color: 'var(--text-primary)' }} className="markdown-content">
          {msg.streaming
            ? <>{msg.content}<StreamingCursor /></>
            : <ReactMarkdown>{tabContent || msg.content}</ReactMarkdown>
          }
        </div>

        {/* Sources */}
        {!msg.streaming && msg.sources && msg.sources.length > 0 && (
          <SourcesPanel sources={msg.sources} />
        )}

        {/* Rating */}
        {!msg.streaming && (
          <RatingButtons msgId={msg.id} topic={topic} />
        )}
      </div>

      {/* Hover effect: show rating on hover */}
      <style>{`
        .assistant-msg:hover .msg-rating { opacity: 1 !important; }
      `}</style>
    </div>
  )
}

// ── Explain Mode Selector ──────────────────────────────────────────────────────
function ExplainModeSelector({
  mode, onChange,
}: {
  mode: ExplainMode
  onChange: (m: ExplainMode) => void
}) {
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12, alignItems: 'center' }}>
      <span style={{ color: 'var(--text-secondary)', fontSize: 12, fontWeight: 500, marginRight: 4, flexShrink: 0 }}>
        Adapt style:
      </span>
      {EXPLAIN_MODES.map(({ id, label, emoji }) => (
        <motion.button
          key={id}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onChange(id)}
          style={{
            padding: '4px 12px', borderRadius: 99, fontSize: 12, fontWeight: 500, cursor: 'pointer',
            border: '1px solid', borderColor: mode === id ? 'var(--primary)' : 'var(--border-subtle)',
            background: mode === id ? 'var(--primary-subtle)' : 'var(--bg-elevated)',
            color: mode === id ? 'var(--primary)' : 'var(--text-secondary)',
            transition: 'all 0.15s',
            boxShadow: mode === id ? 'none' : 'var(--shadow-sm)',
          }}
        >
          {emoji} {label}
        </motion.button>
      ))}
    </div>
  )
}

// ── Main TutorPage ─────────────────────────────────────────────────────────────
export default function TutorPage() {
  const { currentTopic, selectedLevel } = useUIStore()
  const topic = currentTopic || 'Neural Networks'
  const level = selectedLevel  || 'Intermediate'

  const [messages, setMessages]       = useState<Message[]>([
    {
      id: '0', role: 'assistant', streaming: false,
      content: `## Explanation\nHello! I'm **Synapse**, your adaptive AI tutor. You're studying **${topic}** at **${level}** level.\n\nAsk me anything — I'll explain concepts, give analogies, walk through examples, and provide practice questions tailored to your level.\n\n## Analogy\nThink of me as a private tutor who knows exactly where you are in your learning journey and adapts every explanation to match your level.\n\n## Worked Example\nFor example, try asking: *"What is ${topic} and why does it matter?"* or *"Can you give me a beginner-friendly explanation of the core concepts?"*\n\n## Practice Questions\n1. What topics within ${topic} are you most curious about?\n2. What's your current understanding of ${topic}?\n3. Are there specific concepts you found confusing before?`,
    },
  ])
  const [input, setInput]             = useState('')
  const [streaming, setStreaming]     = useState(false)
  const [explainMode, setExplainMode] = useState<ExplainMode>('college')
  const [voiceMode, setVoiceMode]     = useState(false)
  const [recording, setRecording]     = useState(false)
  const [ttsLoading, setTtsLoading]   = useState(false)
  const bottomRef                     = useRef<HTMLDivElement>(null)
  const cleanupRef                    = useRef<(() => void) | null>(null)
  const inputRef                      = useRef(input)
  const topicRef                      = useRef(topic)
  const explainModeRef                = useRef(explainMode)
  const voiceModeRef                  = useRef(voiceMode)
  const mediaRecorderRef              = useRef<MediaRecorder | null>(null)
  const audioChunksRef                = useRef<Blob[]>([])
  const audioRef                      = useRef<HTMLAudioElement | null>(null)

  // ── Voice: TTS playback ──────────────────────────────────────────────────
  const speakText = useCallback(async (text: string) => {
    if (!voiceModeRef.current) return
    if (!text || text.startsWith('❌')) return
    setTtsLoading(true)
    try {
      // Use browser's built-in SpeechSynthesis — no API key, no network, no autoplay issues
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel()
        const utterance = new SpeechSynthesisUtterance(text.slice(0, 2000))
        utterance.lang = 'en-US'
        utterance.rate = 1.1
        utterance.pitch = 1.0
        utterance.onend = () => setTtsLoading(false)
        utterance.onerror = () => setTtsLoading(false)
        window.speechSynthesis.speak(utterance)
        return  // don't fall through to backend TTS
      }
    } catch { /* SpeechSynthesis not available, fall through */ }

    // Fallback: backend TTS
    try {
      const { data } = await voiceApi.tts(text.slice(0, 1000))
      if (data.audio_url) {
        const url = data.audio_url.startsWith('http') ? data.audio_url : `http://localhost:8000${data.audio_url}`
        if (audioRef.current) audioRef.current.pause()
        const audio = new Audio(url)
        audioRef.current = audio
        await audio.play()
      }
    } catch { /* TTS not available */ }
    setTtsLoading(false)
  }, [])

  // ── Voice: STT recording ─────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      mediaRecorderRef.current = mr
      audioChunksRef.current = []
      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data) }
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        if (blob.size < 1000) return
        try {
          const { data } = await voiceApi.stt(blob)
          if (data.transcript) setInput(prev => prev + data.transcript)
        } catch { toast.error('Speech recognition failed') }
      }
      mr.start()
      setRecording(true)
    } catch { toast.error('Microphone access denied') }
  }, [])

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop()
    mediaRecorderRef.current = null
    setRecording(false)
  }, [])

  useEffect(() => { inputRef.current = input }, [input])
  useEffect(() => { topicRef.current = topic }, [topic])
  useEffect(() => { explainModeRef.current = explainMode }, [explainMode])
  useEffect(() => { voiceModeRef.current = voiceMode }, [voiceMode])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async () => {
    const currentInput = inputRef.current
    if (!currentInput.trim() || streaming) return
    const question = currentInput.trim()
    setInput('')

    const userMsg: Message      = { id: Date.now().toString(), role: 'user', content: question }
    const assistantId           = (Date.now() + 1).toString()
    const assistantMsg: Message = { id: assistantId, role: 'assistant', content: '', streaming: true }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setStreaming(true)

    let accumulated = ''
    let sources: SourceItem[] = []

    const modeMap: Record<string, string> = {
      highschool: 'high_school',
    }
    const backendMode = modeMap[explainModeRef.current] ?? explainModeRef.current

    const cleanup = await streamSSE('/api/v1/agent/tutor', {
      question,
      topic: topicRef.current,
      explain_mode: backendMode,
    }, {
      onChunk: (text) => {
        accumulated += text
        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: accumulated } : m))
      },
      onSources: (srcs) => { sources = srcs as SourceItem[] },
      onDone: () => {
        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, streaming: false, sources } : m))
        setStreaming(false)
        if (voiceModeRef.current && accumulated) speakText(accumulated)
      },
      onError: (err) => {
        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: `❌ Error: ${err}`, streaming: false } : m))
        setStreaming(false)
      },
      onEvent: (event) => {
        switch (event.type) {
          case 'plan':
            accumulated += `**Planning:** ${(event.steps ?? []).join(', ')}\n\n`
            setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: accumulated } : m))
            break
          case 'analogy':
            accumulated += `**Analogy:**\n${event.content}\n\n`
            setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: accumulated } : m))
            break
          case 'quiz':
            accumulated += `**Quiz:**\n${event.content}\n\n`
            setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: accumulated } : m))
            break
          case 'summary':
            accumulated += `**Summary:**\n${event.content}\n\n`
            setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: accumulated } : m))
            break
          case 'prerequisites':
            accumulated += `**Prerequisites:**\n${event.content}\n\n`
            setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: accumulated } : m))
            break
        }
      },
    })
    cleanupRef.current = cleanup
  }, [streaming])

  return (
    <div style={{ display: 'flex', height: '100vh', flexDirection: 'column', background: 'var(--bg-base)' }}>
      {/* Header */}
      <div style={{
        padding: '20px 32px', borderBottom: '1px solid var(--border-subtle)',
        display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0,
        background: 'var(--bg-elevated)', zIndex: 10, boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ width: 40, height: 40, borderRadius: 12, background: 'var(--primary-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
           <Sparkles size={20} color="var(--primary)" />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: 16, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>AI Tutor — {topic}</div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{level} · Auto-routed & RAG enabled</div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '32px 0', display: 'flex', flexDirection: 'column', gap: 32 }}>
        <div style={{ maxWidth: 800, margin: '0 auto', width: '100%', padding: '0 24px', display: 'flex', flexDirection: 'column', gap: 32 }}>
          <AnimatePresence initial={false}>
            {messages.map(msg => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}
              >
                {msg.role === 'user' ? (
                  <div style={{
                    maxWidth: '75%', padding: '12px 18px',
                    borderRadius: '16px 16px 4px 16px',
                    background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                    color: 'var(--text-primary)', fontSize: 15, lineHeight: 1.5,
                    boxShadow: 'var(--shadow-sm)'
                  }}>
                    {msg.content}
                  </div>
                ) : (
                  <AssistantMessage msg={msg} topic={topic} />
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={bottomRef} style={{ height: 1 }} />
        </div>
      </div>

      {/* Input area */}
      <div style={{
        padding: '24px 32px 32px',
        borderTop: '1px solid var(--border-subtle)',
        flexShrink: 0,
        background: 'var(--bg-base)',
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto', width: '100%' }}>
          
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <ExplainModeSelector mode={explainMode} onChange={setExplainMode} />

            <button
              onClick={() => setVoiceMode(v => !v)}
              title={voiceMode ? 'Voice mode on' : 'Voice mode off'}
              style={{
                padding: '6px 12px', borderRadius: 99, fontSize: 12, fontWeight: 500, cursor: 'pointer',
                border: '1px solid', borderColor: voiceMode ? 'var(--primary)' : 'var(--border-subtle)',
                background: voiceMode ? 'var(--primary-subtle)' : 'var(--bg-elevated)',
                color: voiceMode ? 'var(--primary)' : 'var(--text-secondary)',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              {voiceMode ? <Volume2 size={12} /> : <MicOff size={12} />}
              {voiceMode ? 'Voice On' : 'Voice Off'}
            </button>

            {ttsLoading && <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>🔊 Speaking…</div>}
          </div>

          {/* Input box container */}
          <div style={{ 
            display: 'flex', gap: 12, alignItems: 'flex-end', 
            background: 'var(--bg-elevated)', border: '1px solid var(--border)', 
            borderRadius: 16, padding: '12px 16px',
            boxShadow: 'var(--shadow-sm)', transition: 'border-color 0.2s'
          }}>

            <textarea
              value={input}
              onChange={e => {
                setInput(e.target.value)
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px'
              }}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              placeholder={`Ask about ${topic}…`}
              disabled={streaming}
              rows={1}
              style={{
                flex: 1, padding: '4px 8px', resize: 'none', border: 'none',
                background: 'transparent', color: 'var(--text-primary)', 
                fontSize: 15, lineHeight: 1.5, outline: 'none',
                fontFamily: 'Inter, sans-serif',
              }}
            />
            
            {voiceMode && (
              <motion.button
                onClick={recording ? stopRecording : startRecording}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title={recording ? 'Stop recording' : 'Record'}
                style={{
                  width: 36, height: 36, borderRadius: 10, border: 'none', cursor: 'pointer',
                  background: recording ? 'var(--danger)' : 'var(--bg-hover)',
                  color: recording ? '#fff' : 'var(--text-muted)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.2s', flexShrink: 0,
                  animation: recording ? 'pulse 1s ease-in-out infinite' : 'none',
                }}
              >
                {recording ? <MicOff size={16} /> : <Mic size={16} />}
              </motion.button>
            )}

            <motion.button
              onClick={sendMessage}
              disabled={!input.trim() || streaming}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              style={{
                width: 36, height: 36, borderRadius: 10, border: 'none',
                cursor: !input.trim() || streaming ? 'not-allowed' : 'pointer',
                background: !input.trim() || streaming ? 'var(--bg-hover)' : 'var(--primary)',
                color: !input.trim() || streaming ? 'var(--text-muted)' : '#fff',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 0.2s', flexShrink: 0, paddingBottom: 2,
              }}
            >
              {streaming
                ? <div style={{ width: 14, height: 14, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite' }} />
                : <Send size={16} />
              }
            </motion.button>
          </div>
          <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-secondary)', marginTop: 12 }}>
            Synapse AI can make mistakes. Consider verifying important information.
          </div>
        </div>
      </div>
    </div>
  )
}
