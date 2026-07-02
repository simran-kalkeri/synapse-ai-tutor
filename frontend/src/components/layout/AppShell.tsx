import { type ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sidebar } from './Sidebar'
import { useUIStore } from '@/store/uiStore'

const PAGE_VARIANTS = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' as const } },
  exit:    { opacity: 0, y: -8, transition: { duration: 0.15 } },
}

export function AppShell({ children }: { children: ReactNode }) {
  const collapsed = useUIStore(s => s.sidebarCollapsed)

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-base)' }}>
      <Sidebar />
      <motion.main
        animate={{ marginLeft: collapsed ? 72 : 240 }}
        transition={{ duration: 0.25, ease: 'easeInOut' }}
        style={{ flex: 1, minHeight: '100vh', overflowX: 'hidden' }}
      >
        <AnimatePresence mode="wait">
          <motion.div
            variants={PAGE_VARIANTS}
            initial="initial"
            animate="animate"
            exit="exit"
            style={{ minHeight: '100vh' }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </motion.main>
    </div>
  )
}
