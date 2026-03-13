import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface PerformanceLineChartProps {
  data: number[]
  target?: number
  height?: number
  className?: string
}

export default function PerformanceLineChart({ data, target = 8.5, height = 280, className = '' }: PerformanceLineChartProps) {
  const chartData = data.map((score, i) => ({ iteration: i + 1, score: +score.toFixed(2) }))

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis
            dataKey="iteration"
            tick={{ fontSize: 11, fill: 'var(--color-text-muted)', fontFamily: 'JetBrains Mono' }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
            label={{ value: 'Iteration', position: 'insideBottom', offset: -2, fontSize: 11, fill: 'var(--color-text-muted)' }}
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
              fontFamily: 'JetBrains Mono',
              color: 'var(--color-text-primary)',
            }}
            labelStyle={{ color: 'var(--color-text-secondary)' }}
            formatter={(value: number) => [value.toFixed(2), 'Score']}
          />
          {target > 0 && (
            <ReferenceLine
              y={target}
              stroke="var(--color-text-muted)"
              strokeDasharray="6 4"
              label={{ value: `Target ${target}`, position: 'right', fontSize: 10, fill: 'var(--color-text-muted)' }}
            />
          )}
          <Line
            type="monotone"
            dataKey="score"
            stroke="var(--color-accent)"
            strokeWidth={2}
            dot={{ r: 4, fill: 'var(--color-surface-1)', stroke: 'var(--color-accent)', strokeWidth: 2 }}
            activeDot={{ r: 6, fill: 'var(--color-accent)' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
