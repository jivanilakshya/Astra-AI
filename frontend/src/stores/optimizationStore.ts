import { create } from 'zustand'
import type { IterationLog, OptimizationResults, OptimizationConfig } from '../types'

interface OptimizationState {
  isRunning: boolean
  sessionId: string | null
  currentIteration: number
  totalIterations: number
  currentScore: number
  status: string
  statusLabel: string
  iterations: IterationLog[]
  performanceHistory: number[]
  config: OptimizationConfig | null
  results: OptimizationResults | null
  /* actions */
  start: (sessionId: string, config: OptimizationConfig) => void
  addIteration: (log: IterationLog) => void
  setStatus: (status: string, label: string) => void
  setResults: (results: OptimizationResults) => void
  reset: () => void
}

export const useOptimizationStore = create<OptimizationState>()((set) => ({
  isRunning: false,
  sessionId: null,
  currentIteration: 0,
  totalIterations: 10,
  currentScore: 0,
  status: 'idle',
  statusLabel: 'Ready',
  iterations: [],
  performanceHistory: [],
  config: null,
  results: null,
  start: (sessionId, config) => set({
    isRunning: true, sessionId, config,
    currentIteration: 0, currentScore: 0,
    iterations: [], performanceHistory: [],
    results: null, status: 'running', statusLabel: 'Initializing...',
    totalIterations: config.maxIterations ?? 10,
  }),
  addIteration: (log) => set(s => ({
    currentIteration: log.iteration,
    currentScore: log.compositeScore,
    iterations: [log, ...s.iterations],
    performanceHistory: [...s.performanceHistory, log.compositeScore],
  })),
  setStatus: (status, label) => set({ status, statusLabel: label }),
  setResults: (results) => set({ isRunning: false, results, status: 'complete', statusLabel: 'Complete' }),
  reset: () => set({
    isRunning: false, sessionId: null, currentIteration: 0, totalIterations: 10,
    currentScore: 0, status: 'idle', statusLabel: 'Ready',
    iterations: [], performanceHistory: [], config: null, results: null,
  }),
}))
