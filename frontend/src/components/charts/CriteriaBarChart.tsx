import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { scoreToColor } from '../../utils/formatters'
import { CRITERIA_LABELS } from '../../utils/constants'
import type { Scores } from '../../types'

interface CriteriaBarChartProps {
  scores: Scores | Record<string, number>
  height?: number
  className?: string
}

export default function CriteriaBarChart({ scores, height = 280, className = '' }: CriteriaBarChartProps) {
  const data = Object.entries(scores).map(([key, value]) => ({
    name: CRITERIA_LABELS[key] ?? key,
    value: +value.toFixed(1),
    color: scoreToColor(value),
  }))

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: 'var(--color-text-secondary)', fontFamily: 'DM Sans' }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 10]}
            tick={{ fontSize: 11, fill: 'var(--color-text-muted)', fontFamily: 'JetBrains Mono' }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: '10px',
              fontSize: 12,
              color: 'var(--color-text-primary)',
            }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={40}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
