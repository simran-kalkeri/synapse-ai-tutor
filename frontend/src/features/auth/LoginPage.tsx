import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, Lock, User, AlertCircle, Zap } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

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
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg || 'Invalid username or password')
    }
  }

  const handleDemo = async () => {
    setUsername('demo'); setPassword('demo123')
    setError('')
    try {
      await login('demo', 'demo123')
      navigate('/dashboard')
    } catch {
      // try user1 fallback
      try { await login('user1', 'synapse123'); navigate('/dashboard') } catch (e) {
        setError('Demo login failed — please enter credentials manually')
      }
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'radial-gradient(ellipse at 50% 0%, rgba(124,58,237,0.25) 0%, #0a0a1a 60%)',
      padding: '1rem',
    }}>
      {/* Animated background orbs */}
      <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
        {[0,1,2].map(i => (
          <motion.div key={i}
            animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.5, 0.3] }}
            transition={{ duration: 4 + i * 2, repeat: Infinity, delay: i * 1.5 }}
            style={{
              position: 'absolute',
              width: 300 + i * 100, height: 300 + i * 100,
              borderRadius: '50%',
              background: i === 0
                ? 'radial-gradient(circle, rgba(124,58,237,0.15) 0%, transparent 70%)'
                : i === 1
                ? 'radial-gradient(circle, rgba(6,182,212,0.1) 0%, transparent 70%)'
                : 'radial-gradient(circle, rgba(167,139,250,0.1) 0%, transparent 70%)',
              left: `${[10, 60, 30][i]}%`,
              top:  `${[20, 60, 80][i]}%`,
              transform: 'translate(-50%,-50%)',
            }}
          />
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 420 }}
      >
        {/* Card */}
        <div className="glass" style={{ padding: '2.5rem 2rem', boxShadow: '0 0 60px rgba(124,58,237,0.2), 0 25px 50px rgba(0,0,0,0.5)' }}>
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <motion.div
              animate={{ boxShadow: ['0 0 20px rgba(124,58,237,0.4)', '0 0 40px rgba(124,58,237,0.7)', '0 0 20px rgba(124,58,237,0.4)'] }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{
                width: 60, height: 60, borderRadius: 16, margin: '0 auto 16px',
                background: 'linear-gradient(135deg, #7c3aed, #06b6d4)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              <Zap size={28} color="#fff" />
            </motion.div>
            <h1 className="gradient-text" style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: 6 }}>
              Synapse AI Tutor
            </h1>
            <p style={{ color: '#64748b', fontSize: 14 }}>
              Your adaptive AI learning companion
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Username */}
            <div style={{ position: 'relative' }}>
              <User size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="text" value={username} onChange={e => setUsername(e.target.value)}
                placeholder="Username" required autoFocus
                style={{
                  width: '100%', padding: '12px 12px 12px 38px',
                  background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(124,58,237,0.25)',
                  borderRadius: 10, color: '#f1f5f9', fontSize: 14, outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={e => e.target.style.borderColor = '#7c3aed'}
                onBlur={e => e.target.style.borderColor = 'rgba(124,58,237,0.25)'}
              />
            </div>
            {/* Password */}
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)}
                placeholder="Password" required
                style={{
                  width: '100%', padding: '12px 12px 12px 38px',
                  background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(124,58,237,0.25)',
                  borderRadius: 10, color: '#f1f5f9', fontSize: 14, outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={e => e.target.style.borderColor = '#7c3aed'}
                onBlur={e => e.target.style.borderColor = 'rgba(124,58,237,0.25)'}
              />
            </div>

            {/* Error */}
            {error && (
              <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
                style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', color: '#fca5a5', fontSize: 13 }}>
                <AlertCircle size={14} />
                {error}
              </motion.div>
            )}

            {/* Submit */}
            <motion.button type="submit" disabled={isLoading} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
              style={{
                padding: '13px', borderRadius: 10, border: 'none', cursor: isLoading ? 'not-allowed' : 'pointer',
                background: isLoading ? 'rgba(124,58,237,0.4)' : 'linear-gradient(135deg, #7c3aed, #6d28d9)',
                color: '#fff', fontWeight: 600, fontSize: 15,
                boxShadow: isLoading ? 'none' : '0 4px 20px rgba(124,58,237,0.4)',
                transition: 'all 0.2s', marginTop: 4,
              }}>
              {isLoading ? 'Signing in…' : 'Sign In'}
            </motion.button>
          </form>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '16px 0', color: '#475569', fontSize: 13 }}>
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.06)' }} />
            or
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.06)' }} />
          </div>

          {/* Demo */}
          <motion.button onClick={handleDemo} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
            style={{
              width: '100%', padding: '12px', borderRadius: 10, cursor: 'pointer',
              background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.25)',
              color: '#a78bfa', fontWeight: 500, fontSize: 14, transition: 'all 0.2s',
            }}>
            ⚡ Try Demo Account
          </motion.button>

          {/* Hint */}
          <p style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: '#475569' }}>
            Demo: <code style={{ color: '#7c3aed' }}>user1</code> / <code style={{ color: '#7c3aed' }}>synapse123</code>
          </p>
        </div>

        {/* Badges */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginTop: 16 }}>
          {['Groq Powered', 'RAG + GraphRAG', 'Voice I/O'].map(b => (
            <div key={b} style={{ fontSize: 11, color: '#64748b', padding: '4px 10px', borderRadius: 99, border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.03)' }}>
              {b}
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
