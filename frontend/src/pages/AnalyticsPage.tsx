import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, Clock, Filter } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import PerformanceLineChart from '../components/charts/PerformanceLineChart'
import SkeletonLoader from '../components/ui/SkeletonLoader'
import { listSessions } from '../services/api'
import { formatDate, scoreToColor } from '../utils/formatters'
import { STATUS_LABELS } from '../utils/constants'
import type { SessionSummary } from '../types'

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }

export default function AnalyticsPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const navigate = useNavigate()

  useEffect(() => {
    listSessions().then(s => { setSessions(s); setLoading(false) })
  }, [])

  const filtered = filter === 'all' ? sessions : sessions.filter(s => s.status === filter)
  const completed = sessions.filter(s => s.status === 'completed')
  const avgScore = completed.length ? +(completed.reduce((a, b) => a + (b.finalScore ?? 0), 0) / completed.length).toFixed(1) : 0
  const avgImprovement = completed.length ? +(completed.reduce((a, b) => a + (b.improvement ?? 0), 0) / completed.length).toFixed(1) : 0
  const avgIterations = sessions.length ? +(sessions.reduce((a, b) => a + b.totalIterations, 0) / sessions.length).toFixed(1) : 0
  const allScores = completed.filter(s => s.finalScore).map(s => s.finalScore!).reverse()

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

        {/* Chart */}
        {allScores.length > 1 && (
          <motion.div variants={fadeUp} className="mb-8">
            <Card>
              <h2 className="section-title mb-4">Score Trend</h2>
              <PerformanceLineChart data={allScores} target={8.5} height={280} />
            </Card>
          </motion.div>
        )}

        {/* Score Distribution */}
        <motion.div variants={fadeUp} className="mb-8">
          <Card>
            <h2 className="section-title mb-4">Score Distribution</h2>
            <div className="flex items-end gap-1 h-32">
              {Array.from({ length: 10 }, (_, i) => {
                const min = i + 1
                const max = i + 2
                const count = completed.filter(s => (s.finalScore ?? 0) >= min && (s.finalScore ?? 0) < max).length
                const height = completed.length ? (count / completed.length) * 100 : 0
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <motion.div
                      className="w-full rounded-t"
                      style={{ backgroundColor: scoreToColor(min + 0.5), height: `${Math.max(height, 4)}%` }}
                      initial={{ scaleY: 0 }}
                      animate={{ scaleY: 1 }}
                      transition={{ delay: i * 0.05, duration: 0.4 }}
                    />
                    <span className="text-[10px] font-mono text-text-muted">{min}</span>
                  </div>
                )
              })}
            </div>
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
                    <th className="text-left px-5 py-3 table-header">Date</th>
                  </tr>
                </thead>
                <tbody>
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
