import type { CSSProperties } from 'react'

interface SkeletonProps {
  width?: string | number
  height?: string | number
  borderRadius?: string | number
  style?: CSSProperties
}

export function Skeleton({ width = '100%', height = 20, borderRadius = 8, style }: SkeletonProps) {
  return (
    <div
      className="animate-shimmer"
      style={{ width, height, borderRadius, ...style }}
    />
  )
}

export function SkeletonCard({ height = 120 }: { height?: number }) {
  return (
    <div style={{
      padding: 24, borderRadius: 16,
      background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
    }}>
      <Skeleton height={height} />
    </div>
  )
}

export function SkeletonLine({ width = '100%', style }: { width?: string | number; style?: CSSProperties }) {
  return <Skeleton width={width} height={14} borderRadius={4} style={{ marginBottom: 12, ...style }} />
}

export function DashboardSkeleton() {
  return (
    <div style={{ padding: '40px 48px', maxWidth: 1100, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
      <Skeleton width={200} height={32} style={{ marginBottom: 12 }} />
      <Skeleton width={300} height={20} style={{ marginBottom: 40 }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        {[1,2,3,4].map(i => <SkeletonCard key={i} height={80} />)}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24 }}>
        {[1,2].map(i => <SkeletonCard key={i} height={300} />)}
      </div>
    </div>
  )
}
