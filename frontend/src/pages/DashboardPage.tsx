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
import { formatDate, scoreToColor } from '../utils/formatters'
import { STATUS_LABELS } from '../utils/constants'
import type { SessionSummary } from '../types'

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } } }

export default function DashboardPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [modelCalls, setModelCalls] = useState<any[]>([])
  const [modelCallsTotal, setModelCallsTotal] = useState(0)
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
        const calls = getModelCallHistory()
        setModelCalls(calls.slice(0, 8))
        setModelCallsTotal(calls.length)
        setLoading(false)
      }).catch(() => setLoading(false))
    }

    refresh()
    const iv = setInterval(refresh, 5000)
    return () => clearInterval(iv)
  }, [])

  const sortedSessions = [...sessions].sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
  const completed = sessions.filter(s => s.status === 'completed')
  const avgScore = completed.length ? +(completed.reduce((a, b) => a + (b.finalScore ?? 0), 0) / completed.length).toFixed(1) : 0
  const avgImprovement = completed.length ? +(completed.reduce((a, b) => a + (b.improvement ?? 0), 0) / completed.length).toFixed(1) : 0
  const avgDuration = sessions.length ? +(sessions.reduce((a, b) => a + (b.durationSeconds || 0), 0) / sessions.length).toFixed(1) : 0
  const completionRate = sessions.length ? (completed.length / sessions.length) * 100 : 0
  const totalCost = sessions.reduce((a, b) => a + (b.totalCost ?? 0), 0)
  const bestSession = [...completed].sort((a, b) => (b.finalScore ?? 0) - (a.finalScore ?? 0))[0]
  const recentScores = [...completed].slice(0, 8).reverse().flatMap(s => s.finalScore ? [s.finalScore] : [])
  const recentSessions = sortedSessions.slice(0, 6)
  const lastSession = sortedSessions[0]
  const runningCount = sessions.filter(s => s.status === 'running').length
  const lastScore = recentScores[recentScores.length - 1] ?? 0
  const prevScore = recentScores[recentScores.length - 2] ?? lastScore
  const scoreDelta = +(lastScore - prevScore).toFixed(2)

  const metrics = [
    { icon: ActivitySquare, label: 'Total Sessions', value: sessions.length, decimals: 0, suffix: '' },
    { icon: TrendingUp, label: 'Avg Score', value: avgScore, decimals: 1, suffix: '/10' },
    { icon: Zap, label: 'Completion Rate', value: completionRate, decimals: 0, suffix: '%' },
    { icon: Clock, label: 'Avg Duration', value: avgDuration, decimals: 1, suffix: 's' },
    { icon: DollarSign, label: 'Total Cost', value: totalCost, decimals: 3, suffix: '', prefix: '$' },
    { icon: ActivitySquare, label: 'Model Calls', value: modelCallsTotal, decimals: 0, suffix: '' },
  ]

  const activityItems = [
    ...recentSessions.map((s) => ({
      id: s.sessionId,
      type: 'session',
      title: `Optimization ${s.status}`,
      subtitle: `${s.totalIterations} iters • ${s.finalScore != null ? s.finalScore.toFixed(1) : '—'}/10`,
      time: s.startedAt,
      badge: STATUS_LABELS[s.status] ?? STATUS_LABELS.idle,
    })),
    ...modelCalls.map((c) => ({
      id: c.id,
      type: 'call',
      title: `${c.endpoint} call`,
      subtitle: `${c.model?.split('/').pop() || c.model} • ${c.tokensUsed || 0} tokens`,
      time: c.timestamp,
      badge: { label: 'Model Call', variant: 'muted' },
    })),
  ]
    .sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())
    .slice(0, 8)

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
        <motion.div variants={fadeUp} className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-8">
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

        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Chart */}
          <motion.div variants={fadeUp} className="lg:col-span-2">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h2 className="section-title">Performance Trend</h2>
                {recentScores.length >= 2 && (
                  <Badge variant={scoreDelta >= 0 ? 'success' : 'danger'}>
                    {scoreDelta >= 0 ? '+' : ''}{scoreDelta.toFixed(1)} vs last run
                  </Badge>
                )}
              </div>
              {recentScores.length > 1 ? (
                <PerformanceLineChart data={recentScores} height={260} />
              ) : (
                <div className="h-64 flex items-center justify-center text-text-muted text-sm">
                  Run optimization sessions to see trends
                </div>
              )}
            </Card>
          </motion.div>

          {/* Insights + Actions */}
          <motion.div variants={fadeUp} className="space-y-6">
            <Card>
              <h2 className="section-title mb-4">Quick Insights</h2>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">Latest run</span>
                  <span className="text-text-primary font-mono">{lastSession ? formatDate(lastSession.startedAt) : '—'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">Best score</span>
                  <span className="font-mono" style={{ color: scoreToColor(bestSession?.finalScore ?? 0) }}>
                    {bestSession?.finalScore != null ? bestSession.finalScore.toFixed(1) : '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">Avg improvement</span>
                  <span className="text-text-primary font-mono">{avgImprovement > 0 ? '+' : ''}{avgImprovement.toFixed(1)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">Running now</span>
                  <span className="text-text-primary font-mono">{runningCount}</span>
                </div>
              </div>
            </Card>

            <Card>
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

        <motion.div variants={fadeUp} className="mb-8">
          <Card>
            <h2 className="section-title mb-3">Recent Activity</h2>
            <div className="space-y-2">
              {activityItems.length === 0 && (
                <div className="text-sm text-text-muted">No recent activity yet. Run Ask, Compare, or Optimize to populate this feed.</div>
              )}
              {activityItems.map((item) => (
                <div
                  key={item.id}
                  className={`rounded-button border border-border p-3 ${item.type === 'session' ? 'cursor-pointer hover:bg-surface-2' : ''}`}
                  onClick={() => item.type === 'session' && navigate(`/sessions/${item.id}`)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Badge variant={item.badge.variant as 'accent' | 'success' | 'warn' | 'danger' | 'muted' | 'info'}>{item.badge.label}</Badge>
                      <span className="text-xs font-mono text-text-secondary">{item.title}</span>
                    </div>
                    <span className="text-[11px] text-text-muted">{formatDate(item.time)}</span>
                  </div>
                  <p className="text-sm text-text-primary break-words">{item.subtitle}</p>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>

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
                  {recentSessions.map(s => {
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
