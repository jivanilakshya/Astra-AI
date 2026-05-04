import { useEffect, useMemo, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { DollarSign, TrendingUp, TrendingDown, Calendar, PieChart } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart as RePie, Pie, Cell, Legend,
} from 'recharts'
import Card from '../components/ui/Card'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import Badge from '../components/ui/Badge'
import SkeletonLoader from '../components/ui/SkeletonLoader'
import { getCostHistory } from '../services/api'
import { formatCost } from '../utils/formatters'

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }

interface CostRecord {
  date: string
  totalCost: number
  generatorCost: number
  judgeCost: number
  optimizerCost: number
  tokensUsed: number
  requests: number
}

const PIE_COLORS = ['var(--color-accent)', 'var(--color-text-muted)', 'var(--color-border-strong)']
const LS_KEY = 'astra_cost_history_v1'

function readCostCache(): CostRecord[] {
  if (typeof window === 'undefined') return []
  try {
    const cached = localStorage.getItem(LS_KEY)
    if (!cached) return []
    const parsed = JSON.parse(cached)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeCostCache(rows: CostRecord[]) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(rows))
  } catch {
    // ignore quota and serialization errors
  }
}

function buildScaffold(days = 7): CostRecord[] {
  return Array.from({ length: days }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - (days - 1 - i))
    return {
      date: d.toISOString().slice(0, 10),
      totalCost: 0,
      generatorCost: 0,
      judgeCost: 0,
      optimizerCost: 0,
      tokensUsed: 0,
      requests: 0,
    }
  })
}

export default function CostTrackingPage() {
  const cachedRef = useRef<CostRecord[]>(readCostCache())
  const [data, setData] = useState<CostRecord[]>(cachedRef.current)
  const [loading, setLoading] = useState(cachedRef.current.length === 0)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const scaffoldData = useMemo(() => buildScaffold(7), [])

  useEffect(() => {
    const refresh = () => {
      getCostHistory().then((d: any) => {
        const normalized = Array.isArray(d) ? d : []
        if (normalized.length > 0) {
          setData(normalized)
          writeCostCache(normalized)
        } else {
          setData(prev => (prev.length > 0 ? prev : scaffoldData))
        }
        setError(null)
        setLastUpdated(new Date().toISOString())
        setLoading(false)
      }).catch(() => {
        setError('Unable to load cost history right now.')
        setData(prev => (prev.length > 0 ? prev : scaffoldData))
        setLoading(false)
      })
    }

    refresh()
    const iv = setInterval(refresh, 5000)
    return () => clearInterval(iv)
  }, [scaffoldData])

  if (loading) return <div className="page-container"><SkeletonLoader rows={6} /></div>

  const baseData = data.length > 0 ? data : scaffoldData

  const totalCost = baseData.reduce((a, b) => a + b.totalCost, 0)
  const totalTokens = baseData.reduce((a, b) => a + b.tokensUsed, 0)
  const totalRequests = baseData.reduce((a, b) => a + b.requests, 0)
  const avgDaily = baseData.length ? totalCost / baseData.length : 0
  const hasRealData = baseData.some(row => row.totalCost > 0 || row.tokensUsed > 0 || row.requests > 0)
  const maxCost = baseData.reduce((max, row) => Math.max(max, row.totalCost || 0), 0)
  const yMax = maxCost > 0 ? Math.max(maxCost * 1.2, 0.01) : 0.01

  const genTotal = baseData.reduce((a, b) => a + b.generatorCost, 0)
  const judgeTotal = baseData.reduce((a, b) => a + b.judgeCost, 0)
  const optTotal = baseData.reduce((a, b) => a + b.optimizerCost, 0)

  const pieData = [
    { name: 'Generator', value: +genTotal.toFixed(4) },
    { name: 'Judge', value: +judgeTotal.toFixed(4) },
    { name: 'Optimizer', value: +optTotal.toFixed(4) },
  ]

  const last7 = baseData.slice(-7)
  const prev7 = baseData.slice(-14, -7)
  const recentCost = last7.reduce((a, b) => a + b.totalCost, 0)
  const prevCost = prev7.reduce((a, b) => a + b.totalCost, 0)
  const costChange = prevCost > 0 ? ((recentCost - prevCost) / prevCost) * 100 : 0

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        <motion.div variants={fadeUp} className="mb-8">
          <h1 className="page-title">Cost Tracking</h1>
          <p className="text-text-secondary text-sm mt-1">Monitor API usage and costs over time</p>
          {!hasRealData && (
            <p className="text-xs text-text-muted mt-2 font-mono">Showing starter chart scaffold. Real values appear as soon as model calls run.</p>
          )}
          {error && <p className="text-xs text-amber-400 mt-2">{error}</p>}
          {lastUpdated && (
            <p className="text-[10px] text-text-muted mt-1 font-mono">Last updated: {new Date(lastUpdated).toLocaleTimeString()}</p>
          )}
        </motion.div>

        {/* Summary */}
        <motion.div variants={fadeUp} className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Cost', value: totalCost, prefix: '$', decimals: 3 },
            { label: 'Avg Daily', value: avgDaily, prefix: '$', decimals: 4 },
            { label: 'Total Tokens', value: totalTokens, decimals: 0, suffix: '' },
            { label: 'Total Requests', value: totalRequests, decimals: 0, suffix: '' },
          ].map(m => (
            <Card key={m.label} className="text-center">
              <p className="text-xs font-mono text-text-muted uppercase mb-1">{m.label}</p>
              <p className="text-2xl font-body font-bold text-text-primary">
                <AnimatedNumber value={m.value} decimals={m.decimals} prefix={m.prefix} suffix={m.suffix} />
              </p>
            </Card>
          ))}
        </motion.div>

        {!hasRealData && (
          <motion.div variants={fadeUp} className="mb-8">
            <Card>
              <div className="flex items-center gap-3 text-sm text-text-secondary">
                <Calendar size={14} className="text-text-muted" />
                No usage recorded yet. Run Ask, Compare, or Optimize to populate real costs and token usage.
              </div>
            </Card>
          </motion.div>
        )}

        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Cost Timeline */}
          <motion.div variants={fadeUp} className="lg:col-span-2">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h2 className="section-title">Cost Over Time</h2>
                <div className="flex items-center gap-2 text-xs">
                  {costChange !== 0 && (
                    <Badge variant={costChange > 0 ? 'danger' : 'success'}>
                      {costChange > 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                      {Math.abs(costChange).toFixed(0)}% vs prev week
                    </Badge>
                  )}
                </div>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={baseData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: 'var(--color-text-muted)', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                    tickFormatter={v => new Date(v).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                    label={{ value: 'Date', position: 'insideBottom', offset: -2, fontSize: 11, fill: 'var(--color-text-muted)' }}
                  />
                  <YAxis
                    tick={{ fill: 'var(--color-text-muted)', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                    tickFormatter={v => `$${v}`}
                    domain={[0, yMax]}
                    label={{ value: 'Cost (USD)', angle: -90, position: 'insideLeft', fontSize: 11, fill: 'var(--color-text-muted)' }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: '8px',
                      color: 'var(--color-text-primary)',
                      fontFamily: 'JetBrains Mono',
                      fontSize: '12px',
                    }}
                    formatter={(v: number) => [`$${v.toFixed(4)}`, 'Cost']}
                  />
                  <Legend
                    verticalAlign="top"
                    height={20}
                    formatter={(value) => (
                      <span style={{ color: 'var(--color-text-secondary)', fontSize: '11px', fontFamily: 'JetBrains Mono' }}>{value}</span>
                    )}
                  />
                  <Area
                    type="monotone"
                    dataKey="totalCost"
                    name="Total Cost"
                    stroke="var(--color-accent)"
                    fill="var(--color-accent)"
                    fillOpacity={0.1}
                    strokeWidth={2}
                    dot={{ r: 3, fill: 'var(--color-surface-1)', stroke: 'var(--color-accent)', strokeWidth: 1 }}
                    activeDot={{ r: 5, fill: 'var(--color-accent)' }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>

          {/* Agent Breakdown Pie */}
          <motion.div variants={fadeUp}>
            <Card className="h-full">
              <h2 className="section-title mb-4">By Agent</h2>
              <ResponsiveContainer width="100%" height={220}>
                <RePie>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i]} />
                    ))}
                  </Pie>
                  <Legend
                    verticalAlign="bottom"
                    formatter={(value) => <span style={{ color: 'var(--color-text-secondary)', fontSize: '11px', fontFamily: 'JetBrains Mono' }}>{value}</span>}
                  />
                </RePie>
              </ResponsiveContainer>
              <div className="space-y-2 mt-4">
                {pieData.map((d, i) => (
                  <div key={d.name} className="flex justify-between text-sm">
                    <span className="text-text-secondary flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{ background: PIE_COLORS[i] }} />
                      {d.name}
                    </span>
                    <span className="font-mono text-text-primary">{formatCost(d.value)}</span>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Daily Breakdown Table */}
        <motion.div variants={fadeUp}>
          <Card noPad>
            <div className="px-5 py-4 border-b border-border">
              <h2 className="section-title">Daily Breakdown</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-5 py-3 table-header">Date</th>
                    <th className="text-left px-5 py-3 table-header">Total</th>
                    <th className="text-left px-5 py-3 table-header">Generator</th>
                    <th className="text-left px-5 py-3 table-header">Judge</th>
                    <th className="text-left px-5 py-3 table-header">Optimizer</th>
                    <th className="text-left px-5 py-3 table-header">Tokens</th>
                    <th className="text-left px-5 py-3 table-header">Requests</th>
                  </tr>
                </thead>
                <tbody>
                  {baseData.slice().reverse().slice(0, 14).map(d => (
                    <tr key={d.date} className="table-row">
                      <td className="px-5 py-3 text-sm text-text-primary">{new Date(d.date).toLocaleDateString('en', { month: 'short', day: 'numeric' })}</td>
                      <td className="px-5 py-3 font-mono text-sm font-semibold text-text-primary">{formatCost(d.totalCost)}</td>
                      <td className="px-5 py-3 font-mono text-sm text-text-secondary">{formatCost(d.generatorCost)}</td>
                      <td className="px-5 py-3 font-mono text-sm text-text-secondary">{formatCost(d.judgeCost)}</td>
                      <td className="px-5 py-3 font-mono text-sm text-text-secondary">{formatCost(d.optimizerCost)}</td>
                      <td className="px-5 py-3 font-mono text-sm text-text-secondary">{d.tokensUsed.toLocaleString()}</td>
                      <td className="px-5 py-3 font-mono text-sm text-text-secondary">{d.requests}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  )
}
