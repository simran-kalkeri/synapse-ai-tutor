import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Pause, ChevronLeft, ChevronRight, RefreshCw, Image, Info, RotateCcw } from 'lucide-react'
import { visualizeApi } from '@/lib/api'
import type { VisualFrame } from '@/types'

const SPEED_OPTIONS = [
  { label: '0.5×', value: 2000 },
  { label: '1×', value: 1000 },
  { label: '1.5×', value: 667 },
  { label: '2×', value: 500 },
]

export default function VisualEnginePage() {
  const [topic, setTopic]       = useState('neural_network')
  const [level, setLevel]       = useState('intermediate')
  const [frameIdx, setFrameIdx] = useState(0)
  const [playing, setPlaying]   = useState(false)
  const [speed, setSpeed]       = useState(1000)
  const [loop, setLoop]         = useState(true)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const { data: topicsData } = useQuery({
    queryKey: ['visualize-topics'],
    queryFn: () => visualizeApi.topics().then(r => r.data),
    staleTime: 10 * 60_000,
  })

  const generateMut = useMutation({
    mutationFn: (body: { topic: string; level: string }) =>
      visualizeApi.generate(body).then(r => r.data),
  })

  const frames: VisualFrame[] = generateMut.data?.frames ?? []
  const currentFrame = frames[frameIdx]

  const nextFrame = useCallback(() => {
    setFrameIdx(i => {
      if (i < frames.length - 1) return i + 1
      if (loop) return 0
      setPlaying(false)
      return i
    })
  }, [frames.length, loop])

  useEffect(() => {
    if (playing && frames.length > 1) {
      intervalRef.current = setInterval(nextFrame, speed)
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [playing, speed, frames.length, nextFrame])

  const handleGenerate = () => {
    setPlaying(false)
    setFrameIdx(0)
    generateMut.mutate({ topic, level })
  }

  const togglePlay = () => {
    if (frames.length <= 1) return
    if (frameIdx === frames.length - 1 && !loop) return setPlaying(false)
    setPlaying(p => !p)
  }

  const goTo = (i: number) => {
    setPlaying(false)
    setFrameIdx(i)
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-base)' }}>
      <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)', display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0, flexWrap: 'wrap', zIndex: 10, boxShadow: 'var(--shadow-sm)' }}>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontWeight: 600, fontSize: 18, color: 'var(--text-primary)', letterSpacing: '-0.01em', marginBottom: 2 }}>Visual Engine</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Step-by-step concept animations</p>
        </div>

        <select value={topic} onChange={e => setTopic(e.target.value)}
          style={{ padding: '10px 14px', borderRadius: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', fontSize: 14, outline: 'none', fontWeight: 500, cursor: 'pointer' }}>
          {(topicsData?.canonical_types ?? ['neural_network', 'transformer', 'binary_search', 'linked_list', 'recursion', 'rag_pipeline']).map(t => (
            <option key={t} value={t}>{t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>
          ))}
        </select>

        <select value={level} onChange={e => setLevel(e.target.value)}
          style={{ padding: '10px 14px', borderRadius: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', fontSize: 14, outline: 'none', fontWeight: 500, cursor: 'pointer' }}>
          {['beginner', 'intermediate', 'advanced'].map(l => (
            <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>
          ))}
        </select>

        <motion.button onClick={handleGenerate} disabled={generateMut.isPending} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
          style={{
            padding: '10px 20px', borderRadius: 12, border: 'none', cursor: generateMut.isPending ? 'not-allowed' : 'pointer',
            background: generateMut.isPending ? 'var(--bg-surface)' : 'var(--text-primary)',
            color: generateMut.isPending ? 'var(--text-muted)' : 'var(--bg-base)',
            fontWeight: 600, fontSize: 14, display: 'flex', alignItems: 'center', gap: 8,
          }}>
          {generateMut.isPending ? <RefreshCw size={16} style={{ animation: 'spin 0.8s linear infinite' }} /> : <Play size={16} />}
          {generateMut.isPending ? 'Generating…' : 'Generate'}
        </motion.button>
      </div>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden', padding: 32 }}>
        {!generateMut.data && !generateMut.isPending && (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Image size={48} style={{ margin: '0 auto 16px', opacity: 0.4 }} />
            <p style={{ fontWeight: 500, fontSize: 15 }}>Select a topic and click <strong>Generate</strong> to create an animation</p>
          </div>
        )}

        {generateMut.isPending && (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
            <RefreshCw size={32} style={{ margin: '0 auto 16px', animation: 'spin 0.8s linear infinite' }} />
            <p style={{ fontWeight: 500, fontSize: 15 }}>Generating visualization frames with AI…</p>
          </div>
        )}

        {generateMut.isError && (
          <div style={{ textAlign: 'center', color: 'var(--danger)', maxWidth: 400 }}>
            <Info size={32} style={{ margin: '0 auto 16px' }} />
            <p style={{ fontWeight: 500, fontSize: 15 }}>{(generateMut.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Visualization failed. Check console for details.'}</p>
          </div>
        )}

        <AnimatePresence mode="wait">
          {currentFrame && (
            <motion.div
              key={frameIdx}
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.92 }}
              transition={{ duration: 0.25 }}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24, maxWidth: '90%' }}>
              <div style={{
                background: '#fff', borderRadius: 16, padding: 16, boxShadow: 'var(--shadow-md)',
                border: '1px solid var(--border-subtle)', maxWidth: '100%', overflow: 'hidden',
              }}>
                <img
                  src={`data:image/png;base64,${currentFrame.image_b64}`}
                  alt={currentFrame.caption}
                  style={{ display: 'block', maxWidth: '100%', maxHeight: '60vh', borderRadius: 8 }}
                />
              </div>
              <div style={{ textAlign: 'center', maxWidth: 600 }}>
                <p style={{ color: 'var(--text-primary)', fontSize: 15, fontWeight: 500, marginBottom: 4 }}>{currentFrame.caption}</p>
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Frame {frameIdx + 1} of {frames.length}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {frames.length > 1 && (
        <div style={{ padding: '16px 32px', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, flexShrink: 0 }}>
          <button onClick={() => goTo(Math.max(0, frameIdx - 1))} disabled={frameIdx === 0}
            style={{ padding: '10px 16px', borderRadius: 12, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', cursor: frameIdx === 0 ? 'not-allowed' : 'pointer', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 500, fontSize: 14 }}>
            <ChevronLeft size={16} /> Previous
          </button>

          <button onClick={togglePlay}
            style={{ padding: '10px 16px', borderRadius: 12, border: '1px solid var(--border-subtle)', background: playing ? 'var(--text-primary)' : 'var(--bg-surface)', color: playing ? 'var(--bg-base)' : 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, fontSize: 14, cursor: 'pointer' }}>
            {playing ? <Pause size={16} /> : <Play size={16} />}
            {playing ? 'Pause' : 'Play'}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {SPEED_OPTIONS.map(opt => (
              <button key={opt.label} onClick={() => setSpeed(opt.value)}
                style={{
                  padding: '6px 10px', borderRadius: 8, border: '1px solid var(--border-subtle)',
                  background: speed === opt.value ? 'var(--text-primary)' : 'var(--bg-surface)',
                  color: speed === opt.value ? 'var(--bg-base)' : 'var(--text-secondary)',
                  fontWeight: speed === opt.value ? 600 : 400, fontSize: 12, cursor: 'pointer',
                }}>
                {opt.label}
              </button>
            ))}
          </div>

          <button onClick={() => { setLoop(l => !l) }}
            style={{
              padding: '10px 16px', borderRadius: 12, border: '1px solid var(--border-subtle)',
              background: loop ? 'var(--text-primary)' : 'var(--bg-surface)',
              color: loop ? 'var(--bg-base)' : 'var(--text-secondary)',
              display: 'flex', alignItems: 'center', gap: 6, fontWeight: 500, fontSize: 14, cursor: 'pointer',
            }}>
            <RotateCcw size={16} /> {loop ? 'Looping' : 'No Loop'}
          </button>

          <div style={{ display: 'flex', gap: 6 }}>
            {frames.map((_, i) => (
              <button key={i} onClick={() => goTo(i)}
                style={{
                  width: 10, height: 10, borderRadius: '50%', border: 'none', cursor: 'pointer',
                  background: i === frameIdx ? 'var(--text-primary)' : 'var(--border)',
                  transition: 'all 0.2s',
                }} />
            ))}
          </div>

          <button onClick={() => goTo(Math.min(frames.length - 1, frameIdx + 1))} disabled={frameIdx === frames.length - 1}
            style={{ padding: '10px 16px', borderRadius: 12, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', cursor: frameIdx === frames.length - 1 ? 'not-allowed' : 'pointer', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 500, fontSize: 14 }}>
            Next <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
