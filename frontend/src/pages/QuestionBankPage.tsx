import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Trash2, Search, BookOpen, Play, ChevronDown, ChevronUp, BarChart3, X } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import SkeletonLoader from '../components/ui/SkeletonLoader'
import { listQuestions, addQuestion, deleteQuestion, testQuestion, getQuestionStats, listTemplates } from '../services/api'
import { CATEGORIES } from '../utils/constants'
import type { Question, QuestionTestResult, QuestionBankStats, PromptTemplate } from '../types'

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }
const DIFFICULTY_COLORS: Record<string, string> = {
  easy: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  hard: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
}

export default function QuestionBankPage() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [catFilter, setCatFilter] = useState<string>('all')
  const [diffFilter, setDiffFilter] = useState<string>('all')
  const [showAdd, setShowAdd] = useState(false)
  const [newQ, setNewQ] = useState('')
  const [newCat, setNewCat] = useState('general')
  const [newGT, setNewGT] = useState('')
  const [newDiff, setNewDiff] = useState('medium')

  // Testing state
  const [testingId, setTestingId] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, QuestionTestResult>>({})
  const [expandedId, setExpandedId] = useState<string | null>(null)

  // Stats
  const [stats, setStats] = useState<QuestionBankStats | null>(null)
  const [showStats, setShowStats] = useState(false)

  // Templates
  const [templates, setTemplates] = useState<PromptTemplate[]>([])
  const [testTemplateId, setTestTemplateId] = useState<string>('')

  useEffect(() => {
    listQuestions().then(q => { setQuestions(q); setLoading(false) })
    getQuestionStats().then(setStats)
    listTemplates().then(setTemplates)
  }, [])

  const filtered = questions
    .filter(q => catFilter === 'all' || q.category === catFilter)
    .filter(q => diffFilter === 'all' || q.difficulty === diffFilter)
    .filter(q => q.question.toLowerCase().includes(search.toLowerCase()))

  const categories = ['all', ...new Set(questions.map(q => q.category))]

  const handleAdd = async () => {
    if (!newQ.trim()) return
    const q = await addQuestion(newQ, newCat, newGT || undefined)
    q.difficulty = newDiff as any
    setQuestions(prev => [...prev, q])
    setNewQ('')
    setNewGT('')
    setShowAdd(false)
    getQuestionStats().then(setStats)
  }

  const handleDelete = async (id: string) => {
    await deleteQuestion(id)
    setQuestions(prev => prev.filter(q => q.id !== id))
    getQuestionStats().then(setStats)
  }

  const handleTest = async (id: string) => {
    setTestingId(id)
    try {
      const result = await testQuestion(id, { templateId: testTemplateId || undefined })
      setTestResults(prev => ({ ...prev, [id]: result }))
      setExpandedId(id)
    } catch (err: any) {
      // Show error inline
      setTestResults(prev => ({
        ...prev,
        [id]: {
          question: '', questionId: id, category: '', difficulty: '',
          answer: `Error: ${err?.response?.data?.detail || err?.message || 'Test failed'}`,
          fullResponse: '', templateUsed: '', templateName: '', promptUsed: '',
          evaluation: { hasGroundTruth: false, groundTruth: '', matchScore: null, verdict: 'NO_GROUND_TRUTH', notes: [] },
          metadata: { model: 'N/A', tokens_used: 0, input_tokens: 0, output_tokens: 0, cost_usd: 0, latency_ms: 0, temperature: 0, maxTokens: 0, timestamp: '' },
        },
      }))
      setExpandedId(id)
    }
    setTestingId(null)
  }

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        <motion.div variants={fadeUp} className="flex items-center justify-between mb-8">
          <div>
            <h1 className="page-title">Question Bank</h1>
            <p className="text-text-secondary text-sm mt-1">{questions.length} questions available</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setShowStats(!showStats)} className="btn-ghost">
              <BarChart3 size={14} /> Stats
            </button>
            <button onClick={() => setShowAdd(true)} className="btn-primary">
              <Plus size={14} /> Add Question
            </button>
          </div>
        </motion.div>

        <motion.div variants={fadeUp} className="mb-4">
          <Card>
            <div className="text-sm text-text-secondary">
              Use <span className="text-text-primary font-medium">Test</span> on any question to measure answer quality against ground truth.
              Score now combines keyword precision/recall, concept coverage, and response quality notes.
            </div>
          </Card>
        </motion.div>

        {/* Stats Panel */}
        <AnimatePresence>
          {showStats && stats && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
              <Card className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="section-title">Question Bank Statistics</h3>
                  <button onClick={() => setShowStats(false)} className="btn-ghost text-xs"><X size={12} /></button>
                </div>
                <div className="grid sm:grid-cols-4 gap-4 mb-4">
                  <div className="text-center p-3 rounded-card bg-surface-secondary">
                    <div className="text-2xl font-bold text-text-primary">{stats.total}</div>
                    <div className="text-xs text-text-muted">Total Questions</div>
                  </div>
                  <div className="text-center p-3 rounded-card bg-surface-secondary">
                    <div className="text-2xl font-bold text-emerald-400">{stats.withGroundTruth}</div>
                    <div className="text-xs text-text-muted">With Ground Truth</div>
                  </div>
                  <div className="text-center p-3 rounded-card bg-surface-secondary">
                    <div className="text-2xl font-bold text-text-primary">{Object.keys(stats.byCategory).length}</div>
                    <div className="text-xs text-text-muted">Categories</div>
                  </div>
                  <div className="text-center p-3 rounded-card bg-surface-secondary">
                    <div className="flex items-center justify-center gap-2">
                      {Object.entries(stats.byDifficulty).map(([d, count]) => (
                        <Badge key={d} variant="muted" className={DIFFICULTY_COLORS[d]}>
                          {d}: {count}
                        </Badge>
                      ))}
                    </div>
                    <div className="text-xs text-text-muted mt-1">By Difficulty</div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(stats.byCategory).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
                    <Badge key={cat} variant="muted">{cat}: {count}</Badge>
                  ))}
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Filters */}
        <motion.div variants={fadeUp} className="flex flex-col md:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search questions..."
              className="input-base w-full pl-9"
            />
          </div>
          {/* Difficulty filter */}
          <div className="flex gap-1">
            {['all', 'easy', 'medium', 'hard'].map(d => (
              <button
                key={d}
                onClick={() => setDiffFilter(d)}
                className={`px-3 py-1.5 rounded-full text-xs font-mono transition-colors ${
                  diffFilter === d
                    ? 'bg-accent text-accent-contrast'
                    : 'border border-border text-text-muted hover:text-text-primary'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
          {/* Template selector for testing */}
          <select
            value={testTemplateId}
            onChange={e => setTestTemplateId(e.target.value)}
            className="input-base text-xs w-48"
          >
            <option value="">Auto template</option>
            {templates.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </motion.div>

        {/* Category filter chips */}
        <motion.div variants={fadeUp} className="flex gap-1 flex-wrap mb-6">
          {categories.map(c => (
            <button
              key={c}
              onClick={() => setCatFilter(c)}
              className={`px-3 py-1.5 rounded-full text-xs font-mono transition-colors ${
                catFilter === c
                  ? 'bg-accent text-accent-contrast'
                  : 'border border-border text-text-muted hover:text-text-primary'
              }`}
            >
              {c}
            </button>
          ))}
        </motion.div>

        {/* Questions Grid */}
        <motion.div variants={fadeUp}>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
            <AnimatePresence mode="popLayout">
              {filtered.map(q => (
                <motion.div
                  key={q.id}
                  layout
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                >
                  <Card hover className="h-full group relative">
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div className="flex gap-1.5 flex-wrap">
                        <Badge variant="muted">{q.category}</Badge>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono border ${DIFFICULTY_COLORS[q.difficulty] || DIFFICULTY_COLORS.medium}`}>
                          {q.difficulty}
                        </span>
                      </div>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => handleTest(q.id)}
                          disabled={testingId === q.id}
                          className="text-accent hover:text-accent/80 disabled:opacity-40"
                          title="Test this question"
                        >
                          {testingId === q.id ? (
                            <div className="w-3.5 h-3.5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Play size={14} />
                          )}
                        </button>
                        <button
                          onClick={() => handleDelete(q.id)}
                          className="text-text-muted hover:text-danger"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>

                    <p className="text-sm text-text-primary leading-relaxed mb-3">{q.question}</p>

                    {/* Ground Truth */}
                    {q.groundTruth && (
                      <div className="pt-3 border-t border-border">
                        <button
                          onClick={() => setExpandedId(expandedId === q.id ? null : q.id)}
                          className="flex items-center gap-1 text-xs text-text-muted font-mono uppercase mb-1 hover:text-text-secondary w-full text-left"
                        >
                          Ground Truth
                          {expandedId === q.id ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                        </button>
                        <p className={`text-xs text-text-secondary ${expandedId === q.id ? '' : 'line-clamp-2'}`}>
                          {q.groundTruth}
                        </p>
                      </div>
                    )}

                    {/* Test Result (inline) */}
                    {testResults[q.id] && expandedId === q.id && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="mt-3 pt-3 border-t border-border"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-mono text-text-muted uppercase">Test Result</span>
                          <div className="flex items-center gap-2">
                            {testResults[q.id].evaluation.matchScore !== null && (
                              <Badge variant={testResults[q.id].evaluation.matchScore! >= 7 ? 'success' : testResults[q.id].evaluation.matchScore! >= 4 ? 'warn' : 'danger'}>
                                Match: {testResults[q.id].evaluation.matchScore}/10
                              </Badge>
                            )}
                            {testResults[q.id].evaluation.verdict && (
                              <Badge variant="muted">{testResults[q.id].evaluation.verdict}</Badge>
                            )}
                            <Badge variant="muted">{testResults[q.id].templateName}</Badge>
                          </div>
                        </div>
                        <div className="bg-surface-secondary rounded-card p-3 text-xs text-text-secondary leading-relaxed max-h-64 overflow-y-auto whitespace-pre-wrap">
                          {testResults[q.id].fullResponse || testResults[q.id].answer}
                        </div>
                        <div className="flex items-center gap-3 mt-2 text-[10px] text-text-muted font-mono">
                          <span>{testResults[q.id].metadata.model.split('/').pop()}</span>
                          <span>{testResults[q.id].metadata.tokens_used} tokens</span>
                          <span>${(testResults[q.id].metadata.cost_usd || 0).toFixed(6)}</span>
                          <span>{testResults[q.id].metadata.latency_ms.toFixed(0)}ms</span>
                        </div>

                        {testResults[q.id].evaluation.details && (
                          <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] font-mono text-text-muted">
                            <div className="bg-surface-secondary rounded px-2 py-1">F1: {((testResults[q.id].evaluation.details?.keywordF1 || 0) * 100).toFixed(1)}%</div>
                            <div className="bg-surface-secondary rounded px-2 py-1">Coverage: {((testResults[q.id].evaluation.details?.conceptCoverage || 0) * 100).toFixed(1)}%</div>
                            <div className="bg-surface-secondary rounded px-2 py-1">Precision: {((testResults[q.id].evaluation.details?.keywordPrecision || 0) * 100).toFixed(1)}%</div>
                            <div className="bg-surface-secondary rounded px-2 py-1">Recall: {((testResults[q.id].evaluation.details?.keywordRecall || 0) * 100).toFixed(1)}%</div>
                          </div>
                        )}

                        {testResults[q.id].evaluation.notes?.length ? (
                          <div className="mt-2 space-y-1">
                            {testResults[q.id].evaluation.notes?.map((n, ni) => (
                              <div key={ni} className="text-[11px] text-amber-300">• {n}</div>
                            ))}
                          </div>
                        ) : null}

                        {(testResults[q.id]?.context?.related?.length || 0) > 0 && (
                          <div className="mt-2 pt-2 border-t border-border">
                            <div className="text-[10px] font-mono text-text-muted uppercase mb-1">Context Used</div>
                            <div className="space-y-1">
                              {testResults[q.id]?.context?.related?.slice(0, 3).map((c, ci) => (
                                <div key={`${c.id || ci}`} className="text-[11px] text-text-secondary bg-surface-secondary rounded px-2 py-1">
                                  {c.question}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </motion.div>
                    )}
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {filtered.length === 0 && (
            <div className="text-center py-16">
              <BookOpen size={32} className="mx-auto text-text-muted mb-3" />
              <p className="text-text-muted">No questions match your filters</p>
            </div>
          )}
        </motion.div>

        {/* Add Modal */}
        <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Add Question">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-mono text-text-muted uppercase block mb-1">Question</label>
              <textarea
                value={newQ}
                onChange={e => setNewQ(e.target.value)}
                rows={3}
                className="input-base w-full resize-none"
                placeholder="Enter your question..."
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-mono text-text-muted uppercase block mb-1">Category</label>
                <select value={newCat} onChange={e => setNewCat(e.target.value)} className="input-base w-full">
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-mono text-text-muted uppercase block mb-1">Difficulty</label>
                <select value={newDiff} onChange={e => setNewDiff(e.target.value)} className="input-base w-full">
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-xs font-mono text-text-muted uppercase block mb-1">Ground Truth (optional)</label>
              <textarea
                value={newGT}
                onChange={e => setNewGT(e.target.value)}
                rows={2}
                className="input-base w-full resize-none"
                placeholder="Expected answer..."
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowAdd(false)} className="btn-ghost">Cancel</button>
              <button onClick={handleAdd} disabled={!newQ.trim()} className="btn-primary disabled:opacity-40">Add Question</button>
            </div>
          </div>
        </Modal>
      </motion.div>
    </div>
  )
}
