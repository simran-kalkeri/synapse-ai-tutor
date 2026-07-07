import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { CheckCircle2, Lock, Loader2, ChevronLeft, Circle } from 'lucide-react'
import { roadmapApi } from '@/lib/api'
import { TOPICS } from '@/types'
import type { RoadmapStep } from '@/types'
import { useState } from 'react'

const STATUS_CONFIG = {
  complete: { icon: CheckCircle2, color: 'var(--success)', bg: 'var(--success-subtle)', border: 'var(--success)' },
  current:  { icon: Circle,       color: 'var(--primary)', bg: 'var(--primary-subtle)', border: 'var(--primary)' },
  locked:   { icon: Lock,         color: 'var(--text-muted)', bg: 'var(--bg-surface)', border: 'var(--border-subtle)' },
}

const TYPE_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  prerequisite: { label: 'Prerequisite', color: 'var(--accent)', bg: 'var(--accent-subtle)' },
  gap:          { label: 'Gap',          color: 'var(--danger)', bg: 'var(--danger-subtle)' },
  core:         { label: 'Core',         color: 'var(--primary)', bg: 'var(--primary-subtle)' },
  advanced:     { label: 'Advanced',     color: 'var(--warning)', bg: 'var(--warning-subtle)' },
}

function StepCard({ step, onComplete }: { step: RoadmapStep; onComplete: () => void }) {
  const cfg   = STATUS_CONFIG[step.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.locked
  const Icon  = cfg.icon
  const type  = TYPE_LABELS[step.step_type] ?? { label: step.step_type, color: 'var(--text-muted)', bg: 'var(--bg-surface)' }
  const isCur = step.status === 'current'

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
      transition={{ delay: step.order * 0.05 }}
      style={{ display: 'flex', gap: 24, alignItems: 'flex-start', marginBottom: 0 }}>
      {/* Connector */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
        <div
          style={{ 
            width: 36, height: 36, borderRadius: '50%', background: cfg.bg, 
            border: `2px solid ${cfg.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: isCur ? '0 0 0 4px var(--primary-subtle)' : 'none'
          }}>
          <Icon size={16} color={cfg.color} />
        </div>
        <div style={{ width: 2, height: 48, background: 'var(--border-subtle)', marginTop: 4, opacity: 0.5 }} />
      </div>
      {/* Card */}
      <div style={{
        flex: 1, padding: '24px', borderRadius: 16, marginBottom: 24,
        background: 'var(--bg-elevated)', border: `1px solid var(--border-subtle)`,
        opacity: step.status === 'locked' ? 0.6 : 1,
        boxShadow: isCur ? 'var(--shadow-md)' : 'var(--shadow-sm)',
        transition: 'all 0.2s ease',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <span style={{ fontWeight: 600, fontSize: 16, color: step.status === 'locked' ? 'var(--text-secondary)' : 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            {step.name}
          </span>
          <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 99, fontWeight: 500, background: type.bg, color: type.color }}>
            {type.label}
          </span>
          {step.status === 'complete' && <CheckCircle2 size={16} color="var(--success)" style={{ marginLeft: 'auto' }} />}
        </div>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{step.description}</p>
        {step.status === 'current' && (
          <motion.button onClick={onComplete} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            style={{ 
              marginTop: 16, padding: '10px 20px', borderRadius: 10, border: 'none', 
              background: 'var(--text-primary)', color: 'var(--bg-base)', 
              fontWeight: 600, fontSize: 14, cursor: 'pointer', transition: 'opacity 0.2s' 
            }}
            onMouseEnter={e => e.currentTarget.style.opacity = '0.9'}
            onMouseLeave={e => e.currentTarget.style.opacity = '1'}
          >
            Mark Complete
          </motion.button>
        )}
      </div>
    </motion.div>
  )
}

export default function RoadmapPage() {
  const { topic: topicParam } = useParams()
  const navigate              = useNavigate()
  const qc                    = useQueryClient()
  const [topicState, setTopicState] = useState(topicParam ?? TOPICS[0])
  const topic = topicState

  const { data: roadmap, isLoading, error } = useQuery({
    queryKey: ['roadmap', topic],
    queryFn:  () => roadmapApi.get(topic).then(r => r.data),
    staleTime: 5 * 60_000,
  })

  const completeMutation = useMutation({
    mutationFn: (step: string) => roadmapApi.completeStep(topic, step),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['roadmap', topic] }),
  })

  const steps       = (roadmap?.steps ?? []) as RoadmapStep[]
  const completed   = steps.filter((s: RoadmapStep) => s.status === 'complete').length
  const progress    = steps.length ? Math.round((completed / steps.length) * 100) : 0

  return (
    <div style={{ padding: '40px 48px', maxWidth: 860, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
          <button onClick={() => navigate(-1)} 
            style={{ 
              background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer', 
              color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6, 
              fontSize: 13, padding: '6px 12px', borderRadius: 8, fontWeight: 500
            }}>
            <ChevronLeft size={16} /> Back
          </button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <h1 style={{ fontSize: '28px', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', margin: 0 }}>Learning Roadmap</h1>
          {/* Topic selector */}
          <select value={topic} onChange={e => { setTopicState(e.target.value); navigate(`/roadmap/${encodeURIComponent(e.target.value)}`) }}
            style={{ 
              padding: '10px 16px', borderRadius: 12, background: 'var(--bg-elevated)', 
              border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', 
              fontSize: 14, outline: 'none', cursor: 'pointer', boxShadow: 'var(--shadow-sm)',
              fontWeight: 500,
            }}>
            {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </motion.div>

      {/* Progress bar */}
      {roadmap && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          style={{ marginBottom: 40, padding: '24px 32px', borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 16, letterSpacing: '-0.01em', marginBottom: 4 }}>{topic}</div>
              <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{roadmap.level} · {completed}/{steps.length} steps complete</div>
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--primary)', letterSpacing: '-0.02em' }}>{progress}%</div>
          </div>
          <div style={{ height: 6, borderRadius: 3, background: 'var(--border-subtle)', overflow: 'hidden' }}>
            <motion.div
              initial={{ width: 0 }} animate={{ width: `${progress}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              style={{ height: '100%', borderRadius: 3, background: 'var(--primary)' }} />
          </div>
        </motion.div>
      )}

      {/* Steps */}
      {isLoading && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: 'var(--text-secondary)', gap: 12, fontSize: 15, fontWeight: 500 }}>
          <Loader2 size={20} style={{ animation: 'spin 0.8s linear infinite' }} /> Generating your personalized roadmap…
        </div>
      )}
      {error && (
        <div style={{ padding: 24, borderRadius: 16, background: 'var(--danger-subtle)', border: '1px solid var(--danger)', color: 'var(--danger)', fontSize: 15, fontWeight: 500 }}>
          Failed to load roadmap. Make sure the backend is running.
        </div>
      )}
      {steps.map((step: RoadmapStep) => (
        <StepCard key={step.name} step={step} onComplete={() => completeMutation.mutate(step.name)} />
      ))}
    </div>
  )
}
