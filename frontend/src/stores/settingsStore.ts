import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Scores } from '../types'

interface SettingsState {
  generatorModel: string
  judgeModel: string
  optimizerModel: string
  smartRouterEnabled: boolean
  maxIterations: number
  convergenceThreshold: number
  batchSize: number
  weights: Record<string, number>
  temperature: number
  topP: number
  maxTokens: number
  huggingfaceToken: string
  langsmithKey: string
  langsmithEnabled: boolean
  enableSmartRouting: boolean
  enableCostTracking: boolean
  setGeneratorModel: (v: string) => void
  setJudgeModel: (v: string) => void
  setOptimizerModel: (v: string) => void
  setTemperature: (v: number) => void
  setMaxTokens: (v: number) => void
  setMaxIterations: (v: number) => void
  setConvergenceThreshold: (v: number) => void
  setHuggingfaceToken: (v: string) => void
  setLangsmithKey: (v: string) => void
  setEnableSmartRouting: (v: boolean) => void
  setEnableCostTracking: (v: boolean) => void
  resetToDefaults: () => void
}

const defaults = {
  generatorModel: 'Qwen/Qwen2.5-72B-Instruct',
  judgeModel: 'Qwen/Qwen2.5-72B-Instruct',
  optimizerModel: 'Qwen/Qwen2.5-72B-Instruct',
  smartRouterEnabled: true,
  maxIterations: 10,
  convergenceThreshold: 8.5,
  batchSize: 5,
  weights: { correctness: 0.4, clarity: 0.2, reasoning: 0.2, relevance: 0.1, conciseness: 0.1 } as Record<string, number>,
  temperature: 0.7,
  topP: 0.9,
  maxTokens: 500,
  huggingfaceToken: '',
  langsmithKey: '',
  langsmithEnabled: false,
  enableSmartRouting: true,
  enableCostTracking: true,
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...defaults,
      setGeneratorModel: (v) => set({ generatorModel: v }),
      setJudgeModel: (v) => set({ judgeModel: v }),
      setOptimizerModel: (v) => set({ optimizerModel: v }),
      setTemperature: (v) => set({ temperature: v }),
      setMaxTokens: (v) => set({ maxTokens: v }),
      setMaxIterations: (v) => set({ maxIterations: v }),
      setConvergenceThreshold: (v) => set({ convergenceThreshold: v }),
      setHuggingfaceToken: (v) => set({ huggingfaceToken: v }),
      setLangsmithKey: (v) => set({ langsmithKey: v }),
      setEnableSmartRouting: (v) => set({ enableSmartRouting: v }),
      setEnableCostTracking: (v) => set({ enableCostTracking: v }),
      resetToDefaults: () => set(defaults),
    }),
    { name: 'astra-settings' }
  )
)
