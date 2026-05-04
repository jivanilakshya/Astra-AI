import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Zap, TrendingUp, Clock, DollarSign, ArrowRight, ActivitySquare } from 'lucide-react'
import Card from '../components/ui/Card'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import Badge from '../components/ui/Badge'
import PerformanceLineChart from '../components/charts/PerformanceLineChart'
import SkeletonLoader from '../components/ui/SkeletonLoader'
import { getModelCallHistory, listSessions } from '../services/api'
import { formatDate, formatCost, formatDuration, scoreToColor } from '../utils/formatters'
import { STATUS_LABELS } from '../utils/constants'
import type { SessionSummary } from '../types'

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } } }

export default function DashboardPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [modelCalls, setModelCalls] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const LS_KEY = 'astra_dashboard_sessions_v1'
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
        setModelCalls(getModelCallHistory().slice(0, 8))
        setLoading(false)
      }).catch(() => setLoading(false))
    }

    refresh()
    const iv = setInterval(refresh, 5000)
    return () => clearInterval(iv)
  }, [])

  const completed = sessions.filter(s => s.status === 'completed')
  const avgScore = completed.length ? +(completed.reduce((a, b) => a + (b.finalScore ?? 0), 0) / completed.length).toFixed(1) : 0
  const totalCost = sessions.reduce((a, b) => a + (b.totalCost ?? 0), 0)
  const bestSession = completed.sort((a, b) => (b.finalScore ?? 0) - (a.finalScore ?? 0))[0]
  const recentScores = completed.slice(0, 8).reverse().flatMap(s => s.finalScore ? [s.finalScore] : [])

  const metrics = [
    { icon: ActivitySquare, label: 'Sessions', value: sessions.length, decimals: 0, suffix: '' },
    { icon: Clock, label: 'Model Calls', value: modelCalls.length, decimals: 0, suffix: '' },
    { icon: TrendingUp, label: 'Avg Score', value: avgScore, decimals: 1, suffix: '/10' },
    { icon: DollarSign, label: 'Total Cost', value: totalCost, decimals: 3, suffix: '', prefix: '$' },
    { icon: Zap, label: 'Best Score', value: bestSession?.finalScore ?? 0, decimals: 1, suffix: '/10' },
  ]

  if (loading) {
    return <div className="page-container"><SkeletonLoader rows={6} /></div>
  }

  return (
    <div className="page-container">
      <motion.div variants={stagger} initial="hidden" animate="show">
        {/* Header */}
        <motion.div variants={fadeUp} className="flex items-center justify-between mb-8">
          <div>
            <h1 className="page-title">Dashboard</h1>
            <p className="text-text-secondary text-sm mt-1">Overview of your optimization sessions</p>
          </div>
          <Link to="/optimize" className="btn-primary">
            <Zap size={14} /> New Optimization
          </Link>
        </motion.div>

        {/* Metrics */}
        <motion.div variants={fadeUp} className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          {metrics.map(m => (
            <Card key={m.label} className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-button bg-surface-2 flex items-center justify-center flex-shrink-0">
                <m.icon size={18} className="text-text-muted" />
              </div>
              <div>
                <p className="text-xs text-text-muted font-mono uppercase tracking-wide">{m.label}</p>
                <p className="text-2xl font-body font-semibold text-text-primary mt-0.5">
                  <AnimatedNumber value={m.value} decimals={m.decimals} prefix={m.prefix} suffix={m.suffix} />
                </p>
              </div>
            </Card>
          ))}
        </motion.div>

        <motion.div variants={fadeUp} className="mb-8">
          <Card>
            <h2 className="section-title mb-3">Recent Model Outputs</h2>
            <div className="space-y-2">
              {modelCalls.length === 0 && (
                <div className="text-sm text-text-muted">No model outputs yet. Ask or Compare to capture outputs.</div>
              )}
              {modelCalls.slice(0, 5).map((c) => (
                <div key={c.id} className="rounded-button border border-border p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-text-secondary">{c.model?.split('/').pop() || c.model}</span>
                    <span className="text-[11px] text-text-muted">{new Date(c.timestamp).toLocaleString()}</span>
                  </div>
                  <p className="text-sm text-text-primary line-clamp-2 break-words">{c.output || 'No output'}</p>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Chart */}
          <motion.div variants={fadeUp} className="lg:col-span-2">
            <Card>
              <h2 className="section-title mb-4">Performance Trend</h2>
              {recentScores.length > 1 ? (
                <PerformanceLineChart data={recentScores} height={260} />
              ) : (
                <div className="h-64 flex items-center justify-center text-text-muted text-sm">
                  Run optimization sessions to see trends
                </div>
              )}
            </Card>
          </motion.div>

          {/* Quick Actions */}
          <motion.div variants={fadeUp}>
            <Card className="h-full">
              <h2 className="section-title mb-4">Quick Actions</h2>
              <div className="space-y-2">
                {[
                  { to: '/optimize', label: 'Run Optimization', icon: Zap },
                  { to: '/ask', label: 'Ask a Question', icon: Zap },
                  { to: '/compare', label: 'Compare Models', icon: Zap },
                  { to: '/prompt-analyzer', label: 'Analyze Prompt', icon: Zap },
                ].map(a => (
                  <Link key={a.to} to={a.to} className="flex items-center justify-between p-3 rounded-button hover:bg-surface-2 transition-colors group">
                    <span className="text-sm text-text-primary">{a.label}</span>
                    <ArrowRight size={14} className="text-text-muted group-hover:text-text-primary transition-colors" />
                  </Link>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Sessions Table */}
        <motion.div variants={fadeUp}>
          <Card noPad>
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
              <h2 className="section-title">Recent Sessions</h2>
              <Link to="/analytics" className="text-xs text-text-muted hover:text-text-primary font-mono">View all →</Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-5 py-3 table-header">Session</th>
                    <th className="text-left px-5 py-3 table-header">Status</th>
                    <th className="text-left px-5 py-3 table-header">Score</th>
                    <th className="text-left px-5 py-3 table-header">Improvement</th>
                    <th className="text-left px-5 py-3 table-header">Iterations</th>
                    <th className="text-left px-5 py-3 table-header">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.length === 0 && (
                    <tr>
                      <td className="px-5 py-8 text-sm text-text-muted" colSpan={6}>
                        No sessions yet. Start with Ask or Optimize and this dashboard will auto-fill in real time.
                      </td>
                    </tr>
                  )}
                  {sessions.slice(0, 6).map(s => {
                    const st = STATUS_LABELS[s.status] ?? STATUS_LABELS.idle
                    return (
                      <tr
                        key={s.sessionId}
                        className="table-row cursor-pointer"
                        onClick={() => navigate(`/sessions/${s.sessionId}`)}
                      >
                        <td className="px-5 py-3 text-sm font-mono text-text-primary">{s.sessionId.slice(0, 12)}</td>
                        <td className="px-5 py-3">
                          <Badge variant={st.variant as 'success'}>{st.label}</Badge>
                        </td>
                        <td className="px-5 py-3">
                          <span className="data-mono font-semibold" style={{ color: scoreToColor(s.finalScore ?? 0) }}>
                            {s.finalScore?.toFixed(1) ?? '—'}
                          </span>
                        </td>
                        <td className="px-5 py-3 data-mono text-text-secondary">
                          {s.improvement != null ? `${s.improvement > 0 ? '+' : ''}${s.improvement.toFixed(1)}` : '—'}
                        </td>
                        <td className="px-5 py-3 data-mono text-text-secondary">{s.totalIterations}</td>
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
