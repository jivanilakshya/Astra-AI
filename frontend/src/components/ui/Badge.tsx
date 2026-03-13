interface BadgeProps {
  variant?: 'accent' | 'success' | 'warn' | 'danger' | 'muted' | 'info'
  children: React.ReactNode
  className?: string
}

const variantMap: Record<string, string> = {
  accent: 'badge-accent',
  success: 'badge-success',
  warn: 'badge-warn',
  danger: 'badge-danger',
  muted: 'badge-muted',
  info: 'badge bg-info-muted text-info',
}

export default function Badge({ variant = 'muted', children, className = '' }: BadgeProps) {
  return <span className={`${variantMap[variant] ?? 'badge-muted'} ${className}`}>{children}</span>
}
