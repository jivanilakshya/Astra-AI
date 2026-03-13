/* ─── Prompt Templates ─── */
export interface PromptTemplate {
  id: string
  name: string
  description: string
  template: string
  categories: string[]
  intents: string[]
  complexity: string
  output_format: string
  is_default: boolean
}

export interface TemplateAutoSelectResult {
  selectedTemplate: PromptTemplate
  detectedIntent: string
  detectedComplexity: string
  category: string
  renderedPrompt: string
}

/* ─── Routing ─── */
export interface RoutingExplanation {
  complexity: string
  recommendedModel: string
  alternatives: Array<{
    model: string
    cost_estimate: number
    latency_estimate: number
    quality_tier: number
  }>
  reasons: string[]
  costEstimate: number
  latencyEstimate: number
  tokenEstimate: number
  category: string
}

/* ─── Runtime Mode ─── */
export interface RuntimeModeInfo {
  mode: 'developer' | 'production'
  description: string
  features: {
    showDebugLogs: boolean
    showRawPrompts: boolean
    showChainOfThought: boolean
    showRawResponses: boolean
    showDetailedMetrics: boolean
    showCostBreakdown: boolean
    showFinalAnswer: boolean
    showSummaryScore: boolean
  }
}

/* ─── Question Test Result ─── */
export interface QuestionTestResult {
  question: string
  questionId: string
  category: string
  difficulty: string
  answer: string
  fullResponse: string
  templateUsed: string
  templateName: string
  promptUsed: string
  evaluation: {
    hasGroundTruth: boolean
    groundTruth: string
    matchScore: number | null
  }
  metadata: {
    model: string
    tokens_used: number
    input_tokens: number
    output_tokens: number
    latency_ms: number
    temperature: number
    maxTokens: number
    timestamp: string
  }
}

/* ─── Question Bank Stats ─── */
export interface QuestionBankStats {
  total: number
  withGroundTruth: number
  withoutGroundTruth: number
  byCategory: Record<string, number>
  byDifficulty: Record<string, number>
}

/* ─── Question ─── */
export type QuestionCategory =
  | 'computer_science' | 'code_python' | 'code_javascript' | 'code_java'
  | 'code_cpp' | 'code_sql' | 'code_rust' | 'code_debug' | 'code_refactor'
  | 'code_api' | 'code_html_css' | 'physics' | 'biology' | 'mathematics'
  | 'economics' | 'history' | 'earth_science' | 'astronomy' | 'chemistry'
  | 'logic' | 'prompt_quality' | 'relevance_test' | 'general'

export type Difficulty = 'easy' | 'medium' | 'hard'

export interface Question {
  id: string
  question: string
  groundTruth?: string
  category: string
  difficulty: Difficulty
  context?: string
  metadata?: Record<string, unknown>
}

/* ─── Scores & Evaluation ─── */
export interface Scores {
  correctness: number
  clarity: number
  reasoning: number
  relevance: number
  conciseness: number
}

export interface Evaluation {
  scores: Scores
  composite_score: number
  feedback?: {
    correctness_reason?: string
    clarity_reason?: string
    reasoning_reason?: string
    relevance_reason?: string
    conciseness_reason?: string
  }
  suggestions?: string[]
  flags?: string[]
  metadata?: {
    judge_model?: string
    timestamp?: string
    tokens_used?: number
    confidence?: number
  }
}

export interface GeneratedOutput {
  question: string
  answer: string
  explanation: string
  fullResponse?: string
  confidence?: number
  templateUsed?: string
  routing?: RoutingExplanation
  debug?: {
    fullPrompt: string
    rawResponse: string
    templateUsed: string | null
    modelRouting: RoutingExplanation | null
  }
  metadata?: {
    model?: string
    tokens_used?: number
    input_tokens?: number
    output_tokens?: number
    latency_ms?: number
    timestamp?: string
    status?: string
  }
}

/* ─── Optimization ─── */
export interface OptimizationConfig {
  model?: string
  initialPrompt?: string
  generatorModel?: string
  judgeModel?: string
  optimizerModel?: string
  maxIterations?: number
  convergenceThreshold?: number
  criteriaWeights?: Record<string, number>
  weights?: Scores
  batchSize?: number
  temperature?: number
  topP?: number
  maxTokens?: number
  smartRouter?: boolean
  questionIds?: string[]
  templateId?: string
}

export interface IterationLog {
  iteration: number
  prompt: string
  score: number
  compositeScore: number
  avgCompositeScore: number
  averageScores: Record<string, number>
  avgScores?: Scores
  evaluations: Evaluation[]
  generatedOutputs?: GeneratedOutput[]
  timestamp: string
  perQuestionScores?: Record<string, Scores>
  weakCriteria?: string[]
  strongCriteria?: string[]
  optimizationModifications?: string[]
  durationSeconds?: number
}

export interface OptimizationResults {
  sessionId: string
  finalPrompt: string
  initialPrompt?: string
  initialScore: number
  finalScore: number
  improvement: number
  iterations: number
  converged: boolean
  convergenceReason?: string
  performanceHistory: number[]
  iterationLogs: IterationLog[]
  totalCost: number
  totalDurationSeconds: number
  config?: OptimizationConfig & {
    generatorModel?: string
    judgeModel?: string
    optimizerModel?: string
    templateId?: string
    questionsCount?: number
  }
}

/* ─── Models ─── */
export interface ModelProfile {
  id: string
  name: string
  provider: string
  description: string
  parameters: string
  contextWindow: number
  costPer1MTokens: number
  avgLatency?: number
  avgScore?: number
  status: 'available' | 'offline'
  strengths: string[]
  context_window: number
  cost_input_per_1k: number
  cost_output_per_1k: number
  avg_latency_seconds: number
  quality_tier: 1 | 2 | 3
  is_available: boolean
}

export interface CostPrediction {
  estimatedInputTokens: number
  estimatedOutputTokens: number
  estimatedCostPerQuestion: number
  prompt_tokens_est: number
  response_tokens_est: number
  total_tokens_est: number
  cost_estimate_usd: number
  latency_estimate_seconds: number
  complexity: 'SIMPLE' | 'MODERATE' | 'COMPLEX' | 'CRITICAL'
  recommended_model: string
  alternative_models: Array<{ model: string; cost: number; latency: number }>
}

/* ─── Prompt Analysis ─── */
export interface PromptAnalysis {
  qualityScore: number
  overallScore: number
  qualityGrade: string
  wordCount?: number
  components: string[]
  issues: string[]
  suggestions: string[]
  scores: Record<string, number>
  flags: string[]
  detectedIntent?: string
}

/* ─── Sessions ─── */
export interface SessionSummary {
  sessionId: string
  startedAt: string
  status: string
  durationSeconds?: number
  questionsCount?: number
  initialScore?: number
  finalScore?: number
  improvement?: number
  totalIterations: number
  converged?: boolean
  model?: string
  totalCost?: number
}

export interface SessionDetail extends SessionSummary {
  finalPrompt?: string
  performanceHistory?: number[]
  iterationLogs?: IterationLog[]
  config?: OptimizationConfig
}

/* ─── Comparison ─── */
export interface ComparisonResult {
  model: string
  answer: string
  explanation: string
  scores: Scores
  compositeScore: number
  metadata: { tokensUsed?: number; latencyMs?: number; costUsd?: number }
}

export interface ComparisonReport {
  results: ComparisonResult[]
  ranking: Array<{ model: string; rank: number; score: number }>
  consistency_score: number
  summary: string
}

/* ─── Router ─── */
export interface RouterStats {
  total_routings: number
  totalRoutings: number
  total_cost: number
  avgScore: number
  avgLatency: number
  modelUsage: Array<{ model: string; count: number }>
  per_model: Record<string, { uses: number; avg_score: number; success_rate: number }>
}

/* ─── Anomaly ─── */
export interface Anomaly {
  type: 'performance_drop' | 'prompt_length_spike' | 'cost_spike' | 'convergence_failure'
  severity: 'low' | 'medium' | 'high'
  timestamp: string
  details: string
  session_id?: string
}

/* ─── WebSocket ─── */
export type WSMessage =
  | { type: 'iteration_start'; data: { iteration: number; total: number } }
  | { type: 'generation_complete'; data: { outputs: GeneratedOutput[]; duration_ms: number } }
  | { type: 'evaluation_complete'; data: { evaluations: Evaluation[]; avg_score: number; scores_by_criterion: Scores } }
  | { type: 'iteration_complete'; data: IterationLog }
  | { type: 'convergence'; data: { final_score: number; iterations: number; reason: string } }
  | { type: 'max_iterations'; data: { final_score: number } }
  | { type: 'rollback'; data: { from_score: number; to_score: number; rolled_back_to_iteration: number } }
  | { type: 'stopped'; data: { reason: string; message?: string } }
  | { type: 'error'; data: { agent: string; message: string; recoverable: boolean } }
  | { type: 'complete'; data: OptimizationResults }
