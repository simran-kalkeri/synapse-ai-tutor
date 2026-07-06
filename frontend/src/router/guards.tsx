import { type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

function HydratingSpinner() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '100vh', background: 'var(--bg-base)',
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: '50%',
        border: '3px solid var(--primary-subtle)',
        borderTopColor: 'var(--primary)',
        animation: 'spin 0.8s linear infinite',
      }} />
    </div>
  )
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isHydrated } = useAuthStore()
  if (!isHydrated) return <HydratingSpinner />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export function PublicRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isHydrated } = useAuthStore()
  if (!isHydrated) return <HydratingSpinner />
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
