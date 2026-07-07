import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { User, BookOpen, Target, Flame, TrendingUp, Save, CheckCircle, Sparkles, Award, AlertTriangle, RefreshCw } from 'lucide-react'
import { memoryApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import type { StudentProfile } from '@/types'
import { Skeleton, SkeletonLine } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/ErrorState'

const LEARNING_STYLES = ['balanced', 'visual', 'textual', 'example-heavy', 'conversational']

export default function ProfilePage() {
  const { user }  = useAuthStore()
  const qc        = useQueryClient()
  const [saved, setSaved] = useState(false)
  const [style, setStyle] = useState('balanced')

  const { data: profile, isLoading, isError, refetch } = useQuery<StudentProfile>({
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
    m >= 80 ? 'var(--success)' : m >= 60 ? 'var(--primary)' : m >= 40 ? 'var(--warning)' : 'var(--danger)'

  if (isLoading) {
    return (
      <div style={{ padding: '40px 48px', maxWidth: 1000, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 40 }}>
          <Skeleton width={80} height={80} borderRadius={24} />
          <div>
            <Skeleton width={200} height={32} style={{ marginBottom: 8 }} />
            <Skeleton width={120} height={20} />
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 24 }}>
          <div style={{ padding: 32, borderRadius: 20, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
            <Skeleton width={120} height={16} style={{ marginBottom: 24 }} />
            {[1,2,3,4].map(i => <SkeletonLine key={i} width={`${60 + i * 10}%`} />)}
          </div>
          <div style={{ padding: 32, borderRadius: 20, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
            <Skeleton width={100} height={16} style={{ marginBottom: 24 }} />
            <Skeleton width="100%" height={120} />
          </div>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div style={{ padding: '40px 48px', maxWidth: 1000, margin: '0 auto' }}>
        <ErrorState
          title="Failed to load profile"
          message="Could not load your learning profile. Please try again."
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  return (
    <div style={{ padding: '40px 48px', maxWidth: 1000, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <div style={{
            width: 80, height: 80, borderRadius: 24,
            background: 'var(--text-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 32, fontWeight: 700, color: 'var(--bg-base)',
            boxShadow: 'var(--shadow-md)',
          }}>
            {(user?.display_name || user?.username || '?').charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: 4 }}>
              {user?.display_name || user?.username}
            </h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-secondary)', fontWeight: 500 }}>
              {profile?.level !== 'Not Assessed' ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '4px 12px', background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: 99, border: '1px solid var(--primary-subtle)' }}>
                  <Award size={14} /> {profile?.level} Learner
                </span>
              ) : 'No assessments yet'}
            </div>
          </div>
        </div>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 24 }}>
        {/* Stats */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.1 } }}
          style={{ padding: 32, borderRadius: 20, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 24, letterSpacing: '-0.01em' }}>Learning Stats</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {([
              { icon: BookOpen,   label: 'Sessions',  value: profile?.total_sessions ?? 0,          color: 'var(--primary)' },
              { icon: Target,     label: 'Topics',    value: masteryEntries.length,                 color: 'var(--accent)' },
              { icon: Flame,      label: 'Streak',    value: `${profile?.streak_days ?? 0}d`,       color: 'var(--warning)' },
              { icon: TrendingUp, label: 'Level',     value: profile?.level ?? 'New',               color: 'var(--success)' },
            ] as const).map(({ icon: Icon, label, value, color }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ width: 44, height: 44, borderRadius: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={20} color={color} />
                </div>
                <div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500, marginBottom: 2 }}>{label}</div>
                  <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>{value}</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Learning style */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.15 } }}
          style={{ padding: 32, borderRadius: 20, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 24, letterSpacing: '-0.01em' }}>Preferences</h2>
          <div style={{ marginBottom: 24 }}>
            <label style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500, display: 'block', marginBottom: 12 }}>Learning Style</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {LEARNING_STYLES.map(s => {
                const isSelected = style === s;
                return (
                  <button key={s} onClick={() => setStyle(s)}
                    style={{
                      padding: '8px 16px', borderRadius: 12, cursor: 'pointer', textTransform: 'capitalize',
                      border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-subtle)'}`,
                      background: isSelected ? 'var(--primary-subtle)' : 'var(--bg-surface)',
                      color: isSelected ? 'var(--primary)' : 'var(--text-secondary)',
                      fontSize: 13, fontWeight: isSelected ? 600 : 500, transition: 'all 0.15s ease',
                      boxShadow: isSelected ? '0 0 0 1px var(--primary-subtle)' : 'none',
                    }}>
                    {s}
                  </button>
                )
              })}
            </div>
          </div>
          <motion.button onClick={() => prefMutation.mutate()} disabled={prefMutation.isPending}
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            style={{
              width: '100%', padding: '14px', borderRadius: 12, border: 'none', cursor: 'pointer',
              background: saved ? 'var(--success)' : 'var(--text-primary)',
              color: saved ? '#fff' : 'var(--bg-base)', fontWeight: 600, fontSize: 15,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, transition: 'all 0.2s',
            }}>
            {saved ? <><CheckCircle size={16} /> Saved Successfully</> : <><Save size={16} /> Save Preferences</>}
          </motion.button>
        </motion.div>

        {/* Mastery by topic */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.2 } }}
          style={{ gridColumn: '1 / -1', padding: 32, borderRadius: 20, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 24, letterSpacing: '-0.01em' }}>Topic Mastery</h2>
          {masteryEntries.length === 0 ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 15, fontWeight: 500 }}>
              <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'var(--bg-surface)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <Target size={24} color="var(--text-muted)" />
              </div>
              No assessments yet. Take an assessment to track your mastery!
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 24 }}>
              {masteryEntries.map(([topic, mastery]) => {
                const m = mastery as number
                return (
                  <div key={topic} style={{ background: 'var(--bg-surface)', padding: '16px', borderRadius: 16, border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                      <span style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 600 }}>{topic}</span>
                      <span style={{ fontSize: 14, fontWeight: 700, color: getMasteryColor(m) }}>{m}%</span>
                    </div>
                    <div style={{ height: 6, borderRadius: 3, background: 'var(--border-subtle)', overflow: 'hidden' }}>
                      <motion.div
                        initial={{ width: 0 }} animate={{ width: `${m}%` }} transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
                        style={{ height: '100%', borderRadius: 3, background: getMasteryColor(m) }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </motion.div>

        {/* Strengths & Weaknesses */}
        {((profile?.strong_topics && profile.strong_topics.length > 0) || (profile?.weak_topics && profile.weak_topics.length > 0)) && (
          <div style={{ gridColumn: '1 / -1', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 24 }}>
            {profile?.strong_topics && profile.strong_topics.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.3 } }}
                style={{ padding: 24, borderRadius: 16, background: 'var(--success-subtle)', border: '1px solid var(--success)' }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--success)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Sparkles size={16} /> Strong Topics
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                  {profile.strong_topics.map((t: string) => (
                    <span key={t} style={{ padding: '6px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500, background: 'var(--bg-elevated)', color: 'var(--success)', border: '1px solid var(--success)' }}>{t}</span>
                  ))}
                </div>
              </motion.div>
            )}
            
            {profile?.weak_topics && profile.weak_topics.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.35 } }}
                style={{ padding: 24, borderRadius: 16, background: 'var(--danger-subtle)', border: '1px solid var(--danger)' }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--danger)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Target size={16} /> Needs Work
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                  {profile.weak_topics.map((t: string) => (
                    <span key={t} style={{ padding: '6px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500, background: 'var(--bg-elevated)', color: 'var(--danger)', border: '1px solid var(--danger)' }}>{t}</span>
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
