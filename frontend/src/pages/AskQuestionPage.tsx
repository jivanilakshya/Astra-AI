import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, RotateCcw, Sparkles, Clock, Zap, Route, ChevronDown, ChevronUp, Code, BookOpen, FlaskConical, GitCompare, ListOrdered, MessageCircle, FileJson, Bug, PenLine, Eye, EyeOff } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import SkeletonLoader from '../components/ui/SkeletonLoader'
import { askQuestion, listTemplates, autoSelectTemplate, explainRouting, getRuntimeMode, getModels } from '../services/api'
import type { PromptTemplate, RoutingExplanation, RuntimeModeInfo, GeneratedOutput, ModelProfile } from '../types'

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }

const TEMPLATE_ICONS: Record<string, React.ReactNode> = {
  general_qa: <MessageCircle size={14} />,
  scientific: <FlaskConical size={14} />,
  code_generation: <Code size={14} />,
  code_debug: <Bug size={14} />,
  comparison: <GitCompare size={14} />,
  step_by_step: <ListOrdered size={14} />,
  concise: <Zap size={14} />,
  educational: <BookOpen size={14} />,
  creative: <PenLine size={14} />,
  json_output: <FileJson size={14} />,
}

interface HistoryEntry extends GeneratedOutput {
  templateName?: string
}

export default function AskQuestionPage() {
  const [question, setQuestion] = useState('')
  const [customPrompt, setCustomPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<GeneratedOutput | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [showPrompt, setShowPrompt] = useState(false)
  const [showRouting, setShowRouting] = useState(false)
  const [showDebug, setShowDebug] = useState(false)
  const [useContext, setUseContext] = useState(true)

  // Template state
  const [templates, setTemplates] = useState<PromptTemplate[]>([])
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('auto')
  const [autoDetectedTemplate, setAutoDetectedTemplate] = useState<string | null>(null)
  const [autoIntent, setAutoIntent] = useState<string>('question')
  const [autoComplexity, setAutoComplexity] = useState<string>('moderate')

  // Model state
  const [models, setModels] = useState<ModelProfile[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')

  // Category
  const [category, setCategory] = useState<string>('general')

  // Routing
  const [routingInfo, setRoutingInfo] = useState<RoutingExplanation | null>(null)
  const [routingLoading, setRoutingLoading] = useState(false)

  // Mode
  const [modeInfo, setModeInfo] = useState<RuntimeModeInfo | null>(null)

  // Load templates, models, mode on mount
  useEffect(() => {
    listTemplates().then(setTemplates)
    getModels().then(m => {
      setModels(m)
      if (m.length > 0) setSelectedModel(m[0].id)
    })
    getRuntimeMode().then(setModeInfo)
  }, [])

  // Auto-detect template when question changes
  const detectTemplate = useCallback(async () => {
    if (!question.trim() || selectedTemplateId !== 'auto') return
    try {
      const result = await autoSelectTemplate(question, category)
      setAutoDetectedTemplate(result.selectedTemplate.id)
      setAutoIntent(result.detectedIntent || 'question')
      setAutoComplexity(result.detectedComplexity || 'moderate')
    } catch { /* ignore */ }
  }, [question, category, selectedTemplateId])

  useEffect(() => {
    const timeout = setTimeout(detectTemplate, 500)
    return () => clearTimeout(timeout)
  }, [detectTemplate])

  // Explain routing
  const handleExplainRouting = async () => {
    if (!question.trim()) return
    setRoutingLoading(true)
    try {
      const info = await explainRouting(question, category)
      setRoutingInfo(info)
      setShowRouting(true)
    } catch { /* ignore */ }
    setRoutingLoading(false)
  }

  const handleAsk = async () => {
    if (!question.trim()) return
    setLoading(true)
    setAnswer(null)

    try {
      const templateId = selectedTemplateId === 'auto'
        ? autoDetectedTemplate || undefined
        : selectedTemplateId

      const res = await askQuestion(
        question,
        showPrompt && customPrompt.trim() ? customPrompt : undefined,
        {
          model: selectedModel || undefined,
          templateId: showPrompt ? undefined : templateId,
          category,
          showRouting: true,
          useContext,
        }
      )

      setAnswer(res)
      const entry: HistoryEntry = {
        ...res,
        templateName: templates.find(t => t.id === (res.templateUsed || templateId))?.name,
      }
      setHistory(prev => [entry, ...prev].slice(0, 30))

      // Update routing info from response
      if (res.routing) {
        setRoutingInfo(res.routing)
      }
    } catch (err: any) {
      setAnswer({
        question,
        answer: `Error: ${err?.response?.data?.detail || err?.message || 'Unknown error'}`,
        explanation: '',
        confidence: 0,
        metadata: { model: 'N/A', tokens_used: 0, input_tokens: 0, output_tokens: 0, latency_ms: 0, timestamp: new Date().toISOString() },
      })
    }
    setLoading(false)
  }

  const handleClear = () => {
    setQuestion('')
    setAnswer(null)
    setRoutingInfo(null)
    setShowRouting(false)
  }

  const activeTemplateName = selectedTemplateId === 'auto'
    ? templates.find(t => t.id === autoDetectedTemplate)?.name || 'Auto-detect'
    : templates.find(t => t.id === selectedTemplateId)?.name || selectedTemplateId

  const isDev = modeInfo?.mode === 'developer'

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        <motion.div variants={fadeUp} className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title">Ask a Question</h1>
              <p className="text-text-secondary text-sm mt-1">
                AI-powered answers with intelligent template selection &amp; smart routing
              </p>
            </div>
            {modeInfo && (
              <Badge variant={isDev ? 'warn' : 'success'}>
                {isDev ? 'Developer' : 'Production'} Mode
              </Badge>
            )}
          </div>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Input Column */}
          <motion.div variants={fadeUp} className="lg:col-span-2 space-y-4">

            {/* Template & Model Selectors */}
            <Card>
              <div className="grid sm:grid-cols-3 gap-4">
                {/* Template Selector */}
                <div>
                  <label className="block text-xs font-mono text-text-muted uppercase mb-1.5">Prompt Template</label>
                  <select
                    value={selectedTemplateId}
                    onChange={e => setSelectedTemplateId(e.target.value)}
                    className="input-base w-full text-sm"
                  >
                    <option value="auto">Auto-detect{autoDetectedTemplate ? ` (${templates.find(t => t.id === autoDetectedTemplate)?.name || ''})` : ''}</option>
                    {templates.map(t => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>

                {/* Model Selector */}
                <div>
                  <label className="block text-xs font-mono text-text-muted uppercase mb-1.5">Model</label>
                  <select
                    value={selectedModel}
                    onChange={e => setSelectedModel(e.target.value)}
                    className="input-base w-full text-sm"
                  >
                    {models.map(m => (
                      <option key={m.id} value={m.id}>{m.name} ({m.parameters})</option>
                    ))}
                  </select>
                </div>

                {/* Category */}
                <div>
                  <label className="block text-xs font-mono text-text-muted uppercase mb-1.5">Category</label>
                  <select
                    value={category}
                    onChange={e => setCategory(e.target.value)}
                    className="input-base w-full text-sm"
                  >
                    <option value="general">General</option>
                    <option value="biology">Biology</option>
                    <option value="physics">Physics</option>
                    <option value="chemistry">Chemistry</option>
                    <option value="mathematics">Mathematics</option>
                    <option value="computer_science">Computer Science</option>
                    <option value="earth_science">Earth Science</option>
                    <option value="astronomy">Astronomy</option>
                    <option value="economics">Economics</option>
                    <option value="history">History</option>
                    <option value="logic">Logic</option>
                    <option value="code_python">Python</option>
                    <option value="code_javascript">JavaScript</option>
                    <option value="code_java">Java</option>
                    <option value="code_cpp">C++</option>
                    <option value="code_debug">Code Debug</option>
                  </select>
                </div>
              </div>

              {/* Active Template Badge */}
              <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border">
                <span className="text-xs text-text-muted">Active template:</span>
                <Badge variant="accent">
                  {TEMPLATE_ICONS[autoDetectedTemplate || selectedTemplateId] || <Sparkles size={12} />}
                  <span className="ml-1">{activeTemplateName}</span>
                </Badge>
                {selectedTemplateId === 'auto' && question.trim() && (
                  <span className="text-[11px] text-text-muted">
                    intent: {autoIntent} · complexity: {autoComplexity}
                  </span>
                )}
              </div>
            </Card>

            {/* Question Input */}
            <Card>
              <div className="flex items-center justify-between mb-3">
                <h2 className="section-title">Your Question</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => setUseContext(!useContext)}
                    className={`btn-ghost text-xs ${useContext ? 'text-accent' : ''}`}
                    title="Toggle context engineering"
                  >
                    {useContext ? 'Context ON' : 'Context OFF'}
                  </button>
                  <button onClick={() => setShowPrompt(!showPrompt)} className="btn-ghost text-xs">
                    {showPrompt ? <EyeOff size={12} /> : <Eye size={12} />}
                    {showPrompt ? ' Hide' : ' Edit'} Prompt
                  </button>
                  <button
                    onClick={handleExplainRouting}
                    disabled={!question.trim() || routingLoading}
                    className="btn-ghost text-xs"
                  >
                    <Route size={12} /> Routing
                  </button>
                </div>
              </div>

              {showPrompt && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}>
                  <textarea
                    value={customPrompt}
                    onChange={e => setCustomPrompt(e.target.value)}
                    rows={4}
                    placeholder="Custom prompt template. Use {question} as placeholder. Leave empty to use selected template."
                    className="input-base font-mono text-sm w-full mb-3 resize-none"
                  />
                </motion.div>
              )}

              <div className="flex gap-2">
                <input
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleAsk()}
                  placeholder="e.g. What is photosynthesis?"
                  className="input-base flex-1"
                />
                <button onClick={handleAsk} disabled={!question.trim() || loading} className="btn-primary disabled:opacity-40">
                  <Send size={14} /> Ask
                </button>
                <button onClick={handleClear} className="btn-ghost">
                  <RotateCcw size={14} />
                </button>
              </div>
            </Card>

            {/* Routing Info */}
            <AnimatePresence>
              {showRouting && routingInfo && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <Card className="border-l-4 border-l-accent">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Route size={16} className="text-accent" />
                        <h3 className="section-title">Smart Routing Analysis</h3>
                      </div>
                      <button onClick={() => setShowRouting(false)} className="btn-ghost text-xs">Hide</button>
                    </div>

                    <div className="grid sm:grid-cols-4 gap-4 mb-4">
                      <div className="text-center p-3 rounded-card bg-surface-secondary">
                        <div className="text-xs text-text-muted mb-1">Complexity</div>
                        <Badge variant={routingInfo.complexity === 'SIMPLE' ? 'success' : routingInfo.complexity === 'CRITICAL' ? 'danger' : 'warn'}>
                          {routingInfo.complexity}
                        </Badge>
                      </div>
                      <div className="text-center p-3 rounded-card bg-surface-secondary">
                        <div className="text-xs text-text-muted mb-1">Recommended</div>
                        <div className="text-sm font-medium text-text-primary truncate">{routingInfo.recommendedModel.split('/').pop()}</div>
                      </div>
                      <div className="text-center p-3 rounded-card bg-surface-secondary">
                        <div className="text-xs text-text-muted mb-1">Est. Latency</div>
                        <div className="text-sm font-medium text-text-primary">{routingInfo.latencyEstimate.toFixed(1)}s</div>
                      </div>
                      <div className="text-center p-3 rounded-card bg-surface-secondary">
                        <div className="text-xs text-text-muted mb-1">Est. Tokens</div>
                        <div className="text-sm font-medium text-text-primary">{routingInfo.tokenEstimate}</div>
                      </div>
                    </div>

                    {/* Reasons */}
                    <div className="mb-3">
                      <div className="text-xs font-mono text-text-muted uppercase mb-1">Routing Reasons</div>
                      <ul className="space-y-1">
                        {routingInfo.reasons.map((r, i) => (
                          <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                            <span className="text-accent mt-0.5">&#8594;</span> {r}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Alternatives */}
                    {routingInfo.alternatives.length > 0 && (
                      <details className="group">
                        <summary className="text-xs font-mono text-text-muted uppercase cursor-pointer hover:text-text-secondary">
                          Alternative Models ({routingInfo.alternatives.length})
                        </summary>
                        <div className="mt-2 space-y-1">
                          {routingInfo.alternatives.map((alt, i) => (
                            <div key={i} className="flex items-center justify-between text-sm p-2 rounded bg-surface-secondary">
                              <span className="text-text-primary">{alt.model.split('/').pop()}</span>
                              <div className="flex gap-3 text-xs text-text-muted">
                                <span>Tier {alt.quality_tier}</span>
                                <span>{alt.latency_estimate.toFixed(1)}s</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Loading */}
            {loading && (
              <Card>
                <SkeletonLoader rows={6} />
              </Card>
            )}

            {/* Answer (Full Structured Output) */}
            {answer && !loading && (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
                <Card>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Sparkles size={16} className="text-accent" />
                      <h2 className="section-title">Answer</h2>
                      <Badge variant="muted">{((answer.confidence ?? 0) * 100).toFixed(0)}% confidence</Badge>
                    </div>
                    {answer.templateUsed && (
                      <Badge variant="accent">
                        {TEMPLATE_ICONS[answer.templateUsed] || <Sparkles size={12} />}
                        <span className="ml-1">{templates.find(t => t.id === answer.templateUsed)?.name || answer.templateUsed}</span>
                      </Badge>
                    )}
                  </div>

                  {/* Full Structured Response */}
                  <div className="prose-container">
                    <StructuredOutput text={answer.fullResponse || answer.answer} />
                  </div>

                  {/* Metadata footer */}
                  <div className="flex flex-wrap items-center gap-4 mt-4 pt-4 border-t border-border text-xs text-text-muted font-mono">
                    <span className="flex items-center gap-1">{answer.metadata?.model?.split('/').pop() ?? 'unknown'}</span>
                    <span>{answer.metadata?.tokens_used ?? 0} tokens</span>
                    <span className="flex items-center gap-1"><Clock size={10} />{(answer.metadata?.latency_ms ?? 0).toFixed(0)}ms</span>
                    <span>In: {answer.metadata?.input_tokens ?? 0} / Out: {answer.metadata?.output_tokens ?? 0}</span>
                    <span>Cost: ${(answer.metadata?.cost_usd ?? 0).toFixed(6)}</span>
                  </div>

                  {answer.context?.related && answer.context.related.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-border">
                      <div className="text-xs font-mono text-text-muted uppercase mb-2">Context Engineering</div>
                      <div className="text-xs text-text-secondary mb-2">
                        Used {answer.context.related.length} related items from category {answer.context.category || category}.
                      </div>
                      <div className="space-y-1">
                        {answer.context.related.map((item, idx) => (
                          <div key={`${item.id || idx}`} className="text-xs text-text-secondary bg-surface-secondary rounded-card px-2 py-1">
                            {item.question}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Developer Mode Debug Info */}
                  {isDev && answer.debug && (
                    <div className="mt-4 pt-4 border-t border-border">
                      <button
                        onClick={() => setShowDebug(!showDebug)}
                        className="flex items-center gap-1 text-xs font-mono text-text-muted hover:text-text-secondary mb-2"
                      >
                        {showDebug ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        Debug Info (Developer Mode)
                      </button>
                      <AnimatePresence>
                        {showDebug && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="space-y-3 overflow-hidden"
                          >
                            <div>
                              <div className="text-xs font-mono text-text-muted mb-1">Full Prompt Sent</div>
                              <pre className="text-xs bg-surface-secondary p-3 rounded-card overflow-x-auto whitespace-pre-wrap max-h-48 overflow-y-auto">{answer.debug.fullPrompt}</pre>
                            </div>
                            <div>
                              <div className="text-xs font-mono text-text-muted mb-1">Raw Response</div>
                              <pre className="text-xs bg-surface-secondary p-3 rounded-card overflow-x-auto whitespace-pre-wrap max-h-48 overflow-y-auto">{answer.debug.rawResponse}</pre>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                </Card>
              </motion.div>
            )}
          </motion.div>

          {/* Sidebar — History */}
          <motion.div variants={fadeUp}>
            <Card className="h-full">
              <h2 className="section-title mb-3">History</h2>
              {history.length === 0 ? (
                <p className="text-text-muted text-sm">No questions asked yet</p>
              ) : (
                <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                  {history.map((h, i) => (
                    <button
                      key={i}
                      onClick={() => { setQuestion(h.question); setAnswer(h) }}
                      className="w-full text-left p-3 rounded-button border border-border hover:border-border-strong transition-colors"
                    >
                      <p className="text-sm text-text-primary truncate">{h.question}</p>
                      <p className="text-xs text-text-muted mt-1 truncate">
                        {h.answer.slice(0, 80)}...
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {h.templateUsed && (
                          <Badge variant="muted" className="text-[10px]">{h.templateName || h.templateUsed}</Badge>
                        )}
                        <span className="text-[10px] text-text-muted">{h.metadata?.model?.split('/').pop() ?? ''}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </Card>
          </motion.div>
        </div>
      </motion.div>
    </div>
  )
}


/* ── Structured Output Renderer ── */
function StructuredOutput({ text }: { text: string }) {
  if (!text) return null

  // Split into sections by **Header:** patterns
  const sections = text.split(/(?=\*\*[^*]+:\*\*)/)
  const hasStructuredSections = sections.length > 1

  if (!hasStructuredSections) {
    // Plain text — render as paragraphs
    return (
      <div className="space-y-3">
        {text.split('\n\n').map((para, i) => (
          <p key={i} className="text-text-primary leading-relaxed text-sm">{para}</p>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {sections.map((section, i) => {
        const headerMatch = section.match(/^\*\*(.+?):\*\*\s*/)
        if (!headerMatch) {
          return section.trim() ? (
            <p key={i} className="text-text-primary leading-relaxed text-sm">{section.trim()}</p>
          ) : null
        }

        const header = headerMatch[1]
        const content = section.slice(headerMatch[0].length).trim()

        return (
          <div key={i} className="border-l-2 border-accent/30 pl-4">
            <h3 className="text-sm font-semibold text-text-primary mb-2 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-accent" />
              {header}
            </h3>
            <div className="text-sm text-text-secondary leading-relaxed">
              {content.split('\n').map((line, j) => {
                const trimmed = line.trim()
                if (!trimmed) return null
                if (trimmed.startsWith('- ')) {
                  return (
                    <div key={j} className="flex items-start gap-2 ml-2 mb-1">
                      <span className="text-accent mt-1 text-xs">&bull;</span>
                      <span>{trimmed.slice(2)}</span>
                    </div>
                  )
                }
                if (trimmed.startsWith('Step ') || trimmed.match(/^\d+\.\s/)) {
                  return <p key={j} className="font-medium text-text-primary mb-1">{trimmed}</p>
                }
                if (trimmed.startsWith('```')) {
                  return null
                }
                return <p key={j} className="mb-1">{trimmed}</p>
              })}
              {content.includes('```') && (
                <pre className="bg-surface-secondary rounded-card p-3 font-mono text-xs overflow-x-auto mt-2">
                  {content.split('```').filter((_, idx) => idx % 2 === 1).join('\n')}
                </pre>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
