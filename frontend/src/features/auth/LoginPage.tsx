import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, Lock, User, AlertCircle, Zap, Sparkles } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

function getLoginError(err: unknown) {
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
  if (detail) return detail

  const message = (err as { message?: string })?.message ?? ''
  if (message.includes('Network Error') || message.includes('Failed to fetch')) {
    return 'Cannot reach the backend. Make sure FastAPI is running on port 8000.'
  }
  return message || 'Invalid username or password'
}

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const { login, isLoading }    = useAuthStore()
  const navigate                = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await login(username, password)
      navigate('/dashboard')
    } catch (err: unknown) {
      setError(getLoginError(err))
    }
  }

  const handleDemo = async () => {
    setUsername('demo'); setPassword('demo123')
    setError('')
    try {
      await login('demo', 'demo123')
      navigate('/dashboard')
    } catch (err: unknown) {
      setError(`Demo login failed: ${getLoginError(err)}`)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-base)', padding: '16px', position: 'relative', overflow: 'hidden'
    }}>
      {/* Subtle ambient background glow */}
      <div style={{ position: 'absolute', top: '20%', left: '30%', width: '50vw', height: '50vw', background: 'radial-gradient(circle, var(--primary-subtle) 0%, transparent 60%)', opacity: 0.5, pointerEvents: 'none', transform: 'translate(-50%, -50%)' }} />
      <div style={{ position: 'absolute', bottom: '10%', right: '10%', width: '40vw', height: '40vw', background: 'radial-gradient(circle, rgba(6,182,212,0.05) 0%, transparent 60%)', opacity: 0.5, pointerEvents: 'none', transform: 'translate(50%, 50%)' }} />

      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 400 }}
      >
        <div style={{ padding: '40px', borderRadius: 24, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-md)' }}>
          
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{ width: 56, height: 56, borderRadius: 16, background: 'var(--primary)', margin: '0 auto 20px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px var(--primary-subtle)' }}>
              <Sparkles size={24} color="#fff" />
            </div>
            <h1 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8, letterSpacing: '-0.02em' }}>
              Welcome to Synapse
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>
              Your adaptive AI learning companion
            </p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ position: 'relative' }}>
              <User size={18} style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text" value={username} onChange={e => setUsername(e.target.value)}
                placeholder="Username" required autoFocus
                style={{
                  width: '100%', padding: '14px 16px 14px 44px',
                  background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                  borderRadius: 12, color: 'var(--text-primary)', fontSize: 15, outline: 'none',
                  transition: 'border-color 0.2s', boxSizing: 'border-box'
                }}
                onFocus={e => e.target.style.borderColor = 'var(--primary)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-subtle)'}
              />
            </div>
            
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)}
                placeholder="Password" required
                style={{
                  width: '100%', padding: '14px 16px 14px 44px',
                  background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                  borderRadius: 12, color: 'var(--text-primary)', fontSize: 15, outline: 'none',
                  transition: 'border-color 0.2s', boxSizing: 'border-box'
                }}
                onFocus={e => e.target.style.borderColor = 'var(--primary)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-subtle)'}
              />
            </div>

            {error && (
              <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
                style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', borderRadius: 12, background: 'var(--danger-subtle)', border: '1px solid var(--danger)', color: 'var(--danger)', fontSize: 14, fontWeight: 500 }}>
                <AlertCircle size={16} />
                {error}
              </motion.div>
            )}

            <motion.button type="submit" disabled={isLoading} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              style={{
                width: '100%', padding: '14px', borderRadius: 12, border: 'none', cursor: isLoading ? 'not-allowed' : 'pointer',
                background: isLoading ? 'var(--bg-surface)' : 'var(--text-primary)',
                color: isLoading ? 'var(--text-muted)' : 'var(--bg-base)', fontWeight: 600, fontSize: 15,
                transition: 'all 0.2s', marginTop: 8,
              }}>
              {isLoading ? 'Signing in…' : 'Sign In'}
            </motion.button>
          </form>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '24px 0', color: 'var(--text-muted)', fontSize: 13 }}>
            <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
            or
            <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
          </div>

          <motion.button onClick={handleDemo} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            style={{
              width: '100%', padding: '12px', borderRadius: 12, cursor: 'pointer',
              background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)', fontWeight: 500, fontSize: 14, transition: 'all 0.2s',
            }}>
            Try Demo Account
          </motion.button>

          <p style={{ textAlign: 'center', marginTop: 24, fontSize: 13, color: 'var(--text-muted)' }}>
            Demo credentials: <strong>demo</strong> / <strong>demo123</strong>
          </p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginTop: 24 }}>
          {['Groq Powered', 'RAG + GraphRAG', 'Voice I/O'].map(b => (
            <div key={b} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '4px 12px', borderRadius: 99, border: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)', fontWeight: 500 }}>
              {b}
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
