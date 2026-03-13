import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Suspense, lazy } from 'react'
import AppShell from './components/layout/AppShell'

const LandingPage = lazy(() => import('./pages/LandingPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const OptimizationPage = lazy(() => import('./pages/OptimizationPage'))
const AskQuestionPage = lazy(() => import('./pages/AskQuestionPage'))
const ComparisonPage = lazy(() => import('./pages/ComparisonPage'))
const PromptAnalyzerPage = lazy(() => import('./pages/PromptAnalyzerPage'))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const QuestionBankPage = lazy(() => import('./pages/QuestionBankPage'))
const SessionDetailPage = lazy(() => import('./pages/SessionDetailPage'))
const CostTrackingPage = lazy(() => import('./pages/CostTrackingPage'))
const ModelsPage = lazy(() => import('./pages/ModelsPage'))

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false } },
})

function Loader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="flex gap-1.5">
        {[0, 1, 2].map(i => (
          <div key={i} className="w-1.5 h-1.5 rounded-full bg-text-muted animate-pulse-soft" style={{ animationDelay: `${i * 0.2}s` }} />
        ))}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Suspense fallback={<Loader />}><LandingPage /></Suspense>} />
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<Suspense fallback={<Loader />}><DashboardPage /></Suspense>} />
            <Route path="/optimize" element={<Suspense fallback={<Loader />}><OptimizationPage /></Suspense>} />
            <Route path="/ask" element={<Suspense fallback={<Loader />}><AskQuestionPage /></Suspense>} />
            <Route path="/compare" element={<Suspense fallback={<Loader />}><ComparisonPage /></Suspense>} />
            <Route path="/prompt-analyzer" element={<Suspense fallback={<Loader />}><PromptAnalyzerPage /></Suspense>} />
            <Route path="/analytics" element={<Suspense fallback={<Loader />}><AnalyticsPage /></Suspense>} />
            <Route path="/questions" element={<Suspense fallback={<Loader />}><QuestionBankPage /></Suspense>} />
            <Route path="/settings" element={<Suspense fallback={<Loader />}><SettingsPage /></Suspense>} />
            <Route path="/sessions/:sessionId" element={<Suspense fallback={<Loader />}><SessionDetailPage /></Suspense>} />
            <Route path="/costs" element={<Suspense fallback={<Loader />}><CostTrackingPage /></Suspense>} />
            <Route path="/models" element={<Suspense fallback={<Loader />}><ModelsPage /></Suspense>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
