import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, RotateCcw, CheckCircle2, ChevronDown, ChevronUp, Search, Sparkles, Eye, EyeOff, FileText, Wand2 } from 'lucide-react'
import Card from '../components/ui/Card'
import AnimatedNumber from '../components/ui/AnimatedNumber'
import ScoreBar from '../components/ui/ScoreBar'
import Badge from '../components/ui/Badge'
import PerformanceLineChart from '../components/charts/PerformanceLineChart'
import ScoreRadar from '../components/charts/ScoreRadar'
import { startOptimization, getOptimizationResults, listQuestions, getModels, listTemplates, autoSelectTemplate } from '../services/api'
import { scoreToColor } from '../utils/formatters'
import { CRITERIA_LABELS } from '../utils/constants'
import type { Question, OptimizationResults, PromptTemplate } from '../types'

type Phase = 'setup' | 'running' | 'results'

export default function OptimizationPage() {
  const [phase, setPhase] = useState<Phase>('setup')
  const [questions, setQuestions] = useState<Question[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [prompt, setPrompt] = useState('Answer the following question clearly and concisely.\n\nQuestion: {question}\n\nProvide a detailed explanation.\n\nAnswer:')
  const [maxIter, setMaxIter] = useState(5)
  const [model, setModel] = useState('')
  const [temperature, setTemperature] = useState(0.7)
  const [maxTokens, setMaxTokens] = useState(500)
  const [templateId, setTemplateId] = useState('')
  const [autoTemplate, setAutoTemplate] = useState(true)
  const [models, setModels] = useState<{id: string; name: string}[]>([])
  const [templates, setTemplates] = useState<PromptTemplate[]>([])
  const [qSearch, setQSearch] = useState('')
  const [qCatFilter, setQCatFilter] = useState('all')

  // Running state
  const [currentIter, setCurrentIter] = useState(0)
  const [totalIter, setTotalIter] = useState(0)
  const [liveScores, setLiveScores] = useState<number[]>([])
  const [running, setRunning] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Results state
  const [results, setResults] = useState<OptimizationResults | null>(null)

  useEffect(() => {
    listQuestions().then(q => {
      setQuestions(q)
      setSelectedIds(q.slice(0, 3).map(x => x.id))
    })
    getModels().then(m => {
      setModels(m)
      if (m.length > 0 && !model) setModel(m[0].id)
    })
    listTemplates().then(setTemplates)
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [])

  // Auto-select template when first selected question changes
  useEffect(() => {
    if (!autoTemplate || selectedIds.length === 0) return
    const firstQ = questions.find(q => q.id === selectedIds[0])
    if (!firstQ) return
    autoSelectTemplate(firstQ.question, firstQ.category).then(r => {
      if (r.selectedTemplate) {
        setTemplateId(r.selectedTemplate.id)
        setPrompt(r.renderedPrompt || r.selectedTemplate.template)
      }
    }).catch(() => {})
  }, [selectedIds, questions, autoTemplate])

  const toggleQuestion = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const handleTemplateChange = (id: string) => {
    setTemplateId(id)
    setAutoTemplate(false)
    if (id) {
      const t = templates.find(t => t.id === id)
      if (t) setPrompt(t.template)
    }
  }

  const handleStart = async () => {
    setPhase('running')
    setCurrentIter(0)
    setTotalIter(maxIter)
    setLiveScores([])
    setRunning(true)

    try {
      const { sessionId } = await startOptimization({
        initialPrompt: prompt,
        model,
        generatorModel: model,
        maxIterations: maxIter,
        questionIds: selectedIds,
        temperature,
        maxTokens,
        templateId: templateId || undefined,
        batchSize: Math.min(selectedIds.length, 5),
      })

      const poll = setInterval(async () => {
        try {
          const r = await getOptimizationResults(sessionId)
          const history = r.performanceHistory ?? []
          if (history.length > 0) {
            setCurrentIter(history.length)
            setLiveScores([...history])
          }
          const detail = r as any
          const isDone =
            history.length >= maxIter ||
            r.converged ||
            detail.status === 'completed' ||
            detail.status === 'error' ||
            detail.status === 'stopped'

          if (isDone) {
            clearInterval(poll)
            intervalRef.current = null
            setRunning(false)
            setResults(r)
            setPhase('results')
          }
        } catch { /* keep polling */ }
      }, 4000)

      intervalRef.current = poll as unknown as ReturnType<typeof setInterval>
    } catch {
      // Fallback: simulate
      let iter = 0
      const scores: number[] = []
      intervalRef.current = setInterval(() => {
        iter++
        const score = 5.0 + iter * 0.4 + Math.random() * 0.6
        scores.push(+score.toFixed(1))
        setCurrentIter(iter)
        setLiveScores([...scores])
        if (iter >= maxIter) {
          if (intervalRef.current) clearInterval(intervalRef.current)
          setRunning(false)
          getOptimizationResults('sim').then(r => { setResults(r); setPhase('results') })
        }
      }, 1200)
    }
  }

  const handleReset = () => {
    setPhase('setup')
    setResults(null)
    setCurrentIter(0)
    setLiveScores([])
  }

  // Filter questions
  const qCategories = ['all', ...new Set(questions.map(q => q.category))]
  const filteredQs = questions
    .filter(q => qCatFilter === 'all' || q.category === qCatFilter)
    .filter(q => q.question.toLowerCase().includes(qSearch.toLowerCase()))

  return (
    <div className="page-container">
      <AnimatePresence mode="wait">
        {phase === 'setup' && (
          <motion.div key="setup" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="page-title">Optimization</h1>
                <p className="text-text-secondary text-sm mt-1">Configure and run a self-improving prompt optimization</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="muted">{selectedIds.length} questions</Badge>
                <button onClick={handleStart} disabled={selectedIds.length === 0} className="btn-primary disabled:opacity-40">
                  <Play size={14} /> Start Optimization
                </button>
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Prompt Template */}
              <Card>
                <div className="flex items-center justify-between mb-3">
                  <h2 className="section-title">Prompt Template</h2>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setAutoTemplate(!autoTemplate)
                        if (!autoTemplate) setTemplateId('')
                      }}
                      className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${autoTemplate ? 'bg-accent/10 text-accent' : 'text-text-muted hover:text-text-secondary'}`}
                    >
                      <Wand2 size={12} /> Auto
                    </button>
                  </div>
                </div>
                {autoTemplate && templateId && (
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles size={12} className="text-accent" />
                    <span className="text-xs text-accent">Auto-selected: {templates.find(t => t.id === templateId)?.name || templateId}</span>
                  </div>
                )}
                <textarea
                  value={prompt}
                  onChange={e => { setPrompt(e.target.value); setAutoTemplate(false) }}
                  rows={8}
                  className="input-base font-mono text-sm w-full resize-none"
                  placeholder="Enter your prompt template..."
                />
                <p className="text-xs text-text-muted mt-2">Use {'`{question}`'} as placeholder. Edit directly or select a template.</p>
              </Card>

              {/* Config */}
              <Card>
                <h2 className="section-title mb-3">Configuration</h2>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-mono text-text-muted uppercase">Model</label>
                    <select value={model} onChange={e => setModel(e.target.value)} className="input-base w-full mt-1">
                      {models.map(m => (
                        <option key={m.id} value={m.id}>{m.name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-mono text-text-muted uppercase">Prompt Template</label>
                    <select value={templateId} onChange={e => handleTemplateChange(e.target.value)} className="input-base w-full mt-1">
                      <option value="">Custom (use editor)</option>
                      {templates.map(t => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-mono text-text-muted uppercase">Max Iterations</label>
                    <div className="flex items-center gap-3 mt-1">
                      <input type="range" min={2} max={10} value={maxIter} onChange={e => setMaxIter(+e.target.value)} className="flex-1 accent-accent" />
                      <span className="font-mono text-text-primary w-8 text-right">{maxIter}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-mono text-text-muted uppercase">Temperature</label>
                      <div className="flex items-center gap-2 mt-1">
                        <input type="range" min={0} max={1} step={0.1} value={temperature} onChange={e => setTemperature(parseFloat(e.target.value))} className="flex-1 accent-accent" />
                        <span className="font-mono text-text-primary text-sm">{temperature}</span>
                      </div>
                    </div>
                    <div>
                      <label className="text-xs font-mono text-text-muted uppercase">Max Tokens</label>
                      <div className="flex items-center gap-2 mt-1">
                        <input type="range" min={100} max={2000} step={100} value={maxTokens} onChange={e => setMaxTokens(parseInt(e.target.value))} className="flex-1 accent-accent" />
                        <span className="font-mono text-text-primary text-sm">{maxTokens}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Questions (from Question Bank) */}
            <Card className="mt-6">
              <div className="flex items-center justify-between mb-3">
                <h2 className="section-title">Select Questions from Bank ({selectedIds.length})</h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      if (selectedIds.length === filteredQs.length) {
                        filteredQs.forEach(q => { if (selectedIds.includes(q.id)) toggleQuestion(q.id) })
                      } else {
                        filteredQs.forEach(q => { if (!selectedIds.includes(q.id)) toggleQuestion(q.id) })
                      }
                    }}
                    className="btn-ghost text-xs"
                  >
                    {selectedIds.length === filteredQs.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
              </div>

              {/* Search + category filter */}
              <div className="flex gap-2 mb-3">
                <div className="relative flex-1">
                  <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
                  <input
                    value={qSearch}
                    onChange={e => setQSearch(e.target.value)}
                    placeholder="Search questions..."
                    className="input-base w-full pl-8 text-sm py-1.5"
                  />
                </div>
                <select value={qCatFilter} onChange={e => setQCatFilter(e.target.value)} className="input-base text-xs w-36">
                  {qCategories.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-64 overflow-y-auto pr-2">
                {filteredQs.map(q => (
                  <button
                    key={q.id}
                    onClick={() => toggleQuestion(q.id)}
                    className={`text-left p-3 rounded-button border text-sm transition-colors ${
                      selectedIds.includes(q.id)
                        ? 'border-accent bg-accent/5 text-text-primary'
                        : 'border-border text-text-secondary hover:border-border-strong'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-1">
                      <span className="line-clamp-2">{q.question}</span>
                      <Badge variant="muted" className="shrink-0 text-[10px]">{q.category}</Badge>
                    </div>
                  </button>
                ))}
              </div>
              {selectedIds.length > 5 && (
                <p className="text-xs text-amber-400 mt-2">Tip: More questions = longer optimization. 3-5 questions recommended for speed.</p>
              )}
            </Card>
          </motion.div>
        )}

        {phase === 'running' && (
          <RunningView key="running" currentIter={currentIter} totalIter={totalIter} scores={liveScores} running={running} />
        )}

        {phase === 'results' && results && (
          <ResultsView key="results" results={results} onReset={handleReset} templates={templates} />
        )}
      </AnimatePresence>
    </div>
  )
}

/* ── Running ───────────────────────────────────────────── */

function RunningView({ currentIter, totalIter, scores, running }: {
  currentIter: number; totalIter: number; scores: number[]; running: boolean
}) {
  const pct = totalIter > 0 ? (currentIter / totalIter) * 100 : 0
  const lastScore = scores[scores.length - 1] ?? 0

  return (
    <motion.div key="running" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center justify-center min-h-[60vh]">
      <div className="max-w-lg w-full text-center">
        <motion.div
          animate={{ rotate: running ? 360 : 0 }}
          transition={{ duration: 2, repeat: running ? Infinity : 0, ease: 'linear' }}
          className="w-20 h-20 mx-auto mb-8 rounded-full border-2 border-border border-t-accent"
        />
        <h2 className="font-display text-3xl text-text-primary mb-2">Optimizing</h2>
        <p className="text-text-secondary text-sm mb-8">Iteration {currentIter} of {totalIter}</p>
        <div className="w-full h-2 bg-surface-2 rounded-full mb-2 overflow-hidden">
          <motion.div className="h-full bg-accent rounded-full" animate={{ width: `${pct}%` }} transition={{ duration: 0.4 }} />
        </div>
        <p className="text-xs text-text-muted font-mono mb-8">{pct.toFixed(0)}% complete</p>
        {lastScore > 0 && (
          <Card className="text-center">
            <p className="text-xs font-mono text-text-muted uppercase mb-1">Current Score</p>
            <p className="text-4xl font-body font-bold" style={{ color: scoreToColor(lastScore) }}>
              <AnimatedNumber value={lastScore} decimals={1} />
            </p>
            {scores.length > 1 && <div className="mt-4"><PerformanceLineChart data={scores} height={140} /></div>}
          </Card>
        )}
      </div>
    </motion.div>
  )
}

/* ── Results ───────────────────────────────────────────── */

function ResultsView({ results, onReset, templates }: { results: OptimizationResults; onReset: () => void; templates: PromptTemplate[] }) {
  const improvement = results.finalScore - results.initialScore
  const lastLog = results.iterationLogs[results.iterationLogs.length - 1]
  const scores = results.performanceHistory.length > 0
    ? results.performanceHistory
    : results.iterationLogs.map(l => l.avgCompositeScore)

  const [expandedIter, setExpandedIter] = useState<number | null>(null)
  const [showInitialPrompt, setShowInitialPrompt] = useState(false)

  const configInfo = results.config as any
  const templateName = configInfo?.templateId
    ? templates.find(t => t.id === configInfo.templateId)?.name || configInfo.templateId
    : 'Custom Prompt'

  return (
    <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <CheckCircle2 size={24} className="text-success" />
          <div>
            <h1 className="page-title">Optimization Complete</h1>
            <p className="text-text-secondary text-sm mt-0.5">
              {results.iterations} iterations — {results.converged ? 'Converged' : 'Max iterations reached'}
              {results.totalDurationSeconds > 0 && ` — ${results.totalDurationSeconds.toFixed(0)}s`}
            </p>
          </div>
        </div>
        <button onClick={onReset} className="btn-secondary">
          <RotateCcw size={14} /> New Run
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        {[
          { label: 'Initial Score', value: results.initialScore, color: scoreToColor(results.initialScore) },
          { label: 'Final Score', value: results.finalScore, color: scoreToColor(results.finalScore) },
          { label: 'Improvement', value: improvement, color: improvement > 0 ? 'var(--color-success)' : 'var(--color-danger)', prefix: improvement > 0 ? '+' : '' },
          { label: 'Iterations', value: results.iterations, color: 'var(--color-text-primary)', decimals: 0 },
          { label: 'Questions', value: configInfo?.questionsCount || 0, color: 'var(--color-text-primary)', decimals: 0 },
        ].map(m => (
          <Card key={m.label} className="text-center">
            <p className="text-xs font-mono text-text-muted uppercase mb-1">{m.label}</p>
            <p className="text-2xl font-body font-bold" style={{ color: m.color }}>
              {(m as any).prefix}<AnimatedNumber value={m.value} decimals={(m as any).decimals ?? 1} />
            </p>
          </Card>
        ))}
      </div>

      {/* Config used */}
      {configInfo && (
        <Card className="mb-6">
          <h2 className="section-title mb-3">Configuration Used</h2>
          <div className="flex flex-wrap gap-3">
            <Badge variant="accent">Model: {configInfo.generatorModel?.split('/').pop()}</Badge>
            <Badge variant="muted">Template: {templateName}</Badge>
            <Badge variant="muted">Temp: {configInfo.temperature}</Badge>
            <Badge variant="muted">Max Tokens: {configInfo.maxTokens}</Badge>
            <Badge variant="muted">Judge: {configInfo.judgeModel?.split('/').pop()}</Badge>
          </div>
        </Card>
      )}

      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <h2 className="section-title mb-4">Score Progress</h2>
          <PerformanceLineChart data={scores} target={8.5} height={280} />
        </Card>
        <Card>
          <h2 className="section-title mb-4">Final Criteria Breakdown</h2>
          {lastLog?.avgScores ? (
            <ScoreRadar scores={lastLog.avgScores} height={280} />
          ) : (
            <p className="text-text-muted text-sm">No data</p>
          )}
        </Card>
      </div>

      {/* Per-criteria bars */}
      {lastLog?.avgScores && (
        <Card className="mb-8">
          <h2 className="section-title mb-4">Criteria Scores</h2>
          <div className="space-y-3">
            {Object.entries(lastLog.avgScores).map(([k, v]) => (
              <ScoreBar key={k} label={CRITERIA_LABELS[k] ?? k} value={v} max={10} />
            ))}
          </div>
        </Card>
      )}

      {/* Prompts: Initial vs Optimized */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <div className="flex items-center justify-between mb-3">
            <h2 className="section-title">
              <FileText size={14} className="inline mr-1" />
              Initial Prompt
            </h2>
            <button onClick={() => setShowInitialPrompt(!showInitialPrompt)} className="btn-ghost text-xs">
              {showInitialPrompt ? <EyeOff size={12} /> : <Eye size={12} />}
              {showInitialPrompt ? ' Hide' : ' Show'}
            </button>
          </div>
          {showInitialPrompt && (
            <pre className="font-mono text-xs text-text-secondary bg-surface-2 rounded-card p-3 whitespace-pre-wrap overflow-auto max-h-48">
              {results.initialPrompt || results.iterationLogs[0]?.prompt || '(not recorded)'}
            </pre>
          )}
          {!showInitialPrompt && <p className="text-xs text-text-muted">Click Show to view the initial prompt</p>}
        </Card>
        <Card>
          <h2 className="section-title mb-3">
            <Sparkles size={14} className="inline mr-1 text-accent" />
            Optimized Prompt
          </h2>
          <pre className="font-mono text-xs text-text-secondary bg-surface-2 rounded-card p-3 whitespace-pre-wrap overflow-auto max-h-48 border border-accent/20">
            {results.finalPrompt || '(no optimized prompt)'}
          </pre>
        </Card>
      </div>

      {/* Iteration Details with full answers */}
      <Card className="mb-8">
        <h2 className="section-title mb-4">Iteration Details & Full Answers</h2>
        <div className="space-y-2">
          {results.iterationLogs.map((log, idx) => (
            <div key={idx} className="border border-border rounded-card overflow-hidden">
              <button
                onClick={() => setExpandedIter(expandedIter === idx ? null : idx)}
                className="w-full flex items-center justify-between p-3 hover:bg-surface-secondary transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono text-text-muted">Iter {idx + 1}</span>
                  <span className="text-sm font-bold" style={{ color: scoreToColor(log.avgCompositeScore || log.score) }}>
                    {(log.avgCompositeScore || log.score).toFixed(1)}/10
                  </span>
                  {log.optimizationModifications && log.optimizationModifications.length > 0 && (
                    <Badge variant="muted" className="text-[10px]">{log.optimizationModifications.length} changes</Badge>
                  )}
                </div>
                {expandedIter === idx ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              <AnimatePresence>
                {expandedIter === idx && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="p-4 pt-0 space-y-4">
                      {/* Prompt used */}
                      {log.prompt && (
                        <div>
                          <p className="text-xs font-mono text-text-muted uppercase mb-1">Prompt Used</p>
                          <pre className="font-mono text-xs text-text-secondary bg-surface-2 rounded p-2 whitespace-pre-wrap max-h-32 overflow-auto">
                            {log.prompt}
                          </pre>
                        </div>
                      )}

                      {/* Scores */}
                      {log.avgScores && (
                        <div>
                          <p className="text-xs font-mono text-text-muted uppercase mb-1">Scores</p>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(log.avgScores).map(([k, v]) => (
                              <Badge key={k} variant={v >= 7 ? 'success' : v >= 4 ? 'warn' : 'danger'}>
                                {k}: {v.toFixed(1)}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Generated outputs (full answers) */}
                      {log.generatedOutputs && log.generatedOutputs.length > 0 && (
                        <div>
                          <p className="text-xs font-mono text-text-muted uppercase mb-2">Full Answers ({log.generatedOutputs.length})</p>
                          <div className="space-y-2">
                            {log.generatedOutputs.map((out, oi) => (
                              <div key={oi} className="border border-border rounded p-3">
                                <p className="text-xs font-medium text-text-primary mb-1">Q: {out.question}</p>
                                <div className="bg-surface-2 rounded p-2 text-xs text-text-secondary whitespace-pre-wrap max-h-40 overflow-auto">
                                  {out.answer || out.explanation || '(empty)'}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Evaluations */}
                      {log.evaluations && log.evaluations.length > 0 && (
                        <div>
                          <p className="text-xs font-mono text-text-muted uppercase mb-1">Evaluations</p>
                          <div className="space-y-1">
                            {log.evaluations.map((ev, ei) => (
                              <div key={ei} className="flex items-center gap-2 text-xs">
                                <span className="font-mono text-text-muted">Q{ei + 1}:</span>
                                <span className="font-bold" style={{ color: scoreToColor(ev.composite_score || 0) }}>
                                  {(ev.composite_score || 0).toFixed(1)}
                                </span>
                                {ev.suggestions && ev.suggestions.length > 0 && (
                                  <span className="text-text-muted truncate max-w-xs">— {ev.suggestions[0]}</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Optimization modifications */}
                      {log.optimizationModifications && log.optimizationModifications.length > 0 && (
                        <div>
                          <p className="text-xs font-mono text-text-muted uppercase mb-1">Prompt Changes Made</p>
                          <ul className="text-xs text-text-secondary space-y-1">
                            {log.optimizationModifications.map((mod, mi) => (
                              <li key={mi} className="flex items-start gap-1">
                                <span className="text-accent shrink-0">•</span> {mod}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </Card>
    </motion.div>
  )
}
