import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence, type Easing } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, Tooltip, LineChart, Line, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import {
  BookOpen, Flame, Brain, Target, TrendingUp,
  ChevronRight, Star, AlertTriangle, Calendar,
  Trophy, X, Zap, CheckCircle2, Clock, Sparkles,
  BarChart3, Activity, Lightbulb, ArrowRight, Plus,
  Target as TargetIcon, Trash2,
} from 'lucide-react'
import api, { dashboardApi, memoryApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { TOPICS, DashboardStats, type AnalyticsData, type StudyGoal, type Recommendation } from '@/types'

const easeOut = 'easeOut' as Easing
const STAGGER = { animate: { transition: { staggerChildren: 0.05 } } }
const ITEM = { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0, transition: { duration: 0.3, ease: easeOut } } }

// ── XP + Level helpers ─────────────────────────────────────────────────────
const LEVELS = [
  { name: 'Novice',  threshold: 0,    color: 'var(--text-muted)' },
  { name: 'Learner', threshold: 500,  color: 'var(--accent)' },
  { name: 'Scholar', threshold: 2000, color: 'var(--primary)' },
  { name: 'Expert',  threshold: 5000, color: 'var(--warning)' },
]
function computeXP(sessions: number, streak: number, mastered: number) {
  return (sessions * 10) + (streak * 25) + (mastered * 100)
}
function getLevel(xp: number) {
  return [...LEVELS].reverse().find(l => xp >= l.threshold) ?? LEVELS[0]
}
function getNextLevel(xp: number) {
  return LEVELS.find(l => l.threshold > xp)
}

// ── Skeleton ────────────────────────────────────────────────────────────────
function SkeletonCard({ height = 120 }: { height?: number }) {
  return (
    <div style={{
      padding: 24, borderRadius: 16,
      background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
    }}>
      <div className="animate-shimmer" style={{
        height, borderRadius: 8, width: '100%',
      }} />
    </div>
  )
}

// ── StatCard ───────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, icon }: { label: string; value: string | number; sub?: string; icon?: React.ReactNode }) {
  return (
    <motion.div variants={ITEM} style={{
      padding: '24px', borderRadius: 16,
      background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
      display: 'flex', flexDirection: 'column', gap: 6,
      boxShadow: 'var(--shadow-sm)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        {icon && <span style={{ color: 'var(--text-muted)' }}>{icon}</span>}
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>{label}</div>
      </div>
      <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em', lineHeight: 1.1 }}>{value}</div>
      {sub && <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{sub}</div>}
    </motion.div>
  )
}

// ── Activity Calendar Heatmap ──────────────────────────────────────────────
function ActivityCalendar({ data }: { data: Record<string, number> }) {
  const days = Object.entries(data).sort(([a], [b]) => a.localeCompare(b))
  const maxVal = Math.max(...Object.values(data), 1)
  const getIntensity = (v: number) => {
    if (v === 0) return 'var(--bg-surface)'
    const ratio = v / maxVal
    if (ratio > 0.66) return 'var(--primary)'
    if (ratio > 0.33) return 'var(--primary-light)'
    return 'var(--primary-subtle)'
  }
  return (
    <div style={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-end' }}>
      {days.map(([day, count]) => (
        <div
          key={day}
          title={`${day}: ${count} activities`}
          style={{
            width: 12, height: 12, borderRadius: 3,
            background: getIntensity(count),
            transition: 'all 0.1s',
            cursor: 'pointer',
          }}
        />
      ))}
    </div>
  )
}

// ── Recommendation Card ────────────────────────────────────────────────────
function RecommendationCard({ rec, onAction }: { rec: Recommendation; onAction: (path: string) => void }) {
  const typeIcon: Record<string, React.ReactNode> = {
    review: <AlertTriangle size={14} color="var(--warning)" />,
    practice: <Brain size={14} color="var(--accent)" />,
    explore: <Lightbulb size={14} color="var(--primary)" />,
    assess: <Target size={14} color="var(--success)" />,
  }
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '12px 16px', borderRadius: 12,
        background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
      }}
    >
      <div style={{ flexShrink: 0 }}>{typeIcon[rec.type] || <Sparkles size={14} />}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500, marginBottom: 2 }}>{rec.reason}</div>
        {rec.topic && <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{rec.topic}</div>}
      </div>
      <button
        onClick={() => onAction(rec.action_path)}
        style={{
          flexShrink: 0, padding: '6px 12px', borderRadius: 6, cursor: 'pointer',
          background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
          color: 'var(--text-primary)', fontSize: 12, fontWeight: 500,
          transition: 'all 0.15s', whiteSpace: 'nowrap',
        }}
      >
        {rec.action_label}
      </button>
    </motion.div>
  )
}

// ── Study Goal Card ────────────────────────────────────────────────────────
function GoalCard({ goal, onComplete, onDelete }: { goal: StudyGoal; onComplete: () => void; onDelete: () => void }) {
  const progress = goal.target_sessions > 0
    ? Math.min(100, Math.round((goal.current_sessions / goal.target_sessions) * 100))
    : 0
  return (
    <div style={{
      padding: '16px', borderRadius: 12,
      background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{goal.title}</div>
          {goal.topic && <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{goal.topic}</div>}
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {goal.status === 'active' && (
            <button onClick={onComplete}
              style={{ padding: '4px 8px', borderRadius: 6, cursor: 'pointer', background: 'var(--success-subtle)', border: 'none', color: 'var(--success)', fontSize: 11, fontWeight: 600 }}>
              Done
            </button>
          )}
          <button onClick={onDelete}
            style={{ padding: '4px', borderRadius: 6, cursor: 'pointer', background: 'transparent', border: 'none', color: 'var(--text-muted)' }}>
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      <div style={{ height: 4, borderRadius: 2, background: 'var(--bg-base)', overflow: 'hidden', marginBottom: 6 }}>
        <div style={{ width: `${progress}%`, height: '100%', borderRadius: 2, background: 'var(--primary)', transition: 'width 0.3s' }} />
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
        {goal.current_sessions} / {goal.target_sessions} sessions
      </div>
    </div>
  )
}

// ── Main Dashboard ─────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [mentorDismissed, setMentorDismissed] = useState(false)
  const [showGoalForm, setShowGoalForm] = useState(false)
  const [goalTitle, setGoalTitle] = useState('')
  const [goalTopic, setGoalTopic] = useState('')

  // ── Data queries ──────────────────────────────────────────────────────────
  const { data: dash, isLoading: dashLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.stats().then(r => r.data),
    staleTime: 60_000,
  })
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => dashboardApi.analytics().then(r => r.data),
    staleTime: 60_000,
  })
  const { data: goals, refetch: refetchGoals } = useQuery({
    queryKey: ['goals'],
    queryFn: () => dashboardApi.goals.list().then(r => r.data),
    staleTime: 30_000,
  })
  const { data: mentorBrief } = useQuery({
    queryKey: ['mentor-brief'],
    queryFn: () => api.get('/api/v1/mentor/daily-brief').then(r => r.data),
    staleTime: 5 * 60_000,
  })
  const { data: dueReviews } = useQuery({
    queryKey: ['revision-due'],
    queryFn: () => api.get('/api/v1/revision/due').then(r => r.data),
    staleTime: 60_000,
  })

  // ── Computed values ───────────────────────────────────────────────────────
  const stats = dash?.stats ?? {} as DashboardStats
  const masteryByTopic: Record<string, number> = dash?.mastery_by_topic ?? {}
  const activity = dash?.recent_activity ?? []
  const masteredCount = Object.values(masteryByTopic).filter(v => v >= 80).length

  const trendData = analytics?.mastery_trend ?? []
  const recommendations = analytics?.recommendations ?? []
  const weeklyActivity = analytics?.weekly_activity ?? {}
  const studyConsistency = analytics?.study_consistency ?? 0
  const studySessions = analytics?.study_sessions ?? []
  const goalList = goals ?? []

  // Aggregate trend data for chart (by date)
  const trendByDate: Record<string, { date: string; avg_mastery: number; count: number }> = {}
  for (const pt of trendData) {
    if (!trendByDate[pt.date]) trendByDate[pt.date] = { date: pt.date, avg_mastery: 0, count: 0 }
    trendByDate[pt.date].avg_mastery += pt.mastery
    trendByDate[pt.date].count += 1
  }
  const trendChartData = Object.values(trendByDate)
    .map(d => ({ ...d, avg_mastery: Math.round(d.avg_mastery / d.count) }))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-14)

  const xp = computeXP(stats.total_sessions ?? 0, stats.streak_days ?? 0, masteredCount)
  const level = getLevel(xp)
  const nextLevel = getNextLevel(xp)
  const xpProgress = nextLevel
    ? ((xp - level.threshold) / (nextLevel.threshold - level.threshold)) * 100
    : 100

  const radarData = TOPICS.map(t => ({
    topic: t.split(' ').slice(0, 2).join(' '),
    mastery: masteryByTopic[t] ?? 0,
  }))

  const dueCount = dueReviews?.count ?? 0
  const dueItems = dueReviews?.due ?? []
  const activeGoals = goalList.filter(g => g.status === 'active')

  // ── Create goal handler ──────────────────────────────────────────────────
  const createGoal = async () => {
    if (!goalTitle.trim()) return
    try {
      await dashboardApi.goals.create({
        title: goalTitle,
        topic: goalTopic || undefined,
      })
      setGoalTitle('')
      setGoalTopic('')
      setShowGoalForm(false)
      refetchGoals()
    } catch { /* ignore */ }
  }

  const completeGoal = async (g: StudyGoal) => {
    try {
      await dashboardApi.goals.update(g.id, { status: 'completed' })
      refetchGoals()
    } catch { /* ignore */ }
  }

  const deleteGoal = async (id: string) => {
    try {
      await dashboardApi.goals.delete(id)
      refetchGoals()
    } catch { /* ignore */ }
  }

  // ── Loading state ─────────────────────────────────────────────────────────
  if (dashLoading) {
    return (
      <div style={{ padding: '40px 48px', maxWidth: 1100, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        <div className="animate-shimmer" style={{ height: 32, width: 200, borderRadius: 8, marginBottom: 12 }} />
        <div className="animate-shimmer" style={{ height: 20, width: 300, borderRadius: 8, marginBottom: 40 }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
          {[1,2,3,4].map(i => <SkeletonCard key={i} height={80} />)}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24 }}>
          {[1,2].map(i => <SkeletonCard key={i} height={300} />)}
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: '40px 48px', maxWidth: 1200, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>

      {/* ── Page Header ───────────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: 4 }}>
              Overview
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>Welcome back, {user?.display_name || user?.username}.</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {studyConsistency > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 99, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
                <Activity size={14} color={studyConsistency >= 0.5 ? 'var(--success)' : 'var(--warning)'} />
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{Math.round(studyConsistency * 100)}% consistency</span>
              </div>
            )}
            {(stats.streak_days ?? 0) > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 99, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
                <Flame size={16} color="var(--warning)" fill="var(--warning)" />
                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{stats.streak_days} Day Streak</span>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* ── AI Mentor Daily Brief ─────────────────────────────────────────── */}
      <AnimatePresence>
        {mentorBrief && !mentorDismissed && (
          <motion.div
            initial={{ opacity: 0, height: 0, marginBottom: 0 }}
            animate={{ opacity: 1, height: 'auto', marginBottom: 32 }}
            exit={{ opacity: 0, height: 0, marginBottom: 0 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{
              padding: '24px', borderRadius: 16,
              background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-sm)', position: 'relative'
            }}>
              <button
                onClick={() => setMentorDismissed(true)}
                style={{ position: 'absolute', top: 16, right: 16, background: 'var(--bg-hover)', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', borderRadius: '50%', width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <X size={14} />
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <Sparkles size={18} color="var(--primary)" />
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                  Mentor Insight · {mentorBrief.greeting}
                </span>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: 15, lineHeight: 1.6, maxWidth: '90%' }}>
                {mentorBrief.message}
              </p>
              {mentorBrief.focus_topics?.length > 0 && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 16 }}>
                  {mentorBrief.focus_topics.map((t: string) => (
                    <span key={t} style={{
                      padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 500,
                      background: 'var(--bg-hover)', color: 'var(--text-primary)',
                      border: '1px solid var(--border-subtle)',
                    }}>{t}</span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Stats Grid ────────────────────────────────────────────────────── */}
      <motion.div variants={STAGGER} initial="initial" animate="animate"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        <StatCard label="Sessions Completed" value={stats.total_sessions ?? 0} icon={<BarChart3 size={16} />} />
        <StatCard label="Average Mastery" value={`${stats.average_mastery ?? 0}%`} icon={<Brain size={16} />} />
        <StatCard label="Topics Explored" value={stats.topics_studied ?? 0} icon={<BookOpen size={16} />} />
        <StatCard label="Current Streak" value={`${stats.streak_days ?? 0}d`} icon={<Flame size={16} />} />
      </motion.div>

      {/* ── Recommendations ────────────────────────────────────────────────── */}
      {recommendations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0, transition: { delay: 0.05 } }}
          style={{ marginBottom: 32 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Lightbulb size={16} color="var(--primary)" />
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Recommended for You</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {recommendations.slice(0, 4).map((rec, i) => (
              <RecommendationCard key={i} rec={rec} onAction={(path) => navigate(path)} />
            ))}
          </div>
        </motion.div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 24, marginBottom: 32 }}>

        {/* Radar Chart / Mastery Map */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.1 } }}
          style={{ padding: '24px', borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
            <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Topic Mastery Map</h2>
            <motion.button
              whileHover={{ scale: 1.05 }}
              onClick={() => navigate('/assessment')}
              style={{ padding: '6px 12px', borderRadius: 6, cursor: 'pointer', background: 'var(--primary-subtle)', border: 'none', color: 'var(--primary)', fontSize: 12, fontWeight: 500 }}
            >
              Assess
            </motion.button>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData} outerRadius={85}>
              <PolarGrid stroke="var(--border)" strokeDasharray="3 3" />
              <PolarAngleAxis dataKey="topic" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <Radar dataKey="mastery" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.15} strokeWidth={2} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 8, boxShadow: 'var(--shadow-md)', color: 'var(--text-primary)' }}
                itemStyle={{ color: 'var(--text-primary)', fontWeight: 500 }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* XP & Level Widget */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0, transition: { delay: 0.15 } }}
            style={{
              padding: '24px', borderRadius: 16,
              background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)'
            }}
          >
             <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Trophy size={18} color="var(--text-primary)" />
                  <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>{level.name}</span>
                </div>
                <span style={{ fontSize: 14, color: 'var(--text-secondary)', fontWeight: 500 }}>{xp.toLocaleString()} XP</span>
             </div>

             <div style={{ height: 6, borderRadius: 3, background: 'var(--bg-surface)', overflow: 'hidden', marginBottom: 8 }}>
                <motion.div
                  initial={{ width: 0 }} animate={{ width: `${xpProgress}%` }} transition={{ duration: 1, ease: 'easeOut', delay: 0.3 }}
                  style={{ height: '100%', borderRadius: 3, background: 'var(--text-primary)' }}
                />
             </div>
             {nextLevel && (
               <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'right' }}>
                 {nextLevel.threshold.toLocaleString()} XP for {nextLevel.name}
               </div>
             )}
          </motion.div>

          {/* Due Reviews */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0, transition: { delay: 0.2 } }}
            style={{
              padding: '24px', borderRadius: 16,
              background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)',
              flex: 1
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Due for Review</span>
              {dueCount > 0 && (
                <span style={{ padding: '2px 8px', borderRadius: 99, background: 'var(--primary)', color: '#fff', fontSize: 12, fontWeight: 600 }}>
                  {dueCount}
                </span>
              )}
            </div>

            {dueCount === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: 14 }}>
                <CheckCircle2 size={16} /> All caught up!
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {dueItems.slice(0, 3).map((item: any) => (
                  <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 12, paddingBottom: 12, borderBottom: '1px solid var(--border-subtle)' }}>
                    <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--bg-surface)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Clock size={14} color="var(--text-secondary)" />
                    </div>
                    <div>
                      <div style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 500 }}>{item.concept}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.topic}</div>
                    </div>
                  </div>
                ))}
                <motion.button
                  whileHover={{ backgroundColor: 'var(--text-primary)', color: 'var(--bg-elevated)' }}
                  onClick={() => navigate('/learn')}
                  style={{
                    marginTop: 8, width: '100%', padding: '10px', borderRadius: 8, cursor: 'pointer',
                    background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                    color: 'var(--text-primary)', fontSize: 13, fontWeight: 500, transition: 'all 0.15s'
                  }}
                >
                  Start Review Session
                </motion.button>
              </div>
            )}
          </motion.div>
        </div>
      </div>

      {/* ── Row 2: Trends + Activity ──────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 24, marginBottom: 32 }}>

        {/* Mastery Trend Chart */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0, transition: { delay: 0.25 } }}
          style={{ padding: '24px', borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
            <TrendingUp size={16} color="var(--text-secondary)" />
            <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Learning Trend</h2>
          </div>
          {trendChartData.length > 1 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickFormatter={(v: string) => v.slice(5)} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                />
                <Line type="monotone" dataKey="avg_mastery" stroke="var(--primary)" strokeWidth={2} dot={{ fill: 'var(--primary)', r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: 'var(--text-muted)', fontSize: 13, flexDirection: 'column', gap: 8 }}>
              <BarChart3 size={24} />
              Complete an assessment to see your learning trend
            </div>
          )}
        </motion.div>

        {/* Activity Calendar + Study Sessions */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0, transition: { delay: 0.3 } }}
          style={{ padding: '24px', borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
            <Calendar size={16} color="var(--text-secondary)" />
            <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Activity (Last 28 Days)</h2>
          </div>
          <ActivityCalendar data={weeklyActivity} />

          {studySessions.length > 0 && (
            <div style={{ marginTop: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12 }}>Recent Sessions</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {studySessions.slice(0, 4).map((s) => (
                  <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)', flexShrink: 0 }} />
                    <span style={{ color: 'var(--text-primary)', fontWeight: 500, flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.topic}</span>
                    <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>{s.duration_minutes}m</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* ── Row 3: Recent Activity + Study Goals ──────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 24 }}>

        {/* Recent Activity Feed */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0, transition: { delay: 0.35 } }}
          style={{ padding: '24px', borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
            <Activity size={16} color="var(--text-secondary)" />
            <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Recent Activity</h2>
          </div>
          {activity.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}> {/* Removed maxHeight and overflow - rely on default flow */}
              {activity.slice(0, 6).map((a, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '8px 0', borderBottom: i < Math.min(activity.length, 6) - 1 ? '1px solid var(--border-subtle)' : 'none',
                }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 8,
                    background: a.event_type === 'assessment_completed' ? 'var(--success-subtle)' : 'var(--primary-subtle)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}>
                    {a.event_type === 'assessment_completed'
                      ? <CheckCircle2 size={14} color="var(--success)" />
                      : <Brain size={14} color="var(--primary)" />
                    }
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>{a.topic}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.details || a.event_type}</div>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', flexShrink: 0 }}>{a.timestamp?.slice(5, 10) || ''}</div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 120, color: 'var(--text-muted)', fontSize: 13, flexDirection: 'column', gap: 8 }}>
              <Activity size={24} />
              No activity yet. Start learning!
            </div>
          )}
        </motion.div>

        {/* Study Goals */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0, transition: { delay: 0.4 } }}
          style={{ padding: '24px', borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <TargetIcon size={16} color="var(--text-secondary)" />
              <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Study Goals</h2>
            </div>
            <button
              onClick={() => setShowGoalForm(true)}
              style={{ padding: '6px', borderRadius: 6, cursor: 'pointer', background: 'var(--primary-subtle)', border: 'none', color: 'var(--primary)' }}
            >
              <Plus size={16} />
            </button>
          </div>

          {/* New goal form */}
          <AnimatePresence>
            {showGoalForm && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                style={{ overflow: 'hidden', marginBottom: 16 }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: 12, borderRadius: 12, background: 'var(--bg-surface)' }}>
                  <input
                    autoFocus
                    placeholder="Goal title..."
                    value={goalTitle}
                    onChange={e => setGoalTitle(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && createGoal()}
                    style={{
                      padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)',
                      background: 'var(--bg-elevated)', color: 'var(--text-primary)', fontSize: 13,
                      outline: 'none',
                    }}
                  />
                  <select
                    value={goalTopic}
                    onChange={e => setGoalTopic(e.target.value)}
                    style={{
                      padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)',
                      background: 'var(--bg-elevated)', color: 'var(--text-primary)', fontSize: 13,
                      outline: 'none',
                    }}
                  >
                    <option value="">Any topic</option>
                    {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                    <button onClick={() => setShowGoalForm(false)}
                      style={{ padding: '6px 12px', borderRadius: 6, cursor: 'pointer', background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-secondary)', fontSize: 12 }}>
                      Cancel
                    </button>
                    <button onClick={createGoal}
                      style={{ padding: '6px 12px', borderRadius: 6, cursor: 'pointer', background: 'var(--primary)', border: 'none', color: '#fff', fontSize: 12, fontWeight: 600 }}>
                      Create
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {activeGoals.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {activeGoals.slice(0, 4).map(g => (
                <GoalCard
                  key={g.id}
                  goal={g}
                  onComplete={() => completeGoal(g)}
                  onDelete={() => deleteGoal(g.id)}
                />
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 120, color: 'var(--text-muted)', fontSize: 13, gap: 8 }}>
              <TargetIcon size={24} />
              <span>No goals yet. Set your first study goal!</span>
            </div>
          )}
        </motion.div>
      </div>

      {/* ── Quick Action Bar ────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0, transition: { delay: 0.45 } }}
        style={{ marginTop: 32, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}
      >
        {[
          { label: 'AI Tutor', icon: <Brain size={16} />, path: '/tutor', color: 'var(--accent)' },
          { label: 'Assessment', icon: <Target size={16} />, path: '/assessment', color: 'var(--primary)' },
          { label: 'Knowledge Graph', icon: <TrendingUp size={16} />, path: '/graph', color: 'var(--success)' },
          { label: 'Visualize', icon: <BarChart3 size={16} />, path: '/visualize', color: 'var(--warning)' },
        ].map((btn, i) => (
          <motion.button
            key={i}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate(btn.path)}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              padding: '14px', borderRadius: 12, cursor: 'pointer',
              background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)', fontSize: 13, fontWeight: 500,
              transition: 'all 0.15s', boxShadow: 'var(--shadow-sm)',
            }}
          >
            <span style={{ color: btn.color }}>{btn.icon}</span>
            {btn.label}
            <ChevronRight size={14} style={{ marginLeft: 'auto', color: 'var(--text-muted)' }} />
          </motion.button>
        ))}
      </motion.div>
    </div>
  )
}
