export default function SkeletonLoader({ rows = 3, className = '' }: { rows?: number; className?: string }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="shimmer h-4 rounded" style={{ width: `${70 + Math.random() * 30}%`, animationDelay: `${i * 0.1}s` }} />
      ))}
    </div>
  )
}
