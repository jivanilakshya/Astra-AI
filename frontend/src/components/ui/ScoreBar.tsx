import { motion } from 'framer-motion'
import { scoreToColor } from '../../utils/formatters'

interface ScoreBarProps {
  value: number
  max?: number
  label?: string
  showValue?: boolean
  height?: number
  delay?: number
  className?: string
}

export default function ScoreBar({ value, max = 10, label, showValue = true, height = 6, delay = 0, className = '' }: ScoreBarProps) {
  const pct = Math.min((value / max) * 100, 100)
  const color = scoreToColor(value)

  return (
    <div className={`w-full ${className}`}>
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && <span className="text-xs font-body text-text-secondary">{label}</span>}
          {showValue && <span className="text-xs font-mono text-text-primary font-medium">{value.toFixed(1)}</span>}
        </div>
      )}
      <div className="score-bar-track" style={{ height }}>
        <motion.div
          className="score-bar-fill"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, delay, ease: [0.16, 1, 0.3, 1] }}
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  )
}
