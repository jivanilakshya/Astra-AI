export function scoreToColor(score: number): string {
  if (score >= 8.5) return '#22C55E'
  if (score >= 7) return '#84CC16'
  if (score >= 5.5) return '#EAB308'
  if (score >= 4) return '#F97316'
  return '#EF4444'
}

export function scoreToLabel(score: number): string {
  if (score >= 8.5) return 'Excellent'
  if (score >= 7) return 'Good'
  if (score >= 5.5) return 'Average'
  if (score >= 4) return 'Poor'
  return 'Critical'
}

export function gradeToColor(grade: string): string {
  switch (grade) {
    case 'A': return '#22C55E'
    case 'B': return '#84CC16'
    case 'C': return '#EAB308'
    case 'D': return '#F97316'
    case 'F': return '#EF4444'
    default: return '#A3A3A3'
  }
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return s > 0 ? `${m}m ${s}s` : `${m}m`
}

export function formatCost(usd: number): string {
  if (usd === 0) return 'Free'
  if (usd < 0.001) return `$${usd.toFixed(5)}`
  if (usd < 0.01) return `$${usd.toFixed(4)}`
  if (usd < 1) return `$${usd.toFixed(3)}`
  return `$${usd.toFixed(2)}`
}

export function formatDate(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function formatNumber(n: number, decimals = 1): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(decimals)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(decimals)}K`
  return n.toFixed(decimals)
}

export function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ')
}

export function truncate(s: string, len: number): string {
  return s.length > len ? s.slice(0, len) + '…' : s
}

export function modelShortName(id: string): string {
  const parts = id.split('/')
  return parts[parts.length - 1]
}
