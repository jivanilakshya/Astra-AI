import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { GitCompare, Plus, X, Loader2, Trophy, Medal, Award } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import { compareModels, getModels } from '../services/api'
import { scoreToColor } from '../utils/formatters'
import { CRITERIA_LABELS } from '../utils/constants'
import type { ComparisonReport, ModelProfile } from '../types'

const FALLBACK_MODELS = [
  'meta-llama/Meta-Llama-3-8B-Instruct',
  'Qwen/Qwen2.5-7B-Instruct',
  'meta-llama/Llama-3.2-3B-Instruct',
  'meta-llama/Llama-3.2-1B-Instruct',
]

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }
const podiumIcons = [Trophy, Medal, Award]

export default function ComparisonPage() {
  const [prompt, setPrompt] = useState('Answer the following question clearly.\n\nQuestion: {question}\n\nAnswer:')
  const [availableModels, setAvailableModels] = useState<string[]>(FALLBACK_MODELS)
  const [selectedModels, setSelectedModels] = useState<string[]>([FALLBACK_MODELS[0], FALLBACK_MODELS[1]])
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<ComparisonReport | null>(null)

  useEffect(() => {
    getModels()
      .then((models: ModelProfile[]) => {
        const backendAvailable = models
          .filter(m => m.is_available && m.status === 'available')
          .map(m => m.id)

        if (backendAvailable.length >= 2) {
          setAvailableModels(backendAvailable)
          setSelectedModels(prev => {
            const valid = prev.filter(m => backendAvailable.includes(m))
            const seeded = [
              ...valid,
              ...backendAvailable.filter(m => !valid.includes(m)),
            ]
            return seeded.slice(0, Math.max(2, Math.min(4, seeded.length)))
          })
        }
      })
      .catch(() => {
        // Keep fallback models when backend list is not available.
      })
  }, [])

  const addModel = () => {
    const available = availableModels.filter(m => !selectedModels.includes(m))
    if (available.length) setSelectedModels([...selectedModels, available[0]])
  }

  const removeModel = (idx: number) => {
    if (selectedModels.length > 2) setSelectedModels(selectedModels.filter((_, i) => i !== idx))
  }

  const changeModel = (idx: number, val: string) => {
    if (selectedModels.includes(val) && selectedModels[idx] !== val) return
    setSelectedModels(selectedModels.map((m, i) => (i === idx ? val : m)))
  }

  const handleCompare = async () => {
    setLoading(true)
    try {
      const res = await compareModels(prompt, selectedModels)
      setReport(res)
    } finally {
      setLoading(false)
    }
  }

  const modelShort = (m: string) => m.split('/').pop()?.split('-')[0] ?? m

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        <motion.div variants={fadeUp} className="flex items-center justify-between mb-8">
          <div>
            <h1 className="page-title">Model Comparison</h1>
            <p className="text-text-secondary text-sm mt-1">Compare performance across different models</p>
          </div>
          <button onClick={handleCompare} disabled={loading || selectedModels.length < 2} className="btn-primary disabled:opacity-40">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <GitCompare size={14} />}
            Compare
          </button>
        </motion.div>

        {/* Setup */}
        <motion.div variants={fadeUp}>
          <Card className="mb-6">
            <h2 className="section-title mb-3">Prompt</h2>
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              rows={3}
              className="input-base font-mono text-sm w-full resize-none"
            />
          </Card>
        </motion.div>

        <motion.div variants={fadeUp}>
          <Card className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <h2 className="section-title">Models ({selectedModels.length})</h2>
              <span className="text-xs text-text-muted font-mono">Available: {availableModels.length}</span>
              <button onClick={addModel} disabled={selectedModels.length >= 5} className="btn-ghost text-xs disabled:opacity-40">
                <Plus size={12} /> Add Model
              </button>
            </div>
            <div className="space-y-2">
              {selectedModels.map((m, i) => (
                <div key={i} className="flex items-center gap-2">
                  <select value={m} onChange={e => changeModel(i, e.target.value)} className="input-base flex-1">
                    {availableModels.map(am => (
                      <option key={am} value={am} disabled={selectedModels.includes(am) && am !== m}>{am}</option>
                    ))}
                  </select>
                  <button onClick={() => removeModel(i)} disabled={selectedModels.length <= 2} className="btn-ghost text-text-muted disabled:opacity-30">
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>

        {/* Results */}
        {report && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="mb-6">
              <h2 className="section-title mb-3">Comparison Summary</h2>
              <p className="text-sm text-text-secondary whitespace-pre-wrap">{report.summary}</p>
              <div className="mt-3 flex items-center gap-2">
                <Badge variant="muted">Consistency</Badge>
                <span className="font-mono text-sm" style={{ color: scoreToColor((report.consistency_score || 0) * 10) }}>
                  {(report.consistency_score * 100).toFixed(0)}%
                </span>
              </div>
            </Card>

            {/* Ranking */}
            <Card className="mb-6">
              <h2 className="section-title mb-4">Ranking</h2>
              <div className="grid md:grid-cols-3 gap-4">
                {report.ranking.slice(0, 3).map((r, i) => {
                  const Icon = podiumIcons[i] ?? Award
                  const result = report.results.find(x => x.model === r.model)
                  return (
                    <div key={r.model} className={`p-4 rounded-card border text-center ${i === 0 ? 'border-accent bg-accent/5' : 'border-border'}`}>
                      <Icon size={24} className={`mx-auto mb-2 ${i === 0 ? 'text-accent' : 'text-text-muted'}`} />
                      <p className="font-mono text-sm text-text-primary mb-1">{modelShort(r.model)}</p>
                      <p className="text-2xl font-body font-bold" style={{ color: scoreToColor(r.score ?? 0) }}>
                        <AnimatedNumber value={r.score ?? 0} decimals={1} />
                      </p>
                      <Badge variant={i === 0 ? 'accent' : 'muted'} className="mt-2">#{r.rank}</Badge>
                    </div>
                  )
                })}
              </div>
            </Card>

            {/* Detailed Comparison */}
            <Card className="mb-6">
              <h2 className="section-title mb-4">Criteria Comparison</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left px-4 py-3 table-header">Criterion</th>
                      {report.results.map(r => (
                        <th key={r.model} className="text-center px-4 py-3 table-header">{modelShort(r.model)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(['correctness', 'clarity', 'reasoning', 'relevance', 'conciseness'] as const).map(c => (
                      <tr key={c} className="table-row">
                        <td className="px-4 py-3 text-sm text-text-primary">{CRITERIA_LABELS[c]}</td>
                        {report.results.map(r => (
                          <td key={r.model} className="text-center px-4 py-3 font-mono font-semibold" style={{ color: scoreToColor(r.scores[c]) }}>
                            {r.scores[c].toFixed(1)}
                          </td>
                        ))}
                      </tr>
                    ))}
                    <tr className="border-t border-border font-semibold">
                      <td className="px-4 py-3 text-sm text-text-primary">Composite</td>
                      {report.results.map(r => (
                        <td key={r.model} className="text-center px-4 py-3 font-mono" style={{ color: scoreToColor(r.compositeScore) }}>
                          {r.compositeScore.toFixed(1)}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Sample Answers */}
            <Card>
              <h2 className="section-title mb-4">Sample Responses</h2>
              <div className="space-y-4">
                {report.results.map(r => (
                  <div key={r.model} className="border border-border rounded-card p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-sm text-text-primary">{modelShort(r.model)}</span>
                      <div className="flex items-center gap-2">
                        {r.metadata?.status === 'error' && <Badge variant="danger">error</Badge>}
                        <Badge variant={r.compositeScore >= 7 ? 'success' : r.compositeScore >= 5 ? 'warn' : 'danger'}>
                          {r.compositeScore.toFixed(1)}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mb-2 text-xs font-mono text-text-muted">
                      <span>Latency: {(r.metadata?.latencyMs ?? 0).toFixed(0)}ms</span>
                      <span>Tokens: {r.metadata?.tokensUsed ?? 0}</span>
                      <span>Cost: ${(r.metadata?.costUsd ?? 0).toFixed(6)}</span>
                    </div>
                    {r.metadata?.error && (
                      <p className="text-xs text-red-400 mb-2 break-words">Reason: {r.metadata.error}</p>
                    )}
                    <p className="text-sm text-text-secondary whitespace-pre-wrap break-words max-h-56 overflow-auto">
                      {r.answer?.trim() || r.explanation?.trim() || 'No response returned from backend for this model.'}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
