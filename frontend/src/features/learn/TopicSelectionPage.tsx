import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, ChevronRight, BookOpen, Map, ClipboardCheck } from 'lucide-react'
import { useUIStore } from '@/store/uiStore'
import { TOPICS } from '@/types'

const LEVELS = ['Beginner', 'Intermediate', 'Advanced']

const STAGGER = { animate: { transition: { staggerChildren: 0.05 } } }
const ITEM    = { initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 } }

export default function TopicSelectionPage() {
  const navigate = useNavigate()
  const { setCurrentTopic, setSelectedLevel, currentTopic, selectedLevel } = useUIStore()
  const [hoveredTopic, setHoveredTopic] = useState<string | null>(null)

  const handleStart = (path: string) => {
    if (!currentTopic) return
    navigate(path)
  }

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1100, margin: '0 auto' }}>
      <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f5f9', marginBottom: 6 }}>
          What do you want to <span className="gradient-text">learn today?</span>
        </h1>
        <p style={{ color: '#64748b', fontSize: 15 }}>Choose a topic and level to begin your adaptive learning session.</p>
      </motion.div>

      {/* Level selector */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.1 } }} style={{ marginBottom: 28 }}>
        <label style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Your Level</label>
        <div style={{ display: 'flex', gap: 10 }}>
          {LEVELS.map(l => (
            <button key={l} onClick={() => setSelectedLevel(l)}
              style={{
                padding: '9px 22px', borderRadius: 10, border: `1px solid ${selectedLevel === l ? 'rgba(124,58,237,0.6)' : 'rgba(255,255,255,0.08)'}`,
                background: selectedLevel === l ? 'rgba(124,58,237,0.15)' : 'rgba(255,255,255,0.02)',
                color: selectedLevel === l ? '#a78bfa' : '#64748b', fontWeight: selectedLevel === l ? 700 : 400,
                fontSize: 14, cursor: 'pointer', transition: 'all 0.15s',
              }}>
              {l}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Topic grid */}
      <label style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Select Topic</label>
      <motion.div variants={STAGGER} initial="initial" animate="animate"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 14, marginBottom: 32 }}>
        {TOPICS.map((topic) => {
          const isSelected = currentTopic === topic
          return (
            <motion.div key={topic} variants={ITEM}
              onHoverStart={() => setHoveredTopic(topic)} onHoverEnd={() => setHoveredTopic(null)}
              onClick={() => setCurrentTopic(topic)}
              whileHover={{ scale: 1.03, y: -2 }} whileTap={{ scale: 0.97 }}
              style={{
                padding: '22px 20px', borderRadius: 16, cursor: 'pointer',
                background: isSelected ? 'rgba(124,58,237,0.15)' : 'rgba(26,26,46,0.7)',
                border: `1px solid ${isSelected ? 'rgba(124,58,237,0.6)' : 'rgba(124,58,237,0.12)'}`,
                transition: 'all 0.15s', position: 'relative', overflow: 'hidden',
              }}>
              {isSelected && (
                <div style={{ position: 'absolute', top: 12, right: 12, width: 20, height: 20, borderRadius: '50%', background: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                    <path d="M1 4L4 7L9 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              )}
              <div style={{ fontSize: 28, marginBottom: 10 }}>
                {['🧠','🖼️','🔄','⚡','💬','✍️','🤖','🎨','🌊','🔧'][TOPICS.indexOf(topic)] ?? '📚'}
              </div>
              <div style={{ fontWeight: 700, fontSize: 14, color: isSelected ? '#a78bfa' : '#e2e8f0', marginBottom: 4 }}>{topic}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>AI/ML · {selectedLevel}</div>
            </motion.div>
          )
        })}
      </motion.div>

      {/* Action panel */}
      {currentTopic && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          style={{ padding: '24px', borderRadius: 16, background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>Selected:</div>
              <div style={{ fontSize: 17, fontWeight: 700, color: '#a78bfa' }}>{currentTopic}</div>
              <div style={{ fontSize: 13, color: '#64748b' }}>{selectedLevel} level</div>
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {[
                { label: 'Start Tutoring', icon: Brain,          path: '/tutor' },
                { label: 'Take Assessment', icon: ClipboardCheck, path: `/assessment` },
                { label: 'View Roadmap',   icon: Map,            path: `/roadmap/${encodeURIComponent(currentTopic)}` },
              ].map(({ label, icon: Icon, path }) => (
                <motion.button key={label} onClick={() => handleStart(path)}
                  whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '11px 18px', borderRadius: 10, border: 'none', background: label === 'Start Tutoring' ? 'linear-gradient(135deg,#7c3aed,#6d28d9)' : 'rgba(255,255,255,0.05)', color: '#fff', fontWeight: 600, fontSize: 14, cursor: 'pointer', boxShadow: label === 'Start Tutoring' ? '0 4px 15px rgba(124,58,237,0.4)' : 'none', transition: 'all 0.2s' }}>
                  <Icon size={15} />
                  {label}
                  <ChevronRight size={14} />
                </motion.button>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
