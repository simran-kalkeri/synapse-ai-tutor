import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Mic, Volume2, BookOpen, Lightbulb, Code2, HelpCircle, ExternalLink, Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { streamSSE } from '@/lib/sse'
import { useUIStore } from '@/store/uiStore'
import type { SourceItem } from '@/types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceItem[]
  streaming?: boolean
}

const TABS = [
  { key: 'explanation',       label: 'Explanation', icon: BookOpen },
  { key: 'analogy',           label: 'Analogy',     icon: Lightbulb },
  { key: 'example',           label: 'Example',     icon: Code2 },
  { key: 'practice_questions',label: 'Practice',    icon: HelpCircle },
]

function parseSection(content: string, key: string): string {
  const headers: Record<string, string[]> = {
    explanation:        ['## Explanation', '**Explanation**'],
    analogy:            ['## Analogy', '**Analogy**'],
    example:            ['## Worked Example', '**Worked Example**'],
    practice_questions: ['## Practice Questions', '**Practice Questions**'],
  }
  const markers = headers[key] ?? []
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
  return <span className="animate-blink" style={{ display: 'inline-block', width: 2, height: '1em', background: '#7c3aed', verticalAlign: 'text-bottom', marginLeft: 2 }} />
}

function AssistantMessage({ msg }: { msg: Message }) {
  const [activeTab, setActiveTab] = useState('explanation')
  const tabContent = parseSection(msg.content, activeTab)

  return (
    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
      <div style={{ width: 32, height: 32, borderRadius: 10, background: 'linear-gradient(135deg,#7c3aed,#06b6d4)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Bot size={16} color="#fff" />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Tabs */}
        {!msg.streaming && (
          <div style={{ display: 'flex', gap: 4, marginBottom: 12, flexWrap: 'wrap' }}>
            {TABS.map(({ key, label, icon: Icon }) => {
              const has = parseSection(msg.content, key).length > 10
              if (!has && key !== 'explanation') return null
              return (
                <button key={key} onClick={() => setActiveTab(key)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 5, padding: '5px 12px', borderRadius: 20,
                    fontSize: 12, fontWeight: 500, cursor: 'pointer', border: 'none',
                    background: activeTab === key ? 'rgba(124,58,237,0.25)' : 'rgba(255,255,255,0.04)',
                    color: activeTab === key ? '#a78bfa' : '#64748b',
                    transition: 'all 0.15s',
                  }}>
                  <Icon size={11} /> {label}
                </button>
              )
            })}
          </div>
        )}
        {/* Content */}
        <div style={{ padding: '16px 18px', borderRadius: 12, background: 'rgba(26,26,46,0.8)', border: '1px solid rgba(124,58,237,0.15)', fontSize: 14, lineHeight: 1.7 }} className="markdown-content">
          {msg.streaming
            ? <>{msg.content}<StreamingCursor /></>
            : <ReactMarkdown>{tabContent || msg.content}</ReactMarkdown>
          }
        </div>
        {/* Sources */}
        {msg.sources && msg.sources.length > 0 && (
          <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {msg.sources.map((s, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '3px 10px', borderRadius: 99, fontSize: 11, background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.2)', color: '#67e8f9' }}>
                <ExternalLink size={10} /> {s.source} p.{s.page}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function TutorPage() {
  const { currentTopic, selectedLevel } = useUIStore()
  const topic = currentTopic || 'Neural Networks'
  const level = selectedLevel || 'Intermediate'

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0', role: 'assistant', streaming: false,
      content: `## Explanation\nHello! I'm **Synapse**, your adaptive AI tutor. You're studying **${topic}** at **${level}** level.\n\nAsk me anything — I'll explain concepts, give analogies, walk through examples, and provide practice questions tailored to your level.\n\n## Analogy\nThink of me as a private tutor who knows exactly where you are in your learning journey and adapts every explanation to match your level.\n\n## Worked Example\nFor example, try asking: *"What is ${topic} and why does it matter?"* or *"Can you give me a beginner-friendly explanation of the core concepts?"*\n\n## Practice Questions\n1. What topics within ${topic} are you most curious about?\n2. What's your current understanding of ${topic}?\n3. Are there specific concepts you found confusing before?`,
    }
  ])
  const [input, setInput]         = useState('')
  const [streaming, setStreaming]  = useState(false)
  const bottomRef                  = useRef<HTMLDivElement>(null)
  const cleanupRef                 = useRef<(() => void) | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async () => {
    if (!input.trim() || streaming) return
    const question = input.trim()
    setInput('')

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: question }
    const assistantId = (Date.now() + 1).toString()
    const assistantMsg: Message = { id: assistantId, role: 'assistant', content: '', streaming: true }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setStreaming(true)

    let accumulated = ''
    let sources: SourceItem[] = []

    const cleanup = await streamSSE('/api/v1/tutor/explain', { topic, question, level }, {
      onChunk: (text) => {
        accumulated += text
        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: accumulated } : m))
      },
      onSources: (srcs) => { sources = srcs as SourceItem[] },
      onDone: () => {
        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, streaming: false, sources } : m))
        setStreaming(false)
      },
      onError: (err) => {
        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: `❌ Error: ${err}`, streaming: false } : m))
        setStreaming(false)
      },
    })
    cleanupRef.current = cleanup
  }, [input, streaming, topic, level])

  return (
    <div style={{ display: 'flex', height: '100vh', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '16px 28px', borderBottom: '1px solid rgba(124,58,237,0.12)', display: 'flex', alignItems: 'center', gap: 14, flexShrink: 0, background: 'rgba(10,10,26,0.8)', backdropFilter: 'blur(12px)' }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
        <div>
          <div style={{ fontWeight: 700, fontSize: 16, color: '#f1f5f9' }}>AI Tutor — {topic}</div>
          <div style={{ fontSize: 12, color: '#64748b' }}>{level} level · RAG + GraphRAG enabled</div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 20 }}>
        <AnimatePresence initial={false}>
          {messages.map(msg => (
            <motion.div key={msg.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
              {msg.role === 'user' ? (
                <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                  <div style={{ maxWidth: '70%', padding: '12px 16px', borderRadius: '14px 14px 4px 14px', background: 'linear-gradient(135deg,#7c3aed,#6d28d9)', color: '#fff', fontSize: 14, fontWeight: 500 }}>
                    {msg.content}
                  </div>
                  <div style={{ width: 32, height: 32, borderRadius: 10, background: '#1a1a2e', border: '1px solid rgba(124,58,237,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <User size={15} color="#a78bfa" />
                  </div>
                </div>
              ) : (
                <AssistantMessage msg={msg} />
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '16px 28px', borderTop: '1px solid rgba(124,58,237,0.12)', flexShrink: 0, background: 'rgba(10,10,26,0.8)', backdropFilter: 'blur(12px)' }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', maxWidth: 900, margin: '0 auto' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <textarea
              value={input}
              onChange={e => { setInput(e.target.value); e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px' }}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              placeholder={`Ask about ${topic}… (Enter to send, Shift+Enter for new line)`}
              disabled={streaming}
              rows={1}
              style={{
                width: '100%', padding: '12px 16px', resize: 'none', borderRadius: 12,
                background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(124,58,237,0.25)',
                color: '#f1f5f9', fontSize: 14, lineHeight: 1.5, outline: 'none',
                transition: 'border-color 0.2s', overflow: 'hidden',
                fontFamily: 'Inter, sans-serif',
              }}
              onFocus={e => e.target.style.borderColor = '#7c3aed'}
              onBlur={e => e.target.style.borderColor = 'rgba(124,58,237,0.25)'}
            />
          </div>
          <motion.button
            onClick={sendMessage} disabled={!input.trim() || streaming}
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            style={{
              width: 46, height: 46, borderRadius: 12, border: 'none', cursor: !input.trim() || streaming ? 'not-allowed' : 'pointer',
              background: !input.trim() || streaming ? 'rgba(124,58,237,0.3)' : 'linear-gradient(135deg,#7c3aed,#6d28d9)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: !input.trim() || streaming ? 'none' : '0 4px 15px rgba(124,58,237,0.4)',
              transition: 'all 0.2s', flexShrink: 0,
            }}>
            {streaming
              ? <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite' }} />
              : <Send size={18} color="#fff" />
            }
          </motion.button>
        </div>
        <p style={{ textAlign: 'center', fontSize: 11, color: '#475569', marginTop: 8 }}>
          Powered by Groq · RAG retrieval from your textbooks · Student memory enabled
        </p>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
