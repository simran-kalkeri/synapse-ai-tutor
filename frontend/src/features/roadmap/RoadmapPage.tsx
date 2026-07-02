import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { CheckCircle2, Lock, Loader2, ChevronLeft, Circle } from 'lucide-react'
import { roadmapApi } from '@/lib/api'
import { TOPICS } from '@/types'
import type { RoadmapStep } from '@/types'
import { useState } from 'react'

const STATUS_CONFIG = {
  complete: { icon: CheckCircle2, color: '#10b981', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)' },
  current:  { icon: Circle,       color: '#7c3aed', bg: 'rgba(124,58,237,0.12)', border: 'rgba(124,58,237,0.5)' },
  locked:   { icon: Lock,         color: '#475569', bg: 'rgba(255,255,255,0.02)', border: 'rgba(255,255,255,0.06)' },
}

const TYPE_LABELS: Record<string, { label: string; color: string }> = {
  prerequisite: { label: 'Prerequisite', color: '#06b6d4' },
  gap:          { label: 'Gap',          color: '#ef4444' },
  core:         { label: 'Core',         color: '#7c3aed' },
  advanced:     { label: 'Advanced',     color: '#f59e0b' },
}

function StepCard({ step, onComplete }: { step: RoadmapStep; onComplete: () => void }) {
  const cfg   = STATUS_CONFIG[step.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.locked
  const Icon  = cfg.icon
  const type  = TYPE_LABELS[step.step_type] ?? { label: step.step_type, color: '#64748b' }
  const isCur = step.status === 'current'

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
      transition={{ delay: step.order * 0.05 }}
      style={{ display: 'flex', gap: 20, alignItems: 'flex-start', marginBottom: 0 }}>
      {/* Connector */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
        <motion.div
          animate={isCur ? { boxShadow: ['0 0 8px rgba(124,58,237,0.4)', '0 0 20px rgba(124,58,237,0.8)', '0 0 8px rgba(124,58,237,0.4)'] } : {}}
          transition={{ duration: 1.5, repeat: Infinity }}
          style={{ width: 40, height: 40, borderRadius: '50%', background: cfg.bg, border: `2px solid ${cfg.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={18} color={cfg.color} />
        </motion.div>
        <div style={{ width: 2, height: 32, background: 'rgba(124,58,237,0.15)', marginTop: 2 }} />
      </div>
      {/* Card */}
      <div style={{
        flex: 1, padding: '18px 20px', borderRadius: 14, marginBottom: 16,
        background: cfg.bg, border: `1px solid ${cfg.border}`,
        opacity: step.status === 'locked' ? 0.6 : 1,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <span style={{ fontWeight: 700, fontSize: 15, color: step.status === 'locked' ? '#64748b' : '#f1f5f9' }}>
            {step.name}
          </span>
          <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 99, fontWeight: 600, background: `${type.color}18`, color: type.color, border: `1px solid ${type.color}30` }}>
            {type.label}
          </span>
          {step.status === 'complete' && <CheckCircle2 size={14} color="#10b981" style={{ marginLeft: 'auto' }} />}
        </div>
        <p style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.6 }}>{step.description}</p>
        {step.status === 'current' && (
          <motion.button onClick={onComplete} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            style={{ marginTop: 12, padding: '8px 18px', borderRadius: 8, border: 'none', background: 'linear-gradient(135deg,#7c3aed,#6d28d9)', color: '#fff', fontWeight: 600, fontSize: 13, cursor: 'pointer' }}>
            Mark Complete ✓
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
    <div style={{ padding: '32px 36px', maxWidth: 780, margin: '0 auto' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', gap: 4, fontSize: 13 }}>
            <ChevronLeft size={16} /> Back
          </button>
        </div>
        <h1 style={{ fontSize: '1.7rem', fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>Learning Roadmap</h1>
        {/* Topic selector */}
        <select value={topic} onChange={e => { setTopicState(e.target.value); navigate(`/roadmap/${encodeURIComponent(e.target.value)}`) }}
          style={{ marginTop: 8, padding: '8px 12px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(124,58,237,0.25)', color: '#f1f5f9', fontSize: 14, outline: 'none' }}>
          {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </motion.div>

      {/* Progress bar */}
      {roadmap && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          style={{ marginBottom: 32, padding: '20px', borderRadius: 14, background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.15)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div>
              <div style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 15 }}>{topic}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>{roadmap.level} · {completed}/{steps.length} steps complete</div>
            </div>
            <div style={{ fontSize: 24, fontWeight: 800 }} className="gradient-text">{progress}%</div>
          </div>
          <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)' }}>
            <motion.div
              initial={{ width: 0 }} animate={{ width: `${progress}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              style={{ height: '100%', borderRadius: 3, background: 'linear-gradient(90deg,#7c3aed,#06b6d4)' }} />
          </div>
        </motion.div>
      )}

      {/* Steps */}
      {isLoading && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: '#64748b', gap: 10 }}>
          <Loader2 size={20} style={{ animation: 'spin 0.8s linear infinite' }} /> Generating your personalized roadmap…
        </div>
      )}
      {error && (
        <div style={{ padding: 20, borderRadius: 12, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5', fontSize: 14 }}>
          Failed to load roadmap. Make sure the backend is running.
        </div>
      )}
      {steps.map((step: RoadmapStep) => (
        <StepCard key={step.name} step={step} onComplete={() => completeMutation.mutate(step.name)} />
      ))}
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
