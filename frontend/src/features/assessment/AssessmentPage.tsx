import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation } from '@tanstack/react-query'
import { CheckCircle, XCircle, ChevronRight, Map, Brain, RotateCcw, Trophy, AlertTriangle, Target } from 'lucide-react'
import { assessmentApi } from '@/lib/api'
import { useUIStore } from '@/store/uiStore'
import { TOPICS } from '@/types'
import type { AssessmentQuestion, AssessmentResult } from '@/types'

const DIFF_COLORS = { easy: 'var(--success)', intermediate: 'var(--warning)', hard: 'var(--danger)' }

type Phase = 'select' | 'intro' | 'quiz' | 'results'

function TopicCard({ topic, onClick }: { topic: string; onClick: () => void }) {
  return (
    <motion.button onClick={onClick} whileHover={{ scale: 1.02, y: -2 }} whileTap={{ scale: 0.98 }}
      style={{ 
        padding: '24px 20px', borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', 
        cursor: 'pointer', color: 'var(--text-primary)', fontWeight: 600, fontSize: 15, textAlign: 'left', 
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', transition: 'all 0.2s ease',
        boxShadow: 'var(--shadow-sm)'
      }}>
      {topic}
      <ChevronRight size={16} color="var(--text-muted)" />
    </motion.button>
  )
}

function ScoreRing({ pct }: { pct: number }) {
  const r = 54, c = 2 * Math.PI * r
  const color = pct >= 70 ? 'var(--success)' : pct >= 40 ? 'var(--warning)' : 'var(--danger)'
  return (
    <div style={{ position: 'relative', width: 132, height: 132, margin: '0 auto' }}>
      <svg width={132} height={132} viewBox="0 0 132 132">
        <circle cx={66} cy={66} r={r} fill="none" stroke="var(--border-subtle)" strokeWidth={10} />
        <motion.circle
          cx={66} cy={66} r={r} fill="none" stroke={color} strokeWidth={10}
          strokeLinecap="round" strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c - (c * pct / 100) }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          transform="rotate(-90 66 66)"
        />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ fontSize: 26, fontWeight: 800, color, lineHeight: 1 }}>{pct}%</span>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 500, marginTop: 2 }}>mastery</span>
      </div>
    </div>
  )
}

export default function AssessmentPage() {
  const navigate = useNavigate()
  const { setCurrentTopic } = useUIStore()
  const [phase, setPhase]     = useState<Phase>('select')
  const [topic, setTopic]     = useState('')
  const [questions, setQs]    = useState<AssessmentQuestion[]>([])
  const [sessionId, setSessId]= useState('')
  const [idx, setIdx]         = useState(0)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [selected, setSelected] = useState<number | null>(null)
  const [result, setResult]   = useState<AssessmentResult | null>(null)

  const startMutation = useMutation({
    mutationFn: (t: string) => assessmentApi.start(t).then(r => r.data),
    onSuccess: (data) => {
      setQs(data.questions); setSessId(data.session_id)
      setIdx(0); setAnswers({}); setSelected(null)
      setPhase('quiz')
    },
  })

  const submitMutation = useMutation({
    mutationFn: (body: object) => assessmentApi.submit(body).then(r => r.data),
    onSuccess: (data) => { setResult(data); setPhase('results') },
  })

  const handleSelectTopic = (t: string) => { setTopic(t); setPhase('intro') }
  const handleStart       = () => startMutation.mutate(topic)
  const handleSelect      = (i: number) => { if (selected === null) setSelected(i) }
  const handleNext = () => {
    if (selected === null) return
    const newAnswers = { ...answers, [questions[idx].id]: selected }
    setAnswers(newAnswers)
    setSelected(null)
    if (idx + 1 < questions.length) {
      setIdx(idx + 1)
    } else {
      const answersArr = Object.entries(newAnswers).map(([id, opt]) => ({ question_id: Number(id), selected_option: opt }))
      submitMutation.mutate({ session_id: sessionId, topic, answers: answersArr })
    }
  }

  const reset = () => { setPhase('select'); setTopic(''); setQs([]); setResult(null); setIdx(0); setAnswers({}) }

  return (
    <div style={{ padding: '40px 48px', maxWidth: 960, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 40 }}>
        <h1 style={{ fontSize: '28px', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: 6 }}>
          Assessment Center
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>Test your knowledge with our adaptive 15-question assessments.</p>
      </motion.div>

      <AnimatePresence mode="wait">
        {/* Topic selection */}
        {phase === 'select' && (
          <motion.div key="select" initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} transition={{ duration: 0.2 }}>
            <h2 style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: 20, fontSize: 16 }}>Choose a topic:</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
              {TOPICS.map(t => <TopicCard key={t} topic={t} onClick={() => handleSelectTopic(t)} />)}
            </div>
          </motion.div>
        )}

        {/* Intro */}
        {phase === 'intro' && (
          <motion.div key="intro" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.98 }} transition={{ duration: 0.2 }}
            style={{ textAlign: 'center', padding: '64px 32px', borderRadius: 24, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-md)' }}>
            <div style={{ width: 64, height: 64, borderRadius: 16, background: 'var(--primary-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
              <Target size={32} color="var(--primary)" />
            </div>
            <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12, letterSpacing: '-0.01em' }}>{topic}</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 8, fontSize: 15, fontWeight: 500 }}>15 questions · 5 Easy · 5 Intermediate · 5 Hard</p>
            <p style={{ color: 'var(--text-muted)', marginBottom: 40, fontSize: 13 }}>Weighted scoring: Easy 1pt · Intermediate 2pt · Hard 3pt · Max: 30pts</p>
            
            <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
              <motion.button onClick={reset} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                style={{ padding: '12px 24px', borderRadius: 12, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: 500, fontSize: 15, transition: 'all 0.2s' }}>
                Change Topic
              </motion.button>
              <motion.button onClick={handleStart} disabled={startMutation.isPending} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                style={{ padding: '12px 32px', borderRadius: 12, border: 'none', background: 'var(--text-primary)', color: 'var(--bg-base)', cursor: startMutation.isPending ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: 15, transition: 'all 0.2s' }}>
                {startMutation.isPending ? 'Generating…' : 'Start Assessment'}
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* Quiz */}
        {phase === 'quiz' && questions[idx] && (
          <motion.div key={`q${idx}`} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}>
            {/* Progress */}
            <div style={{ marginBottom: 32 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                <span>Question {idx + 1} of {questions.length}</span>
                <span style={{ color: (DIFF_COLORS as Record<string, string>)[questions[idx].difficulty] ?? 'var(--text-muted)', fontWeight: 600, textTransform: 'capitalize' }}>
                  {questions[idx].difficulty}
                </span>
              </div>
              <div style={{ height: 4, borderRadius: 2, background: 'var(--border-subtle)' }}>
                <motion.div animate={{ width: `${((idx) / questions.length) * 100}%` }} style={{ height: '100%', borderRadius: 2, background: 'var(--text-primary)' }} transition={{ duration: 0.3 }} />
              </div>
            </div>

            {/* Question */}
            <div style={{ padding: '32px', borderRadius: 20, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', marginBottom: 24, boxShadow: 'var(--shadow-sm)' }}>
              <p style={{ fontSize: '18px', fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.6, letterSpacing: '-0.01em' }}>{questions[idx].question}</p>
            </div>

            {/* Options */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {questions[idx].options.map((opt, i) => {
                const isSelected = selected === i
                return (
                  <motion.button key={i} onClick={() => handleSelect(i)} disabled={selected !== null}
                    whileHover={selected === null ? { scale: 1.01 } : {}} whileTap={selected === null ? { scale: 0.99 } : {}}
                    style={{
                      padding: '16px 20px', borderRadius: 16, textAlign: 'left', cursor: selected !== null ? 'default' : 'pointer',
                      border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-subtle)'}`,
                      background: isSelected ? 'var(--primary-subtle)' : 'var(--bg-elevated)',
                      color: isSelected ? 'var(--primary)' : 'var(--text-secondary)', fontWeight: isSelected ? 600 : 500, fontSize: 15,
                      transition: 'all 0.15s ease', display: 'flex', alignItems: 'center', gap: 12,
                      boxShadow: isSelected ? '0 0 0 1px var(--primary-subtle)' : 'none'
                    }}>
                    <span style={{ 
                      width: 28, height: 28, borderRadius: '50%', 
                      background: isSelected ? 'var(--primary)' : 'var(--bg-surface)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', 
                      fontSize: 13, fontWeight: 700, flexShrink: 0, 
                      color: isSelected ? '#fff' : 'var(--text-muted)' 
                    }}>
                      {String.fromCharCode(65 + i)}
                    </span>
                    <span style={{ flex: 1, color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{opt}</span>
                  </motion.button>
                )
              })}
            </div>

            {/* Next */}
            <div style={{ marginTop: 32, display: 'flex', justifyContent: 'flex-end' }}>
              <motion.button onClick={handleNext} disabled={selected === null || submitMutation.isPending}
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                style={{ 
                  padding: '12px 32px', borderRadius: 12, border: 'none', 
                  cursor: selected === null ? 'not-allowed' : 'pointer', 
                  background: selected !== null ? 'var(--text-primary)' : 'var(--bg-surface)', 
                  color: selected !== null ? 'var(--bg-base)' : 'var(--text-muted)', 
                  fontWeight: 600, fontSize: 15, transition: 'all 0.2s', 
                  display: 'flex', alignItems: 'center', gap: 8 
                }}>
                {submitMutation.isPending ? 'Scoring…' : idx + 1 === questions.length ? 'Submit' : 'Next'} <ChevronRight size={18} />
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* Results */}
        {phase === 'results' && result && (
          <motion.div key="results" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.3 }}>
            <div style={{ textAlign: 'center', marginBottom: 40, padding: '48px 32px', background: 'var(--bg-elevated)', borderRadius: 24, border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-md)' }}>
              <ScoreRing pct={result.percentage} />
              <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)', marginTop: 24, letterSpacing: '-0.01em' }}>{topic} Assessment Complete</h2>
              
              <div style={{ marginTop: 16, display: 'inline-flex', alignItems: 'center', gap: 8, padding: '8px 20px', borderRadius: 99, background: 'var(--primary-subtle)', border: '1px solid var(--primary-subtle)' }}>
                <Trophy size={16} color="var(--primary)" />
                <span style={{ color: 'var(--primary)', fontWeight: 600, fontSize: 15 }}>{result.level} Level</span>
              </div>
              
              <p style={{ color: 'var(--text-secondary)', marginTop: 16, fontSize: 15, fontWeight: 500 }}>
                {result.correct} / {result.total} correct · {result.score} / {result.max_score} points
              </p>

              {result.knowledge_gaps.length > 0 && (
                <div style={{ marginTop: 32, paddingTop: 32, borderTop: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, color: 'var(--text-primary)', fontWeight: 600, fontSize: 16 }}>
                    <AlertTriangle size={18} color="var(--warning)" /> Knowledge Gaps Identified
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                    {result.knowledge_gaps.map(g => (
                      <span key={g} style={{ padding: '6px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500, background: 'var(--bg-surface)', color: 'var(--text-secondary)', border: '1px solid var(--border-subtle)' }}>{g}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
              {[
                { label: 'View Roadmap', icon: Map, action: () => { setCurrentTopic(topic); navigate(`/roadmap/${encodeURIComponent(topic)}`) }, primary: false },
                { label: 'Start Learning', icon: Brain, action: () => { setCurrentTopic(topic); navigate('/tutor') }, primary: true },
                { label: 'Retake', icon: RotateCcw, action: () => handleStart(), primary: false },
              ].map(({ label, icon: Icon, action, primary }) => (
                <motion.button key={label} onClick={action} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  style={{ 
                    padding: '12px 24px', borderRadius: 12, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, 
                    fontWeight: 600, fontSize: 15, transition: 'all 0.2s',
                    border: primary ? 'none' : '1px solid var(--border-subtle)',
                    background: primary ? 'var(--text-primary)' : 'var(--bg-elevated)',
                    color: primary ? 'var(--bg-base)' : 'var(--text-primary)',
                    boxShadow: primary ? 'var(--shadow-sm)' : 'none',
                  }}>
                  <Icon size={18} /> {label}
                </motion.button>
              ))}
            </div>
            <div style={{ textAlign: 'center', marginTop: 32 }}>
              <button onClick={reset} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 14, fontWeight: 500, transition: 'color 0.2s' }} onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'} onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}>
                ← Choose different topic
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
