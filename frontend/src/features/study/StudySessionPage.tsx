import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play, Pause, StopCircle, Timer, BookOpen, Brain,
  Target, ChevronRight, Clock, CheckCircle2, Sparkles,
} from 'lucide-react'
import { studyApi } from '@/lib/api'
import { useUIStore } from '@/store/uiStore'
import { TOPICS } from '@/types'

type Phase = 'setup' | 'active' | 'review'

export default function StudySessionPage() {
  const navigate = useNavigate()
  const { currentTopic, setCurrentTopic, selectedLevel } = useUIStore()

  const [phase, setPhase] = useState<Phase>('setup')
  const [topic, setTopic] = useState(currentTopic || TOPICS[0])
  const [sessionId, setSessionId] = useState('')
  const [elapsed, setElapsed] = useState(0)
  const [questionsAnswered, setQuestionsAnswered] = useState(0)
  const [conceptsReviewed, setConceptsReviewed] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const [showSummary, setShowSummary] = useState(false)

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startRef = useRef(0)

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const startSession = useCallback(async () => {
    try {
      const { data } = await studyApi.start(topic)
      setSessionId(data.session_id)
      setPhase('active')
      setElapsed(0)
      setQuestionsAnswered(0)
      setConceptsReviewed(0)
      setIsPaused(false)
      startRef.current = Date.now()
      setCurrentTopic(topic)

      intervalRef.current = setInterval(() => {
        setElapsed(Math.floor((Date.now() - startRef.current) / 1000))
      }, 1000)
    } catch { /* ignore */ }
  }, [topic, setCurrentTopic])

  const togglePause = () => {
    if (isPaused) {
      startRef.current = Date.now() - elapsed * 1000
      intervalRef.current = setInterval(() => {
        setElapsed(Math.floor((Date.now() - startRef.current) / 1000))
      }, 1000)
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
    setIsPaused(!isPaused)
  }

  const endSession = useCallback(async () => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    const minutes = Math.max(1, Math.round(elapsed / 60))
    try {
      await studyApi.end({
        session_id: sessionId,
        topic,
        duration_minutes: minutes,
        questions_answered: questionsAnswered,
        concepts_reviewed: conceptsReviewed,
      })
    } catch { /* ignore */ }
    setShowSummary(true)
  }, [sessionId, topic, elapsed, questionsAnswered, conceptsReviewed])

  useEffect(() => {
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [])

  // ── Setup Phase ────────────────────────────────────────────────────────
  if (phase === 'setup') {
    return (
      <div style={{ padding: '40px 48px', maxWidth: 800, margin: '0 auto' }}>
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 40 }}>
          <h1 style={{ fontSize: 28, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: 8 }}>
            Study Session
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>
            Set up a focused study session. Choose a topic and dive in.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0, transition: { delay: 0.1 } }}
          style={{ padding: 32, borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}
        >
          <div style={{ marginBottom: 24 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, display: 'block' }}>Select Topic</label>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {TOPICS.map(t => (
                <button
                  key={t}
                  onClick={() => setTopic(t)}
                  style={{
                    padding: '8px 16px', borderRadius: 8, cursor: 'pointer',
                    background: t === topic ? 'var(--primary)' : 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    color: t === topic ? '#fff' : 'var(--text-primary)',
                    fontSize: 13, fontWeight: 500, transition: 'all 0.15s',
                  }}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 32 }}>
            <div style={{ padding: 16, borderRadius: 12, background: 'var(--bg-surface)' }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Difficulty</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{selectedLevel}</div>
            </div>
            <div style={{ padding: 16, borderRadius: 12, background: 'var(--bg-surface)' }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Recommended</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>25 min session</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={startSession}
              style={{
                flex: 1, padding: '14px 24px', borderRadius: 12, cursor: 'pointer',
                background: 'var(--primary)', border: 'none', color: '#fff',
                fontSize: 15, fontWeight: 600, display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: 8,
              }}
            >
              <Play size={18} />
              Start Session
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              onClick={() => navigate('/tutor')}
              style={{
                padding: '14px 24px', borderRadius: 12, cursor: 'pointer',
                background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)', fontSize: 14, fontWeight: 500,
              }}
            >
              Open Tutor Instead
            </motion.button>
          </div>
        </motion.div>
      </div>
    )
  }

  // ── Review Phase ────────────────────────────────────────────────────────
  if (showSummary) {
    return (
      <div style={{ padding: '40px 48px', maxWidth: 600, margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          style={{ padding: 40, borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-md)', textAlign: 'center' }}
        >
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--success-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
            <CheckCircle2 size={32} color="var(--success)" />
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>Session Complete!</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 15, marginBottom: 32 }}>Great work on {topic}</p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
            <div style={{ padding: 16, borderRadius: 12, background: 'var(--bg-surface)' }}>
              <Timer size={20} style={{ color: 'var(--primary)', marginBottom: 8 }} />
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>{formatTime(elapsed)}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Duration</div>
            </div>
            <div style={{ padding: 16, borderRadius: 12, background: 'var(--bg-surface)' }}>
              <Brain size={20} style={{ color: 'var(--accent)', marginBottom: 8 }} />
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>{questionsAnswered}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Questions</div>
            </div>
            <div style={{ padding: 16, borderRadius: 12, background: 'var(--bg-surface)' }}>
              <BookOpen size={20} style={{ color: 'var(--success)', marginBottom: 8 }} />
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>{conceptsReviewed}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Concepts</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <motion.button
              whileHover={{ scale: 1.02 }}
              onClick={() => { setShowSummary(false); setPhase('setup') }}
              style={{
                flex: 1, padding: '12px', borderRadius: 10, cursor: 'pointer',
                background: 'var(--primary)', border: 'none', color: '#fff',
                fontSize: 14, fontWeight: 600,
              }}
            >
              New Session
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              onClick={() => navigate('/dashboard')}
              style={{
                flex: 1, padding: '12px', borderRadius: 10, cursor: 'pointer',
                background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)', fontSize: 14, fontWeight: 500,
              }}
            >
              Back to Dashboard
            </motion.button>
          </div>
        </motion.div>
      </div>
    )
  }

  // ── Active Phase ────────────────────────────────────────────────────────
  return (
    <div style={{ padding: '40px 48px', maxWidth: 700, margin: '0 auto' }}>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 40 }}>
          <div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 4 }}>Study Session</div>
            <h1 style={{ fontSize: 22, fontWeight: 600, color: 'var(--text-primary)' }}>{topic}</h1>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 40, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.02em' }}>
              {formatTime(elapsed)}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>elapsed</div>
          </div>
        </div>

        <div style={{
          padding: 32, borderRadius: 16,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-sm)', marginBottom: 24,
        }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 32 }}>
            <div style={{
              width: 160, height: 160, borderRadius: '50%',
              background: 'conic-gradient(var(--primary) ' + `${(elapsed % 3600) / 36}%` + ', var(--bg-surface) 0%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              position: 'relative',
            }}>
              <div style={{
                width: 140, height: 140, borderRadius: '50%',
                background: 'var(--bg-elevated)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexDirection: 'column',
              }}>
                <Timer size={24} color="var(--primary)" />
                <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
                  {formatTime(elapsed)}
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 32 }}>
            <div style={{ padding: 16, borderRadius: 12, background: 'var(--bg-surface)' }}>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4, display: 'block' }}>Questions Answered</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <button
                  onClick={() => setQuestionsAnswered(Math.max(0, questionsAnswered - 1))}
                  style={{ padding: '4px 10px', borderRadius: 6, cursor: 'pointer', background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 16 }}
                >-</button>
                <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', minWidth: 30, textAlign: 'center' }}>{questionsAnswered}</span>
                <button
                  onClick={() => setQuestionsAnswered(questionsAnswered + 1)}
                  style={{ padding: '4px 10px', borderRadius: 6, cursor: 'pointer', background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 16 }}
                >+</button>
              </div>
            </div>
            <div style={{ padding: 16, borderRadius: 12, background: 'var(--bg-surface)' }}>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4, display: 'block' }}>Concepts Reviewed</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <button
                  onClick={() => setConceptsReviewed(Math.max(0, conceptsReviewed - 1))}
                  style={{ padding: '4px 10px', borderRadius: 6, cursor: 'pointer', background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 16 }}
                >-</button>
                <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', minWidth: 30, textAlign: 'center' }}>{conceptsReviewed}</span>
                <button
                  onClick={() => setConceptsReviewed(conceptsReviewed + 1)}
                  style={{ padding: '4px 10px', borderRadius: 6, cursor: 'pointer', background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 16 }}
                >+</button>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={togglePause}
              style={{
                flex: 1, padding: '14px', borderRadius: 10, cursor: 'pointer',
                background: isPaused ? 'var(--primary)' : 'var(--warning-subtle)',
                border: 'none', color: isPaused ? '#fff' : 'var(--warning)',
                fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: 8,
              }}
            >
              {isPaused ? <Play size={18} /> : <Pause size={18} />}
              {isPaused ? 'Resume' : 'Pause'}
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={endSession}
              style={{
                flex: 1, padding: '14px', borderRadius: 10, cursor: 'pointer',
                background: 'var(--success-subtle)', border: 'none', color: 'var(--success)',
                fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: 8,
              }}
            >
              <StopCircle size={18} />
              End Session
            </motion.button>
          </div>
        </div>

        <div style={{
          padding: 16, borderRadius: 12,
          background: 'var(--primary-subtle)', border: '1px solid transparent',
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <Sparkles size={16} color="var(--primary)" style={{ flexShrink: 0 }} />
          <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
            Track questions and concepts as you study. When you're done, end the session to record your progress.
          </div>
        </div>
      </motion.div>
    </div>
  )
}
