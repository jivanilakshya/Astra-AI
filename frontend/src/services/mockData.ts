import type {
  Question, SessionSummary, SessionDetail, IterationLog,
  OptimizationResults, Scores, Evaluation, GeneratedOutput,
  ComparisonResult, ComparisonReport, PromptAnalysis,
  CostPrediction, RouterStats, ModelProfile,
} from '../types'

// ---------- utility helpers ----------
const rid = () => Math.random().toString(36).slice(2, 10)
const rScore = (min = 5, max = 10) => +(min + Math.random() * (max - min)).toFixed(1)
const rDate = (daysAgo: number) => {
  const d = new Date()
  d.setDate(d.getDate() - daysAgo)
  d.setHours(Math.floor(Math.random() * 24), Math.floor(Math.random() * 60))
  return d.toISOString()
}

// ---------- questions ----------
export const mockQuestions: Question[] = [
  { id: '1', question: 'What is photosynthesis?', groundTruth: 'Process by which plants convert light energy into chemical energy', category: 'biology', difficulty: 'easy' },
  { id: '2', question: 'Explain Newton\'s first law of motion.', groundTruth: 'An object at rest stays at rest and an object in motion stays in motion unless acted upon by an external force', category: 'physics', difficulty: 'easy' },
  { id: '3', question: 'Why is the sky blue?', groundTruth: 'Rayleigh scattering causes shorter blue wavelengths of light to scatter more than other colors', category: 'physics', difficulty: 'easy' },
  { id: '4', question: 'Write a Python function to check if a string is a palindrome.', groundTruth: 'def is_palindrome(s): return s == s[::-1]', category: 'code_python', difficulty: 'easy' },
  { id: '5', question: 'Explain the concept of machine learning.', groundTruth: 'A subset of AI where systems learn and improve from experience without being explicitly programmed', category: 'computer_science', difficulty: 'medium' },
  { id: '6', question: 'What is quantum entanglement?', groundTruth: 'A quantum mechanical phenomenon where two particles become linked and instantaneously affect each other regardless of distance', category: 'physics', difficulty: 'hard' },
  { id: '7', question: 'Explain the law of supply and demand.', groundTruth: 'When supply exceeds demand, prices fall; when demand exceeds supply, prices rise', category: 'economics', difficulty: 'medium' },
  { id: '8', question: 'What is the difference between DNA and RNA?', groundTruth: 'DNA is double-stranded with deoxyribose sugar; RNA is single-stranded with ribose sugar', category: 'biology', difficulty: 'medium' },
  { id: '9', question: 'Implement binary search in Python.', groundTruth: 'def binary_search(arr, target): ...', category: 'code_python', difficulty: 'medium' },
  { id: '10', question: 'What causes the seasons on Earth?', groundTruth: 'The tilt of Earth\'s axis (23.5°) relative to its orbital plane around the Sun', category: 'earth_science', difficulty: 'easy' },
  { id: '11', question: 'Explain backpropagation in neural networks.', groundTruth: 'Algorithm that calculates gradients of the loss function with respect to weights by propagating errors backward through the network', category: 'computer_science', difficulty: 'hard' },
  { id: '12', question: 'What is the water cycle?', groundTruth: 'The continuous movement of water through evaporation, condensation, precipitation, and collection', category: 'earth_science', difficulty: 'easy' },
  { id: '13', question: 'Write a debounce function in JavaScript.', groundTruth: 'function debounce(fn, delay) { let timer; return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay) } }', category: 'code_javascript', difficulty: 'medium' },
  { id: '14', question: 'Explain the transformer architecture.', groundTruth: 'A neural network architecture based on self-attention mechanisms that processes input sequences in parallel', category: 'computer_science', difficulty: 'hard' },
  { id: '15', question: 'What are black holes?', groundTruth: 'Regions of spacetime where gravity is so strong that nothing, not even light, can escape', category: 'astronomy', difficulty: 'medium' },
]

// ---------- scores helper ----------
function fakeScores(quality: 'good' | 'mid' | 'low' = 'good'): Scores {
  const base = quality === 'good' ? 7.5 : quality === 'mid' ? 5.5 : 3.5
  return {
    correctness: rScore(base, base + 2.5),
    clarity: rScore(base, base + 2.5),
    reasoning: rScore(base - 0.5, base + 2),
    relevance: rScore(base, base + 2.5),
    conciseness: rScore(base - 0.5, base + 2),
  }
}

function compositeOf(s: Scores) {
  return +(s.correctness * 0.4 + s.clarity * 0.2 + s.reasoning * 0.2 + s.relevance * 0.1 + s.conciseness * 0.1).toFixed(2)
}

// ---------- evaluations ----------
function fakeEvaluation(quality: 'good' | 'mid' | 'low' = 'good'): Evaluation {
  const scores = fakeScores(quality)
  return {
    scores,
    composite_score: compositeOf(scores),
    feedback: {
      correctness_reason: 'The answer demonstrates solid factual understanding with accurate details.',
      clarity_reason: 'Explanation is well-structured and uses accessible language.',
      reasoning_reason: 'Logical flow is coherent with well-supported arguments.',
      relevance_reason: 'Response directly addresses the core question.',
      conciseness_reason: 'Appropriate length without unnecessary verbosity.',
    },
    suggestions: ['Add a concrete example', 'Consider mentioning edge cases', 'Could benefit from a brief summary'],
    flags: quality === 'low' ? ['potential_hallucination'] : [],
    metadata: { judge_model: 'Qwen/Qwen2.5-72B-Instruct', timestamp: new Date().toISOString(), tokens_used: 1200, confidence: 0.88 },
  }
}

// ---------- generated outputs ----------
function fakeOutput(q: Question): GeneratedOutput {
  return {
    question: q.question,
    answer: `This is a well-structured answer to "${q.question}".`,
    explanation: 'The response follows a clear logical progression, starting with the fundamental concept, building toward a comprehensive explanation with supporting details.',
    confidence: +(0.75 + Math.random() * 0.2).toFixed(2),
    metadata: {
      model: 'Qwen/Qwen2.5-72B-Instruct',
      tokens_used: 350,
      input_tokens: 120,
      output_tokens: 230,
      latency_ms: 1200 + Math.random() * 2000,
      timestamp: new Date().toISOString(),
    },
  }
}

// ---------- iteration logs ----------
function buildIterationLogs(count: number): IterationLog[] {
  const logs: IterationLog[] = []
  for (let i = 0; i < count; i++) {
    const progress = i / Math.max(count - 1, 1)
    const quality: 'low' | 'mid' | 'good' = progress < 0.3 ? 'low' : progress < 0.65 ? 'mid' : 'good'
    const scores = fakeScores(quality)
    const composite = compositeOf(scores)
    logs.push({
      iteration: i + 1,
      prompt: `You are an expert educator. Answer clearly and concisely.\n\nQuestion: {question}\n\nProvide a detailed explanation with examples.${i > 2 ? '\nUse step-by-step reasoning.' : ''}${i > 5 ? '\nInclude relevant context and cite key principles.' : ''}`,
      score: composite,
      compositeScore: composite,
      avgCompositeScore: composite,
      averageScores: scores as unknown as Record<string, number>,
      avgScores: scores,
      evaluations: [fakeEvaluation(quality), fakeEvaluation(quality)],
      timestamp: rDate(count - i),
      weakCriteria: Object.entries(scores).filter(([, v]) => v < 6.5).map(([k]) => k),
      strongCriteria: Object.entries(scores).filter(([, v]) => v >= 8).map(([k]) => k),
      optimizationModifications: i > 0 ? ['Added step-by-step instruction', 'Reinforced clarity requirement'] : [],
      durationSeconds: 8 + Math.random() * 15,
    })
  }
  return logs
}

// ---------- sessions ----------
export const mockSessions: SessionSummary[] = [
  { sessionId: 'sess_001', startedAt: rDate(1), status: 'completed', totalIterations: 8, finalScore: 8.72, initialScore: 5.4, improvement: 3.32, converged: true, model: 'Qwen/Qwen2.5-72B-Instruct', totalCost: 0.042, questionsCount: 5, durationSeconds: 180 },
  { sessionId: 'sess_002', startedAt: rDate(2), status: 'completed', totalIterations: 10, finalScore: 7.91, initialScore: 4.8, improvement: 3.11, converged: false, model: 'meta-llama/Meta-Llama-3-8B-Instruct', totalCost: 0.028, questionsCount: 3, durationSeconds: 240 },
  { sessionId: 'sess_003', startedAt: rDate(3), status: 'completed', totalIterations: 6, finalScore: 9.12, initialScore: 6.1, improvement: 3.02, converged: true, model: 'Qwen/Qwen2.5-72B-Instruct', totalCost: 0.035, questionsCount: 5, durationSeconds: 120 },
  { sessionId: 'sess_004', startedAt: rDate(5), status: 'stopped', totalIterations: 4, finalScore: 6.45, initialScore: 4.2, improvement: 2.25, converged: false, model: 'mistralai/Mistral-7B-Instruct-v0.2', totalCost: 0.015, questionsCount: 3, durationSeconds: 90 },
  { sessionId: 'sess_005', startedAt: rDate(7), status: 'completed', totalIterations: 7, finalScore: 8.35, initialScore: 5.8, improvement: 2.55, converged: true, model: 'meta-llama/Meta-Llama-3-8B-Instruct', totalCost: 0.031, questionsCount: 4, durationSeconds: 160 },
  { sessionId: 'sess_006', startedAt: rDate(10), status: 'completed', totalIterations: 9, finalScore: 8.88, initialScore: 5.1, improvement: 3.78, converged: true, model: 'Qwen/Qwen2.5-72B-Instruct', totalCost: 0.048, questionsCount: 5, durationSeconds: 200 },
  { sessionId: 'sess_007', startedAt: rDate(12), status: 'error', totalIterations: 2, finalScore: 3.2, initialScore: 3.2, improvement: 0, converged: false, model: 'meta-llama/Llama-3.2-1B-Instruct', totalCost: 0.004, questionsCount: 2, durationSeconds: 25 },
  { sessionId: 'sess_008', startedAt: rDate(14), status: 'completed', totalIterations: 8, finalScore: 8.55, initialScore: 5.5, improvement: 3.05, converged: true, model: 'Qwen/Qwen2.5-7B-Instruct', totalCost: 0.022, questionsCount: 4, durationSeconds: 170 },
]

export function mockSessionDetail(sessionId: string): SessionDetail {
  const summary = mockSessions.find(s => s.sessionId === sessionId) ?? mockSessions[0]
  const logs = buildIterationLogs(summary.totalIterations)
  return {
    ...summary,
    finalPrompt: `You are an expert educator with deep domain knowledge. Your goal is to provide accurate, clear, and well-reasoned answers.\n\nQuestion: {question}\n\nRequirements:\n- Provide a step-by-step explanation\n- Use precise, accessible language\n- Include relevant examples when helpful\n- Be concise but thorough\n- Cite fundamental principles\n\nAnswer:`,
    performanceHistory: logs.map(l => l.compositeScore),
    iterationLogs: logs,
    config: {
      maxIterations: 10,
      convergenceThreshold: 8.5,
      generatorModel: summary.model,
      judgeModel: 'Qwen/Qwen2.5-72B-Instruct',
      optimizerModel: 'Qwen/Qwen2.5-72B-Instruct',
      temperature: 0.7,
      batchSize: 5,
    },
  }
}

// ---------- optimization results ----------
export function mockOptimizationResults(): OptimizationResults {
  const logs = buildIterationLogs(8)
  return {
    sessionId: 'sess_live_' + rid(),
    finalPrompt: 'You are an expert educator. Provide clear, step-by-step answers with examples.\n\nQuestion: {question}\n\nAnswer:',
    initialScore: logs[0].compositeScore,
    finalScore: logs[logs.length - 1].compositeScore,
    improvement: +(logs[logs.length - 1].compositeScore - logs[0].compositeScore).toFixed(2),
    iterations: logs.length,
    converged: true,
    convergenceReason: 'Score exceeded convergence threshold of 8.5',
    performanceHistory: logs.map(l => l.compositeScore),
    iterationLogs: logs,
    totalCost: 0.038,
    totalDurationSeconds: 145,
    config: { maxIterations: 10, convergenceThreshold: 8.5 },
  }
}

// ---------- comparison ----------
export function mockComparisonReport(prompt: string, models: string[]): ComparisonReport {
  const results: ComparisonResult[] = models.map(model => {
    const scores = fakeScores('good')
    return {
      model,
      answer: `Comprehensive response to: "${prompt.slice(0, 60)}..."`,
      explanation: 'Detailed reasoning with step-by-step analysis and supporting evidence.',
      scores,
      compositeScore: compositeOf(scores),
      metadata: { tokensUsed: 300 + Math.floor(Math.random() * 200), latencyMs: 1000 + Math.random() * 3000, costUsd: 0.002 + Math.random() * 0.01 },
    }
  })
  results.sort((a, b) => b.compositeScore - a.compositeScore)
  return {
    results,
    ranking: results.map((r, i) => ({ model: r.model, rank: i + 1, score: r.compositeScore })),
    consistency_score: +(0.6 + Math.random() * 0.35).toFixed(2),
    summary: `${results[0].model} performed best with a composite score of ${results[0].compositeScore}. Cross-model consistency is ${results.length > 2 ? 'moderate' : 'high'}.`,
  }
}

// ---------- prompt analysis ----------
export function mockPromptAnalysis(prompt: string): PromptAnalysis {
  const wc = prompt.split(/\s+/).length
  const hasQ = prompt.includes('?') || prompt.includes('{question}')
  const score = Math.min(10, Math.max(2, wc > 5 ? 5 + (hasQ ? 2 : 0) + Math.min(wc / 10, 3) : 3))
  const grade = score >= 8 ? 'A' : score >= 6.5 ? 'B' : score >= 5 ? 'C' : score >= 3.5 ? 'D' : 'F'
  return {
    qualityScore: +score.toFixed(1),
    overallScore: +score.toFixed(1),
    qualityGrade: grade as PromptAnalysis['qualityGrade'],
    wordCount: wc,
    components: ['instruction', ...(hasQ ? ['placeholder'] : []), ...(wc > 15 ? ['constraints'] : [])],
    issues: [
      ...(wc < 10 ? ['Prompt is too short — consider adding more context'] : []),
      ...(!hasQ ? ['Missing {question} placeholder'] : []),
      ...(wc > 100 ? ['Prompt is verbose — consider trimming'] : []),
    ],
    suggestions: [
      'Add step-by-step reasoning instruction',
      'Include output format specification',
      'Add domain-specific context',
      'Consider adding few-shot examples',
    ],
    scores: {
      clarity: rScore(score - 1, score + 1),
      specificity: rScore(score - 1.5, score + 0.5),
      structure: rScore(score - 0.5, score + 1),
      completeness: rScore(score - 1, score + 1),
    },
    flags: [
      ...(wc < 10 ? ['too_short'] : []),
      ...(!hasQ ? ['missing_placeholder'] : []),
    ],
    detectedIntent: prompt.toLowerCase().includes('code') ? 'code' : prompt.toLowerCase().includes('explain') ? 'explanation' : 'general',
  }
}

// ---------- cost prediction ----------
export function mockCostPrediction(prompt: string): CostPrediction {
  const tokens = prompt.split(/\s+/).length * 1.3
  return {
    prompt_tokens_est: Math.round(tokens),
    response_tokens_est: Math.round(tokens * 2.5),
    total_tokens_est: Math.round(tokens * 3.5),
    cost_estimate_usd: +(tokens * 3.5 * 0.000003).toFixed(6),
    estimatedInputTokens: Math.round(tokens),
    estimatedOutputTokens: Math.round(tokens * 2.5),
    estimatedCostPerQuestion: +(tokens * 3.5 * 0.000003).toFixed(6),
    latency_estimate_seconds: 1.5 + Math.random() * 3,
    complexity: tokens < 50 ? 'SIMPLE' : tokens < 150 ? 'MODERATE' : 'COMPLEX',
    recommended_model: 'Qwen/Qwen2.5-72B-Instruct',
    alternative_models: [
      { model: 'meta-llama/Meta-Llama-3-8B-Instruct', cost: +(tokens * 3.5 * 0.000001).toFixed(6), latency: 1.2 },
      { model: 'mistralai/Mistral-7B-Instruct-v0.2', cost: +(tokens * 3.5 * 0.0000008).toFixed(6), latency: 1.0 },
    ],
  }
}

// ---------- router stats ----------
export const mockRouterStats: RouterStats = {
  total_routings: 247,
  totalRoutings: 247,
  total_cost: 0.183,
  avgScore: 7.7,
  avgLatency: 1940,
  modelUsage: [
    { model: 'Qwen/Qwen2.5-72B-Instruct', count: 89 },
    { model: 'meta-llama/Meta-Llama-3-8B-Instruct', count: 72 },
    { model: 'mistralai/Mistral-7B-Instruct-v0.2', count: 48 },
    { model: 'Qwen/Qwen2.5-7B-Instruct', count: 25 },
    { model: 'meta-llama/Llama-3.2-3B-Instruct', count: 13 },
  ],
  per_model: {
    'Qwen/Qwen2.5-72B-Instruct': { uses: 89, avg_score: 8.4, success_rate: 0.96 },
    'meta-llama/Meta-Llama-3-8B-Instruct': { uses: 72, avg_score: 7.6, success_rate: 0.92 },
    'mistralai/Mistral-7B-Instruct-v0.2': { uses: 48, avg_score: 7.2, success_rate: 0.88 },
    'Qwen/Qwen2.5-7B-Instruct': { uses: 25, avg_score: 7.8, success_rate: 0.91 },
    'meta-llama/Llama-3.2-3B-Instruct': { uses: 13, avg_score: 6.5, success_rate: 0.82 },
  },
}

// ---------- model profiles ----------
export const mockModels: ModelProfile[] = [
  { id: 'Qwen/Qwen2.5-72B-Instruct', name: 'Qwen 2.5 72B Instruct', provider: 'huggingface', description: 'Large-scale instruction-tuned model with strong reasoning and multilingual capabilities', parameters: '72B', contextWindow: 32768, costPer1MTokens: 3.0, avgLatency: 3200, avgScore: 8.4, status: 'available', strengths: ['Reasoning', 'Code', 'Multilingual'], context_window: 32768, cost_input_per_1k: 0.003, cost_output_per_1k: 0.015, avg_latency_seconds: 3.2, quality_tier: 1, is_available: true },
  { id: 'meta-llama/Meta-Llama-3-8B-Instruct', name: 'Llama 3 8B Instruct', provider: 'huggingface', description: 'Efficient medium-size model with excellent instruction following', parameters: '8B', contextWindow: 8192, costPer1MTokens: 1.0, avgLatency: 1800, avgScore: 7.6, status: 'available', strengths: ['Speed', 'General QA', 'Instruction following'], context_window: 8192, cost_input_per_1k: 0.001, cost_output_per_1k: 0.005, avg_latency_seconds: 1.8, quality_tier: 2, is_available: true },
  { id: 'mistralai/Mistral-7B-Instruct-v0.2', name: 'Mistral 7B Instruct v0.2', provider: 'huggingface', description: 'Fast and cost-effective model with good code generation', parameters: '7B', contextWindow: 32768, costPer1MTokens: 0.8, avgLatency: 1500, avgScore: 7.2, status: 'available', strengths: ['Cost-effective', 'Fast', 'Code'], context_window: 32768, cost_input_per_1k: 0.0008, cost_output_per_1k: 0.004, avg_latency_seconds: 1.5, quality_tier: 2, is_available: true },
  { id: 'Qwen/Qwen2.5-Coder-32B-Instruct', name: 'Qwen 2.5 Coder 32B', provider: 'huggingface', description: 'Specialized code model with strong debugging and refactoring', parameters: '32B', contextWindow: 32768, costPer1MTokens: 2.0, avgLatency: 2500, avgScore: 8.1, status: 'available', strengths: ['Code generation', 'Debugging', 'Refactoring'], context_window: 32768, cost_input_per_1k: 0.002, cost_output_per_1k: 0.01, avg_latency_seconds: 2.5, quality_tier: 1, is_available: true },
  { id: 'Qwen/Qwen2.5-7B-Instruct', name: 'Qwen 2.5 7B Instruct', provider: 'huggingface', description: 'Balanced model offering good quality at lower cost', parameters: '7B', contextWindow: 32768, costPer1MTokens: 0.6, avgLatency: 1400, avgScore: 7.8, status: 'available', strengths: ['Balanced', 'Efficient', 'Multilingual'], context_window: 32768, cost_input_per_1k: 0.0006, cost_output_per_1k: 0.003, avg_latency_seconds: 1.4, quality_tier: 2, is_available: true },
  { id: 'meta-llama/Llama-3.2-3B-Instruct', name: 'Llama 3.2 3B Instruct', provider: 'huggingface', description: 'Ultra-fast lightweight model for simple tasks', parameters: '3B', contextWindow: 8192, costPer1MTokens: 0.3, avgLatency: 800, avgScore: 6.5, status: 'available', strengths: ['Ultra-fast', 'Lightweight', 'Low cost'], context_window: 8192, cost_input_per_1k: 0.0003, cost_output_per_1k: 0.0015, avg_latency_seconds: 0.8, quality_tier: 3, is_available: true },
  { id: 'meta-llama/Llama-3.2-1B-Instruct', name: 'Llama 3.2 1B Instruct', provider: 'huggingface', description: 'Smallest model for edge deployment and testing', parameters: '1B', contextWindow: 8192, costPer1MTokens: 0.1, avgLatency: 500, avgScore: 5.2, status: 'offline', strengths: ['Fastest', 'Cheapest', 'Edge deployment'], context_window: 8192, cost_input_per_1k: 0.0001, cost_output_per_1k: 0.0005, avg_latency_seconds: 0.5, quality_tier: 3, is_available: false },
]

// ---------- ask question ----------
export function mockAskQuestion(question: string, prompt?: string): GeneratedOutput {
  return {
    question,
    answer: `Based on the analysis of "${question.slice(0, 50)}", the answer involves understanding the fundamental principles and their practical applications in real-world scenarios.`,
    explanation: `To address this question comprehensively:\n\n1. **Core Concept**: The fundamental principle at work here relates to the underlying mechanisms that govern this phenomenon.\n\n2. **Key Details**: Several important factors contribute to the outcome, including both primary drivers and secondary influences.\n\n3. **Practical Implications**: Understanding this concept has real-world applications in multiple domains.\n\n${prompt ? `\nNote: This response was generated using the following prompt template for consistency.` : ''}`,
    confidence: 0.87,
    metadata: {
      model: 'Qwen/Qwen2.5-72B-Instruct',
      tokens_used: 420,
      input_tokens: 150,
      output_tokens: 270,
      latency_ms: 2340,
      timestamp: new Date().toISOString(),
    },
  }
}

// ---------- cost tracking ----------
export interface DailyCostRecord {
  date: string
  totalCost: number
  generatorCost: number
  judgeCost: number
  optimizerCost: number
  tokensUsed: number
  requests: number
}

export function mockCostHistory(): DailyCostRecord[] {
  const records: DailyCostRecord[] = []
  for (let d = 30; d >= 0; d--) {
    const genCost = +(0.002 + Math.random() * 0.015).toFixed(4)
    const judgeCost = +(0.003 + Math.random() * 0.012).toFixed(4)
    const optCost = +(0.001 + Math.random() * 0.008).toFixed(4)
    const requests = Math.floor(Math.random() * 12) + 3
    records.push({
      date: rDate(d),
      totalCost: +(genCost + judgeCost + optCost).toFixed(4),
      generatorCost: genCost,
      judgeCost,
      optimizerCost: optCost,
      tokensUsed: (200 + Math.floor(Math.random() * 1200)) * requests,
      requests,
    })
  }
  return records
}

// ---------- debug log ----------
export interface DebugEntry {
  timestamp: string
  agent: string
  type: 'prompt' | 'response' | 'chain_of_thought' | 'metric' | 'debug'
  label: string
  data: string
}

export function mockDebugLog(): DebugEntry[] {
  return [
    { timestamp: rDate(0), agent: 'generator', type: 'prompt', label: 'System Prompt', data: 'You are an expert educator providing clear, accurate answers with detailed explanations.' },
    { timestamp: rDate(0), agent: 'generator', type: 'response', label: 'Raw Response', data: 'Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize nutrients from carbon dioxide and water...' },
    { timestamp: rDate(0), agent: 'judge', type: 'prompt', label: 'Evaluation Prompt', data: 'Evaluate the following AI-generated response on 5 criteria...' },
    { timestamp: rDate(0), agent: 'judge', type: 'chain_of_thought', label: 'CoT', data: 'The answer correctly identifies photosynthesis as a light-dependent process. The explanation is clear but could include more detail about the light and dark reactions...' },
    { timestamp: rDate(0), agent: 'optimizer', type: 'metric', label: 'Composite Score', data: '7.84' },
    { timestamp: rDate(0), agent: 'optimizer', type: 'response', label: 'Optimization', data: 'Added step-by-step reasoning instruction. Reinforced requirement for concrete examples.' },
  ]
}
