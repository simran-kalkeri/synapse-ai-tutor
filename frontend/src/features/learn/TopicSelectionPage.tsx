import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, ChevronRight, BookOpen, Map, ClipboardCheck, Check } from 'lucide-react'
import { useUIStore } from '@/store/uiStore'
import { TOPICS } from '@/types'

const LEVELS = ['Beginner', 'Intermediate', 'Advanced']

const STAGGER = { animate: { transition: { staggerChildren: 0.04 } } }
const ITEM    = { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0, transition: { duration: 0.3 } } }

export default function TopicSelectionPage() {
  const navigate = useNavigate()
  const { setCurrentTopic, setSelectedLevel, currentTopic, selectedLevel } = useUIStore()
  const [hoveredTopic, setHoveredTopic] = useState<string | null>(null)

  const handleStart = (path: string) => {
    if (!currentTopic) return
    navigate(path)
  }

  return (
    <div style={{ padding: '40px 48px', maxWidth: 1100, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 40 }}>
        <h1 style={{ fontSize: '28px', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: 6 }}>
          Library
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>Choose a topic and level to begin your adaptive learning session.</p>
      </motion.div>

      {/* Level selector */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.1 } }} style={{ marginBottom: 32 }}>
        <label style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500, display: 'block', marginBottom: 12 }}>Difficulty Level</label>
        <div style={{ display: 'flex', gap: 12 }}>
          {LEVELS.map(l => {
            const isSelected = selectedLevel === l
            return (
              <button key={l} onClick={() => setSelectedLevel(l)}
                style={{
                  padding: '8px 20px', borderRadius: 8, 
                  border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-subtle)'}`,
                  background: isSelected ? 'var(--primary-subtle)' : 'var(--bg-elevated)',
                  color: isSelected ? 'var(--primary)' : 'var(--text-primary)', 
                  fontWeight: isSelected ? 600 : 500,
                  fontSize: 14, cursor: 'pointer', transition: 'all 0.15s',
                  boxShadow: 'var(--shadow-sm)',
                }}>
                {l}
              </button>
            )
          })}
        </div>
      </motion.div>

      {/* Topic grid */}
      <label style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500, display: 'block', marginBottom: 12 }}>Topics</label>
      <motion.div variants={STAGGER} initial="initial" animate="animate"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16, marginBottom: 40 }}>
        {TOPICS.map((topic, i) => {
          const isSelected = currentTopic === topic
          return (
            <motion.div key={topic} variants={ITEM}
              onHoverStart={() => setHoveredTopic(topic)} onHoverEnd={() => setHoveredTopic(null)}
              onClick={() => setCurrentTopic(topic)}
              style={{
                padding: '24px', borderRadius: 16, cursor: 'pointer',
                background: 'var(--bg-elevated)',
                border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-subtle)'}`,
                boxShadow: isSelected ? '0 0 0 2px var(--primary-subtle)' : 'var(--shadow-sm)',
                transition: 'all 0.15s ease', position: 'relative', overflow: 'hidden',
                transform: hoveredTopic === topic && !isSelected ? 'translateY(-2px)' : 'translateY(0)',
              }}>
              {isSelected && (
                <div style={{ position: 'absolute', top: 16, right: 16, width: 20, height: 20, borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Check size={12} color="#fff" strokeWidth={3} />
                </div>
              )}
              <div style={{ fontSize: 24, marginBottom: 16, opacity: 0.9 }}>
                {['🧠','🖼️','🔄','⚡','💬','✍️','🤖','🎨','🌊','🔧'][i] ?? '📚'}
              </div>
              <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)', marginBottom: 4, letterSpacing: '-0.01em' }}>{topic}</div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>AI/ML · {selectedLevel}</div>
            </motion.div>
          )
        })}
      </motion.div>

      {/* Action panel */}
      <AnimatePresence>
        {currentTopic && (
          <motion.div 
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 16 }}
            style={{ 
              padding: '24px 32px', borderRadius: 16, background: 'var(--bg-elevated)', 
              border: '1px solid var(--primary-subtle)', boxShadow: 'var(--shadow-md)',
              position: 'sticky', bottom: 32, zIndex: 10,
            }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
              <div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>Ready to learn</div>
                <div style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>{currentTopic}</div>
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {[
                  { label: 'Assessment', icon: ClipboardCheck, path: `/assessment`, primary: false },
                  { label: 'Roadmap',    icon: Map,            path: `/roadmap/${encodeURIComponent(currentTopic)}`, primary: false },
                  { label: 'Start Session', icon: Brain,       path: '/tutor', primary: true },
                ].map(({ label, icon: Icon, path, primary }) => (
                  <button key={label} onClick={() => handleStart(path)}
                    style={{ 
                      display: 'flex', alignItems: 'center', gap: 8, padding: '10px 16px', 
                      borderRadius: 10, border: primary ? 'none' : '1px solid var(--border-subtle)', 
                      background: primary ? 'var(--text-primary)' : 'var(--bg-surface)', 
                      color: primary ? 'var(--bg-base)' : 'var(--text-primary)', 
                      fontWeight: 500, fontSize: 14, cursor: 'pointer', transition: 'all 0.15s' 
                    }}
                    onMouseEnter={(e) => {
                      if (primary) e.currentTarget.style.opacity = '0.9'
                      else e.currentTarget.style.background = 'var(--bg-hover)'
                    }}
                    onMouseLeave={(e) => {
                      if (primary) e.currentTarget.style.opacity = '1'
                      else e.currentTarget.style.background = 'var(--bg-surface)'
                    }}
                  >
                    <Icon size={16} />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
