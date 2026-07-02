import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute, PublicRoute } from '@/router/guards'
import { useAuthStore } from '@/store/authStore'

// ── Lazy page imports ──────────────────────────────────────────────────────
const LoginPage          = lazy(() => import('@/features/auth/LoginPage'))
const DashboardPage      = lazy(() => import('@/features/dashboard/DashboardPage'))
const TopicSelectionPage = lazy(() => import('@/features/learn/TopicSelectionPage'))
const TutorPage          = lazy(() => import('@/features/tutor/TutorPage'))
const AssessmentPage     = lazy(() => import('@/features/assessment/AssessmentPage'))
const KnowledgeGraphPage = lazy(() => import('@/features/graph/KnowledgeGraphPage'))
const NotesPage          = lazy(() => import('@/features/notes/NotesPage'))
const RoadmapPage        = lazy(() => import('@/features/roadmap/RoadmapPage'))
const ProfilePage        = lazy(() => import('@/features/profile/ProfilePage'))

// ── QueryClient ────────────────────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
})

// ── Loading fallback ───────────────────────────────────────────────────────
function PageLoader() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '100vh', background: '#0a0a1a',
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: '50%',
        border: '3px solid rgba(124,58,237,0.2)',
        borderTopColor: '#7c3aed',
        animation: 'spin 0.8s linear infinite',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}

// ── Protected wrapper ──────────────────────────────────────────────────────
function Protected({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppShell>{children}</AppShell>
    </ProtectedRoute>
  )
}

// ── Root App ───────────────────────────────────────────────────────────────
function AppRoutes() {
  const { hydrate, isAuthenticated } = useAuthStore()

  useEffect(() => { hydrate() }, [])

  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public */}
        <Route path="/login" element={
          <PublicRoute><LoginPage /></PublicRoute>
        } />

        {/* Protected */}
        <Route path="/dashboard" element={
          <Protected><DashboardPage /></Protected>
        } />
        <Route path="/learn" element={
          <Protected><TopicSelectionPage /></Protected>
        } />
        <Route path="/tutor" element={
          <Protected><TutorPage /></Protected>
        } />
        <Route path="/assessment" element={
          <Protected><AssessmentPage /></Protected>
        } />
        <Route path="/assessment/:topic" element={
          <Protected><AssessmentPage /></Protected>
        } />
        <Route path="/graph" element={
          <Protected><KnowledgeGraphPage /></Protected>
        } />
        <Route path="/notes" element={
          <Protected><NotesPage /></Protected>
        } />
        <Route path="/roadmap" element={
          <Protected><RoadmapPage /></Protected>
        } />
        <Route path="/roadmap/:topic" element={
          <Protected><RoadmapPage /></Protected>
        } />
        <Route path="/profile" element={
          <Protected><ProfilePage /></Protected>
        } />

        {/* Default */}
        <Route path="/" element={
          <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: '#1a1a2e',
              color: '#f1f5f9',
              border: '1px solid rgba(124,58,237,0.3)',
              borderRadius: 12,
              fontSize: 14,
            },
            success: { iconTheme: { primary: '#10b981', secondary: '#fff' } },
            error:   { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
