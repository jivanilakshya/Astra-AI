import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Clock, Cpu, TrendingUp, FileText } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import ScoreBar from '../components/ui/ScoreBar'
import PerformanceLineChart from '../components/charts/PerformanceLineChart'
import ScoreRadar from '../components/charts/ScoreRadar'
import CriteriaBarChart from '../components/charts/CriteriaBarChart'
import SkeletonLoader from '../components/ui/SkeletonLoader'
import { getSession } from '../services/api'
import { formatDate, scoreToColor, formatCost, formatDuration } from '../utils/formatters'
import { STATUS_LABELS, CRITERIA_LABELS } from '../utils/constants'
import type { SessionDetail } from '../types'

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) getSession(id).then(s => { setSession(s); setLoading(false) })
  }, [id])

  if (loading) return <div className="page-container"><SkeletonLoader rows={8} /></div>
  if (!session) return <div className="page-container"><p className="text-text-muted">Session not found</p></div>

  const logs = session.iterationLogs ?? []
  const scores = logs.map(l => l.avgCompositeScore)
  const lastLog = logs[logs.length - 1]
  const st = STATUS_LABELS[session.status] ?? STATUS_LABELS.idle
  const improvement = (session.finalScore ?? 0) - (session.initialScore ?? 0)

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        {/* Header */}
        <motion.div variants={fadeUp} className="flex items-center gap-4 mb-8">
          <button onClick={() => navigate(-1)} className="btn-ghost p-2">
            <ArrowLeft size={16} />
          </button>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="page-title">Session</h1>
              <span className="font-mono text-text-muted text-sm">{session.sessionId.slice(0, 14)}</span>
              <Badge variant={st.variant as 'success'}>{st.label}</Badge>
            </div>
            <p className="text-text-secondary text-sm mt-1">
              Started {formatDate(session.startedAt)}
              {session.model && <> · <span className="font-mono">{session.model.split('/').pop()}</span></>}
            </p>
          </div>
        </motion.div>

        {/* Summary Cards */}
        <motion.div variants={fadeUp} className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          {[
            { label: 'Initial', value: session.initialScore ?? 0, color: scoreToColor(session.initialScore ?? 0), decimals: 1 },
            { label: 'Final', value: session.finalScore ?? 0, color: scoreToColor(session.finalScore ?? 0), decimals: 1 },
            { label: 'Improvement', value: improvement, color: improvement > 0 ? 'var(--color-success)' : 'var(--color-danger)', decimals: 1, prefix: improvement > 0 ? '+' : '' },
            { label: 'Iterations', value: session.totalIterations, color: 'var(--color-text-primary)', decimals: 0 },
            { label: 'Cost', value: session.totalCost ?? 0, color: 'var(--color-text-primary)', decimals: 4, prefix: '$' },
          ].map(m => (
            <Card key={m.label} className="text-center">
              <p className="text-xs font-mono text-text-muted uppercase mb-1">{m.label}</p>
              <p className="text-2xl font-body font-bold" style={{ color: m.color }}>
                {m.prefix}<AnimatedNumber value={m.value} decimals={m.decimals} />
              </p>
            </Card>
          ))}
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Performance Chart */}
          <motion.div variants={fadeUp}>
            <Card>
              <h2 className="section-title mb-4">Score Progress</h2>
              {scores.length > 1 ? (
                <PerformanceLineChart data={scores} target={8.5} height={280} />
              ) : (
                <p className="text-text-muted text-sm py-12 text-center">Insufficient data</p>
              )}
            </Card>
          </motion.div>

          {/* Final Scores Radar */}
          <motion.div variants={fadeUp}>
            <Card>
              <h2 className="section-title mb-4">Final Criteria</h2>
              {lastLog?.avgScores ? (
                <ScoreRadar scores={lastLog.avgScores} height={280} />
              ) : (
                <p className="text-text-muted text-sm py-12 text-center">No data</p>
              )}
            </Card>
          </motion.div>
        </div>

        {/* Criteria Breakdown */}
        {lastLog?.avgScores && (
          <motion.div variants={fadeUp} className="mb-8">
            <Card>
              <h2 className="section-title mb-4">Criteria Breakdown</h2>
              <CriteriaBarChart scores={lastLog.avgScores} height={250} />
            </Card>
          </motion.div>
        )}

        {/* Iteration Log */}
        <motion.div variants={fadeUp}>
          <Card noPad>
            <div className="px-5 py-4 border-b border-border">
              <h2 className="section-title">Iteration Log</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-5 py-3 table-header">#</th>
                    <th className="text-left px-5 py-3 table-header">Composite</th>
                    <th className="text-left px-5 py-3 table-header">Correct.</th>
                    <th className="text-left px-5 py-3 table-header">Clarity</th>
                    <th className="text-left px-5 py-3 table-header">Reason.</th>
                    <th className="text-left px-5 py-3 table-header">Relev.</th>
                    <th className="text-left px-5 py-3 table-header">Concise.</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => (
                    <tr key={log.iteration} className="table-row">
                      <td className="px-5 py-3 font-mono text-sm text-text-primary">{log.iteration}</td>
                      <td className="px-5 py-3 font-mono font-semibold" style={{ color: scoreToColor(log.avgCompositeScore) }}>
                        {log.avgCompositeScore.toFixed(1)}
                      </td>
                      {log.avgScores && Object.values(log.avgScores).map((v, i) => (
                        <td key={i} className="px-5 py-3 font-mono text-sm" style={{ color: scoreToColor(v) }}>
                          {v.toFixed(1)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>

        {/* Config & Prompt */}
        {session.config && (
          <motion.div variants={fadeUp} className="mt-8 grid lg:grid-cols-2 gap-6">
            <Card>
              <h2 className="section-title mb-3">Configuration</h2>
              <div className="space-y-2 text-sm">
                {Object.entries(session.config).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-text-muted font-mono">{k}</span>
                    <span className="text-text-primary font-mono">{String(v)}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card>
              <h2 className="section-title mb-3">Final Prompt</h2>
              <pre className="font-mono text-xs text-text-secondary bg-surface-2 rounded-button p-3 whitespace-pre-wrap overflow-auto max-h-48">
                {session.finalPrompt ?? session.config?.initialPrompt ?? 'N/A'}
              </pre>
            </Card>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
