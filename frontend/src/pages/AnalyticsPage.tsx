import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, Clock, Filter } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import PerformanceLineChart from '../components/charts/PerformanceLineChart'
import SkeletonLoader from '../components/ui/SkeletonLoader'
import { getModelCallHistory, listSessions } from '../services/api'
import { formatDate, scoreToColor } from '../utils/formatters'
import { STATUS_LABELS } from '../utils/constants'
import type { SessionSummary } from '../types'

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }

export default function AnalyticsPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [modelCalls, setModelCalls] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const LS_KEY = 'astra_analytics_sessions_v1'
  const navigate = useNavigate()

  useEffect(() => {
    const cached = localStorage.getItem(LS_KEY)
    if (cached) {
      try {
        const parsed = JSON.parse(cached)
        if (Array.isArray(parsed) && parsed.length > 0) {
          setSessions(parsed)
          setLoading(false)
        }
      } catch {
        // ignore invalid cache
      }
    }

    const refresh = () => {
      listSessions().then((rows) => {
        const normalized = Array.isArray(rows) ? rows : []
        if (normalized.length > 0) {
          setSessions(normalized)
          localStorage.setItem(LS_KEY, JSON.stringify(normalized))
        }
        setModelCalls(getModelCallHistory())
        setLoading(false)
      }).catch(() => {
        setModelCalls(getModelCallHistory())
        setLoading(false)
      })
    }

    refresh()
    const iv = setInterval(refresh, 5000)
    return () => clearInterval(iv)
  }, [])

  const filtered = filter === 'all' ? sessions : sessions.filter(s => s.status === filter)
  const completed = sessions.filter(s => s.status === 'completed')
  const completionRate = sessions.length ? (completed.length / sessions.length) * 100 : 0
  const avgDuration = sessions.length ? (sessions.reduce((a, b) => a + (b.durationSeconds || 0), 0) / sessions.length) : 0
  const totalCost = sessions.reduce((a, b) => a + (b.totalCost || 0), 0)
  const avgScore = completed.length ? +(completed.reduce((a, b) => a + (b.finalScore ?? 0), 0) / completed.length).toFixed(1) : 0
  const avgImprovement = completed.length ? +(completed.reduce((a, b) => a + (b.improvement ?? 0), 0) / completed.length).toFixed(1) : 0
  const avgIterations = sessions.length ? +(sessions.reduce((a, b) => a + b.totalIterations, 0) / sessions.length).toFixed(1) : 0
  const allScores = completed.filter(s => s.finalScore !== undefined && s.finalScore !== null).map(s => s.finalScore as number).reverse()
  const fallbackScores = modelCalls
    .slice()
    .reverse()
    .slice(-12)
    .map((c) => {
      const qualityFromTokens = Math.max(1, Math.min(10, (Number(c.tokensUsed || 0) / 180)))
      return +qualityFromTokens.toFixed(1)
    })
  const chartScores = allScores.length > 1 ? allScores : fallbackScores.length > 1 ? fallbackScores : [4.0, 4.2]

  const distributionScores = allScores.length > 0 ? allScores : fallbackScores
  const usingFallbackDistribution = allScores.length === 0 && fallbackScores.length > 0
  const distributionData = Array.from({ length: 10 }, (_, i) => {
    const min = i
    const max = i + 1
    const count = distributionScores.filter((s) => {
      const score = Math.max(0, Math.min(10, s))
      if (i === 9) return score >= min && score <= 10
      return score >= min && score < max
    }).length
    return {
      range: `${min}-${max}`,
      count,
      color: scoreToColor(min + 0.5),
    }
  })

  if (loading) return <div className="page-container"><SkeletonLoader rows={8} /></div>

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        <motion.div variants={fadeUp} className="mb-8">
          <h1 className="page-title">Analytics</h1>
          <p className="text-text-secondary text-sm mt-1">Aggregated performance metrics and session history</p>
        </motion.div>

        {/* Summary */}
        <motion.div variants={fadeUp} className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Sessions', value: sessions.length, decimals: 0 },
            { label: 'Avg Score', value: avgScore, decimals: 1, suffix: '/10' },
            { label: 'Avg Improvement', value: avgImprovement, decimals: 1, prefix: '+' },
            { label: 'Avg Iterations', value: avgIterations, decimals: 1 },
          ].map(m => (
            <Card key={m.label} className="text-center">
              <p className="text-xs font-mono text-text-muted uppercase mb-1">{m.label}</p>
              <p className="text-2xl font-body font-bold text-text-primary">
                <AnimatedNumber value={m.value} decimals={m.decimals} prefix={m.prefix} suffix={m.suffix} />
              </p>
            </Card>
          ))}
        </motion.div>

        <motion.div variants={fadeUp} className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className="text-center">
            <p className="text-xs font-mono text-text-muted uppercase mb-1">Completion Rate</p>
            <p className="text-2xl font-body font-bold text-text-primary">{completionRate.toFixed(0)}%</p>
          </Card>
          <Card className="text-center">
            <p className="text-xs font-mono text-text-muted uppercase mb-1">Avg Duration</p>
            <p className="text-2xl font-body font-bold text-text-primary">{avgDuration.toFixed(1)}s</p>
          </Card>
          <Card className="text-center">
            <p className="text-xs font-mono text-text-muted uppercase mb-1">Total Cost</p>
            <p className="text-2xl font-body font-bold text-text-primary">${totalCost.toFixed(4)}</p>
          </Card>
          <Card className="text-center">
            <p className="text-xs font-mono text-text-muted uppercase mb-1">Completed Runs</p>
            <p className="text-2xl font-body font-bold text-text-primary">{completed.length}</p>
          </Card>
        </motion.div>

        <motion.div variants={fadeUp} className="mb-8">
          <Card>
            <div className="flex items-center justify-between mb-3">
              <h2 className="section-title">Recent Model Call Outputs</h2>
              <span className="text-xs text-text-muted font-mono">{modelCalls.length} calls saved</span>
            </div>
            <div className="space-y-2">
              {modelCalls.length === 0 && <div className="text-sm text-text-muted">No saved model calls yet.</div>}
              {modelCalls.slice(0, 6).map((c) => (
                <div key={c.id} className="rounded-button border border-border p-3">
                  <div className="flex items-center justify-between text-[11px] text-text-muted mb-1">
                    <span className="font-mono">{c.endpoint} • {c.model?.split('/').pop() || c.model}</span>
                    <span>{new Date(c.timestamp).toLocaleString()}</span>
                  </div>
                  <p className="text-sm text-text-primary break-words line-clamp-2">{c.output || 'No output'}</p>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>

        {/* Chart */}
        <motion.div variants={fadeUp} className="mb-8">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title">Score Trend</h2>
              {allScores.length <= 1 && (
                <span className="text-xs text-text-muted font-mono">Using live model-call fallback</span>
              )}
            </div>
            <PerformanceLineChart data={chartScores} target={8.5} height={280} />
          </Card>
        </motion.div>

        {/* Score Distribution */}
        <motion.div variants={fadeUp} className="mb-8">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title">Score Distribution</h2>
              {usingFallbackDistribution && (
                <span className="text-xs text-text-muted font-mono">Using live model-call fallback</span>
              )}
            </div>
            {distributionScores.length === 0 ? (
              <p className="text-sm text-text-muted text-center py-8">No scored sessions yet. Run optimizations to build distribution data.</p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={distributionData} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                  <XAxis
                    dataKey="range"
                    tick={{ fontSize: 11, fill: 'var(--color-text-muted)', fontFamily: 'JetBrains Mono' }}
                    axisLine={{ stroke: 'var(--color-border)' }}
                    tickLine={false}
                    label={{ value: 'Score Range', position: 'insideBottom', offset: -2, fontSize: 11, fill: 'var(--color-text-muted)' }}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 11, fill: 'var(--color-text-muted)', fontFamily: 'JetBrains Mono' }}
                    axisLine={{ stroke: 'var(--color-border)' }}
                    tickLine={false}
                    label={{ value: 'Sessions', angle: -90, position: 'insideLeft', fontSize: 11, fill: 'var(--color-text-muted)' }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: '10px',
                      fontSize: 12,
                      fontFamily: 'JetBrains Mono',
                      color: 'var(--color-text-primary)',
                    }}
                    labelStyle={{ color: 'var(--color-text-secondary)' }}
                    formatter={(value: number) => [value, 'Sessions']}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={32}>
                    {distributionData.map((entry, i) => (
                      <Cell key={`cell-${i}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </Card>
        </motion.div>

        {/* Filter + Table */}
        <motion.div variants={fadeUp}>
          <Card noPad>
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
              <h2 className="section-title">All Sessions</h2>
              <div className="flex items-center gap-2 text-xs">
                <Filter size={12} className="text-text-muted" />
                {['all', 'completed', 'stopped', 'error'].map(f => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`px-2 py-1 rounded-full font-mono transition-colors ${filter === f ? 'bg-accent text-accent-contrast' : 'text-text-muted hover:text-text-primary'}`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-5 py-3 table-header">Session ID</th>
                    <th className="text-left px-5 py-3 table-header">Status</th>
                    <th className="text-left px-5 py-3 table-header">Model</th>
                    <th className="text-left px-5 py-3 table-header">Score</th>
                    <th className="text-left px-5 py-3 table-header">Δ</th>
                    <th className="text-left px-5 py-3 table-header">Iters</th>
                    <th className="text-left px-5 py-3 table-header">Duration</th>
                    <th className="text-left px-5 py-3 table-header">Cost</th>
                    <th className="text-left px-5 py-3 table-header">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 && (
                    <tr>
                      <td className="px-5 py-8 text-sm text-text-muted" colSpan={9}>
                        No analytics yet. Run Ask, Compare, or Optimize to build live metrics and charts.
                      </td>
                    </tr>
                  )}
                  {filtered.map(s => {
                    const st = STATUS_LABELS[s.status] ?? STATUS_LABELS.idle
                    return (
                      <tr key={s.sessionId} className="table-row cursor-pointer" onClick={() => navigate(`/sessions/${s.sessionId}`)}>
                        <td className="px-5 py-3 font-mono text-sm text-text-primary">{s.sessionId.slice(0, 14)}</td>
                        <td className="px-5 py-3"><Badge variant={st.variant as 'success'}>{st.label}</Badge></td>
                        <td className="px-5 py-3 text-sm text-text-secondary font-mono">{s.model?.split('/').pop()?.split('-')[0] ?? '—'}</td>
                        <td className="px-5 py-3 font-mono font-semibold" style={{ color: scoreToColor(s.finalScore ?? 0) }}>
                          {s.finalScore?.toFixed(1) ?? '—'}
                        </td>
                        <td className="px-5 py-3 font-mono text-sm text-text-secondary">
                          {s.improvement != null ? (s.improvement > 0 ? '+' : '') + s.improvement.toFixed(1) : '—'}
                        </td>
                        <td className="px-5 py-3 font-mono text-sm text-text-secondary">{s.totalIterations}</td>
                        <td className="px-5 py-3 font-mono text-sm text-text-secondary">{(s.durationSeconds || 0).toFixed(1)}s</td>
                        <td className="px-5 py-3 font-mono text-sm text-text-secondary">${(s.totalCost || 0).toFixed(4)}</td>
                        <td className="px-5 py-3 text-sm text-text-muted">{formatDate(s.startedAt)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  )
}
