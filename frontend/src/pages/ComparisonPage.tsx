import { useState } from 'react'
import { motion } from 'framer-motion'
import { GitCompare, Plus, X, Loader2, Trophy, Medal, Award } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import ScoreBar from '../components/ui/ScoreBar'
import CriteriaBarChart from '../components/charts/CriteriaBarChart'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import { compareModels } from '../services/api'
import { scoreToColor } from '../utils/formatters'
import { CRITERIA_LABELS } from '../utils/constants'
import type { ComparisonReport, ComparisonResult } from '../types'

const AVAILABLE_MODELS = [
  'mistralai/Mistral-7B-Instruct-v0.3',
  'google/gemma-2-2b-it',
  'microsoft/Phi-3-mini-4k-instruct',
  'meta-llama/Llama-3.2-3B-Instruct',
  'Qwen/Qwen2.5-3B-Instruct',
  'HuggingFaceTB/SmolLM2-1.7B-Instruct',
  'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
]

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }
const podiumIcons = [Trophy, Medal, Award]

export default function ComparisonPage() {
  const [prompt, setPrompt] = useState('Answer the following question clearly.\n\nQuestion: {question}\n\nAnswer:')
  const [selectedModels, setSelectedModels] = useState<string[]>([AVAILABLE_MODELS[0], AVAILABLE_MODELS[1]])
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<ComparisonReport | null>(null)

  const addModel = () => {
    const available = AVAILABLE_MODELS.filter(m => !selectedModels.includes(m))
    if (available.length) setSelectedModels([...selectedModels, available[0]])
  }

  const removeModel = (idx: number) => {
    if (selectedModels.length > 2) setSelectedModels(selectedModels.filter((_, i) => i !== idx))
  }

  const changeModel = (idx: number, val: string) => {
    setSelectedModels(selectedModels.map((m, i) => (i === idx ? val : m)))
  }

  const handleCompare = async () => {
    setLoading(true)
    const res = await compareModels(prompt, selectedModels)
    setReport(res)
    setLoading(false)
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
              <button onClick={addModel} disabled={selectedModels.length >= 5} className="btn-ghost text-xs disabled:opacity-40">
                <Plus size={12} /> Add Model
              </button>
            </div>
            <div className="space-y-2">
              {selectedModels.map((m, i) => (
                <div key={i} className="flex items-center gap-2">
                  <select value={m} onChange={e => changeModel(i, e.target.value)} className="input-base flex-1">
                    {AVAILABLE_MODELS.map(am => (
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
                      <Badge variant={r.compositeScore >= 7 ? 'success' : r.compositeScore >= 5 ? 'warn' : 'danger'}>
                        {r.compositeScore.toFixed(1)}
                      </Badge>
                    </div>
                    <p className="text-sm text-text-secondary">{r.answer}</p>
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
