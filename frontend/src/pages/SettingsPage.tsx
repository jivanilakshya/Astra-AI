import { useState } from 'react'
import { motion } from 'framer-motion'
import { Settings, Save, RotateCcw } from 'lucide-react'
import Card from '../components/ui/Card'
import Tabs from '../components/ui/Tabs'
import Toggle from '../components/ui/Toggle'
import { useSettingsStore } from '../stores/settingsStore'
import { useAppStore } from '../stores/appStore'

const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }

const MODEL_OPTIONS = [
  'mistralai/Mistral-7B-Instruct-v0.3',
  'google/gemma-2-2b-it',
  'microsoft/Phi-3-mini-4k-instruct',
  'meta-llama/Llama-3.2-3B-Instruct',
  'Qwen/Qwen2.5-3B-Instruct',
  'HuggingFaceTB/SmolLM2-1.7B-Instruct',
  'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
]

export default function SettingsPage() {
  const settings = useSettingsStore()
  const { isDark, toggleTheme } = useAppStore()
  const [tab, setTab] = useState('models')
  const [saved, setSaved] = useState(false)

  const showSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000) }

  const tabs = [
    { key: 'models', label: 'Models' },
    { key: 'params', label: 'Parameters' },
    { key: 'keys', label: 'API Keys' },
    { key: 'general', label: 'General' },
  ]

  return (
    <div className="page-container">
      <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.08 } } }}>
        <motion.div variants={fadeUp} className="flex items-center justify-between mb-8">
          <div>
            <h1 className="page-title">Settings</h1>
            <p className="text-text-secondary text-sm mt-1">Configure models, parameters, and preferences</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => { settings.resetToDefaults(); showSave() }} className="btn-ghost">
              <RotateCcw size={14} /> Reset
            </button>
          </div>
        </motion.div>

        <motion.div variants={fadeUp} className="mb-6">
          <Tabs tabs={tabs} active={tab} onChange={setTab} />
        </motion.div>

        {/* Models Tab */}
        {tab === 'models' && (
          <motion.div variants={fadeUp}>
            <Card>
              <h2 className="section-title mb-4">Model Selection</h2>
              <div className="space-y-4">
                <Field label="Generator Model">
                  <select value={settings.generatorModel} onChange={e => { settings.setGeneratorModel(e.target.value); showSave() }} className="input-base w-full">
                    {MODEL_OPTIONS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </Field>

                <Field label="Judge Model">
                  <select value={settings.judgeModel} onChange={e => { settings.setJudgeModel(e.target.value); showSave() }} className="input-base w-full">
                    {MODEL_OPTIONS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </Field>

                <Field label="Optimizer Model">
                  <select value={settings.optimizerModel} onChange={e => { settings.setOptimizerModel(e.target.value); showSave() }} className="input-base w-full">
                    {MODEL_OPTIONS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </Field>
              </div>
            </Card>
          </motion.div>
        )}

        {/* Parameters Tab */}
        {tab === 'params' && (
          <motion.div variants={fadeUp}>
            <Card>
              <h2 className="section-title mb-4">Generation Parameters</h2>
              <div className="grid md:grid-cols-2 gap-4">
                <Field label="Temperature">
                  <div className="flex items-center gap-3">
                    <input type="range" min={0} max={1} step={0.1} value={settings.temperature} onChange={e => { settings.setTemperature(+e.target.value); showSave() }} className="flex-1 accent-accent" />
                    <span className="font-mono w-10 text-right text-text-primary">{settings.temperature}</span>
                  </div>
                </Field>

                <Field label="Max Tokens">
                  <input type="number" value={settings.maxTokens} onChange={e => { settings.setMaxTokens(+e.target.value); showSave() }} className="input-base w-full" />
                </Field>

                <Field label="Max Iterations">
                  <div className="flex items-center gap-3">
                    <input type="range" min={3} max={15} value={settings.maxIterations} onChange={e => { settings.setMaxIterations(+e.target.value); showSave() }} className="flex-1 accent-accent" />
                    <span className="font-mono w-10 text-right text-text-primary">{settings.maxIterations}</span>
                  </div>
                </Field>

                <Field label="Convergence Threshold">
                  <div className="flex items-center gap-3">
                    <input type="range" min={5} max={10} step={0.5} value={settings.convergenceThreshold} onChange={e => { settings.setConvergenceThreshold(+e.target.value); showSave() }} className="flex-1 accent-accent" />
                    <span className="font-mono w-10 text-right text-text-primary">{settings.convergenceThreshold}</span>
                  </div>
                </Field>
              </div>
            </Card>
          </motion.div>
        )}

        {/* API Keys Tab */}
        {tab === 'keys' && (
          <motion.div variants={fadeUp}>
            <Card>
              <h2 className="section-title mb-4">API Keys</h2>
              <div className="space-y-4">
                <Field label="HuggingFace Token">
                  <input
                    type="password"
                    value={settings.huggingfaceToken}
                    onChange={e => { settings.setHuggingfaceToken(e.target.value); showSave() }}
                    className="input-base w-full font-mono"
                    placeholder="hf_..."
                  />
                </Field>
                <Field label="LangSmith API Key">
                  <input
                    type="password"
                    value={settings.langsmithKey}
                    onChange={e => { settings.setLangsmithKey(e.target.value); showSave() }}
                    className="input-base w-full font-mono"
                    placeholder="ls_..."
                  />
                </Field>
                <p className="text-xs text-text-muted">Keys are stored locally in your browser and never sent to external servers.</p>
              </div>
            </Card>
          </motion.div>
        )}

        {/* General Tab */}
        {tab === 'general' && (
          <motion.div variants={fadeUp}>
            <Card>
              <h2 className="section-title mb-4">Preferences</h2>
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-text-primary">Dark Mode</p>
                    <p className="text-xs text-text-muted mt-0.5">Toggle between light and dark themes</p>
                  </div>
                  <Toggle checked={isDark} onChange={toggleTheme} />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-text-primary">Smart Routing</p>
                    <p className="text-xs text-text-muted mt-0.5">Automatically select the best model for each task</p>
                  </div>
                  <Toggle checked={settings.enableSmartRouting} onChange={() => { settings.setEnableSmartRouting(!settings.enableSmartRouting); showSave() }} />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-text-primary">Cost Tracking</p>
                    <p className="text-xs text-text-muted mt-0.5">Monitor and log API costs</p>
                  </div>
                  <Toggle checked={settings.enableCostTracking} onChange={() => { settings.setEnableCostTracking(!settings.enableCostTracking); showSave() }} />
                </div>
              </div>
            </Card>
          </motion.div>
        )}

        {/* Save indicator */}
        {saved && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="fixed bottom-6 right-6 bg-accent text-accent-contrast px-4 py-2 rounded-button text-sm font-mono flex items-center gap-2"
          >
            <Save size={14} /> Saved
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-xs font-mono text-text-muted uppercase tracking-wide block mb-1.5">{label}</label>
      {children}
    </div>
  )
}
