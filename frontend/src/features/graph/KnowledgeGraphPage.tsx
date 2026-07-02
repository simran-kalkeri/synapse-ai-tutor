import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import * as d3 from 'd3'
import { ZoomIn, ZoomOut, RotateCcw, Search, X, Info } from 'lucide-react'
import { graphApi } from '@/lib/api'
import type { GraphNode, GraphEdge } from '@/types'

const TOPIC_COLORS: Record<string, string> = {
  'Neural Networks':           '#7c3aed',
  'CNNs':                      '#06b6d4',
  'RNNs':                      '#10b981',
  'Transformers':               '#f59e0b',
  'LLMs':                      '#ef4444',
  'Prompt Engineering':         '#a855f7',
  'Generative AI Fundamentals': '#3b82f6',
  'GANs':                      '#ec4899',
  'Diffusion Models':           '#14b8a6',
  'Fine-Tuning and RAG':        '#f97316',
}
const DEFAULT_COLOR = '#64748b'

interface SimNode extends d3.SimulationNodeDatum, GraphNode {
  color: string
  radius: number
}

export default function KnowledgeGraphPage() {
  const svgRef    = useRef<SVGSVGElement>(null)
  const wrapRef   = useRef<HTMLDivElement>(null)
  const simRef    = useRef<d3.Simulation<SimNode, undefined> | null>(null)

  const [selected, setSelected]  = useState<SimNode | null>(null)
  const [filterTopic, setFilter] = useState<string>('all')
  const [search, setSearch]      = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['graph-data'],
    queryFn: () => graphApi.data().then(r => r.data),
    staleTime: 5 * 60_000,
  })

  const nodes: GraphNode[] = data?.nodes ?? []
  const edges: GraphEdge[] = data?.edges ?? []

  useEffect(() => {
    if (!svgRef.current || !wrapRef.current || nodes.length === 0) return

    const W = wrapRef.current.clientWidth
    const H = wrapRef.current.clientHeight

    // Clear previous
    d3.select(svgRef.current).selectAll('*').remove()
    if (simRef.current) simRef.current.stop()

    const svg = d3.select(svgRef.current)
      .attr('width', W).attr('height', H)

    // Zoom behaviour
    const g = svg.append('g')
    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.15, 4])
        .on('zoom', (event) => g.attr('transform', event.transform))
    )

    // Filter nodes
    const filteredNodes: SimNode[] = nodes
      .filter(n => filterTopic === 'all' || n.topic === filterTopic)
      .filter(n => !search || n.label.toLowerCase().includes(search.toLowerCase()))
      .map(n => ({
        ...n,
        color: TOPIC_COLORS[n.topic ?? ''] ?? DEFAULT_COLOR,
        radius: n.node_type === 'topic' ? 14 : 8,
      }))

    const nodeIds = new Set(filteredNodes.map(n => n.id))
    const filteredEdges = edges.filter(e => nodeIds.has(e.source as string) && nodeIds.has(e.target as string))

    // Simulation
    const sim = d3.forceSimulation(filteredNodes)
      .force('link', d3.forceLink<SimNode, GraphEdge>(filteredEdges)
        .id(d => d.id).distance(80).strength(0.4))
      .force('charge', d3.forceManyBody().strength(-180))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide<SimNode>(d => d.radius + 6))

    simRef.current = sim

    // Edges
    const link = g.append('g').selectAll('line')
      .data(filteredEdges).join('line')
      .attr('stroke', 'rgba(124,58,237,0.2)')
      .attr('stroke-width', 1)

    // Node groups
    const node = g.append('g').selectAll<SVGGElement, SimNode>('g')
      .data(filteredNodes).join('g')
      .style('cursor', 'pointer')
      .call(
        d3.drag<SVGGElement, SimNode>()
          .on('start', (event, d) => { if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
          .on('drag',  (event, d) => { d.fx = event.x; d.fy = event.y })
          .on('end',   (event, d) => { if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null })
      )
      .on('click', (_e, d) => setSelected(prev => prev?.id === d.id ? null : d))

    // Circles
    node.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => d.color + '33')
      .attr('stroke', d => d.color)
      .attr('stroke-width', 2)

    // Labels
    node.append('text')
      .text(d => d.label.length > 18 ? d.label.slice(0, 16) + '…' : d.label)
      .attr('x', d => d.radius + 4).attr('y', 4)
      .attr('fill', '#94a3b8').attr('font-size', '10px')
      .style('pointer-events', 'none')

    // Tick
    sim.on('tick', () => {
      link
        .attr('x1', d => ((d.source as unknown) as SimNode).x ?? 0)
        .attr('y1', d => ((d.source as unknown) as SimNode).y ?? 0)
        .attr('x2', d => ((d.target as unknown) as SimNode).x ?? 0)
        .attr('y2', d => ((d.target as unknown) as SimNode).y ?? 0)
      node.attr('transform', d => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    return () => { sim.stop() }
  }, [nodes, edges, filterTopic, search])

  const topics = Array.from(new Set(nodes.map(n => n.topic).filter(Boolean))) as string[]

  const handleZoom = (factor: number) => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.15, 4])
    svg.transition().duration(300).call(zoom.scaleBy as never, factor)
  }

  const handleReset = () => {
    if (!svgRef.current) return
    const W = wrapRef.current?.clientWidth ?? 800
    const H = wrapRef.current?.clientHeight ?? 600
    d3.select(svgRef.current).transition().duration(400)
      .call(d3.zoom<SVGSVGElement, unknown>().transform as never, d3.zoomIdentity.translate(W / 2, H / 2).scale(0.8))
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(124,58,237,0.12)', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0, flexWrap: 'wrap' }}>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontWeight: 800, fontSize: 18, color: '#f1f5f9' }}>Knowledge Graph Explorer</h1>
          <p style={{ fontSize: 12, color: '#64748b' }}>{nodes.length} nodes · {edges.length} relationships</p>
        </div>
        {/* Search */}
        <div style={{ position: 'relative' }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search nodes…"
            style={{ padding: '7px 10px 7px 30px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(124,58,237,0.2)', color: '#f1f5f9', fontSize: 13, outline: 'none', width: 180 }} />
        </div>
        {/* Topic filter */}
        <select value={filterTopic} onChange={e => setFilter(e.target.value)}
          style={{ padding: '7px 10px', borderRadius: 8, background: 'rgba(26,26,46,0.9)', border: '1px solid rgba(124,58,237,0.2)', color: '#f1f5f9', fontSize: 13, outline: 'none' }}>
          <option value="all">All Topics</option>
          {topics.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        {/* Zoom controls */}
        <div style={{ display: 'flex', gap: 6 }}>
          {[{ icon: ZoomIn, action: () => handleZoom(1.3) }, { icon: ZoomOut, action: () => handleZoom(0.7) }, { icon: RotateCcw, action: handleReset }].map(({ icon: Icon, action }, i) => (
            <button key={i} onClick={action}
              style={{ width: 32, height: 32, borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
              <Icon size={14} />
            </button>
          ))}
        </div>
      </div>

      {/* Graph canvas */}
      <div ref={wrapRef} style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {isLoading && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 15 }}>
            <div>Loading knowledge graph…</div>
          </div>
        )}
        {!isLoading && nodes.length === 0 && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', textAlign: 'center' }}>
            <div>
              <Info size={32} style={{ marginBottom: 8, color: '#475569' }} />
              <p>Knowledge graph not loaded.<br />Ensure the backend is running and knowledge_graph.json exists.</p>
            </div>
          </div>
        )}
        <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />

        {/* Legend */}
        <div style={{ position: 'absolute', bottom: 16, left: 16, padding: '12px 16px', borderRadius: 12, background: 'rgba(10,10,26,0.85)', border: '1px solid rgba(124,58,237,0.15)', backdropFilter: 'blur(8px)' }}>
          <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Topics</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {Object.entries(TOPIC_COLORS).slice(0, 6).map(([t, c]) => (
              <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: '#94a3b8', cursor: 'pointer' }}
                onClick={() => setFilter(f => f === t ? 'all' : t)}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: c, flexShrink: 0 }} />
                {t}
              </div>
            ))}
          </div>
        </div>

        {/* Node detail panel */}
        <AnimatePresence>
          {selected && (
            <motion.div
              initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}
              style={{ position: 'absolute', top: 16, right: 16, width: 260, padding: 20, borderRadius: 14, background: 'rgba(26,26,46,0.95)', border: '1px solid rgba(124,58,237,0.3)', backdropFilter: 'blur(12px)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: selected.color }} />
                <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}><X size={16} /></button>
              </div>
              <div style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 15, marginBottom: 6 }}>{selected.label}</div>
              {selected.topic && <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>Topic: <span style={{ color: selected.color }}>{selected.topic}</span></div>}
              {selected.node_type && <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>Type: <span style={{ color: '#94a3b8' }}>{selected.node_type}</span></div>}
              {selected.level && <div style={{ fontSize: 12, color: '#64748b' }}>Level: <span style={{ color: '#94a3b8' }}>{selected.level}</span></div>}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
