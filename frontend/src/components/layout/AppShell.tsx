import { type ReactNode } from 'react'
import { motion, AnimatePresence, type Easing } from 'framer-motion'
import { Sidebar } from './Sidebar'
import { useUIStore } from '@/store/uiStore'
import { useLocation } from 'react-router-dom'

const easeInOut = [0.23, 1, 0.32, 1] as Easing

const PAGE_VARIANTS = {
  initial: { opacity: 0, y: 8, filter: 'blur(4px)' },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.3, ease: easeInOut } },
  exit:    { opacity: 0, y: -4, filter: 'blur(2px)', transition: { duration: 0.2 } },
}

export function AppShell({ children }: { children: ReactNode }) {
  const collapsed = useUIStore(s => s.sidebarCollapsed)
  const location = useLocation()

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-base)' }}>
      <Sidebar />
      <motion.main
        animate={{ marginLeft: collapsed ? 68 : 240 }}
        transition={{ type: 'spring', damping: 24, stiffness: 200 }}
        style={{ flex: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            variants={PAGE_VARIANTS}
            initial="initial"
            animate="animate"
            exit="exit"
            style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowX: 'hidden' }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </motion.main>
    </div>
  )
}
