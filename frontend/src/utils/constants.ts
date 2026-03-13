export const AVAILABLE_MODELS = [
  { id: 'Qwen/Qwen2.5-72B-Instruct', label: 'Qwen 2.5 72B', tier: 'premium' },
  { id: 'Qwen/Qwen2.5-Coder-32B-Instruct', label: 'Qwen 2.5 Coder 32B', tier: 'premium' },
  { id: 'meta-llama/Meta-Llama-3-8B-Instruct', label: 'Llama 3 8B', tier: 'recommended' },
  { id: 'mistralai/Mistral-7B-Instruct-v0.2', label: 'Mistral 7B v0.2', tier: 'recommended' },
  { id: 'Qwen/Qwen2.5-7B-Instruct', label: 'Qwen 2.5 7B', tier: 'good' },
  { id: 'meta-llama/Llama-3.2-3B-Instruct', label: 'Llama 3.2 3B', tier: 'good' },
  { id: 'meta-llama/Llama-3.2-1B-Instruct', label: 'Llama 3.2 1B', tier: 'lightweight' },
] as const

export const CRITERIA_WEIGHTS = {
  correctness: 0.4,
  clarity: 0.2,
  reasoning: 0.2,
  relevance: 0.1,
  conciseness: 0.1,
} as const

export const CRITERIA_LABELS: Record<string, string> = {
  correctness: 'Correctness',
  clarity: 'Clarity',
  reasoning: 'Reasoning',
  relevance: 'Relevance',
  conciseness: 'Conciseness',
}

export const CATEGORIES = [
  'biology', 'physics', 'chemistry', 'earth_science', 'astronomy',
  'computer_science', 'mathematics', 'economics', 'history', 'logic',
  'code_python', 'code_javascript', 'code_java', 'code_cpp', 'code_sql',
] as const

export const STATUS_LABELS: Record<string, { label: string; variant: string }> = {
  completed: { label: 'Completed', variant: 'success' },
  running: { label: 'Running', variant: 'accent' },
  stopped: { label: 'Stopped', variant: 'warn' },
  error: { label: 'Error', variant: 'danger' },
  idle: { label: 'Idle', variant: 'muted' },
}
