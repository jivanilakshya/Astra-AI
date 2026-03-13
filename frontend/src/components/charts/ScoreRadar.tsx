import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts'
import type { Scores } from '../../types'
import { CRITERIA_LABELS } from '../../utils/constants'

interface ScoreRadarProps {
  scores: Scores | Record<string, number>
  height?: number
  className?: string
}

export default function ScoreRadar({ scores, height = 280, className = '' }: ScoreRadarProps) {
  const data = Object.entries(scores).map(([key, value]) => ({
    criterion: CRITERIA_LABELS[key] ?? key,
    value: +value.toFixed(1),
    fullMark: 10,
  }))

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid stroke="var(--color-border)" />
          <PolarAngleAxis
            dataKey="criterion"
            tick={{ fontSize: 11, fill: 'var(--color-text-secondary)', fontFamily: 'DM Sans' }}
          />
          <PolarRadiusAxis
            domain={[0, 10]}
            tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }}
            axisLine={false}
          />
          <Radar
            dataKey="value"
            stroke="var(--color-accent)"
            fill="var(--color-accent)"
            fillOpacity={0.1}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
