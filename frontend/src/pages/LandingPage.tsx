import { Link } from 'react-router-dom'
import { motion, useInView, useScroll, useTransform, AnimatePresence } from 'framer-motion'
import { useRef, useState, useEffect } from 'react'
import {
  ArrowRight, Zap, BarChart3, GitCompare, Brain, Target,
  MessageSquare, BookOpen, DollarSign, ArrowUpRight,
  CheckCircle2, TrendingUp, Sparkles, Layers, ChevronDown,
  Play, Shield
} from 'lucide-react'

/* ── animation config ── */
const ease = [0.22, 1, 0.36, 1] as const
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.1, delayChildren: 0.1 } } }
const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  show: { opacity: 1, y: 0, transition: { duration: 0.8, ease } },
}
const fadeUpFast = {
  hidden: { opacity: 0, y: 20 },
  show: (i: number) => ({ opacity: 1, y: 0, transition: { duration: 0.6, ease, delay: i * 0.08 } }),
}
const scaleUp = {
  hidden: { opacity: 0, scale: 0.88, y: 40 },
  show: { opacity: 1, scale: 1, y: 0, transition: { duration: 1, ease } },
}

/* ── data ── */
const features = [
  {
    icon: Brain, title: 'Self-Improving Prompts',
    desc: 'Your prompts get better automatically. The system learns from every answer and rewrites prompts to be more effective.',
    to: '/optimize', label: 'Start Optimizing', gradient: 'from-violet-500/10 to-transparent',
  },
  {
    icon: Target, title: 'Quality Scoring',
    desc: 'Every answer is scored on 5 criteria — correctness, clarity, reasoning, relevance, and conciseness.',
    to: '/analytics', label: 'View Analytics', gradient: 'from-emerald-500/10 to-transparent',
  },
  {
    icon: GitCompare, title: 'Model Comparison',
    desc: 'Run the same questions across multiple AI models and see which one performs best, side by side.',
    to: '/compare', label: 'Compare Models', gradient: 'from-blue-500/10 to-transparent',
  },
  {
    icon: Zap, title: 'Smart Routing',
    desc: 'Automatically picks the best AI model for each question type based on performance and cost.',
    to: '/models', label: 'Explore Models', gradient: 'from-amber-500/10 to-transparent',
  },
  {
    icon: BarChart3, title: 'Deep Analytics',
    desc: 'Track improvement over time with interactive charts. See score trends, cost breakdowns, and history.',
    to: '/analytics', label: 'See Analytics', gradient: 'from-rose-500/10 to-transparent',
  },
  {
    icon: DollarSign, title: 'Cost Tracking',
    desc: 'Monitor API spending in real time. Know exactly how much each model and iteration costs.',
    to: '/costs', label: 'Track Costs', gradient: 'from-cyan-500/10 to-transparent',
  },
]

const steps = [
  { num: '01', title: 'Ask a Question', desc: 'Enter any question. The Generator Agent creates a detailed answer using your prompt template.', icon: MessageSquare, color: 'bg-violet-500' },
  { num: '02', title: 'Judge the Answer', desc: 'The Judge Agent scores the answer on 5 quality criteria with specific, actionable feedback.', icon: CheckCircle2, color: 'bg-emerald-500' },
  { num: '03', title: 'Optimize the Prompt', desc: 'The Optimizer Agent rewrites your prompt based on feedback, fixing weaknesses while keeping strengths.', icon: TrendingUp, color: 'bg-blue-500' },
  { num: '04', title: 'Repeat & Improve', desc: 'This loop runs automatically until your prompt converges on the best possible score.', icon: Sparkles, color: 'bg-amber-500' },
]

const quickLinks = [
  { to: '/ask', icon: MessageSquare, label: 'Ask a Question', desc: 'Get instant answers' },
  { to: '/questions', icon: BookOpen, label: 'Question Bank', desc: 'Manage Q&A sets' },
  { to: '/optimize', icon: Zap, label: 'Run Optimization', desc: 'Improve prompts' },
  { to: '/compare', icon: GitCompare, label: 'Compare Models', desc: 'Benchmark models' },
]

/* ── animated counter ── */
function Counter({ value, suffix = '' }: { value: string; suffix?: string }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })
  return (
    <motion.span ref={ref} className="text-4xl lg:text-5xl font-display font-bold text-text-primary tabular-nums">
      {inView ? (
        <motion.span
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease }}
        >
          {value}{suffix}
        </motion.span>
      ) : '—'}
    </motion.span>
  )
}

/* ── section with scroll-reveal ── */
function Section({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })
  return (
    <motion.section
      ref={ref}
      initial="hidden"
      animate={inView ? 'show' : 'hidden'}
      variants={stagger}
      className={className}
    >
      {children}
    </motion.section>
  )
}

/* ── Logo ── */
function Logo({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="64" height="64" rx="16" fill="var(--color-accent)" />
      <ellipse cx="32" cy="32" rx="22" ry="10" fill="none" stroke="var(--color-accent-contrast)" strokeWidth="0.8" opacity="0.2" transform="rotate(-25 32 32)" />
      <path d="M32 14L20 50h5.5l2.8-8h11.4l2.8 8H48L32 14z" fill="var(--color-accent-contrast)" />
      <path d="M29.6 38L32 29l2.4 9h-4.8z" fill="var(--color-accent)" />
      <circle cx="32" cy="11" r="1.5" fill="var(--color-accent-contrast)" />
    </svg>
  )
}

/* ── Animated agent loop ── */
function AgentLoopDiagram() {
  const [activeNode, setActiveNode] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setActiveNode(n => (n + 1) % 3), 2000)
    return () => clearInterval(t)
  }, [])

  const agents = [
    { label: 'Generator', sublabel: 'Creates answers', x: 200, y: 50, color: '#8B5CF6' },
    { label: 'Judge', sublabel: 'Scores quality', x: 360, y: 185, color: '#10B981' },
    { label: 'Optimizer', sublabel: 'Improves prompts', x: 40, y: 185, color: '#3B82F6' },
  ]

  return (
    <div className="relative w-full max-w-[460px] mx-auto aspect-[23/14]">
      <svg viewBox="0 0 400 245" className="w-full h-full" fill="none">
        {/* Dashed orbit */}
        <motion.ellipse
          cx="200" cy="140" rx="160" ry="78"
          stroke="var(--color-border)" strokeWidth="1" strokeDasharray="5 5"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 0.6 }}
          transition={{ duration: 2, ease }}
        />

        {/* Directional arrows */}
        <defs>
          <marker id="arr" markerWidth="7" markerHeight="5" refX="7" refY="2.5" orient="auto">
            <path d="M 0 0 L 7 2.5 L 0 5 z" fill="var(--color-text-muted)" opacity="0.5" />
          </marker>
        </defs>
        <motion.path d="M 260 63 Q 320 100 347 158" stroke="var(--color-text-muted)" strokeWidth="1" markerEnd="url(#arr)"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1.2, duration: 0.6, ease }} opacity={0.4} fill="none" />
        <motion.path d="M 330 205 Q 200 235 80 205" stroke="var(--color-text-muted)" strokeWidth="1" markerEnd="url(#arr)"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1.5, duration: 0.6, ease }} opacity={0.4} fill="none" />
        <motion.path d="M 60 162 Q 90 100 155 65" stroke="var(--color-text-muted)" strokeWidth="1" markerEnd="url(#arr)"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1.8, duration: 0.6, ease }} opacity={0.4} fill="none" />

        {/* Agent nodes */}
        {agents.map((a, i) => (
          <motion.g key={a.label}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 + i * 0.2, type: 'spring', stiffness: 180, damping: 18 }}
          >
            {/* Glow ring on active */}
            {activeNode === i && (
              <motion.rect
                x={a.x - 56} y={a.y - 25} width="112" height="50" rx="14"
                fill="none" stroke={a.color} strokeWidth="2" opacity={0.3}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: [0, 0.4, 0], scale: [0.95, 1.05, 1.1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
            <rect x={a.x - 52} y={a.y - 22} width="104" height="44" rx="12"
              fill="var(--color-surface-1)" stroke={activeNode === i ? a.color : 'var(--color-border-strong)'} strokeWidth={activeNode === i ? 2 : 1}
              style={{ transition: 'stroke 0.3s ease, stroke-width 0.3s ease' }}
            />
            <text x={a.x} y={a.y - 2} textAnchor="middle" className="text-[11px] font-body font-semibold" fill="var(--color-text-primary)">
              {a.label}
            </text>
            <text x={a.x} y={a.y + 12} textAnchor="middle" className="text-[8px] font-body" fill="var(--color-text-muted)">
              {a.sublabel}
            </text>
          </motion.g>
        ))}

        {/* Orbiting data particle */}
        <motion.circle
          r="5" fill="var(--color-accent)"
          animate={{ offsetDistance: ['0%', '100%'] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
          style={{ offsetPath: 'path("M 200 62 C 350 62 370 220 200 218 C 30 220 50 62 200 62")' }}
        />
        <motion.circle
          r="3" fill="var(--color-accent)" opacity={0.3}
          animate={{ offsetDistance: ['0%', '100%'] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'linear', delay: 2 }}
          style={{ offsetPath: 'path("M 200 62 C 350 62 370 220 200 218 C 30 220 50 62 200 62")' }}
        />
      </svg>
    </div>
  )
}

/* ── Typing text effect for hero ── */
function TypingWord({ words }: { words: string[] }) {
  const [index, setIndex] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setIndex(i => (i + 1) % words.length), 3000)
    return () => clearInterval(t)
  }, [words.length])

  return (
    <span className="inline-block relative">
      <AnimatePresence mode="wait">
        <motion.span
          key={words[index]}
          initial={{ opacity: 0, y: 20, filter: 'blur(4px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          exit={{ opacity: 0, y: -20, filter: 'blur(4px)' }}
          transition={{ duration: 0.5, ease }}
          className="inline-block italic"
        >
          {words[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}

/* ══════════════════════════════════════════════════════════════ */
/*                         LANDING PAGE                         */
/* ══════════════════════════════════════════════════════════════ */
export default function LandingPage() {
  const heroRef = useRef(null)
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] })
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0])
  const heroScale = useTransform(scrollYProgress, [0, 0.8], [1, 0.96])

  return (
    <div className="min-h-screen bg-bg flex flex-col overflow-x-hidden selection:bg-accent selection:text-accent-contrast">
      {/* ──── Navbar ──── */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-bg/70 border-b border-border/60">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-6 lg:px-8 h-16">
          <Link to="/" className="flex items-center gap-3 group">
            <motion.div whileHover={{ rotate: -6 }} transition={{ type: 'spring', stiffness: 400 }}>
              <Logo size={32} />
            </motion.div>
            <span className="font-display text-xl text-text-primary tracking-tight">Astra AI</span>
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-text-secondary hover:text-text-primary transition-colors font-body font-medium">Features</a>
            <a href="#how-it-works" className="text-sm text-text-secondary hover:text-text-primary transition-colors font-body font-medium">How it works</a>
            <a href="#quick-access" className="text-sm text-text-secondary hover:text-text-primary transition-colors font-body font-medium">Get Started</a>
            <Link to="/dashboard" className="btn-primary text-sm">
              Dashboard <ArrowRight size={14} />
            </Link>
          </nav>
          <Link to="/dashboard" className="md:hidden btn-primary text-sm py-2 px-4">
            Dashboard
          </Link>
        </div>
      </header>

      {/* ──── Hero ──── */}
      <section ref={heroRef} className="relative min-h-[90vh] flex items-center px-6 lg:px-8">
        <motion.div style={{ opacity: heroOpacity, scale: heroScale }} className="w-full">
          <motion.div variants={stagger} initial="hidden" animate="show" className="max-w-7xl mx-auto">
            <div className="grid lg:grid-cols-[1.2fr_1fr] gap-12 lg:gap-20 items-center">
              {/* Left — text */}
              <div className="pt-8 lg:pt-0">
                <motion.div variants={fadeUp} className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full border border-border bg-surface-1/80 backdrop-blur text-xs font-mono text-text-secondary mb-10">
                  <motion.span
                    className="w-2 h-2 rounded-full bg-success"
                    animate={{ scale: [1, 1.4, 1], opacity: [1, 0.5, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                  Closed-Loop Intelligence
                </motion.div>

                <motion.h1 variants={fadeUp} className="font-display text-[3.5rem] lg:text-[4.5rem] xl:text-display-hero text-text-primary mb-6 leading-[0.92] tracking-tight">
                  Prompts that
                  <br />
                  <TypingWord words={['learn', 'evolve', 'improve', 'adapt']} />
                </motion.h1>

                <motion.p variants={fadeUp} className="text-base lg:text-lg text-text-secondary max-w-lg mb-10 font-body leading-relaxed">
                  An AI system that generates answers, judges their quality, and optimizes its own prompts — achieving measurably better results with every iteration.
                </motion.p>

                <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-4">
                  <Link to="/optimize" className="btn-primary text-base px-8 py-3.5 group">
                    Start Optimizing
                    <motion.span className="inline-block" whileHover={{ x: 3 }}>
                      <ArrowRight size={16} />
                    </motion.span>
                  </Link>
                  <Link to="/ask" className="btn-secondary text-base px-8 py-3.5 group">
                    <Play size={14} className="text-text-muted group-hover:text-accent transition-colors" />
                    Try a Question
                  </Link>
                </motion.div>

                {/* Trust bar */}
                <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-6 mt-14 pt-8 border-t border-border">
                  {[
                    { val: '5', label: 'Quality Criteria' },
                    { val: '7+', label: 'AI Models' },
                    { val: '10x', label: 'Faster Iteration' },
                    { val: '24/7', label: 'Always Running' },
                  ].map((s, i) => (
                    <motion.div key={s.label} custom={i} variants={fadeUpFast}>
                      <p className="text-2xl font-display font-semibold text-text-primary">{s.val}</p>
                      <p className="text-[11px] font-body text-text-muted mt-0.5 tracking-wide">{s.label}</p>
                    </motion.div>
                  ))}
                </motion.div>
              </div>

              {/* Right — Interactive diagram */}
              <motion.div variants={scaleUp} className="hidden lg:block">
                <div className="relative p-8 pt-12 rounded-2xl border border-border bg-surface-1/50 backdrop-blur-sm shadow-card">
                  <div className="absolute top-4 left-5 flex items-center gap-2">
                    <Layers size={13} className="text-text-muted" />
                    <span className="text-[10px] font-mono text-text-muted uppercase tracking-[0.15em]">Agent Loop</span>
                  </div>
                  <div className="absolute top-4 right-5 flex gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-danger/40" />
                    <span className="w-2.5 h-2.5 rounded-full bg-warn/40" />
                    <span className="w-2.5 h-2.5 rounded-full bg-success/40" />
                  </div>
                  <AgentLoopDiagram />
                </div>
              </motion.div>
            </div>
          </motion.div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            className="flex flex-col items-center gap-1 text-text-muted"
          >
            <span className="text-[10px] font-mono uppercase tracking-widest">Scroll</span>
            <ChevronDown size={14} />
          </motion.div>
        </motion.div>

        {/* Background pattern */}
        <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
          <div className="absolute inset-0 opacity-[0.025]"
            style={{
              backgroundImage: 'radial-gradient(var(--color-text-primary) 1px, transparent 1px)',
              backgroundSize: '32px 32px',
            }}
          />
          <div className="absolute top-0 right-0 w-[600px] h-[600px] opacity-[0.03] rounded-full"
            style={{ background: 'radial-gradient(circle, var(--color-accent) 0%, transparent 70%)' }}
          />
        </div>
      </section>

      {/* ──── Features ──── */}
      <section id="features" className="py-28 px-6 lg:px-8 border-t border-border">
        <Section className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-[1fr_2fr] gap-16">
            {/* Left — section header (sticky) */}
            <motion.div variants={fadeUp} className="lg:sticky lg:top-24 lg:self-start">
              <p className="text-xs font-mono text-text-muted uppercase tracking-[0.2em] mb-4">Capabilities</p>
              <h2 className="font-display text-display-lg text-text-primary mb-5 leading-tight">
                Everything you need for{' '}
                <span className="italic">better AI</span>
              </h2>
              <p className="text-text-secondary font-body text-base leading-relaxed mb-8">
                From automatic optimization to cost tracking — a complete toolkit for teams that want their AI to perform at its best.
              </p>
              <Link to="/dashboard" className="btn-secondary text-sm">
                Explore Dashboard <ArrowRight size={14} />
              </Link>
            </motion.div>

            {/* Right — feature cards */}
            <div className="grid sm:grid-cols-2 gap-4">
              {features.map(({ icon: Icon, title, desc, to, label, gradient }, i) => (
                <motion.div key={title} custom={i} variants={fadeUpFast}>
                  <Link
                    to={to}
                    className="group card card-hover p-6 h-full flex flex-col relative overflow-hidden"
                  >
                    {/* Subtle gradient background */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                    <div className="relative z-10">
                      <div className="w-10 h-10 rounded-xl bg-surface-3 flex items-center justify-center mb-4 group-hover:bg-accent group-hover:text-accent-contrast transition-all duration-300 group-hover:scale-110">
                        <Icon size={18} />
                      </div>
                      <h3 className="font-body font-semibold text-[15px] text-text-primary mb-2">{title}</h3>
                      <p className="text-sm text-text-secondary leading-relaxed flex-1">{desc}</p>
                      <div className="flex items-center gap-1.5 mt-5 text-xs font-body font-medium text-text-muted group-hover:text-accent transition-colors">
                        {label}
                        <ArrowUpRight size={12} className="transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </Section>
      </section>

      {/* ──── How It Works ──── */}
      <section id="how-it-works" className="py-28 px-6 lg:px-8 border-t border-border bg-surface-1">
        <Section className="max-w-5xl mx-auto">
          <motion.div variants={fadeUp} className="text-center mb-20">
            <p className="text-xs font-mono text-text-muted uppercase tracking-[0.2em] mb-4">Process</p>
            <h2 className="font-display text-display-lg text-text-primary mb-5">
              How it <span className="italic">works</span>
            </h2>
            <p className="text-text-secondary font-body text-base max-w-xl mx-auto leading-relaxed">
              Four steps, fully automated. Provide questions — the system handles everything else.
            </p>
          </motion.div>

          {/* Steps timeline */}
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-[29px] top-0 bottom-0 w-px bg-border hidden md:block" />

            <div className="space-y-6">
              {steps.map(({ num, title, desc, icon: Icon, color }, i) => (
                <motion.div
                  key={num}
                  custom={i}
                  variants={fadeUpFast}
                  className="relative flex gap-6 md:gap-8 items-start"
                >
                  {/* Step circle */}
                  <motion.div
                    className={`flex-shrink-0 w-[60px] h-[60px] rounded-2xl ${color} text-white flex items-center justify-center font-mono text-sm font-bold relative z-10 shadow-lg`}
                    whileHover={{ scale: 1.1, rotate: -3 }}
                    transition={{ type: 'spring', stiffness: 300 }}
                  >
                    {num}
                  </motion.div>

                  {/* Content */}
                  <div className="card p-6 flex-1">
                    <div className="flex items-center gap-2.5 mb-2">
                      <h3 className="font-body font-semibold text-base text-text-primary">{title}</h3>
                      <Icon size={15} className="text-text-muted" />
                    </div>
                    <p className="text-sm text-text-secondary leading-relaxed">{desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* CTA */}
          <motion.div variants={fadeUp} className="text-center mt-16">
            <Link to="/optimize" className="btn-primary text-base px-10 py-4 group">
              Try It Now
              <motion.span className="inline-block" whileHover={{ x: 3 }}>
                <ArrowRight size={16} />
              </motion.span>
            </Link>
          </motion.div>
        </Section>
      </section>

      {/* ──── Quick Access ──── */}
      <section id="quick-access" className="py-24 px-6 lg:px-8 border-t border-border">
        <Section className="max-w-5xl mx-auto">
          <motion.div variants={fadeUp} className="text-center mb-14">
            <h2 className="font-display text-display-md text-text-primary mb-3">
              Jump right in
            </h2>
            <p className="text-text-secondary font-body text-sm">Quick access to the tools you'll use most</p>
          </motion.div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {quickLinks.map(({ to, icon: Icon, label, desc }, i) => (
              <motion.div key={to} custom={i} variants={fadeUpFast}>
                <Link
                  to={to}
                  className="group card card-hover p-6 flex flex-col items-center text-center h-full"
                >
                  <motion.div
                    className="w-12 h-12 rounded-2xl bg-surface-3 flex items-center justify-center mb-4 group-hover:bg-accent group-hover:text-accent-contrast transition-all duration-300"
                    whileHover={{ scale: 1.1, rotate: -5 }}
                    transition={{ type: 'spring', stiffness: 300 }}
                  >
                    <Icon size={20} />
                  </motion.div>
                  <p className="font-body font-semibold text-sm text-text-primary mb-1">{label}</p>
                  <p className="text-xs text-text-muted leading-relaxed">{desc}</p>
                </Link>
              </motion.div>
            ))}
          </div>
        </Section>
      </section>

      {/* ──── Bottom CTA ──── */}
      <section className="py-28 px-6 lg:px-8 border-t border-border bg-surface-1">
        <Section className="max-w-3xl mx-auto text-center">
          <motion.div variants={fadeUp}>
            <Shield size={32} className="mx-auto text-text-muted mb-6" />
            <h2 className="font-display text-display-lg text-text-primary mb-5">
              Ready to build <span className="italic">better prompts?</span>
            </h2>
            <p className="text-text-secondary font-body text-base mb-10 leading-relaxed max-w-md mx-auto">
              Start your first optimization loop in seconds. No configuration needed — just bring your questions.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link to="/optimize" className="btn-primary text-base px-10 py-4">
                Get Started Free <ArrowRight size={16} />
              </Link>
              <Link to="/dashboard" className="btn-secondary text-base px-8 py-4">
                View Dashboard
              </Link>
            </div>
          </motion.div>
        </Section>
      </section>

      {/* ──── Footer ──── */}
      <footer className="border-t border-border bg-bg">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-12 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <Logo size={24} />
            <span className="font-display text-base text-text-primary">Astra AI</span>
          </div>
          <p className="text-xs text-text-muted font-body">&copy; {new Date().getFullYear()} Astra AI — Self-Improving LLM System</p>
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="text-xs text-text-secondary hover:text-text-primary transition-colors font-body font-medium">Dashboard</Link>
            <Link to="/settings" className="text-xs text-text-secondary hover:text-text-primary transition-colors font-body font-medium">Settings</Link>
            <Link to="/costs" className="text-xs text-text-secondary hover:text-text-primary transition-colors font-body font-medium">Pricing</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
