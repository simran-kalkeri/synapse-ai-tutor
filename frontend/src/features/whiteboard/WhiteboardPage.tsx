import { useEffect, useRef, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Pen, Square, Circle as CircleIcon, Type, Eraser, Trash2,
  Download, Undo2, MousePointer,
} from 'lucide-react'
import toast from 'react-hot-toast'

interface Point { x: number; y: number }

interface CanvasElement {
  type: 'path' | 'rect' | 'circle' | 'text'
  color: string
  width: number
  points?: Point[]
  x?: number; y?: number; w?: number; h?: number
  radius?: number
  text?: string; fontSize?: number
}

interface DragState {
  active: boolean
  startX: number; startY: number
  currentX: number; currentY: number
  drawing: boolean
  moving: boolean
  moveOffsetX: number; moveOffsetY: number
}

const COLORS = [
  'var(--text-primary)', 'var(--primary)', 'var(--accent)', 'var(--warning)',
  'var(--danger)', 'var(--success)', '#3b82f6', '#f97316',
]

const TOOLS = [
  { id: 'select', icon: MousePointer, label: 'Select' },
  { id: 'pen', icon: Pen, label: 'Draw' },
  { id: 'rect', icon: Square, label: 'Rectangle' },
  { id: 'circle', icon: CircleIcon, label: 'Circle' },
  { id: 'text', icon: Type, label: 'Text' },
  { id: 'eraser', icon: Eraser, label: 'Eraser' },
]

function resolveColor(cssVar: string): string {
  if (cssVar.startsWith('#')) return cssVar
  return getComputedStyle(document.documentElement).getPropertyValue(cssVar.slice(4, -1)).trim() || '#000'
}

function hitTest(pt: Point, el: CanvasElement): boolean {
  const margin = 8
  if (el.type === 'path' && el.points) {
    for (const p of el.points) {
      if (Math.abs(p.x - pt.x) < margin && Math.abs(p.y - pt.y) < margin) return true
    }
    return false
  }
  if (el.type === 'rect' && el.x !== undefined && el.y !== undefined && el.w !== undefined && el.h !== undefined) {
    return pt.x >= el.x - margin && pt.x <= el.x + el.w + margin && pt.y >= el.y - margin && pt.y <= el.y + el.h + margin
  }
  if (el.type === 'circle' && el.x !== undefined && el.y !== undefined && el.radius !== undefined) {
    const dx = pt.x - el.x; const dy = pt.y - el.y
    return Math.sqrt(dx * dx + dy * dy) <= el.radius + margin
  }
  if (el.type === 'text' && el.x !== undefined && el.y !== undefined && el.text) {
    const tw = el.text.length * (el.fontSize || 24) * 0.6
    const th = (el.fontSize || 24) * 1.4
    return pt.x >= el.x - margin && pt.x <= el.x + tw + margin && pt.y >= el.y - th + margin && pt.y <= el.y + margin
  }
  return false
}

export default function WhiteboardPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const [elements, setElements] = useState<CanvasElement[]>([])
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [activeTool, setActiveTool] = useState('pen')
  const [activeColor, setActiveColor] = useState('var(--primary)')
  const [strokeWidth, setStrokeWidth] = useState(3)
  const [editingText, setEditingText] = useState<{ x: number; y: number } | null>(null)
  const textInputRef = useRef<HTMLTextAreaElement>(null)
  const dragRef = useRef<DragState>({
    active: false, startX: 0, startY: 0, currentX: 0, currentY: 0,
    drawing: false, moving: false, moveOffsetX: 0, moveOffsetY: 0,
  })

  const elementsRef = useRef(elements)
  elementsRef.current = elements

  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    const w = canvas.width / dpr
    const h = canvas.height / dpr

    // Reset transform to identity first, then apply scale — prevents compounding
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.setTransform(1 / dpr, 0, 0, 1 / dpr, 0, 0)

    const allEls = elementsRef.current
    const drag = dragRef.current

    for (let i = 0; i < allEls.length; i++) {
      const el = allEls[i]
      const resolvedColor = resolveColor(el.color)
      ctx.strokeStyle = resolvedColor
      ctx.fillStyle = resolvedColor
      ctx.lineWidth = el.width * dpr
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'

      if (el.type === 'path' && el.points && el.points.length > 1) {
        ctx.beginPath()
        ctx.moveTo(el.points[0].x * dpr, el.points[0].y * dpr)
        for (let j = 1; j < el.points.length; j++) {
          ctx.lineTo(el.points[j].x * dpr, el.points[j].y * dpr)
        }
        ctx.stroke()
      }

      if (el.type === 'rect' && el.x !== undefined && el.y !== undefined && el.w !== undefined && el.h !== undefined) {
        ctx.strokeRect(el.x * dpr, el.y * dpr, el.w * dpr, el.h * dpr)
      }

      if (el.type === 'circle' && el.x !== undefined && el.y !== undefined && el.radius !== undefined) {
        ctx.beginPath()
        ctx.arc(el.x * dpr, el.y * dpr, el.radius * dpr, 0, Math.PI * 2)
        ctx.stroke()
      }

      if (el.type === 'text' && el.x !== undefined && el.y !== undefined && el.text) {
        const fontSize = (el.fontSize || 24) * dpr
        ctx.font = `${fontSize}px Inter, sans-serif`
        ctx.fillText(el.text, el.x * dpr, el.y * dpr)
      }

      if (i === selectedIndex) {
        ctx.strokeStyle = resolveColor('var(--primary)')
        ctx.lineWidth = 2 * dpr
        ctx.setLineDash([6 * dpr, 4 * dpr])
        const padding = 10 * dpr
        if (el.type === 'path' && el.points) {
          const xs = el.points.map(p => p.x); const ys = el.points.map(p => p.y)
          const minX = Math.min(...xs) * dpr - padding; const minY = Math.min(...ys) * dpr - padding
          const maxX = Math.max(...xs) * dpr + padding; const maxY = Math.max(...ys) * dpr + padding
          ctx.strokeRect(minX, minY, maxX - minX, maxY - minY)
        } else if (el.type === 'rect' && el.x !== undefined && el.y !== undefined && el.w !== undefined && el.h !== undefined) {
          ctx.strokeRect(el.x * dpr - padding, el.y * dpr - padding, el.w * dpr + padding * 2, el.h * dpr + padding * 2)
        } else if (el.type === 'circle' && el.x !== undefined && el.y !== undefined && el.radius !== undefined) {
          const r = el.radius * dpr + padding
          ctx.strokeRect(el.x * dpr - r, el.y * dpr - r, r * 2, r * 2)
        } else if (el.type === 'text' && el.x !== undefined && el.y !== undefined && el.text) {
          const tw = el.text.length * (el.fontSize || 24) * 0.6 * dpr
          const th = (el.fontSize || 24) * 1.4 * dpr
          ctx.strokeRect(el.x * dpr - padding, el.y * dpr - th - padding, tw + padding * 2, th + padding * 2)
        }
        ctx.setLineDash([])
      }
    }

    const dd = drag
    if (dd.active && dd.drawing && activeTool === 'rect') {
      const resolved = resolveColor(activeColor)
      ctx.strokeStyle = resolved
      ctx.lineWidth = strokeWidth * dpr
      ctx.strokeRect(dd.startX * dpr, dd.startY * dpr, (dd.currentX - dd.startX) * dpr, (dd.currentY - dd.startY) * dpr)
    }
    if (dd.active && dd.drawing && activeTool === 'circle') {
      const resolved = resolveColor(activeColor)
      ctx.strokeStyle = resolved
      ctx.lineWidth = strokeWidth * dpr
      const cx = (dd.startX + dd.currentX) / 2; const cy = (dd.startY + dd.currentY) / 2
      const rx = Math.abs(dd.currentX - dd.startX) / 2; const ry = Math.abs(dd.currentY - dd.startY) / 2
      const r = Math.max(rx, ry)
      ctx.beginPath()
      ctx.arc(cx * dpr, cy * dpr, r * dpr, 0, Math.PI * 2)
      ctx.stroke()
    }
  }, [activeTool, activeColor, strokeWidth, selectedIndex])

  useEffect(() => {
    drawCanvas()
  }, [drawCanvas, elements])

  const setCanvasSize = useCallback(() => {
    const canvas = canvasRef.current
    const container = containerRef.current
    if (!canvas || !container) return
    const dpr = window.devicePixelRatio || 1
    const w = container.clientWidth; const h = container.clientHeight
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px'
    canvas.width = w * dpr; canvas.height = h * dpr
    drawCanvas()
  }, [drawCanvas])

  useEffect(() => {
    setCanvasSize()
    const onResize = () => setCanvasSize()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [setCanvasSize])

  const getPos = (e: React.MouseEvent | MouseEvent | React.TouchEvent | TouchEvent): Point => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }
    const rect = canvas.getBoundingClientRect()
    let clientX: number, clientY: number
    if ('touches' in e) {
      const touch = e.touches[0] || (e as TouchEvent).changedTouches[0]
      clientX = touch.clientX; clientY = touch.clientY
    } else {
      clientX = (e as MouseEvent).clientX; clientY = (e as MouseEvent).clientY
    }
    return { x: clientX - rect.left, y: clientY - rect.top }
  }

  const startDrawing = (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault()
    const pos = getPos(e)
    const dd = dragRef.current
    dd.active = true; dd.startX = pos.x; dd.startY = pos.y
    dd.currentX = pos.x; dd.currentY = pos.y

    if (activeTool === 'pen' || activeTool === 'eraser') {
      dd.drawing = true
      const el: CanvasElement = {
        type: 'path',
        color: activeTool === 'eraser' ? 'var(--bg-base)' : activeColor,
        width: activeTool === 'eraser' ? strokeWidth * 3 : strokeWidth,
        points: [pos],
      }
      setElements(prev => [...prev, el])
      setSelectedIndex(null)
    } else if (activeTool === 'rect' || activeTool === 'circle') {
      dd.drawing = true
      setSelectedIndex(null)
    } else if (activeTool === 'select') {
      const els = elementsRef.current
      let found = -1
      for (let i = els.length - 1; i >= 0; i--) {
        if (hitTest(pos, els[i])) { found = i; break }
      }
      if (found !== -1) {
        setSelectedIndex(found)
        dd.moving = true
        dd.moveOffsetX = pos.x; dd.moveOffsetY = pos.y
      } else {
        setSelectedIndex(null)
      }
    } else if (activeTool === 'text') {
      // Show inline text input overlay on the canvas
      setEditingText({ x: pos.x, y: pos.y })
    }
  }

  const draw = (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault()
    const pos = getPos(e)
    const dd = dragRef.current
    dd.currentX = pos.x; dd.currentY = pos.y

    if (!dd.active) return

    if ((activeTool === 'pen' || activeTool === 'eraser') && dd.drawing) {
      const els = elementsRef.current
      if (els.length === 0) return
      const last = { ...els[els.length - 1], points: [...(els[els.length - 1].points || []), pos] }
      const newEls = [...els.slice(0, -1), last]
      elementsRef.current = newEls
      setElements(newEls)
      drawCanvas()
    } else if ((activeTool === 'rect' || activeTool === 'circle') && dd.drawing) {
      drawCanvas()
    } else if (activeTool === 'select' && dd.moving && selectedIndex !== null) {
      const els = elementsRef.current
      if (selectedIndex >= els.length) return
      const el = { ...els[selectedIndex] }
      const dx = pos.x - dd.moveOffsetX; const dy = pos.y - dd.moveOffsetY
      dd.moveOffsetX = pos.x; dd.moveOffsetY = pos.y
      if (el.type === 'path' && el.points) {
        el.points = el.points.map(p => ({ x: p.x + dx, y: p.y + dy }))
      }
      if (el.x !== undefined) el.x += dx
      if (el.y !== undefined) el.y += dy
      const newElements = els.map((e, i) => i === selectedIndex ? el : e)
      elementsRef.current = newElements
      setElements(newElements)
      drawCanvas()
    }
  }

  const stopDrawing = () => {
    const dd = dragRef.current
    if ((activeTool === 'rect' || activeTool === 'circle') && dd.drawing) {
      const x = Math.min(dd.startX, dd.currentX)
      const y = Math.min(dd.startY, dd.currentY)
      const w = Math.abs(dd.currentX - dd.startX)
      const h = Math.abs(dd.currentY - dd.startY)
      if (w > 5 || h > 5) {
        const el: CanvasElement = activeTool === 'rect'
          ? { type: 'rect', color: activeColor, width: strokeWidth, x, y, w, h }
          : { type: 'circle', color: activeColor, width: strokeWidth, x: (dd.startX + dd.currentX) / 2, y: (dd.startY + dd.currentY) / 2, radius: Math.max(w, h) / 2 }
        const newElements = [...elementsRef.current, el]
        elementsRef.current = newElements
        setElements(newElements)
        drawCanvas()
      }
    }
    if (activeTool === 'select') {
      setSelectedIndex(selectedIndex)
    }
    dd.active = false; dd.drawing = false; dd.moving = false
  }

  const undo = () => {
    setElements(prev => prev.length > 0 ? prev.slice(0, -1) : [])
    setSelectedIndex(null)
  }

  const clearCanvas = () => {
    setElements([])
    setSelectedIndex(null)
  }

  const saveAsPng = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const link = document.createElement('a')
    link.download = 'synapse-whiteboard.png'
    link.href = canvas.toDataURL('image/png')
    link.click()
    toast.success('Whiteboard saved!')
  }

  const toolBtn = (id: string) => ({
    background: activeTool === id ? 'var(--primary-subtle)' : 'var(--bg-surface)',
    border: `1px solid ${activeTool === id ? 'var(--primary-subtle)' : 'transparent'}`,
    borderRadius: 10,
    padding: '8px 12px',
    cursor: 'pointer',
    color: activeTool === id ? 'var(--primary)' : 'var(--text-secondary)',
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: '13px',
    fontWeight: 500,
    transition: 'all 0.15s ease',
  } as React.CSSProperties)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-base)', overflow: 'hidden' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, padding: '12px 24px',
        background: 'var(--bg-elevated)',
        borderBottom: '1px solid var(--border-subtle)',
        flexWrap: 'wrap', flexShrink: 0,
        boxShadow: 'var(--shadow-sm)', zIndex: 10,
      }}>
        <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '15px', marginRight: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Pen size={16} color="var(--primary)" /> Whiteboard
        </span>

        <div style={{ width: 1, height: 24, background: 'var(--border-subtle)', margin: '0 4px' }} />

        <div style={{ display: 'flex', gap: 6 }}>
          {TOOLS.map(({ id, icon: Icon, label }) => (
            <motion.button
              key={id}
              whileHover={activeTool !== id ? { background: 'var(--bg-hover)' } : {}}
              whileTap={{ scale: 0.95 }}
              onClick={() => setActiveTool(id)}
              style={toolBtn(id)}
              title={label}
            >
              <Icon size={16} />
              <span>{label}</span>
            </motion.button>
          ))}
        </div>

        <div style={{ width: 1, height: 24, background: 'var(--border-subtle)', margin: '0 4px' }} />

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {COLORS.map(c => (
            <motion.div
              key={c}
              whileHover={{ scale: 1.15 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setActiveColor(c)}
              style={{
                width: 24, height: 24, borderRadius: '50%', background: c, cursor: 'pointer',
                border: activeColor === c ? '2px solid var(--bg-base)' : '2px solid transparent',
                boxShadow: activeColor === c ? `0 0 0 2px ${c}` : '0 0 0 1px var(--border-subtle)',
                transition: 'all 0.15s ease',
              }}
              title={c}
            />
          ))}
        </div>

        <div style={{ width: 1, height: 24, background: 'var(--border-subtle)', margin: '0 4px' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 500 }}>Size:</span>
          <input
            type="range" min={1} max={20} value={strokeWidth}
            onChange={e => setStrokeWidth(+e.target.value)}
            style={{ width: 80, accentColor: 'var(--primary)', cursor: 'pointer' }}
          />
          <span style={{ color: 'var(--text-secondary)', fontSize: '13px', minWidth: 32, fontWeight: 500 }}>{strokeWidth}px</span>
        </div>

        <div style={{ flex: 1 }} />

        <div style={{ display: 'flex', gap: 8 }}>
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={undo}
            style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '8px 14px', cursor: 'pointer', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6, fontSize: '13px', fontWeight: 500 }}>
            <Undo2 size={16} /> Undo
          </motion.button>
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={saveAsPng}
            style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '8px 14px', cursor: 'pointer', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6, fontSize: '13px', fontWeight: 500 }}>
            <Download size={16} /> Save
          </motion.button>
          {/* Ask AI button removed — no backend endpoint available */}
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={clearCanvas}
            style={{ background: 'var(--danger-subtle)', border: '1px solid var(--danger-subtle)', borderRadius: 10, padding: '8px 14px', cursor: 'pointer', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 6, fontSize: '13px', fontWeight: 500 }}>
            <Trash2 size={16} /> Clear
          </motion.button>
        </div>
      </div>

      <div ref={containerRef} style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <div style={{
          position: 'absolute', inset: 0, opacity: 0.4,
          backgroundImage: 'radial-gradient(var(--border-subtle) 1px, transparent 1px)',
          backgroundSize: '24px 24px', pointerEvents: 'none'
        }} />
        <canvas
          ref={canvasRef}
          style={{ display: 'block', touchAction: 'none', cursor: activeTool === 'text' ? 'crosshair' : activeTool === 'select' ? 'default' : 'crosshair' }}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
        />

        {/* Inline text editor overlay */}
        {editingText && (
          <textarea
            ref={textInputRef}
            autoFocus
            placeholder="Type here…"
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                const val = (e.target as HTMLTextAreaElement).value.trim()
                if (val) {
                  const el: CanvasElement = {
                    type: 'text', color: activeColor, width: strokeWidth,
                    x: editingText.x, y: editingText.y, text: val, fontSize: 24,
                  }
                  const newElements = [...elementsRef.current, el]
                  elementsRef.current = newElements
                  setElements(newElements)
                  setSelectedIndex(newElements.length - 1)
                  drawCanvas()
                }
                setEditingText(null)
              }
            }}
            onBlur={e => {
              const val = e.target.value.trim()
              if (val) {
                const el: CanvasElement = {
                  type: 'text', color: activeColor, width: strokeWidth,
                  x: editingText.x, y: editingText.y, text: val, fontSize: 24,
                }
                const newElements = [...elementsRef.current, el]
                elementsRef.current = newElements
                setElements(newElements)
                setSelectedIndex(newElements.length - 1)
                drawCanvas()
              }
              setEditingText(null)
            }}
            style={{
              position: 'absolute',
              left: editingText.x,
              top: editingText.y - 4,
              minWidth: 160, minHeight: 32,
              padding: '6px 10px',
              fontSize: 24,
              fontFamily: 'Inter, sans-serif',
              background: 'var(--bg-base)',
              color: resolveColor(activeColor),
              border: '2px dashed var(--primary)',
              borderRadius: 8,
              outline: 'none',
              resize: 'both',
              overflow: 'hidden',
              zIndex: 20,
              lineHeight: 1.3,
              boxShadow: 'var(--shadow-md)',
            }}
          />
        )}

        <div style={{ position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)', color: 'var(--text-muted)', fontSize: '12px', pointerEvents: 'none', whiteSpace: 'nowrap', background: 'var(--bg-elevated)', padding: '6px 16px', borderRadius: 99, border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
          Draw · Select to move · Text tool: click then type · Undo to remove
        </div>
      </div>

      {/* AI panel removed — no backend endpoint available */}
    </div>
  )
}
