import { useEffect, useRef } from 'react'
import { useMotionValue, useSpring, useTransform, motion } from 'framer-motion'

interface AnimatedNumberProps {
  value: number
  decimals?: number
  className?: string
  prefix?: string
  suffix?: string
}

export default function AnimatedNumber({ value, decimals = 1, className = '', prefix = '', suffix = '' }: AnimatedNumberProps) {
  const motionVal = useMotionValue(0)
  const spring = useSpring(motionVal, { stiffness: 80, damping: 25 })
  const display = useTransform(spring, v => `${prefix}${v.toFixed(decimals)}${suffix}`)
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => { motionVal.set(value) }, [value, motionVal])
  useEffect(() => {
    const unsub = display.on('change', v => { if (ref.current) ref.current.textContent = v })
    return unsub
  }, [display])

  return <motion.span ref={ref} className={`tabular-nums ${className}`}>{prefix}{(0).toFixed(decimals)}{suffix}</motion.span>
}
