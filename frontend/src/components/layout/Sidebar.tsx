import { NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, BookOpen, Brain, ClipboardCheck,
  Share2, FileText, Map, User, ChevronLeft, ChevronRight,
  LogOut, Zap,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'

const NAV_ITEMS = [
  { to: '/dashboard',  label: 'Dashboard',  icon: LayoutDashboard },
  { to: '/learn',      label: 'Learn',       icon: BookOpen },
  { to: '/tutor',      label: 'AI Tutor',    icon: Brain },
  { to: '/assessment', label: 'Assessment',  icon: ClipboardCheck },
  { to: '/graph',      label: 'KG Explorer', icon: Share2 },
  { to: '/notes',      label: 'Notes',       icon: FileText },
  { to: '/roadmap',    label: 'Roadmap',     icon: Map },
  { to: '/profile',    label: 'Profile',     icon: User },
]

export function Sidebar() {
  const { collapsed, toggle } = { collapsed: useUIStore(s => s.sidebarCollapsed), toggle: useUIStore(s => s.toggleSidebar) }
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => { await logout(); navigate('/login') }

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 240 }}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      style={{
        background: 'linear-gradient(180deg, #0f0f23 0%, #0a0a1a 100%)',
        borderRight: '1px solid rgba(124,58,237,0.15)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 40,
        overflow: 'hidden',
      }}
    >
      {/* Logo */}
      <div style={{ padding: collapsed ? '20px 0' : '20px 16px', display: 'flex', alignItems: 'center', gap: 10, minHeight: 72 }}>
        <div style={{
          width: 38, height: 38, borderRadius: 10, flexShrink: 0,
          background: 'linear-gradient(135deg,#7c3aed,#06b6d4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 20px rgba(124,58,237,0.4)',
        }}>
          <Zap size={20} color="#fff" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
            >
              <div style={{ fontWeight: 700, fontSize: 16, letterSpacing: '-0.3px' }} className="gradient-text">Synapse</div>
              <div style={{ fontSize: 11, color: '#64748b', marginTop: -2 }}>AI Tutor</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Nav items */}
      <nav style={{ flex: 1, padding: collapsed ? '0 8px' : '0 10px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} title={collapsed ? label : undefined}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: collapsed ? '10px 0' : '9px 12px',
              justifyContent: collapsed ? 'center' : 'flex-start',
              borderRadius: 10,
              textDecoration: 'none',
              fontSize: 14, fontWeight: 500,
              transition: 'all 0.15s',
              background: isActive ? 'rgba(124,58,237,0.15)' : 'transparent',
              color: isActive ? '#a78bfa' : '#94a3b8',
              borderLeft: isActive && !collapsed ? '2px solid #7c3aed' : '2px solid transparent',
            })}
          >
            {({ isActive }) => (
              <>
                <Icon size={18} color={isActive ? '#a78bfa' : '#64748b'} />
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      transition={{ duration: 0.15 }}
                    >{label}</motion.span>
                  )}
                </AnimatePresence>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer: user + collapse */}
      <div style={{ padding: collapsed ? '12px 8px' : '12px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        {!collapsed && user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'linear-gradient(135deg,#7c3aed,#06b6d4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, fontWeight: 700, color: '#fff', flexShrink: 0,
            }}>
              {(user.display_name || user.username).charAt(0).toUpperCase()}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.display_name || user.username}
              </div>
              <div style={{ fontSize: 11, color: '#64748b' }}>Student</div>
            </div>
            <button onClick={handleLogout} title="Logout" style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', display: 'flex' }}>
              <LogOut size={15} />
            </button>
          </div>
        )}
        <button
          onClick={toggle}
          style={{
            width: '100%', padding: '8px 0', borderRadius: 8,
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
            cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b',
            transition: 'all 0.15s',
          }}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </motion.aside>
  )
}
