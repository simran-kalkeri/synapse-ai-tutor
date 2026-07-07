import type { ReactNode } from 'react'
import { motion } from 'framer-motion'

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', padding: '48px 24px',
        color: 'var(--text-muted)', textAlign: 'center',
      }}
    >
      <div style={{ marginBottom: 16, opacity: 0.5 }}>{icon}</div>
      <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>{title}</h3>
      {description && <p style={{ fontSize: 14, color: 'var(--text-muted)', maxWidth: 300, lineHeight: 1.5, marginBottom: action ? 20 : 0 }}>{description}</p>}
      {action && (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={action.onClick}
          style={{
            padding: '10px 20px', borderRadius: 8, cursor: 'pointer',
            background: 'var(--primary)', border: 'none', color: '#fff',
            fontSize: 13, fontWeight: 600,
          }}
        >
          {action.label}
        </motion.button>
      )}
    </motion.div>
  )
}
