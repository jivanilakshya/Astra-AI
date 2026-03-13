import { useState } from 'react'
import { motion } from 'framer-motion'
import { Search, Loader2, FileText, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import ScoreBar from '../components/ui/ScoreBar'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import { analyzePrompt, getCostPrediction } from '../services/api'
import { scoreToColor, formatCost } from '../utils/formatters'
import type { PromptAnalysis, CostPrediction } from '../types'

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }

const samplePrompts = [
  { label: 'Basic', value: 'Answer: {question}' },
  { label: 'Structured', value: 'Answer the following question clearly and concisely.\n\nQuestion: {question}\n\nProvide your reasoning step-by-step.\n\nAnswer:' },
  { label: 'Expert', value: 'You are an expert educator. Answer the question with accuracy, clarity, and proper reasoning.\n\nQuestion: {question}\n\nRequirements:\n- Be factually correct\n- Explain step-by-step\n- Use simple language\n- Be concise\n\nAnswer:' },
]

const gradeColors: Record<string, string> = {
  'A+': '#16a34a', A: '#22c55e', 'A-': '#4ade80',
  'B+': '#a3e635', B: '#eab308', 'B-': '#f59e0b',
  'C+': '#f97316', C: '#ef4444', 'C-': '#dc2626',
  D: '#991b1b', F: '#7f1d1d',
}

export default function PromptAnalyzerPage() {
  const [prompt, setPrompt] = useState(samplePrompts[1].value)
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<PromptAnalysis | null>(null)
  const [cost, setCost] = useState<CostPrediction | null>(null)

  const handleAnalyze = async () => {
    setLoading(true)
    const [a, c] = await Promise.all([analyzePrompt(prompt), getCostPrediction(prompt)])
    setAnalysis(a)
    setCost(c)
    setLoading(false)
  }

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        <motion.div variants={fadeUp} className="flex items-center justify-between mb-8">
          <div>
            <h1 className="page-title">Prompt Analyzer</h1>
            <p className="text-text-secondary text-sm mt-1">Analyze prompt quality and get cost predictions</p>
          </div>
          <button onClick={handleAnalyze} disabled={!prompt.trim() || loading} className="btn-primary disabled:opacity-40">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
            Analyze
          </button>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Input */}
          <motion.div variants={fadeUp} className="lg:col-span-2">
            <Card>
              <div className="flex items-center justify-between mb-3">
                <h2 className="section-title">Prompt Template</h2>
                <div className="flex gap-1">
                  {samplePrompts.map(sp => (
                    <button key={sp.label} onClick={() => setPrompt(sp.value)} className="btn-ghost text-xs">
                      {sp.label}
                    </button>
                  ))}
                </div>
              </div>
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                rows={10}
                className="input-base font-mono text-sm w-full resize-none"
                placeholder="Enter your prompt template..."
              />
              <div className="flex justify-between mt-2 text-xs text-text-muted font-mono">
                <span>{prompt.length} chars</span>
                <span>{prompt.split(/\s+/).length} words</span>
              </div>
            </Card>
          </motion.div>

          {/* Quick Stats */}
          <motion.div variants={fadeUp} className="space-y-4">
            {cost && (
              <Card>
                <h2 className="section-title mb-3">Cost Estimate</h2>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-text-muted">Input tokens</span>
                    <span className="font-mono text-text-primary">{cost.estimatedInputTokens}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-text-muted">Output tokens</span>
                    <span className="font-mono text-text-primary">{cost.estimatedOutputTokens}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-text-muted">Per question</span>
                    <span className="font-mono text-text-primary">{formatCost(cost.estimatedCostPerQuestion)}</span>
                  </div>
                  <div className="border-t border-border pt-3 flex justify-between font-semibold">
                    <span className="text-sm text-text-primary">10-question run</span>
                    <span className="font-mono text-text-primary">{formatCost(cost.estimatedCostPerQuestion * 10)}</span>
                  </div>
                </div>
              </Card>
            )}

            {analysis && (
              <Card className="text-center">
                <p className="text-xs font-mono text-text-muted uppercase mb-2">Quality Grade</p>
                <div
                  className="text-6xl font-display font-bold mb-2"
                  style={{ color: gradeColors[analysis.qualityGrade] ?? 'var(--color-text-muted)' }}
                >
                  {analysis.qualityGrade}
                </div>
                <p className="text-2xl font-body font-semibold text-text-primary">
                  <AnimatedNumber value={analysis.overallScore} decimals={1} suffix="/10" />
                </p>
              </Card>
            )}
          </motion.div>
        </div>

        {/* Analysis Results */}
        {analysis && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-8 grid lg:grid-cols-2 gap-6">
            {/* Scores */}
            <Card>
              <h2 className="section-title mb-4">Quality Breakdown</h2>
              <div className="space-y-3">
                {Object.entries(analysis.scores).map(([k, v]) => (
                  <ScoreBar key={k} label={k.charAt(0).toUpperCase() + k.slice(1).replace('_', ' ')} value={v} max={10} />
                ))}
              </div>
            </Card>

            {/* Suggestions */}
            <Card>
              <h2 className="section-title mb-4">Suggestions</h2>
              <div className="space-y-3">
                {analysis.suggestions.map((s, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-button bg-surface-2">
                    <ArrowRight size={14} className="text-accent mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-text-secondary">{s}</p>
                  </div>
                ))}
              </div>

              {analysis.flags.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border">
                  <h3 className="text-xs font-mono text-text-muted uppercase mb-2">Flags</h3>
                  <div className="flex flex-wrap gap-2">
                    {analysis.flags.map((f, i) => (
                      <Badge key={i} variant="warn">{f}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
