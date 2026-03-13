import { useEffect, useState } from 'react'
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

export default function CostTrackingPage() {
  const [data, setData] = useState<CostRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCostHistory().then((d: any) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <div className="page-container"><SkeletonLoader rows={6} /></div>

  const totalCost = data.reduce((a, b) => a + b.totalCost, 0)
  const totalTokens = data.reduce((a, b) => a + b.tokensUsed, 0)
  const totalRequests = data.reduce((a, b) => a + b.requests, 0)
  const avgDaily = data.length ? totalCost / data.length : 0

  const genTotal = data.reduce((a, b) => a + b.generatorCost, 0)
  const judgeTotal = data.reduce((a, b) => a + b.judgeCost, 0)
  const optTotal = data.reduce((a, b) => a + b.optimizerCost, 0)

  const pieData = [
    { name: 'Generator', value: +genTotal.toFixed(4) },
    { name: 'Judge', value: +judgeTotal.toFixed(4) },
    { name: 'Optimizer', value: +optTotal.toFixed(4) },
  ]

  const last7 = data.slice(-7)
  const prev7 = data.slice(-14, -7)
  const recentCost = last7.reduce((a, b) => a + b.totalCost, 0)
  const prevCost = prev7.reduce((a, b) => a + b.totalCost, 0)
  const costChange = prevCost > 0 ? ((recentCost - prevCost) / prevCost) * 100 : 0

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        <motion.div variants={fadeUp} className="mb-8">
          <h1 className="page-title">Cost Tracking</h1>
          <p className="text-text-secondary text-sm mt-1">Monitor API usage and costs over time</p>
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
                <AreaChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: 'var(--color-text-muted)', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                    tickFormatter={v => new Date(v).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis
                    tick={{ fill: 'var(--color-text-muted)', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                    tickFormatter={v => `$${v}`}
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
                    formatter={(v: number) => [`$${v.toFixed(4)}`, '']}
                  />
                  <Area
                    type="monotone"
                    dataKey="totalCost"
                    stroke="var(--color-accent)"
                    fill="var(--color-accent)"
                    fillOpacity={0.1}
                    strokeWidth={2}
                    name="Cost"
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
                  {data.slice().reverse().slice(0, 14).map(d => (
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
