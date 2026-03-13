import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Cpu, CheckCircle, XCircle, ExternalLink, Zap } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import SkeletonLoader from '../components/ui/SkeletonLoader'
import { getModels, getRouterStats } from '../services/api'
import type { ModelProfile, RouterStats } from '../types'

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }

export default function ModelsPage() {
  const [models, setModels] = useState<ModelProfile[]>([])
  const [router, setRouter] = useState<RouterStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getModels(), getRouterStats()]).then(([m, r]) => {
      setModels(m)
      setRouter(r)
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="page-container"><SkeletonLoader rows={6} /></div>

  const activeCount = models.filter(m => m.status === 'available').length

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        <motion.div variants={fadeUp} className="flex items-center justify-between mb-8">
          <div>
            <h1 className="page-title">Models</h1>
            <p className="text-text-secondary text-sm mt-1">{activeCount} of {models.length} models available</p>
          </div>
        </motion.div>

        {/* Router Stats */}
        {router && (
          <motion.div variants={fadeUp} className="mb-8">
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <Zap size={16} className="text-accent" />
                <h2 className="section-title">Smart Router</h2>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-xs font-mono text-text-muted uppercase">Total Routings</p>
                  <p className="text-xl font-body font-bold text-text-primary mt-1">
                    <AnimatedNumber value={router.totalRoutings} decimals={0} />
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-mono text-text-muted uppercase">Avg Score</p>
                  <p className="text-xl font-body font-bold text-text-primary mt-1">
                    <AnimatedNumber value={router.avgScore} decimals={1} suffix="/10" />
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-mono text-text-muted uppercase">Avg Latency</p>
                  <p className="text-xl font-body font-bold text-text-primary mt-1">
                    <AnimatedNumber value={router.avgLatency} decimals={0} suffix="ms" />
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-mono text-text-muted uppercase">Top Model</p>
                  <p className="text-sm font-mono text-text-primary mt-2">
                    {router.modelUsage[0]?.model.split('/').pop()?.split('-')[0] ?? '—'}
                  </p>
                </div>
              </div>

              {/* Usage breakdown */}
              <div className="space-y-2">
                {router.modelUsage.map(u => {
                  const pct = router.totalRoutings > 0 ? (u.count / router.totalRoutings) * 100 : 0
                  return (
                    <div key={u.model} className="flex items-center gap-3">
                      <span className="text-xs font-mono text-text-muted w-24 truncate">{u.model.split('/').pop()?.split('-')[0]}</span>
                      <div className="flex-1 h-2 bg-surface-2 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-accent rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                        />
                      </div>
                      <span className="text-xs font-mono text-text-muted w-16 text-right">{u.count} ({pct.toFixed(0)}%)</span>
                    </div>
                  )
                })}
              </div>
            </Card>
          </motion.div>
        )}

        {/* Models Grid */}
        <motion.div variants={fadeUp}>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {models.map(m => (
              <motion.div
                key={m.id}
                whileHover={{ y: -2 }}
                transition={{ duration: 0.2 }}
              >
                <Card hover className="h-full">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Cpu size={16} className="text-text-muted" />
                      <h3 className="font-mono text-sm font-semibold text-text-primary">{m.name}</h3>
                    </div>
                    {m.status === 'available' ? (
                      <Badge variant="success"><CheckCircle size={10} /> Active</Badge>
                    ) : (
                      <Badge variant="danger"><XCircle size={10} /> Offline</Badge>
                    )}
                  </div>

                  <p className="text-xs text-text-secondary mb-4 leading-relaxed">{m.description}</p>

                  <div className="space-y-2 text-xs border-t border-border pt-3">
                    <Row label="Provider" value={m.provider} />
                    <Row label="Parameters" value={m.parameters} />
                    <Row label="Context" value={`${m.contextWindow.toLocaleString()} tokens`} />
                    <Row label="Cost / 1M tokens" value={`$${m.costPer1MTokens.toFixed(2)}`} />
                    {m.avgLatency && <Row label="Avg Latency" value={`${m.avgLatency}ms`} />}
                    {m.avgScore && <Row label="Avg Score" value={m.avgScore.toFixed(1)} />}
                  </div>

                  {m.strengths && m.strengths.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border">
                      <p className="text-[10px] font-mono text-text-muted uppercase mb-1">Strengths</p>
                      <div className="flex flex-wrap gap-1">
                        {m.strengths.map(s => (
                          <Badge key={s} variant="muted">{s}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between">
      <span className="text-text-muted">{label}</span>
      <span className="font-mono text-text-primary">{value}</span>
    </div>
  )
}
