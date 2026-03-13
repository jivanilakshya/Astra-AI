import { forwardRef } from 'react'
import { motion, type HTMLMotionProps } from 'framer-motion'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean
  active?: boolean
  noPad?: boolean
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className = '', hover, active, noPad, children, ...props }, ref) => (
    <div
      ref={ref}
      className={`card ${hover ? 'card-hover' : ''} ${active ? 'card-active' : ''} ${noPad ? '' : 'p-5'} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
)
Card.displayName = 'Card'

export default Card

type MotionCardProps = HTMLMotionProps<'div'> & CardProps
export const AnimatedCard = forwardRef<HTMLDivElement, MotionCardProps>(
  ({ className = '', hover, active, noPad, children, ...props }, ref) => (
    <motion.div
      ref={ref}
      className={`card ${hover ? 'card-hover' : ''} ${active ? 'card-active' : ''} ${noPad ? '' : 'p-5'} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  )
)
AnimatedCard.displayName = 'AnimatedCard'
