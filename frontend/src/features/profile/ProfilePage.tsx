import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { User, BookOpen, Target, Flame, TrendingUp, Save, CheckCircle } from 'lucide-react'
import { memoryApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import type { StudentProfile } from '@/types'

const LEARNING_STYLES = ['balanced', 'visual', 'textual', 'example-heavy', 'conversational']

export default function ProfilePage() {
  const { user }  = useAuthStore()
  const qc        = useQueryClient()
  const [saved, setSaved] = useState(false)
  const [style, setStyle] = useState('balanced')

  const { data: profile, isLoading } = useQuery<StudentProfile>({
    queryKey: ['profile'],
    queryFn:  () => memoryApi.profile().then(r => r.data as StudentProfile),
    staleTime: 60_000,
  })

  // Sync learning style from profile when it loads
  useEffect(() => {
    if (profile?.learning_style) setStyle(profile.learning_style)
  }, [profile?.learning_style])

  const prefMutation = useMutation({
    mutationFn: () => memoryApi.preferences({ learning_style: style }),
    onSuccess:  () => {
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
      qc.invalidateQueries({ queryKey: ['profile'] })
    },
  })

  const masteryEntries = Object.entries(profile?.mastery_scores ?? {})
    .filter(([, v]) => (v as number) > 0)
    .sort(([, a], [, b]) => (b as number) - (a as number))

  const getMasteryColor = (m: number) =>
    m >= 80 ? '#10b981' : m >= 60 ? '#06b6d4' : m >= 40 ? '#f59e0b' : '#ef4444'

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#64748b', fontSize: 15 }}>
        Loading profile…
      </div>
    )
  }

  return (
    <div style={{ padding: '32px 36px', maxWidth: 900, margin: '0 auto' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{
            width: 72, height: 72, borderRadius: 20,
            background: 'linear-gradient(135deg,#7c3aed,#06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 28, fontWeight: 800, color: '#fff',
            boxShadow: '0 0 30px rgba(124,58,237,0.4)',
          }}>
            {(user?.display_name || user?.username || '?').charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f1f5f9' }}>
              {user?.display_name || user?.username}
            </h1>
            <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>
              {profile?.level !== 'Not Assessed' ? `${profile?.level ?? ''} learner` : 'No assessments yet'}
            </div>
          </div>
        </div>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Stats */}
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0, transition: { delay: 0.1 } }}
          style={{ padding: 24, borderRadius: 16, background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.15)' }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 20 }}>Learning Stats</h2>
          {([
            { icon: BookOpen,   label: 'Total Sessions',  value: profile?.total_sessions ?? 0,          color: '#7c3aed' },
            { icon: Target,     label: 'Topics Studied',  value: masteryEntries.length,                  color: '#06b6d4' },
            { icon: Flame,      label: 'Day Streak',      value: `${profile?.streak_days ?? 0}d`,        color: '#f59e0b' },
            { icon: TrendingUp, label: 'Level',           value: profile?.level ?? 'Not Assessed',       color: '#10b981' },
          ] as const).map(({ icon: Icon, label, value, color }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={16} color={color} />
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>{value}</div>
              </div>
            </div>
          ))}
        </motion.div>

        {/* Learning style */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0, transition: { delay: 0.15 } }}
          style={{ padding: 24, borderRadius: 16, background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.15)' }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 16 }}>Learning Preferences</h2>
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 13, color: '#94a3b8', fontWeight: 500, display: 'block', marginBottom: 10 }}>Learning Style</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {LEARNING_STYLES.map(s => (
                <button key={s} onClick={() => setStyle(s)}
                  style={{
                    padding: '9px 12px', borderRadius: 10, cursor: 'pointer', textTransform: 'capitalize',
                    border: `1px solid ${style === s ? 'rgba(124,58,237,0.6)' : 'rgba(255,255,255,0.08)'}`,
                    background: style === s ? 'rgba(124,58,237,0.15)' : 'rgba(255,255,255,0.02)',
                    color: style === s ? '#a78bfa' : '#94a3b8',
                    fontSize: 13, fontWeight: style === s ? 600 : 400, transition: 'all 0.15s',
                  }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
          <motion.button onClick={() => prefMutation.mutate()} disabled={prefMutation.isPending}
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            style={{
              width: '100%', padding: '11px', borderRadius: 10, border: 'none', cursor: 'pointer',
              background: saved ? 'rgba(16,185,129,0.2)' : 'linear-gradient(135deg,#7c3aed,#6d28d9)',
              color: saved ? '#10b981' : '#fff', fontWeight: 600, fontSize: 14,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, transition: 'all 0.3s',
            }}>
            {saved ? <><CheckCircle size={15} /> Saved!</> : <><Save size={15} /> Save Preferences</>}
          </motion.button>
        </motion.div>

        {/* Mastery by topic */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.2 } }}
          style={{ gridColumn: '1 / -1', padding: 24, borderRadius: 16, background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.15)' }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 20 }}>Topic Mastery</h2>
          {masteryEntries.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: 14, textAlign: 'center', padding: '20px 0' }}>
              No assessments yet. Take an assessment to track your mastery!
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {masteryEntries.map(([topic, mastery]) => {
                const m = mastery as number
                return (
                  <div key={topic}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: 13, color: '#e2e8f0', fontWeight: 500 }}>{topic}</span>
                      <span style={{ fontSize: 13, fontWeight: 700, color: getMasteryColor(m) }}>{m}%</span>
                    </div>
                    <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.05)' }}>
                      <motion.div
                        initial={{ width: 0 }} animate={{ width: `${m}%` }} transition={{ duration: 0.6, delay: 0.3 }}
                        style={{ height: '100%', borderRadius: 3, background: getMasteryColor(m) }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </motion.div>

        {/* Strengths & Weaknesses */}
        {profile?.strong_topics && profile.strong_topics.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.3 } }}
            style={{ padding: 20, borderRadius: 14, background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
            <h3 style={{ fontSize: 13, fontWeight: 700, color: '#10b981', marginBottom: 12 }}>✨ Strong Topics</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {profile.strong_topics.map((t: string) => (
                <span key={t} style={{ padding: '4px 12px', borderRadius: 99, fontSize: 12, background: 'rgba(16,185,129,0.12)', color: '#34d399', border: '1px solid rgba(16,185,129,0.2)' }}>{t}</span>
              ))}
            </div>
          </motion.div>
        )}
        {profile?.weak_topics && profile.weak_topics.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.35 } }}
            style={{ padding: 20, borderRadius: 14, background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)' }}>
            <h3 style={{ fontSize: 13, fontWeight: 700, color: '#ef4444', marginBottom: 12 }}>⚠️ Needs Work</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {profile.weak_topics.map((t: string) => (
                <span key={t} style={{ padding: '4px 12px', borderRadius: 99, fontSize: 12, background: 'rgba(239,68,68,0.1)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.2)' }}>{t}</span>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
