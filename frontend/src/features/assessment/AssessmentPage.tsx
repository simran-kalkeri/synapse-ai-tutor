import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation } from '@tanstack/react-query'
import { CheckCircle, XCircle, ChevronRight, Map, Brain, RotateCcw, Trophy, AlertTriangle } from 'lucide-react'
import { assessmentApi } from '@/lib/api'
import { useUIStore } from '@/store/uiStore'
import { TOPICS } from '@/types'
import type { AssessmentQuestion, AssessmentResult } from '@/types'

const DIFF_COLORS = { easy: '#10b981', intermediate: '#f59e0b', hard: '#ef4444' }

type Phase = 'select' | 'intro' | 'quiz' | 'results'

function TopicCard({ topic, onClick }: { topic: string; onClick: () => void }) {
  return (
    <motion.button onClick={onClick} whileHover={{ scale: 1.03, borderColor: 'rgba(124,58,237,0.5)' }} whileTap={{ scale: 0.97 }}
      style={{ padding: '20px', borderRadius: 14, background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.15)', cursor: 'pointer', color: '#e2e8f0', fontWeight: 600, fontSize: 15, textAlign: 'left', display: 'flex', alignItems: 'center', justifyContent: 'space-between', transition: 'all 0.2s' }}>
      {topic}
      <ChevronRight size={16} color="#64748b" />
    </motion.button>
  )
}

function ScoreRing({ pct }: { pct: number }) {
  const r = 54, c = 2 * Math.PI * r
  const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444'
  return (
    <svg width={132} height={132} viewBox="0 0 132 132">
      <circle cx={66} cy={66} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={10} />
      <motion.circle
        cx={66} cy={66} r={r} fill="none" stroke={color} strokeWidth={10}
        strokeLinecap="round" strokeDasharray={c}
        initial={{ strokeDashoffset: c }}
        animate={{ strokeDashoffset: c - (c * pct / 100) }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
        transform="rotate(-90 66 66)"
      />
      <text x={66} y={62} textAnchor="middle" fill={color} fontSize={26} fontWeight={800} fontFamily="Inter">{pct}%</text>
      <text x={66} y={80} textAnchor="middle" fill="#64748b" fontSize={12} fontFamily="Inter">mastery</text>
    </svg>
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
    <div style={{ padding: '32px 36px', maxWidth: 860, margin: '0 auto' }}>
      <motion.h1 initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}
        style={{ fontSize: '1.7rem', fontWeight: 800, color: '#f1f5f9', marginBottom: 8 }}>
        Assessment Center
      </motion.h1>
      <p style={{ color: '#64748b', marginBottom: 28, fontSize: 15 }}>Test your knowledge with our adaptive 15-question assessments.</p>

      <AnimatePresence mode="wait">
        {/* Topic selection */}
        {phase === 'select' && (
          <motion.div key="select" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
            <h2 style={{ color: '#e2e8f0', fontWeight: 600, marginBottom: 16, fontSize: 16 }}>Choose a topic:</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
              {TOPICS.map(t => <TopicCard key={t} topic={t} onClick={() => handleSelectTopic(t)} />)}
            </div>
          </motion.div>
        )}

        {/* Intro */}
        {phase === 'intro' && (
          <motion.div key="intro" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
            style={{ textAlign: 'center', padding: '48px 32px', borderRadius: 20, background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.2)' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎯</div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f1f5f9', marginBottom: 8 }}>{topic}</h2>
            <p style={{ color: '#94a3b8', marginBottom: 8, fontSize: 15 }}>15 questions · 5 Easy · 5 Intermediate · 5 Hard</p>
            <p style={{ color: '#64748b', marginBottom: 32, fontSize: 13 }}>Weighted scoring: Easy 1pt · Intermediate 2pt · Hard 3pt · Max: 30pts</p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
              <motion.button onClick={reset} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                style={{ padding: '12px 24px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: '#94a3b8', cursor: 'pointer', fontWeight: 500 }}>
                Change Topic
              </motion.button>
              <motion.button onClick={handleStart} disabled={startMutation.isPending} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                style={{ padding: '12px 32px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#7c3aed,#6d28d9)', color: '#fff', cursor: startMutation.isPending ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: 15, boxShadow: '0 4px 20px rgba(124,58,237,0.4)' }}>
                {startMutation.isPending ? 'Generating…' : 'Start Assessment'}
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* Quiz */}
        {phase === 'quiz' && questions[idx] && (
          <motion.div key={`q${idx}`} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }}>
            {/* Progress */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 13, color: '#64748b' }}>
                <span>Question {idx + 1} of {questions.length}</span>
                <span style={{ color: (DIFF_COLORS as Record<string, string>)[questions[idx].difficulty] ?? '#94a3b8', fontWeight: 600, textTransform: 'capitalize' }}>
                  {questions[idx].difficulty}
                </span>
              </div>
              <div style={{ height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.06)' }}>
                <motion.div animate={{ width: `${(idx / questions.length) * 100}%` }} style={{ height: '100%', borderRadius: 2, background: 'linear-gradient(90deg,#7c3aed,#06b6d4)' }} />
              </div>
            </div>
            {/* Question */}
            <div style={{ padding: '28px', borderRadius: 16, background: 'rgba(26,26,46,0.8)', border: '1px solid rgba(124,58,237,0.2)', marginBottom: 20 }}>
              <p style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f1f5f9', lineHeight: 1.6 }}>{questions[idx].question}</p>
            </div>
            {/* Options */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {questions[idx].options.map((opt, i) => {
                const isSelected = selected === i
                return (
                  <motion.button key={i} onClick={() => handleSelect(i)} disabled={selected !== null}
                    whileHover={selected === null ? { scale: 1.01 } : {}} whileTap={selected === null ? { scale: 0.99 } : {}}
                    style={{
                      padding: '14px 18px', borderRadius: 12, textAlign: 'left', cursor: selected !== null ? 'default' : 'pointer',
                      border: `1px solid ${isSelected ? 'rgba(124,58,237,0.6)' : 'rgba(255,255,255,0.08)'}`,
                      background: isSelected ? 'rgba(124,58,237,0.15)' : 'rgba(255,255,255,0.02)',
                      color: isSelected ? '#a78bfa' : '#c4cdd6', fontWeight: isSelected ? 600 : 400, fontSize: 14,
                      transition: 'all 0.15s', display: 'flex', alignItems: 'center', gap: 10,
                    }}>
                    <span style={{ width: 24, height: 24, borderRadius: '50%', border: `2px solid ${isSelected ? '#7c3aed' : 'rgba(255,255,255,0.15)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, flexShrink: 0, color: isSelected ? '#a78bfa' : '#64748b' }}>
                      {String.fromCharCode(65 + i)}
                    </span>
                    {opt}
                  </motion.button>
                )
              })}
            </div>
            {/* Next */}
            <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
              <motion.button onClick={handleNext} disabled={selected === null || submitMutation.isPending}
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                style={{ padding: '12px 28px', borderRadius: 10, border: 'none', cursor: selected === null ? 'not-allowed' : 'pointer', background: selected !== null ? 'linear-gradient(135deg,#7c3aed,#6d28d9)' : 'rgba(124,58,237,0.2)', color: '#fff', fontWeight: 600, fontSize: 14, transition: 'all 0.2s', display: 'flex', alignItems: 'center', gap: 8 }}>
                {submitMutation.isPending ? 'Scoring…' : idx + 1 === questions.length ? 'Submit' : 'Next'} <ChevronRight size={16} />
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* Results */}
        {phase === 'results' && result && (
          <motion.div key="results" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <ScoreRing pct={result.percentage} />
              <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f1f5f9', marginTop: 16 }}>{topic} Assessment Complete</h2>
              <div style={{ marginTop: 8, display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 16px', borderRadius: 99, background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.3)' }}>
                <Trophy size={14} color="#a78bfa" />
                <span style={{ color: '#a78bfa', fontWeight: 700, fontSize: 14 }}>{result.level} Level</span>
              </div>
              <p style={{ color: '#64748b', marginTop: 8, fontSize: 14 }}>{result.correct} / {result.total} correct · {result.score} / {result.max_score} points</p>
            </div>
            {result.knowledge_gaps.length > 0 && (
              <div style={{ padding: 20, borderRadius: 14, background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)', marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, color: '#fca5a5', fontWeight: 600 }}>
                  <AlertTriangle size={16} /> Knowledge Gaps to Address
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {result.knowledge_gaps.map(g => (
                    <span key={g} style={{ padding: '4px 12px', borderRadius: 99, fontSize: 12, background: 'rgba(239,68,68,0.1)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.2)' }}>{g}</span>
                  ))}
                </div>
              </div>
            )}
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              {[
                { label: 'View Roadmap', icon: Map, action: () => { setCurrentTopic(topic); navigate(`/roadmap/${encodeURIComponent(topic)}`) } },
                { label: 'Start Learning', icon: Brain, action: () => { setCurrentTopic(topic); navigate('/tutor') } },
                { label: 'Retake', icon: RotateCcw, action: () => handleStart() },
              ].map(({ label, icon: Icon, action }) => (
                <motion.button key={label} onClick={action} whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                  style={{ padding: '11px 20px', borderRadius: 10, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: 14, border: '1px solid rgba(124,58,237,0.3)', background: 'rgba(124,58,237,0.08)', color: '#a78bfa', transition: 'all 0.2s' }}>
                  <Icon size={15} /> {label}
                </motion.button>
              ))}
            </div>
            <div style={{ textAlign: 'center', marginTop: 20 }}>
              <button onClick={reset} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 13 }}>← Choose different topic</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
