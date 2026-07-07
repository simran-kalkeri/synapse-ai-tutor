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
const WhiteboardPage     = lazy(() => import('@/features/whiteboard/WhiteboardPage'))
const ConceptsPage       = lazy(() => import('@/features/concepts/ConceptsPage'))
const VisualEnginePage   = lazy(() => import('@/features/visualize/VisualEnginePage'))
const StudySessionPage   = lazy(() => import('@/features/study/StudySessionPage'))



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
        <Route path="/whiteboard" element={
          <Protected><WhiteboardPage /></Protected>
        } />
        <Route path="/concepts" element={
          <Protected><ConceptsPage /></Protected>
        } />
        <Route path="/visualize" element={
          <Protected><VisualEnginePage /></Protected>
        } />
        <Route path="/study" element={
          <Protected><StudySessionPage /></Protected>
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
              background: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 12,
              fontSize: 14,
              boxShadow: 'var(--shadow-md)',
            },
            success: { iconTheme: { primary: 'var(--success)', secondary: '#fff' } },
            error:   { iconTheme: { primary: 'var(--danger)', secondary: '#fff' } },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
