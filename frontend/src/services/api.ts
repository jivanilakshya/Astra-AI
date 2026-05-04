/**
 * API service — connects to the FastAPI backend at /api/*
 * Falls back to mock data if the backend is unreachable.
 */
import axios from 'axios'
import {
  mockQuestions, mockSessions, mockSessionDetail,
  mockOptimizationResults, mockComparisonReport,
  mockPromptAnalysis, mockCostPrediction, mockAskQuestion,
  mockRouterStats, mockModels, mockCostHistory, mockDebugLog,
} from './mockData'
import type {
  Question, SessionSummary, SessionDetail, OptimizationResults,
  ComparisonReport, PromptAnalysis, CostPrediction, RouterStats,
  ModelProfile, GeneratedOutput, OptimizationConfig,
  PromptTemplate, TemplateAutoSelectResult, RoutingExplanation,
  RuntimeModeInfo, QuestionTestResult, QuestionBankStats,
} from '../types'
import type { DebugEntry, DailyCostRecord } from './mockData'

/* ─── Axios instance (Vite proxy sends /api/* → http://localhost:8000) ─── */
const api = axios.create({ baseURL: '/api', timeout: 60_000 })

/* ─── Helpers ─── */
const delay = (ms = 400) => new Promise(r => setTimeout(r, ms + Math.random() * 300))

let _backendOnline: boolean | null = null

const MODEL_CALLS_KEY = 'astra_model_calls_v1'
const MAX_MODEL_CALLS = 300

export interface ModelCallRecord {
  id: string
  timestamp: string
  endpoint: 'ask' | 'compare' | 'question_test'
  model: string
  prompt: string
  output: string
  status: 'success' | 'error'
  latencyMs: number
  tokensUsed: number
  costUsd: number
}

function readModelCallHistory(): ModelCallRecord[] {
  try {
    const raw = localStorage.getItem(MODEL_CALLS_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeModelCallHistory(rows: ModelCallRecord[]) {
  try {
    localStorage.setItem(MODEL_CALLS_KEY, JSON.stringify(rows.slice(0, MAX_MODEL_CALLS)))
  } catch {
    // ignore quota and serialization errors
  }
}

function logModelCall(entry: Omit<ModelCallRecord, 'id' | 'timestamp'> & { timestamp?: string }) {
  const record: ModelCallRecord = {
    id: `mc_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    timestamp: entry.timestamp || new Date().toISOString(),
    endpoint: entry.endpoint,
    model: entry.model || 'unknown',
    prompt: entry.prompt || '',
    output: entry.output || '',
    status: entry.status,
    latencyMs: entry.latencyMs || 0,
    tokensUsed: entry.tokensUsed || 0,
    costUsd: entry.costUsd || 0,
  }
  const current = readModelCallHistory()
  writeModelCallHistory([record, ...current])
}

export function getModelCallHistory(): ModelCallRecord[] {
  return readModelCallHistory()
}

function aggregateCostFromModelCalls(calls: ModelCallRecord[]): DailyCostRecord[] {
  const daily: Record<string, DailyCostRecord> = {}
  for (const c of calls) {
    const date = (c.timestamp || new Date().toISOString()).slice(0, 10)
    if (!daily[date]) {
      daily[date] = {
        date,
        totalCost: 0,
        generatorCost: 0,
        judgeCost: 0,
        optimizerCost: 0,
        tokensUsed: 0,
        requests: 0,
      }
    }
    daily[date].totalCost += c.costUsd || 0
    daily[date].generatorCost += c.costUsd || 0
    daily[date].tokensUsed += c.tokensUsed || 0
    daily[date].requests += 1
  }
  return Object.keys(daily)
    .sort()
    .map((k) => daily[k])
}

function mergeDailyCostHistory(primary: DailyCostRecord[], secondary: DailyCostRecord[]): DailyCostRecord[] {
  const merged: Record<string, DailyCostRecord> = {}
  for (const row of [...primary, ...secondary]) {
    const base = merged[row.date] || {
      date: row.date,
      totalCost: 0,
      generatorCost: 0,
      judgeCost: 0,
      optimizerCost: 0,
      tokensUsed: 0,
      requests: 0,
    }
    base.totalCost += row.totalCost || 0
    base.generatorCost += row.generatorCost || 0
    base.judgeCost += row.judgeCost || 0
    base.optimizerCost += row.optimizerCost || 0
    base.tokensUsed += row.tokensUsed || 0
    base.requests += row.requests || 0
    merged[row.date] = base
  }
  return Object.keys(merged)
    .sort()
    .map((k) => ({
      ...merged[k],
      totalCost: +merged[k].totalCost.toFixed(6),
      generatorCost: +merged[k].generatorCost.toFixed(6),
      judgeCost: +merged[k].judgeCost.toFixed(6),
      optimizerCost: +merged[k].optimizerCost.toFixed(6),
    }))
}

async function isBackendOnline(): Promise<boolean> {
  if (_backendOnline !== null) return _backendOnline
  try {
    const res = await api.get('/health', { timeout: 3000 })
    _backendOnline = res.data?.status === 'ok'
  } catch {
    _backendOnline = false
  }
  // Re-check every 30s
  setTimeout(() => { _backendOnline = null }, 30_000)
  return _backendOnline
}

/** Reset cached status (e.g. after settings change). */
export function resetBackendStatus() { _backendOnline = null }

/* ─── Questions ─── */
export async function listQuestions(): Promise<Question[]> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/questions')
      return data
    } catch { /* fall through */ }
  }
  await delay()
  return mockQuestions
}

export async function addQuestion(question: string, category: string, groundTruth?: string): Promise<Question> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.post('/questions', { question, category, groundTruth, difficulty: 'medium' })
      return data
    } catch { /* fall through */ }
  }
  await delay()
  const nq: Question = { id: String(mockQuestions.length + 1), question, category: category as any, groundTruth, difficulty: 'medium' }
  mockQuestions.push(nq)
  return nq
}

export async function deleteQuestion(id: string): Promise<void> {
  if (await isBackendOnline()) {
    try { await api.delete(`/questions/${id}`); return } catch { /* fall through */ }
  }
  await delay()
  const idx = mockQuestions.findIndex(q => q.id === id)
  if (idx !== -1) mockQuestions.splice(idx, 1)
}

/* ─── Sessions ─── */
export async function listSessions(): Promise<SessionSummary[]> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/sessions')
      return data
    } catch { /* fall through */ }
  }
  await delay()
  return [...mockSessions].sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
}

export async function getSession(id: string): Promise<SessionDetail> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get(`/sessions/${id}`)
      return data
    } catch { /* fall through */ }
  }
  await delay(600)
  return mockSessionDetail(id)
}

export async function deleteSession(id: string): Promise<void> {
  if (await isBackendOnline()) {
    try { await api.delete(`/sessions/${id}`); return } catch { /* fall through */ }
  }
  await delay()
  const idx = mockSessions.findIndex(s => s.sessionId === id)
  if (idx !== -1) mockSessions.splice(idx, 1)
}

/* ─── Optimization ─── */
export async function startOptimization(config: OptimizationConfig): Promise<{ sessionId: string }> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.post('/optimize/start', config)
      return data
    } catch { /* fall through */ }
  }
  await delay(800)
  return { sessionId: 'sess_live_' + Math.random().toString(36).slice(2, 10) }
}

export async function getOptimizationResults(sessionId: string): Promise<OptimizationResults> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get(`/optimize/${sessionId}/results`)
      return data
    } catch { /* fall through */ }
  }
  await delay(600)
  return mockOptimizationResults()
}

export async function getOptimizationProgress(sessionId: string): Promise<{
  status: string
  phase: string
  iteration: number
  totalIterations: number
  elapsedSeconds: number
  etaSeconds: number | null
  lastUpdate: string
}> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get(`/optimize/${sessionId}/progress`)
      return data
    } catch { /* fall through */ }
  }
  return {
    status: 'running',
    phase: 'generation',
    iteration: 0,
    totalIterations: 0,
    elapsedSeconds: 0,
    etaSeconds: null,
    lastUpdate: new Date().toISOString(),
  }
}

export async function stopOptimization(sessionId: string): Promise<void> {
  if (await isBackendOnline()) {
    try { await api.post(`/optimize/stop/${sessionId}`); return } catch { /* fall through */ }
  }
}

/* ─── Ask ─── */
export async function askQuestion(
  question: string,
  prompt?: string,
  opts?: { model?: string; templateId?: string; category?: string; showRouting?: boolean; useContext?: boolean }
): Promise<GeneratedOutput> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.post('/ask', {
        question,
        prompt,
        model: opts?.model,
        templateId: opts?.templateId,
        category: opts?.category,
        showRouting: opts?.showRouting,
        useContext: opts?.useContext,
      })
      logModelCall({
        endpoint: 'ask',
        model: data?.metadata?.model || opts?.model || 'unknown',
        prompt: prompt || question,
        output: data?.fullResponse || data?.answer || data?.explanation || '',
        status: (data?.metadata?.status === 'error' ? 'error' : 'success'),
        latencyMs: data?.metadata?.latency_ms || 0,
        tokensUsed: data?.metadata?.tokens_used || 0,
        costUsd: data?.metadata?.cost_usd || 0,
      })
      return data
    } catch { /* fall through */ }
  }
  await delay(1500)
  const mock = mockAskQuestion(question, prompt)
  logModelCall({
    endpoint: 'ask',
    model: mock?.metadata?.model || opts?.model || 'mock',
    prompt: prompt || question,
    output: mock?.fullResponse || mock?.answer || mock?.explanation || '',
    status: 'success',
    latencyMs: mock?.metadata?.latency_ms || 0,
    tokensUsed: mock?.metadata?.tokens_used || 0,
    costUsd: mock?.metadata?.cost_usd || 0,
  })
  return mock
}

/* ─── Compare ─── */
export async function compareModels(prompt: string, models: string[]): Promise<ComparisonReport> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.post('/compare', { prompt, models })
      if (Array.isArray(data?.results)) {
        data.results.forEach((r: any) => {
          logModelCall({
            endpoint: 'compare',
            model: r?.metadata?.usedModel || r?.model || 'unknown',
            prompt,
            output: r?.answer || r?.explanation || '',
            status: r?.metadata?.status === 'error' ? 'error' : 'success',
            latencyMs: r?.metadata?.latencyMs || 0,
            tokensUsed: r?.metadata?.tokensUsed || 0,
            costUsd: r?.metadata?.costUsd || 0,
          })
        })
      }
      return data
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Compare request failed'
      return {
        results: models.map(model => ({
          model,
          answer: `Error: ${msg}`,
          explanation: `Error: ${msg}`,
          scores: { correctness: 0, clarity: 0, reasoning: 0, relevance: 0, conciseness: 0 },
          compositeScore: 0,
          metadata: { tokensUsed: 0, latencyMs: 0, costUsd: 0, status: 'error', error: String(msg) },
        })),
        ranking: models.map((model, idx) => ({ model, rank: idx + 1, score: 0 })),
        consistency_score: 0,
        summary: `Backend compare failed: ${msg}`,
      }
    }
  }
  const offline = {
    results: models.map(model => ({
      model,
      answer: 'Error: Backend is offline. Start backend server to run real model comparison.',
      explanation: 'Error: Backend is offline. Start backend server to run real model comparison.',
      scores: { correctness: 0, clarity: 0, reasoning: 0, relevance: 0, conciseness: 0 },
      compositeScore: 0,
      metadata: { tokensUsed: 0, latencyMs: 0, costUsd: 0, status: 'error', error: 'backend_offline' },
    })),
    ranking: models.map((model, idx) => ({ model, rank: idx + 1, score: 0 })),
    consistency_score: 0,
    summary: 'Backend is offline. Model comparison requires live backend responses.',
  }
  offline.results.forEach((r) => {
    logModelCall({
      endpoint: 'compare',
      model: r.model,
      prompt,
      output: r.answer,
      status: 'error',
      latencyMs: r.metadata?.latencyMs || 0,
      tokensUsed: r.metadata?.tokensUsed || 0,
      costUsd: r.metadata?.costUsd || 0,
    })
  })
  return offline
}

/* ─── Prompt Analyzer ─── */
export async function analyzePrompt(prompt: string): Promise<PromptAnalysis> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.post('/prompt/analyze', { prompt })
      return data
    } catch { /* fall through */ }
  }
  await delay(800)
  return mockPromptAnalysis(prompt)
}

export async function optimizePrompt(prompt: string): Promise<{ optimizedPrompt: string }> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.post('/prompt/optimize', { prompt })
      return data
    } catch { /* fall through */ }
  }
  await delay(600)
  return { optimizedPrompt: prompt + '\n\nPlease explain your reasoning step-by-step.' }
}

/* ─── Cost ─── */
export async function getCostPrediction(prompt: string): Promise<CostPrediction> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.post('/cost/predict', { prompt })
      return data
    } catch { /* fall through */ }
  }
  await delay()
  return mockCostPrediction(prompt)
}

export async function getCostHistory(): Promise<DailyCostRecord[]> {
  const localFromCalls = aggregateCostFromModelCalls(getModelCallHistory())
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/cost/history')
      const serverData = Array.isArray(data) ? data : []
      return mergeDailyCostHistory(serverData, localFromCalls)
    } catch { /* fall through */ }
  }
  await delay()
  return mergeDailyCostHistory(mockCostHistory(), localFromCalls)
}

/* ─── Router ─── */
export async function getRouterStats(): Promise<RouterStats> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/router/stats')
      return data
    } catch { /* fall through */ }
  }
  await delay()
  return mockRouterStats
}

/* ─── Models ─── */
export async function getModels(): Promise<ModelProfile[]> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/models')
      return data
    } catch { /* fall through */ }
  }
  await delay()
  return mockModels
}

/* ─── Debug ─── */
export async function getDebugLog(): Promise<DebugEntry[]> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/debug/log')
      return data
    } catch { /* fall through */ }
  }
  await delay()
  return mockDebugLog()
}

/* ─── Settings ─── */
export async function getSettings(): Promise<Record<string, unknown>> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/settings')
      return data
    } catch { /* fall through */ }
  }
  return {}
}

export async function updateSettings(settings: Record<string, unknown>): Promise<void> {
  if (await isBackendOnline()) {
    try { await api.put('/settings', settings); return } catch { /* fall through */ }
  }
}

/* ─── Health ─── */
export async function checkHealth(): Promise<{ status: string }> {
  try {
    const { data } = await api.get('/health', { timeout: 3000 })
    return data
  } catch {
    return { status: 'offline' }
  }
}

/* ─── Prompt Templates ─── */
export async function listTemplates(): Promise<PromptTemplate[]> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/templates')
      return data
    } catch { /* fall through */ }
  }
  // Fallback mock templates
  return [
    { id: 'general_qa', name: 'General Q&A', description: 'Clear, structured answer', template: '', categories: [], intents: ['question'], complexity: 'moderate', output_format: 'structured', is_default: true },
    { id: 'scientific', name: 'Scientific', description: 'Scientific explanation', template: '', categories: [], intents: ['question'], complexity: 'complex', output_format: 'structured', is_default: false },
    { id: 'code_generation', name: 'Code Generation', description: 'Code with explanation', template: '', categories: [], intents: ['code'], complexity: 'complex', output_format: 'markdown', is_default: false },
    { id: 'comparison', name: 'Comparison', description: 'Side-by-side analysis', template: '', categories: [], intents: ['comparison'], complexity: 'complex', output_format: 'structured', is_default: false },
    { id: 'step_by_step', name: 'Step-by-Step', description: 'Chain-of-thought reasoning', template: '', categories: [], intents: ['reasoning'], complexity: 'complex', output_format: 'structured', is_default: false },
    { id: 'concise', name: 'Quick & Concise', description: 'Short direct answer', template: '', categories: [], intents: ['question'], complexity: 'simple', output_format: 'structured', is_default: false },
    { id: 'educational', name: 'Educational', description: 'Teaching-oriented', template: '', categories: [], intents: ['question'], complexity: 'complex', output_format: 'structured', is_default: false },
    { id: 'creative', name: 'Creative / Essay', description: 'Thoughtful essay', template: '', categories: [], intents: ['creative'], complexity: 'complex', output_format: 'structured', is_default: false },
    { id: 'code_debug', name: 'Code Debugging', description: 'Debug analysis', template: '', categories: [], intents: ['code'], complexity: 'complex', output_format: 'markdown', is_default: false },
    { id: 'json_output', name: 'JSON Output', description: 'Structured JSON response', template: '', categories: [], intents: ['question'], complexity: 'moderate', output_format: 'json', is_default: false },
  ]
}

export async function autoSelectTemplate(question: string, category?: string): Promise<TemplateAutoSelectResult> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.post('/templates/auto-select', { question, category })
      return data
    } catch { /* fall through */ }
  }
  return {
    selectedTemplate: { id: 'general_qa', name: 'General Q&A', description: '', template: '', categories: [], intents: [], complexity: 'moderate', output_format: 'structured', is_default: true },
    detectedIntent: 'question',
    detectedComplexity: 'moderate',
    category: category || 'general',
    renderedPrompt: '',
  }
}

/* ─── Question Testing ─── */
export async function testQuestion(
  questionId: string,
  opts?: { templateId?: string; model?: string; temperature?: number; maxTokens?: number }
): Promise<QuestionTestResult> {
  if (await isBackendOnline()) {
    const { data } = await api.post(`/questions/${questionId}/test`, {
      templateId: opts?.templateId,
      model: opts?.model,
      temperature: opts?.temperature ?? 0.7,
      maxTokens: opts?.maxTokens ?? 500,
    })
    logModelCall({
      endpoint: 'question_test',
      model: data?.metadata?.model || opts?.model || 'unknown',
      prompt: data?.promptUsed || '',
      output: data?.fullResponse || data?.answer || '',
      status: data?.metadata?.status === 'error' ? 'error' : 'success',
      latencyMs: data?.metadata?.latency_ms || 0,
      tokensUsed: data?.metadata?.tokens_used || 0,
      costUsd: data?.metadata?.cost_usd || 0,
    })
    return data
  }
  throw new Error('Backend not available for question testing')
}

/* ─── Question Bank Stats ─── */
export async function getQuestionStats(): Promise<QuestionBankStats> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/questions/stats')
      return data
    } catch { /* fall through */ }
  }
  return { total: 0, withGroundTruth: 0, withoutGroundTruth: 0, byCategory: {}, byDifficulty: {} }
}

/* ─── Update Question ─── */
export async function updateQuestion(id: string, question: string, category: string, groundTruth?: string, difficulty?: string): Promise<Question> {
  if (await isBackendOnline()) {
    const { data } = await api.put(`/questions/${id}`, { question, category, groundTruth, difficulty: difficulty || 'medium' })
    return data
  }
  throw new Error('Backend not available')
}

/* ─── Router Explain ─── */
export async function explainRouting(question: string, category?: string): Promise<RoutingExplanation> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.post('/router/explain', { question, category })
      return data
    } catch { /* fall through */ }
  }
  return {
    complexity: 'MODERATE',
    recommendedModel: 'Qwen/Qwen2.5-72B-Instruct',
    alternatives: [],
    reasons: ['Smart router not available — using default model'],
    costEstimate: 0,
    latencyEstimate: 2.0,
    tokenEstimate: 0,
    category: category || 'general',
  }
}

/* ─── Runtime Mode ─── */
export async function getRuntimeMode(): Promise<RuntimeModeInfo> {
  if (await isBackendOnline()) {
    try {
      const { data } = await api.get('/mode')
      return data
    } catch { /* fall through */ }
  }
  return {
    mode: 'production',
    description: 'Backend not available',
    features: {
      showDebugLogs: false, showRawPrompts: false, showChainOfThought: false,
      showRawResponses: false, showDetailedMetrics: false, showCostBreakdown: true,
      showFinalAnswer: true, showSummaryScore: true,
    },
  }
}

export async function setRuntimeMode(mode: 'developer' | 'production'): Promise<RuntimeModeInfo> {
  if (await isBackendOnline()) {
    const { data } = await api.post('/mode', { mode })
    return data
  }
  throw new Error('Backend not available')
}

/* ─── WebSocket helper for optimization ─── */
export function connectOptimizationWS(sessionId: string, handlers: {
  onIterationComplete?: (log: any) => void
  onProgress?: (progress: any) => void
  onComplete?: (results: OptimizationResults) => void
  onError?: (err: any) => void
  onClose?: () => void
}): { close: () => void; stop: () => void } {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/optimize/${sessionId}`
  const ws = new WebSocket(wsUrl)

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      switch (msg.type) {
        case 'iteration_start':
          handlers.onProgress?.(msg.data)
          break
        case 'iteration_complete':
          handlers.onIterationComplete?.(msg.data)
          break
        case 'complete':
          handlers.onComplete?.(msg.data)
          break
        case 'error':
          handlers.onError?.(msg.data)
          break
        case 'stopped':
          handlers.onClose?.()
          break
      }
    } catch { /* ignore parse errors */ }
  }

  ws.onerror = () => handlers.onError?.({ message: 'WebSocket connection error' })
  ws.onclose = () => handlers.onClose?.()

  return {
    close: () => ws.close(),
    stop: () => { try { ws.send('stop') } catch { /* ignore */ } },
  }
}
