import { useEffect, useRef, useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import * as d3 from 'd3'
import { ZoomIn, ZoomOut, RotateCcw, Search, X, Info } from 'lucide-react'
import { graphApi } from '@/lib/api'
import type { GraphNode, GraphEdge } from '@/types'

const TOPIC_COLORS: Record<string, string> = {
  'Neural Networks':           'var(--primary)',
  'CNNs':                      'var(--accent)',
  'RNNs':                      'var(--success)',
  'Transformers':              'var(--warning)',
  'LLMs':                      'var(--danger)',
  'Prompt Engineering':         '#a855f7',
  'Generative AI Fundamentals': '#3b82f6',
  'GANs':                      '#ec4899',
  'Diffusion Models':          '#14b8a6',
  'Fine-Tuning and RAG':       '#f97316',
}
const DEFAULT_COLOR = 'var(--text-muted)'

interface SimNode extends d3.SimulationNodeDatum, GraphNode {
  color: string
  radius: number
}

const posCache = new Map<string, { x: number; y: number }>()

export default function KnowledgeGraphPage() {
  const svgRef    = useRef<SVGSVGElement>(null)
  const wrapRef   = useRef<HTMLDivElement>(null)
  const zoomRef   = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null)
  const simRef    = useRef<d3.Simulation<SimNode, undefined> | null>(null)

  const [selected, setSelected]  = useState<SimNode | null>(null)
  const [filterTopic, setFilter] = useState<string>('all')
  const [search, setSearch]      = useState('')
  const [relayout, setRelayout]  = useState(0)

  const { data, isLoading } = useQuery({
    queryKey: ['graph-data'],
    queryFn: () => graphApi.data().then(r => r.data),
    staleTime: 5 * 60_000,
  })

  const nodes: GraphNode[] = data?.nodes ?? []
  const edges: GraphEdge[] = data?.edges ?? []

  const filtered = useMemo(() => {
    if (nodes.length === 0) return { nodes: [] as SimNode[], edges: [] as GraphEdge[] }

    // When a specific topic is selected, show the topic node + its child concepts
    const isFiltering = filterTopic !== 'all'
    const topicSubtree = new Set<string>()
    if (isFiltering) {
      // Include nodes whose `topic` field matches (set by backend via edges)
      topicSubtree.add(filterTopic)
      for (const n of nodes) {
        if (n.topic === filterTopic) topicSubtree.add(n.id)
      }
      // Also include directly connected nodes (backup for nodes without topic field)
      for (const e of edges) {
        if (e.source === filterTopic) topicSubtree.add(e.target as string)
        if (e.target === filterTopic) topicSubtree.add(e.source as string)
      }
    }

    const fn: SimNode[] = nodes
      .filter(n => !isFiltering || topicSubtree.has(n.id))
      .filter(n => !search || n.label.toLowerCase().includes(search.toLowerCase()))
      .map(n => ({
        ...n, color: TOPIC_COLORS[n.topic ?? ''] ?? DEFAULT_COLOR,
        radius: n.node_type === 'topic' ? 14 : 8,
      }))
    const nid = new Set(fn.map(n => n.id))
    const fe = edges.filter(e => nid.has(e.source as string) && nid.has(e.target as string))
    return { nodes: fn, edges: fe }
  }, [nodes, edges, filterTopic, search, relayout])

  const allCached = filtered.nodes.length > 0 && filtered.nodes.every(n => posCache.has(n.id))
  const needsLayout = filtered.nodes.length > 0 && (!allCached || relayout > 0)

  useEffect(() => {
    if (!svgRef.current || !wrapRef.current || filtered.nodes.length === 0) return

    const W = wrapRef.current.clientWidth
    const H = wrapRef.current.clientHeight

    d3.select(svgRef.current).selectAll('*').remove()
    if (simRef.current) { simRef.current.stop(); simRef.current = null }

    const svg = d3.select(svgRef.current).attr('width', W).attr('height', H)
    const g = svg.append('g')

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.15, 4])
      .on('zoom', (event) => { g.attr('transform', event.transform) })
    svg.call(zoom)
    zoomRef.current = zoom
    svg.call(zoom.transform, d3.zoomIdentity.translate(W / 2, H / 2).scale(0.8))

    // Restore cached positions
    for (const n of filtered.nodes) {
      const c = posCache.get(n.id)
      if (c) { n.x = c.x; n.y = c.y }
    }

    const link = g.append('g').selectAll<SVGLineElement, GraphEdge>('line')
      .data(filtered.edges).join('line')
      .style('stroke', 'var(--border)').attr('stroke-width', 1)

    const node = g.append('g').selectAll<SVGGElement, SimNode>('g')
      .data(filtered.nodes).join('g')
      .style('cursor', 'pointer')
      .call(d3.drag<SVGGElement, SimNode>()
        .on('start', (event, d) => {
          if (!simRef.current) runSim(simRef, filtered, W, H, link, node)
          if (!event.active) simRef.current?.alphaTarget(0.3).restart()
          d.fx = d.x; d.fy = d.y
        })
        .on('drag',  (event, d) => { d.fx = event.x; d.fy = event.y })
        .on('end',   (event, d) => {
          if (!event.active) simRef.current?.alphaTarget(0)
          d.fx = null; d.fy = null
        })
      )
      .on('click', (_e, d) => setSelected(p => p?.id === d.id ? null : d))

    node.append('circle')
      .attr('r', d => d.radius)
      .style('fill', d => d.color)
      .style('stroke', 'var(--bg-base)').attr('stroke-width', 2)

    node.append('text')
      .text(d => d.label.length > 18 ? d.label.slice(0, 16) + '…' : d.label)
      .attr('x', d => d.radius + 6).attr('y', 4)
      .attr('fill', 'var(--text-secondary)').attr('font-size', '11px')
      .attr('font-weight', '500').style('pointer-events', 'none')

    if (needsLayout) {
      runSim(simRef, filtered, W, H, link, node)
    } else {
      // Static render from cache — no simulation jiggle
      link.attr('x1', d => ((d.source as unknown) as SimNode).x ?? 0)
        .attr('y1', d => ((d.source as unknown) as SimNode).y ?? 0)
        .attr('x2', d => ((d.target as unknown) as SimNode).x ?? 0)
        .attr('y2', d => ((d.target as unknown) as SimNode).y ?? 0)
      node.attr('transform', d => `translate(${d.x ?? 0},${d.y ?? 0})`)
    }

    return () => {
      const cur = simRef.current?.nodes() ?? filtered.nodes
      for (const n of cur) posCache.set(n.id, { x: n.x ?? 0, y: n.y ?? 0 })
      simRef.current?.stop()
    }
  }, [filtered, needsLayout])

  // Derive topics from topic-type nodes + any other node that has a TOPIC_COLORS entry
  const topics = Array.from(new Set(
    nodes.filter(n => n.node_type === 'topic' || TOPIC_COLORS[n.id]).map(n => n.id)
  )) as string[]

  const handleZoom = (factor: number) => {
    if (!svgRef.current || !zoomRef.current) return
    d3.select(svgRef.current).transition().duration(300).call(zoomRef.current.scaleBy, factor)
  }

  const handleReset = () => {
    if (!svgRef.current || !zoomRef.current) return
    const W = wrapRef.current?.clientWidth ?? 800
    const H = wrapRef.current?.clientHeight ?? 600
    d3.select(svgRef.current).transition().duration(400)
      .call(zoomRef.current.transform, d3.zoomIdentity.translate(W / 2, H / 2).scale(0.8))
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-base)' }}>
      <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)', display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0, flexWrap: 'wrap', zIndex: 10, boxShadow: 'var(--shadow-sm)' }}>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontWeight: 600, fontSize: 18, color: 'var(--text-primary)', letterSpacing: '-0.01em', marginBottom: 2 }}>Knowledge Graph Explorer</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{nodes.length} nodes · {edges.length} relationships</p>
        </div>
        <div style={{ position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search nodes…"
            style={{ padding: '10px 12px 10px 36px', borderRadius: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', fontSize: 14, outline: 'none', width: 220, fontWeight: 500 }} />
        </div>
        <select value={filterTopic} onChange={e => setFilter(e.target.value)}
          style={{ padding: '10px 14px', borderRadius: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', fontSize: 14, outline: 'none', fontWeight: 500, cursor: 'pointer' }}>
          <option value="all">All Topics</option>
          {topics.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <div style={{ display: 'flex', gap: 8 }}>
          {[{ icon: ZoomIn, action: () => handleZoom(1.3) }, { icon: ZoomOut, action: () => handleZoom(0.7) }, { icon: RotateCcw, action: handleReset }].map(({ icon: Icon, action }, i) => (
            <button key={i} onClick={action}
              style={{ width: 40, height: 40, borderRadius: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              <Icon size={16} />
            </button>
          ))}
        </div>
        <button onClick={() => { setRelayout(v => v + 1) }}
          style={{ padding: '10px 16px', borderRadius: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer', color: 'var(--text-primary)', fontSize: 13, fontWeight: 500 }}>
          Re-layout
        </button>
      </div>

      <div ref={wrapRef} style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {isLoading && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: 15, fontWeight: 500 }}>
            Loading knowledge graph…
          </div>
        )}
        {!isLoading && nodes.length === 0 && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', textAlign: 'center' }}>
            <div style={{ padding: '40px', background: 'var(--bg-elevated)', borderRadius: 20, boxShadow: 'var(--shadow-md)', border: '1px solid var(--border-subtle)' }}>
              <Info size={32} style={{ margin: '0 auto 16px', color: 'var(--text-muted)' }} />
              <p style={{ fontWeight: 500, fontSize: 15 }}>Knowledge graph not loaded.<br />Ensure the backend is running and data exists.</p>
            </div>
          </div>
        )}
        <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />

        <div style={{ position: 'absolute', bottom: 24, left: 24, padding: '16px 20px', borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-md)' }}>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600, marginBottom: 12, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Topics</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {topics.filter(t => TOPIC_COLORS[t]).map(t => (
              <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: 'var(--text-primary)', cursor: 'pointer', fontWeight: 500 }}
                onClick={() => setFilter(f => f === t ? 'all' : t)}>
                <div style={{ width: 12, height: 12, borderRadius: '50%', background: TOPIC_COLORS[t], flexShrink: 0, border: '2px solid var(--bg-base)' }} />
                {t}
              </div>
            ))}
          </div>
        </div>

        <AnimatePresence>
          {selected && (
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}
              style={{ position: 'absolute', top: 24, right: 24, width: 320, padding: 24, borderRadius: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div style={{ width: 12, height: 12, borderRadius: '50%', background: selected.color, border: '2px solid var(--bg-base)' }} />
                <button onClick={() => setSelected(null)} style={{ background: 'var(--bg-surface)', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><X size={14} /></button>
              </div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 18, marginBottom: 12, letterSpacing: '-0.01em' }}>{selected.label}</div>
              {selected.topic && <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 500 }}>Topic: <span style={{ color: selected.color }}>{selected.topic}</span></div>}
              {selected.node_type && <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 500 }}>Type: <span style={{ color: 'var(--text-primary)' }}>{selected.node_type}</span></div>}
              {selected.level && <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>Level: <span style={{ color: 'var(--text-primary)' }}>{selected.level}</span></div>}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

function runSim(
  simRef: React.MutableRefObject<d3.Simulation<SimNode, undefined> | null>,
  filtered: { nodes: SimNode[]; edges: GraphEdge[] },
  W: number, H: number,
  link: d3.Selection<SVGLineElement, GraphEdge, SVGGElement, unknown>,
  node: d3.Selection<SVGGElement, SimNode, SVGGElement, unknown>,
) {
  simRef.current?.stop()
  for (const n of filtered.nodes) {
    if (n.x == null) {
      n.x = W / 2 + (Math.random() - 0.5) * W * 0.6
      n.y = H / 2 + (Math.random() - 0.5) * H * 0.6
    }
  }
  const sim = d3.forceSimulation(filtered.nodes)
    .force('link', d3.forceLink<SimNode, GraphEdge>(filtered.edges)
      .id(d => d.id).distance(100).strength(0.6))
    .force('charge', d3.forceManyBody().strength(-250))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('collision', d3.forceCollide<SimNode>(d => d.radius + 8))
  simRef.current = sim
  sim.on('tick', () => {
    link.attr('x1', d => ((d.source as unknown) as SimNode).x ?? 0)
      .attr('y1', d => ((d.source as unknown) as SimNode).y ?? 0)
      .attr('x2', d => ((d.target as unknown) as SimNode).x ?? 0)
      .attr('y2', d => ((d.target as unknown) as SimNode).y ?? 0)
    node.attr('transform', d => `translate(${d.x ?? 0},${d.y ?? 0})`)
  })
  sim.on('end', () => {
    for (const n of filtered.nodes) posCache.set(n.id, { x: n.x ?? 0, y: n.y ?? 0 })
  })
}
