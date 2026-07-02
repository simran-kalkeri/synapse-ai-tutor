import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, Tooltip,
} from 'recharts'
import {
  BookOpen, Flame, Brain, Target, TrendingUp,
  ChevronRight, Zap, Star, AlertTriangle,
} from 'lucide-react'
import { dashboardApi, memoryApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'
import { TOPICS, type ActivityItem } from '@/types'

const STAGGER = { animate: { transition: { staggerChildren: 0.07 } } }
const ITEM = { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 } }

function StatCard({ icon: Icon, label, value, sub, color }: {
  icon: React.ElementType; label: string; value: string | number; sub?: string; color: string
}) {
  return (
    <motion.div variants={ITEM} whileHover={{ scale: 1.02 }} style={{
      padding: '20px', borderRadius: 14,
      background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.15)',
      display: 'flex', alignItems: 'flex-start', gap: 14, cursor: 'default',
    }}>
      <div style={{ width: 44, height: 44, borderRadius: 12, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={20} color={color} />
      </div>
      <div>
        <div style={{ fontSize: 12, color: '#64748b', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
        <div style={{ fontSize: 26, fontWeight: 700, color: '#f1f5f9', lineHeight: 1.2 }}>{value}</div>
        {sub && <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{sub}</div>}
      </div>
    </motion.div>
  )
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const { setCurrentTopic } = useUIStore()

  const { data: dash } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.stats().then(r => r.data),
    staleTime: 60_000,
  })
  const { data: masteryData } = useQuery({
    queryKey: ['mastery'],
    queryFn: () => memoryApi.mastery().then(r => r.data.mastery ?? []),
    staleTime: 60_000,
  })

  const stats = dash?.stats ?? {}
  const masteryByTopic: Record<string, number> = dash?.mastery_by_topic ?? {}
  const activity = dash?.recent_activity ?? []

  const radarData = TOPICS.map(t => ({
    topic: t.split(' ').slice(0, 2).join(' '),
    mastery: masteryByTopic[t] ?? 0,
  }))

  const handleStartLearning = () => navigate('/learn')

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f5f9' }}>
            Welcome back, <span className="gradient-text">{user?.display_name || user?.username}</span> 👋
          </h1>
          {(stats.streak_days ?? 0) > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 12px', borderRadius: 99, background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.3)' }}>
              <Flame size={14} color="#f59e0b" />
              <span style={{ fontSize: 13, fontWeight: 600, color: '#f59e0b' }}>{stats.streak_days} day streak</span>
            </div>
          )}
        </div>
        <p style={{ color: '#64748b', fontSize: 15 }}>Here's your learning progress at a glance.</p>
      </motion.div>

      {/* Stats Grid */}
      <motion.div variants={STAGGER} initial="initial" animate="animate"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        <StatCard icon={BookOpen}   label="Sessions"      value={stats.total_sessions ?? 0}                    color="#7c3aed" />
        <StatCard icon={Target}     label="Avg Mastery"   value={`${stats.average_mastery ?? 0}%`}              color="#06b6d4" sub="across all topics" />
        <StatCard icon={Brain}      label="Topics Studied" value={stats.topics_studied ?? 0}                   color="#10b981" sub={`of ${TOPICS.length} total`} />
        <StatCard icon={Flame}      label="Streak"        value={`${stats.streak_days ?? 0}d`}                 color="#f59e0b" sub="keep it up!" />
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24, marginBottom: 24 }}>
        {/* Radar Chart */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.3 } }}
          style={{ padding: 24, borderRadius: 16, background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.15)' }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: '#e2e8f0', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Star size={16} color="#a78bfa" /> Topic Mastery Map
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(124,58,237,0.15)" />
              <PolarAngleAxis dataKey="topic" tick={{ fill: '#64748b', fontSize: 11 }} />
              <Radar dataKey="mastery" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.25} strokeWidth={2} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(124,58,237,0.3)', borderRadius: 8 }}
                labelStyle={{ color: '#a78bfa' }} itemStyle={{ color: '#94a3b8' }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Quick Actions + Strengths/Gaps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0, transition: { delay: 0.2 } }}
            style={{ padding: 20, borderRadius: 14, background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.15)' }}>
            <h2 style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', marginBottom: 12 }}>Quick Actions</h2>
            {[
              { label: 'Start Learning', icon: BookOpen, color: '#7c3aed', action: () => navigate('/learn') },
              { label: 'Take Assessment', icon: Target, color: '#06b6d4', action: () => navigate('/assessment') },
              { label: 'Explore Knowledge Graph', icon: Brain, color: '#10b981', action: () => navigate('/graph') },
            ].map(({ label, icon: Icon, color, action }) => (
              <motion.button key={label} onClick={action} whileHover={{ x: 4 }}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                  borderRadius: 10, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
                  cursor: 'pointer', marginBottom: 8, color: '#e2e8f0', fontSize: 14, fontWeight: 500,
                }}>
                <Icon size={16} color={color} />
                {label}
                <ChevronRight size={14} color="#64748b" style={{ marginLeft: 'auto' }} />
              </motion.button>
            ))}
          </motion.div>

          {/* Top/Weakest */}
          {stats.strongest_topic && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.4 } }}
              style={{ padding: 16, borderRadius: 12, background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)' }}>
              <div style={{ fontSize: 12, color: '#10b981', fontWeight: 600, marginBottom: 4 }}>✨ Strongest Topic</div>
              <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: 15 }}>{stats.strongest_topic}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>{masteryByTopic[stats.strongest_topic] ?? 0}% mastery</div>
            </motion.div>
          )}
          {stats.weakest_topic && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.5 } }}
              style={{ padding: 16, borderRadius: 12, background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#ef4444', fontWeight: 600, marginBottom: 4 }}>
                <AlertTriangle size={12} /> Needs Attention
              </div>
              <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: 15 }}>{stats.weakest_topic}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>{masteryByTopic[stats.weakest_topic] ?? 0}% mastery</div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      {activity.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.4 } }}
          style={{ padding: 24, borderRadius: 16, background: 'rgba(26,26,46,0.7)', border: '1px solid rgba(124,58,237,0.15)' }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: '#e2e8f0', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingUp size={16} color="#a78bfa" /> Recent Activity
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {activity.slice(0, 5).map((a: ActivityItem, i: number) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 8, background: 'rgba(255,255,255,0.02)' }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#7c3aed', flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <span style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 500 }}>{a.topic}</span>
                  <span style={{ color: '#64748b', fontSize: 13 }}> — {a.details || a.event_type.replace('_', ' ')}</span>
                </div>
                <span style={{ color: '#475569', fontSize: 12 }}>
                  {a.timestamp ? new Date(a.timestamp).toLocaleDateString() : ''}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
