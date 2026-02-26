# ASTRA AI — Enhanced Frontend Build Prompt

> **For**: AI-powered code generation tool (Orchids / Claude / Cursor / Bolt)
> **Stack**: React 18+ · Vite · Tailwind CSS 3+ · Framer Motion · Recharts · Zustand · TanStack Query
> **Backend**: Python FastAPI (existing Astra AI engine)
> **Design Philosophy**: Distinctive, bold, unforgettable — NOT generic AI aesthetics

---

## 0. DESIGN MANDATE — READ FIRST

### What This MUST NOT Look Like
- ❌ **NO** Inter, Roboto, Arial, system-ui font stacks — these are the hallmark of generic AI slop
- ❌ **NO** purple gradients on white backgrounds — the most overused AI color scheme
- ❌ **NO** cookie-cutter card grids with rounded corners and soft shadows — every AI tool generates this
- ❌ **NO** predictable symmetric layouts with equal-width columns
- ❌ **NO** Space Grotesk, Poppins, or any other "default modern" font
- ❌ **NO** bland hero sections with centered text and a single CTA button
- ❌ **NO** identical spacing everywhere — monotonous rhythm kills design
- ❌ **NO** generic gradient blobs or mesh backgrounds without purpose

### What This MUST Feel Like
- ✅ **BOLD** aesthetic direction — pick ONE: brutalist-tech, editorial-luxe, retro-futuristic, neo-brutalism, dark-industrial, or magazine-editorial
- ✅ **DISTINCTIVE typography** — pair a characterful display font (e.g., Satoshi, Clash Display, Cabinet Grotesk, Neue Haas Grotesk, General Sans, Syne, Outfit, Manrope) with a refined body font (e.g., Instrument Sans, Plus Jakarta Sans, DM Sans, Geist)
- ✅ **ATMOSPHERIC backgrounds** — noise textures, grain overlays, subtle geometric patterns, layered transparencies, depth through shadow systems
- ✅ **UNEXPECTED layouts** — asymmetric grids, overlapping elements, diagonal flow, generous negative space contrasted with dense information areas
- ✅ **DOMINANT color with sharp accents** — not timid, evenly-distributed palettes. Own a primary color and let accents cut through
- ✅ **HIGH-IMPACT animations** — one orchestrated page-load sequence with staggered reveals beats scattered micro-interactions. Scroll-triggered reveals, hover states that surprise.
- ✅ **TEXTURE & DEPTH** — glass morphism with grain, layered card systems, dramatic shadows, decorative borders, custom selection colors

### Recommended Aesthetic Direction: **"Dark Observatory"**
A dark-themed, data-dense command center aesthetic. Think: Bloomberg Terminal meets a NASA mission control dashboard, but with editorial typography and cinematic lighting effects.

- **Background**: Deep charcoal (#0A0A0F) with subtle dot-grid pattern overlay
- **Primary accent**: Electric cyan (#00F0FF) or neon amber (#FFB800) — pick ONE
- **Secondary accent**: Muted warm gray (#8A8A8A) for supporting text
- **Cards**: Frosted glass (backdrop-blur + rgba borders + noise texture)
- **Typography**: Display font weight 800+ for headings, mono font for data/scores
- **Signature element**: Thin 1px accent-color borders that glow subtly, scanline effects on data panels
- **Motion**: Elements emerge from slight blur + scale(0.97) → sharp + scale(1), staggered by 50ms delays

> **NOTE TO AI**: This aesthetic direction is a STRONG SUGGESTION. If you have a bolder, more distinctive vision — go for it. The only rule is: it must NOT look like every other AI-generated dashboard. Make it unforgettable.

---

## 1. PROJECT OVERVIEW

### What is Astra AI?
Astra AI is a **self-improving LLM prompt optimization system**. It runs a closed feedback loop:

```
User Question → Generator (LLM) → Answer → Judge (LLM) → Scores & Feedback → Optimizer (LLM) → Improved Prompt → Loop Back
```

**Core concept**: You give it questions, it generates answers using a prompt template, evaluates those answers across 5 criteria (correctness, clarity, reasoning, relevance, conciseness), then automatically rewrites the prompt to improve scores. This loops until convergence (score ≥ 8.5/10) or max iterations (10).

### Why a Frontend?
The system currently runs as a Python CLI. The frontend transforms it into a **visual, interactive, real-time experience** where users can:
- Watch optimization happen live with animated score changes
- Explore detailed per-question evaluations
- Compare multiple AI models side-by-side
- Analyze prompt quality with visual indicators
- Track costs, performance trends, and anomalies
- Configure every parameter through an intuitive UI

### Backend Compatibility Requirements
- **All API calls go to a Python FastAPI backend** (to be built alongside or already existing)
- **WebSocket connection** for live optimization progress streaming
- **JSON data exchange** matching exact backend schemas (documented below)
- **No direct LLM calls from frontend** — all AI operations are backend-only
- **Session-based architecture** — each optimization run creates a session with full history

---

## 2. TECH STACK — EXACT SPECIFICATIONS

```json
{
  "framework": "React 18.2+",
  "build": "Vite 5+",
  "language": "TypeScript (strict mode)",
  "styling": "Tailwind CSS 3.4+ with custom design system",
  "animation": "Framer Motion 11+",
  "charts": "Recharts 2.12+ OR Victory 37+",
  "routing": "React Router v6.22+",
  "state": "Zustand 4.5+",
  "server_state": "TanStack Query v5+",
  "http": "Axios 1.6+",
  "websocket": "native WebSocket with reconnection wrapper",
  "icons": "Lucide React",
  "fonts": "Google Fonts or Fontsource (NOT Inter/Roboto/Arial)",
  "linting": "ESLint + Prettier",
  "testing": "Vitest + React Testing Library"
}
```

### File Structure

```
frontend/
├── public/
│   ├── favicon.svg
│   └── og-image.png
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css                    # Tailwind directives + custom base styles + noise texture
│   ├── assets/
│   │   ├── fonts/                   # Self-hosted distinctive fonts
│   │   ├── noise.svg                # Grain/noise texture overlay
│   │   └── grid-pattern.svg         # Dot-grid background pattern
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx         # Root layout: sidebar + topbar + main area
│   │   │   ├── Sidebar.tsx          # Collapsible nav with glow-on-active
│   │   │   ├── TopBar.tsx           # Breadcrumb + mode badge + global search
│   │   │   └── Footer.tsx           # Minimal status bar
│   │   ├── ui/
│   │   │   ├── GlassCard.tsx        # Frosted glass card with noise overlay
│   │   │   ├── ScoreBar.tsx         # Animated horizontal score bar (0-10)
│   │   │   ├── ScoreRadar.tsx       # 5-axis radar chart for criteria
│   │   │   ├── Badge.tsx            # Status/category badges
│   │   │   ├── AnimatedNumber.tsx   # Count-up/count-down numbers
│   │   │   ├── GradeDisplay.tsx     # Letter grade (A+ to F) with color
│   │   │   ├── CodeBlock.tsx        # Syntax-highlighted code display
│   │   │   ├── PromptDisplay.tsx    # Diff-highlighted prompt viewer
│   │   │   ├── SkeletonLoader.tsx   # Loading skeletons matching card shapes
│   │   │   ├── Toast.tsx            # Notification toasts
│   │   │   ├── Modal.tsx            # Overlay modal with backdrop blur
│   │   │   ├── Tabs.tsx             # Animated tab switcher with underline
│   │   │   ├── Toggle.tsx           # Dev/Prod mode toggle
│   │   │   ├── SliderInput.tsx      # Range slider with live value
│   │   │   ├── ProgressRing.tsx     # Circular progress indicator
│   │   │   ├── Tooltip.tsx          # Context tooltips
│   │   │   └── EmptyState.tsx       # Beautiful empty states with illustrations
│   │   ├── charts/
│   │   │   ├── PerformanceLineChart.tsx   # Score over iterations
│   │   │   ├── CriteriaBarChart.tsx       # Grouped bar per criterion
│   │   │   ├── ImprovementHeatmap.tsx     # Question × criterion matrix
│   │   │   ├── CostPieChart.tsx           # Cost distribution
│   │   │   ├── LatencyTimeline.tsx        # API latency over time
│   │   │   └── ConvergenceChart.tsx       # Convergence trajectory
│   │   └── features/
│   │       ├── hero/
│   │       │   ├── HeroSection.tsx        # Landing page hero
│   │       │   ├── AgentLoopSVG.tsx       # Animated Generate→Judge→Optimize loop
│   │       │   ├── LiveDemo.tsx           # Interactive mini-demo
│   │       │   └── FeatureGrid.tsx        # Feature showcase cards
│   │       ├── optimization/
│   │       │   ├── SetupPanel.tsx         # Question input + config
│   │       │   ├── LiveProgress.tsx       # Real-time optimization view
│   │       │   ├── IterationCard.tsx      # Single iteration result
│   │       │   ├── ResultsSummary.tsx     # Final optimization summary
│   │       │   ├── AnswerViewer.tsx       # Per-question answer display
│   │       │   ├── MetricsPanel.tsx       # Detailed scoring breakdown
│   │       │   ├── CostPanel.tsx          # Cost tracking display
│   │       │   └── ExportPanel.tsx        # Export options
│   │       ├── question/
│   │       │   ├── SingleQuestion.tsx     # Ask single question flow
│   │       │   ├── PromptAnalysis.tsx     # Visual prompt quality
│   │       │   ├── CostPredictor.tsx      # Pre-execution cost estimate
│   │       │   └── AnswerDisplay.tsx      # Generated answer + scores
│   │       ├── comparison/
│   │       │   ├── ModelSelector.tsx      # Pick models to compare
│   │       │   ├── ComparisonGrid.tsx     # Side-by-side results
│   │       │   └── RankingTable.tsx       # Model ranking display
│   │       ├── analytics/
│   │       │   ├── OverviewDashboard.tsx  # Key metrics at a glance
│   │       │   ├── TrendAnalysis.tsx      # Performance over time
│   │       │   ├── AnomalyDetector.tsx    # Anomaly alerts
│   │       │   └── CostAnalytics.tsx      # Cost trends & projections
│   │       ├── settings/
│   │       │   ├── ModelConfig.tsx        # Model selection
│   │       │   ├── WeightsConfig.tsx      # Criteria weight sliders
│   │       │   ├── OptimizationConfig.tsx # Iteration/threshold settings
│   │       │   └── IntegrationConfig.tsx  # API keys, LangSmith
│   │       └── questions/
│   │           ├── QuestionBank.tsx       # Question CRUD
│   │           ├── QuestionForm.tsx       # Add/edit question
│   │           └── CategoryFilter.tsx     # Filter by category/difficulty
│   ├── hooks/
│   │   ├── useOptimization.ts       # WebSocket-based live optimization
│   │   ├── useApi.ts                # TanStack Query wrappers
│   │   ├── useWebSocket.ts          # WebSocket connection manager
│   │   ├── useAnimatedValue.ts      # Smooth number transitions
│   │   └── useTheme.ts              # Dark/light theme toggle
│   ├── stores/
│   │   ├── appStore.ts              # Global app state (Zustand)
│   │   ├── optimizationStore.ts     # Current optimization state
│   │   └── settingsStore.ts         # User preferences
│   ├── services/
│   │   ├── api.ts                   # Axios instance + interceptors
│   │   ├── optimizationApi.ts       # Optimization endpoints
│   │   ├── questionApi.ts           # Question CRUD endpoints
│   │   ├── analyticsApi.ts          # Analytics/metrics endpoints
│   │   ├── settingsApi.ts           # Settings endpoints
│   │   └── websocket.ts             # WebSocket manager
│   ├── types/
│   │   ├── optimization.ts          # OptimizationState, IterationLog, etc.
│   │   ├── evaluation.ts            # Scores, Feedback, etc.
│   │   ├── question.ts              # Question, Category, Difficulty
│   │   ├── model.ts                 # ModelProfile, CostPrediction
│   │   ├── analytics.ts             # MetricsData, AnomalyAlert
│   │   └── api.ts                   # API response wrappers
│   ├── utils/
│   │   ├── formatters.ts            # Number, date, score formatting
│   │   ├── colors.ts                # Score-to-color mapping
│   │   └── constants.ts             # App-wide constants
│   └── pages/
│       ├── LandingPage.tsx          # /
│       ├── DashboardPage.tsx        # /dashboard
│       ├── OptimizationPage.tsx     # /optimize
│       ├── AskQuestionPage.tsx      # /ask
│       ├── ComparisonPage.tsx       # /compare
│       ├── PromptAnalyzerPage.tsx   # /prompt-analyzer
│       ├── AnalyticsPage.tsx        # /analytics
│       ├── SettingsPage.tsx         # /settings
│       ├── QuestionBankPage.tsx     # /questions
│       └── SessionDetailPage.tsx    # /sessions/:id
├── tailwind.config.ts
├── vite.config.ts
├── tsconfig.json
├── package.json
└── .env
```

---

## 3. DESIGN SYSTEM — CSS VARIABLES & TAILWIND CONFIG

### tailwind.config.ts

```typescript
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Core palette — Dark Observatory theme
        surface: {
          0: '#050508',    // Deepest background
          1: '#0A0A0F',    // Primary background
          2: '#12121A',    // Elevated surface
          3: '#1A1A25',    // Card background
          4: '#222230',    // Hover state
        },
        accent: {
          DEFAULT: '#00F0FF',  // Electric cyan (PRIMARY accent — change this to set theme)
          dim: '#00F0FF33',    // 20% opacity for glows
          muted: '#00F0FF1A',  // 10% opacity for subtle tints
          contrast: '#000000', // Text on accent
        },
        warn: '#FFB800',       // Amber warning
        danger: '#FF3B5C',     // Red-pink error
        success: '#00E676',    // Green success
        info: '#7C8DFF',       // Soft blue info
        text: {
          primary: '#E8E8ED',  // Primary text
          secondary: '#8A8A9A', // Secondary text
          muted: '#555566',    // Muted text
        },
        // Score colors (0-10 scale)
        score: {
          excellent: '#00E676',  // 8-10
          good: '#66FFB2',       // 6-8
          average: '#FFB800',    // 4-6
          poor: '#FF6B35',       // 2-4
          critical: '#FF3B5C',   // 0-2
        },
        // Grade colors (A+ to F)
        grade: {
          a: '#00E676',
          b: '#66FFB2',
          c: '#FFB800',
          d: '#FF6B35',
          f: '#FF3B5C',
        },
      },
      fontFamily: {
        // DISTINCTIVE fonts — NOT Inter/Roboto/Arial
        display: ['Clash Display', 'Satoshi', 'sans-serif'],
        body: ['Instrument Sans', 'Plus Jakarta Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        data: ['Tabular Nums', 'JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'display-xl': ['4.5rem', { lineHeight: '1.05', letterSpacing: '-0.03em', fontWeight: '800' }],
        'display-lg': ['3rem', { lineHeight: '1.1', letterSpacing: '-0.025em', fontWeight: '700' }],
        'display-md': ['2rem', { lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '700' }],
        'display-sm': ['1.5rem', { lineHeight: '1.3', letterSpacing: '-0.015em', fontWeight: '600' }],
        'body-lg': ['1.125rem', { lineHeight: '1.6' }],
        'body': ['0.9375rem', { lineHeight: '1.6' }],
        'body-sm': ['0.8125rem', { lineHeight: '1.5' }],
        'caption': ['0.75rem', { lineHeight: '1.4', letterSpacing: '0.02em' }],
        'mono-data': ['0.875rem', { lineHeight: '1.4', fontWeight: '500' }],
      },
      borderRadius: {
        'card': '12px',
        'button': '8px',
        'badge': '6px',
        'input': '8px',
      },
      boxShadow: {
        'glow-sm': '0 0 10px var(--accent-dim)',
        'glow-md': '0 0 20px var(--accent-dim), 0 0 40px var(--accent-dim)',
        'glow-lg': '0 0 30px var(--accent-dim), 0 0 60px var(--accent-dim), 0 0 90px var(--accent-dim)',
        'card': '0 4px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.05)',
        'card-hover': '0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px var(--accent-dim)',
        'inner-glow': 'inset 0 1px 0 rgba(255, 255, 255, 0.06)',
      },
      backdropBlur: {
        'glass': '16px',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-down': 'slideDown 0.4s ease-out',
        'scale-in': 'scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        'score-fill': 'scoreFill 1.2s cubic-bezier(0.16, 1, 0.3, 1)',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
        'scan-line': 'scanLine 4s linear infinite',
        'number-tick': 'numberTick 0.3s ease-out',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(20px) scale(0.97)' }, '100%': { opacity: '1', transform: 'translateY(0) scale(1)' } },
        slideDown: { '0%': { opacity: '0', transform: 'translateY(-10px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        scaleIn: { '0%': { opacity: '0', transform: 'scale(0.95)' }, '100%': { opacity: '1', transform: 'scale(1)' } },
        scoreFill: { '0%': { width: '0%' }, '100%': { width: 'var(--score-width)' } },
        glowPulse: { '0%, 100%': { boxShadow: '0 0 10px var(--accent-dim)' }, '50%': { boxShadow: '0 0 20px var(--accent-dim), 0 0 40px var(--accent-dim)' } },
        scanLine: { '0%': { transform: 'translateY(-100%)' }, '100%': { transform: 'translateY(100%)' } },
      },
    },
  },
  plugins: [],
} satisfies Config
```

### index.css — Base Styles

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  /* Import distinctive fonts */
  @import url('https://api.fontsource.org/v1/fonts/clash-display/latin-800-normal.woff2');
  @import url('https://api.fontsource.org/v1/fonts/instrument-sans/latin-400-normal.woff2');

  body {
    @apply bg-surface-1 text-text-primary font-body antialiased;
    /* Noise texture overlay on entire app */
    background-image: 
      url('/noise.svg'),
      radial-gradient(circle at 20% 50%, rgba(0, 240, 255, 0.03) 0%, transparent 50%),
      radial-gradient(circle at 80% 50%, rgba(0, 240, 255, 0.02) 0%, transparent 50%);
  }

  /* Custom scrollbar */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

  /* Selection color */
  ::selection { background: rgba(0, 240, 255, 0.3); color: #fff; }
}

@layer components {
  /* Glass card */
  .glass-card {
    @apply bg-surface-3/60 backdrop-blur-glass border border-white/5 rounded-card shadow-card;
    background-image: url('/noise.svg');
    background-blend-mode: overlay;
  }
  .glass-card:hover {
    @apply border-accent/20 shadow-card-hover;
  }

  /* Glow border */
  .glow-border {
    @apply border border-accent/30;
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.1), inset 0 0 10px rgba(0, 240, 255, 0.05);
  }

  /* Score bar fill */
  .score-bar {
    @apply h-2 rounded-full transition-all duration-1000 ease-out;
  }

  /* Scan line effect for data panels */
  .scan-effect::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    animation: scanLine 4s linear infinite;
    opacity: 0.3;
  }

  /* Data cell mono */
  .data-cell {
    @apply font-mono text-mono-data tabular-nums;
  }
}
```

---

## 4. ALL 10 PAGES — DETAILED SPECIFICATIONS

---

### PAGE 1: Landing / Hero Page (`/`)

**Purpose**: First impression. Must be CINEMATIC, not a boring product page.

**Layout**: Full-viewport hero → scrolling feature sections → CTA

#### Section A: Hero (100vh)
- **Background**: 
  - Full dark canvas with animated dot-grid (dots glow faintly in accent color)
  - Subtle radial gradient emanating from center-left
  - Floating geometric shapes (hexagons, circles) at very low opacity, slowly drifting
- **Content** (asymmetric layout — NOT centered):
  - Left 60%:
    - Tiny badge: `SELF-IMPROVING AI` with accent border
    - Headline (font-display, display-xl): 
      ```
      Prompts That
      Evolve.
      ```
    - Subtitle (font-body, body-lg, text-secondary): "Astra AI watches its own answers, judges them, and rewrites its own instructions — automatically."
    - Two buttons (not boring rectangles):
      - Primary: `Start Optimizing →` (accent bg, black text, hover glow effect)
      - Secondary: `See It Work` (transparent, accent border, hover fill)
    - Stats row (3 metrics, mono font): `10 Iterations` · `5 Criteria` · `7 Models`
  - Right 40%:
    - **The Agent Loop SVG** (SIGNATURE ELEMENT): Animated circular diagram showing:
      - 3 nodes: Generator (brain icon) → Judge (scale icon) → Optimizer (wrench icon)
      - Animated arrows flowing between them (dashed line with moving dash)
      - Central score display: `8.5` pulsing with glow
      - Each node lights up sequentially (1s each) to show the loop in action
      - On hover: node expands showing brief description

#### Section B: How It Works (scroll-triggered)
- 4 steps displayed as a **diagonal staircase layout** (not horizontal cards):
  1. "Ask a Question" — Input icon, brief description
  2. "AI Generates Answers" — Generator icon, brief description
  3. "AI Judges Quality" — 5-criteria radar chart mini-preview
  4. "AI Rewrites the Prompt" — Before/after prompt snippet
- Each step fades in + slides from right as user scrolls
- Connecting line (accent color, 1px) flows between steps diagonally

#### Section C: Feature Showcase
- **Bento grid layout** (NOT equal cards):
  - 1 large card (spans 2 cols): "Real-Time Optimization" with embedded animation
  - 2 medium cards: "Multi-Model Comparison" + "Smart Routing"
  - 3 small cards: "Cost Tracking" + "Prompt Analysis" + "15+ Question Categories"
- Cards use glass-card style with hover animations (slight rotate + scale)

#### Section D: Live Stats / Social Proof
- Animated counter row: "Questions Optimized", "Average Improvement", "Models Supported"
- Numbers count up from 0 when scrolled into view

#### Section E: CTA Footer
- Dark section with large display text: "Stop guessing. Start optimizing."
- Single prominent CTA button

**Animations (Framer Motion)**:
```typescript
// Hero elements stagger
const heroContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.3 }
  }
}

const heroChild = {
  hidden: { opacity: 0, y: 20, filter: 'blur(8px)' },
  visible: { 
    opacity: 1, y: 0, filter: 'blur(0px)',
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] }
  }
}

// Agent loop node pulse
const nodePulse = {
  inactive: { scale: 1, boxShadow: '0 0 0px var(--accent)' },
  active: { 
    scale: 1.1, 
    boxShadow: '0 0 20px var(--accent), 0 0 40px var(--accent)',
    transition: { duration: 0.4 }
  }
}

// Scroll-triggered section reveal
const scrollReveal = {
  hidden: { opacity: 0, x: 60 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.7, ease: 'easeOut' } }
}
```

---

### PAGE 2: Dashboard (`/dashboard`)

**Purpose**: Command center. At-a-glance system status + quick actions.

**Layout**: Top metric cards → Quick actions → Recent sessions → System status

#### Top Row: 4 Metric Cards (Glass cards, slight asymmetry in sizes)
1. **Latest Score**: Large AnimatedNumber (e.g., `8.7`), color-coded by quality, small sparkline under it showing recent trend, label "Last Optimization Score"
2. **Total Sessions**: Count with this-week vs all-time breakdown
3. **Avg Improvement**: Percentage with up/down arrow, comparison to previous
4. **Active Model**: Current model name + quality tier badge

#### Quick Action Panel
- 3 large action buttons (not boring — each is a glass card with icon):
  - 🧠 "Run Optimization" → navigates to `/optimize`
  - ❓ "Ask a Question" → navigates to `/ask`
  - ⚔️ "Compare Models" → navigates to `/compare`
- Each has subtle hover animation (icon rotates, border glows)

#### Recent Sessions Table
- Table with columns: Date, Questions, Initial Score, Final Score, Improvement, Iterations, Status (Converged badge / Failed badge)
- Rows clickable → navigate to `/sessions/:id`
- Score cells color-coded (green for high, amber for mid, red for low)
- Empty state: Beautiful illustration + "Run your first optimization" CTA

#### System Status Panel
- Small cards showing:
  - API Connection: Green/red dot + "Connected" / "Disconnected"
  - LangSmith Tracing: Active/Inactive with link to diagnose
  - Current Mode: Production / Developer toggle
  - Model Registry: "7 models available" with link to settings

---

### PAGE 3: Optimization Run (`/optimize`) — THE CORE EXPERIENCE

**Purpose**: This is the main feature. Setup → Run → Watch → Explore results.

**Three-phase UI** (tab-based, with animated tab transitions):

---

#### Phase 1: Setup Tab

**Left panel (60%)**:
- **Question Input Section**:
  - Large textarea: "Enter your questions (one per line)"
  - OR file upload: Drag-and-drop zone for JSON/CSV files
  - OR: "Load from Question Bank" button → opens QuestionBank modal
  - Preview: Shows parsed questions as chips/tags below input
  - Each question chip shows: text (truncated), category badge, difficulty badge, ground truth indicator

- **Initial Prompt Template**:
  - Code editor-style textarea with syntax highlighting
  - Placeholder shows example prompt template with `{question}` variable
  - Below: Prompt quality indicator (calls prompt analysis API on blur)
    - Quality grade badge (A-F)
    - Vagueness / Ambiguity / Specificity mini-bars
    - "Auto-optimize prompt" button

**Right panel (40%)**:
- **Configuration Card**:
  - Model Selection dropdown (shows all available models with tier badges)
  - Max Iterations slider (1-15, default 10)
  - Convergence Threshold slider (5.0-10.0, default 8.5)
  - Criteria Weight sliders (5 sliders, must sum to 1.0):
    - Correctness: 0.40
    - Clarity: 0.20
    - Reasoning: 0.20
    - Relevance: 0.10
    - Conciseness: 0.10
    - Live validation: shows error if sum ≠ 1.0
  - Advanced toggle (collapsed by default):
    - Temperature slider (0.0-1.0)
    - Top P slider (0.0-1.0)
    - Max Tokens input (100-2000)
    - Smart Router toggle (on/off)

- **Cost Prediction Card** (auto-updates when config changes):
  - Estimated cost per iteration
  - Total estimated cost (iterations × per-iteration)
  - Estimated latency per iteration
  - Complexity assessment
  - Recommended model suggestion
  - Alternative model suggestions with cost comparison

- **Start Button**: Large, prominent. "🚀 Start Optimization" with accent glow. Disabled until at least 1 question is entered.

---

#### Phase 2: Live Progress Tab (Active during optimization)

**This is where the magic happens. Must feel ALIVE.**

**Top: Progress Overview Bar**
- Horizontal progress bar showing iteration X of N
- Current score (large, animated number with glow when it increases)
- Status: "Generating..." / "Evaluating..." / "Optimizing..." / "Converged! ✓"
- Elapsed time counter
- "Stop" button (red, cancels optimization)

**Left Column (55%): Live Iteration Feed**
- A scrolling feed of iteration cards, newest at top
- Each **Iteration Card** contains:
  - Header: "Iteration 3" + timestamp + duration
  - Score badge: Composite score with color + change indicator (+0.4 ↑ in green)
  - 5 criteria mini-bars (inline, compact):
    ```
    Correctness  ████████░░  7.8
    Clarity      ██████████  9.2
    Reasoning    ███████░░░  6.5
    Relevance    █████████░  8.9
    Conciseness  ████████░░  7.4
    ```
  - Weak criteria flags (amber badges)
  - Strong criteria flags (green badges)
  - Expand arrow → shows full detail (prompt used, all answers, all evaluations)

- **New iteration cards animate in**: slide from right + fade + scale-in
- **Score changes animate**: numbers morph from old to new value

**Right Column (45%): Live Visualization**
- **Performance Chart** (updating in real-time):
  - Line chart: Composite score over iterations
  - Green zone (≥8.5), yellow zone (6-8.5), red zone (<6)
  - Each point appears with animation when new iteration completes
  - Convergence threshold shown as horizontal dashed line

- **Current Prompt Panel** (collapsible):
  - Shows the CURRENT prompt template being used
  - Highlights changes from previous iteration (diff view: green additions, red removals)
  - Word count + estimated token count

- **Agent Activity Feed** (developer mode only):
  - Small log showing: "[Generator] Generated 5 answers in 3.2s"
  - "[Judge] Evaluated 5 answers, avg correctness: 7.8"
  - "[Optimizer] Made 3 modifications to prompt"

**WebSocket Integration**:
```typescript
// WebSocket message types from backend
type WSMessage = 
  | { type: 'iteration_start', data: { iteration: number } }
  | { type: 'generation_complete', data: { outputs: GeneratedOutput[] } }
  | { type: 'evaluation_complete', data: { evaluations: Evaluation[], avg_score: number } }
  | { type: 'optimization_complete', data: { new_prompt: string, modifications: string[] } }
  | { type: 'iteration_complete', data: IterationLog }
  | { type: 'convergence', data: { final_score: number, iterations: number } }
  | { type: 'error', data: { message: string, agent: string } }
  | { type: 'stopped', data: { reason: string } }
```

---

#### Phase 3: Results Tab (After optimization completes)

**Hero Banner**: 
- Large display: "Optimization Complete" 
- Score journey: `2.6 → 9.3` with animated arrow and color transition
- Letter grade: `A+` (large, glowing)
- Converged badge or "Max iterations reached" badge
- Improvement percentage: `+257%`
- Total time + total iterations

**6 Sub-Tabs** (horizontal tab bar with animated underline):

##### Sub-Tab 3.1: Summary
- **Overview Cards** (3 across):
  - Initial vs Final Score (side-by-side with improvement arrow)
  - Iterations Used / Max
  - Convergence Status

- **Criteria Comparison Table**:
  | Criterion | Initial | Final | Change | Status |
  |-----------|---------|-------|--------|--------|
  | Correctness | 3.2 | 9.1 | +5.9 ↑ | ✅ Excellent |
  | Clarity | 2.8 | 9.5 | +6.7 ↑ | ✅ Excellent |
  | ... | | | | |
  
  Each change cell is color-coded (green for positive, red for negative)

- **Performance Line Chart** (full-width):
  - All 5 criteria + composite as separate lines (toggleable)
  - Convergence threshold horizontal line
  - Hover to see exact values at each iteration

- **Radar Chart**: 
  - Overlay of iteration 1 (translucent red) vs final iteration (solid green)
  - 5 axes for 5 criteria

##### Sub-Tab 3.2: Optimized Prompt
- **Side-by-side prompt display**:
  - Left: Initial prompt (dimmed, red-tinted)
  - Right: Final prompt (bright, green-tinted)
  - Diff highlighting between them
- **Prompt Evolution Timeline**:
  - Scrollable list of ALL prompt versions
  - Each version shows: iteration number, score at that point, list of modifications made
  - Click to view full prompt text
- **Copy button**: Copy final prompt to clipboard
- **"Use This Prompt" button**: Opens ask-question page with this prompt pre-loaded

##### Sub-Tab 3.3: All Answers
- **Per-question accordion/expandable list**:
  - Each question row shows:
    - Question text
    - Category + difficulty badges
    - Best iteration score
    - Expand → shows answers from EVERY iteration for this question
  - Expanded view per iteration:
    - Generated answer (full text)
    - Generated explanation (full text)
    - 5 criteria scores with bars
    - Judge feedback (correctness_reason, clarity_reason, etc.)
    - Judge suggestions
    - Flags (hallucination, off_topic, etc.)
  - Navigation: "Show best iteration" / "Show all iterations" toggle

##### Sub-Tab 3.4: Detailed Metrics
- **Per-Iteration Breakdown Table** (sortable, filterable):
  | Iteration | Composite | Correctness | Clarity | Reasoning | Relevance | Conciseness | Duration |
  |-----------|-----------|-------------|---------|-----------|-----------|-------------|----------|
  | 1 | 2.60 | 3.20 | 2.80 | 2.50 | 2.00 | 1.80 | 4.2s |
  | 2 | 7.10 | 7.50 | 7.20 | 6.80 | 7.50 | 6.00 | 3.8s |
  | ...

- **Improvement Heatmap**: 
  - Matrix: Questions (rows) × Criteria (columns)
  - Color intensity = score value (dark red → bright green)
  - Hover shows exact value

- **Statistical Summary**:
  - Mean, Median, Std Dev, Min, Max for each criterion
  - Improvement rate per iteration
  - Weak criteria identification

- **Trend Analysis**:
  - "Improving" / "Declining" / "Stable" badge per criterion
  - Anomaly alerts (if any detected)

##### Sub-Tab 3.5: Cost Breakdown
- **Total Cost Card**: Large number with dollar sign
- **Cost by Agent** (pie chart):
  - Generator: $X.XX (XX%)
  - Judge: $X.XX (XX%)
  - Optimizer: $X.XX (XX%)
- **Cost by Iteration** (bar chart):
  - Shows cost per iteration — should be roughly constant
- **Token Usage**:
  - Input tokens total + per iteration
  - Output tokens total + per iteration
  - Efficiency: tokens per score-point improvement
- **Projection**: "Running 10 more iterations would cost approximately $X.XX"

##### Sub-Tab 3.6: Export & Debug
- **Export Options** (card grid):
  - JSON: Full results dump
  - CSV: Scores table
  - Markdown: Summary report
  - PNG: Performance chart
  - PDF: Complete report (if available)
- **Developer Debug Panel** (visible in dev mode):
  - Full raw JSON of results
  - Agent communication log
  - Prompt/response pairs for each LLM call
  - Timing breakdown: generation time, evaluation time, optimization time
  - LangSmith trace link (if tracing enabled)

---

### PAGE 4: Ask a Question (`/ask`)

**Purpose**: Quick single-question answering with prompt analysis + smart routing.

**Layout**: Two-column (60/40)

**Left: Question + Prompt Input**
- **Prompt Template** textarea (optional — if empty, uses last optimized prompt):
  - Syntax-highlighted editor
  - Below it: Prompt Analysis widget (auto-analyzes on blur):
    - Quality grade (A-F) as large badge
    - 3 mini bars: Vagueness | Ambiguity | Specificity (0-1 scale each)
    - Detected intent badge: "question" / "instruction" / "code"
    - Suggestions list (bullet points)
    - "Auto-optimize" button → transforms prompt using prompt engine
  
- **Question** input:
  - Large input field
  - Category auto-detect badge
  - Difficulty estimate badge
  - Ground truth (optional) textarea

- **Generate Button**: "⚡ Generate Answer" with loading state

**Right: Configuration + Results**
- **Smart Routing** card:
  - Detected complexity: SIMPLE / MODERATE / COMPLEX / CRITICAL badge
  - Recommended model with reasoning
  - Alternative models list with cost comparison
  - Override: model selector dropdown

- **Cost Prediction** card:
  - Estimated tokens (input/output)
  - Estimated cost
  - Estimated latency
  - Complexity level

- **After Generation — Answer Display** (replaces config cards):
  - Answer text (nicely formatted, code blocks syntax-highlighted)
  - Explanation text
  - 5-criteria score bars (animated fill from 0 to value)
  - Composite score with grade
  - Judge feedback (expandable accordions per criterion)
  - Judge suggestions
  - Flags / warnings
  - Metadata: model used, tokens consumed, latency, timestamp
  - "Ask Another" button to reset

---

### PAGE 5: Model Comparison (`/compare`)

**Purpose**: Side-by-side comparison of multiple models on the same question.

**Layout**: Setup → Results grid

**Setup Section**:
- Question input (single question)
- Prompt template input
- Model selection: Checkboxes for all available models (select 2-7)
  - Each model shows: name, quality tier badge, estimated cost
- "Run Comparison" button

**Results Section** (appears after run):
- **Ranking Podium**: 🥇 🥈 🥉 display with model names and composite scores
- **Comparison Grid**: One column per model
  - Each column contains:
    - Model name + badge
    - Composite score (large)
    - 5 criteria bars
    - Full answer text (scrollable, max-height)
    - Metadata: tokens, latency, cost
- **Consistency Score**: How much models agree (0-100%)
- **Comparison Chart**: Grouped bar chart — each criterion on X axis, one bar per model
- **Summary**: Auto-generated text: "Qwen 2.5 72B scored highest overall..."

---

### PAGE 6: Prompt Analyzer (`/prompt-analyzer`)

**Purpose**: Deep prompt quality analysis tool.

**Layout**: Input → Analysis display

**Input**: Large textarea for prompt, "Analyze" button

**Analysis Display** (appears after analysis):
- **Quality Grade** (massive): Letter A-F in grade color, with score ring around it
- **Score Breakdown** (3 bars):
  - Vagueness: 0.0 (good) → 1.0 (bad) — green to red
  - Ambiguity: 0.0 (good) → 1.0 (bad) — green to red
  - Specificity: 0.0 (bad) → 1.0 (good) — red to green
- **Properties** (badge row):
  - Has Question: ✅/❌
  - Has Context: ✅/❌
  - Has Constraints: ✅/❌
- **Word Count** + **Sentence Count** (mono display)
- **Detected Intent**: Badge (question / instruction / code / conversation)
- **Improvement Suggestions**: Numbered list with explanations
- **Auto-Constraints** detected: List of constraint templates that could help
- **Optimized Version** (collapsible panel):
  - Shows auto-optimized prompt
  - Side-by-side diff with original
  - "Copy Optimized" button
  - "Test with Optimized" button → navigates to `/ask` with optimized prompt

**Prompt Engine Learning Stats** (sidebar or bottom panel):
- Total optimizations performed
- Average outcome score
- Best improvements (list)
- Most used improvement patterns

---

### PAGE 7: Analytics Dashboard (`/analytics`)

**Purpose**: Historical performance analysis, trends, and anomaly detection.

**5 Sub-Tabs**:

#### Tab 7.1: Overview
- **Key Metrics Cards** (4 across):
  - Total Sessions | Average Final Score | Best Session Score | Total Questions Evaluated
- **Recent Performance Timeline**: Line chart of final scores from recent sessions
- **Category Distribution**: Donut chart of question categories used
- **Sessions Table**: Date, score, improvement, status — clickable rows

#### Tab 7.2: Trends
- **Performance Trend Chart**: Line chart across sessions
  - Trend line: "Improving" / "Declining" / "Stable"
  - Each data point is a session
- **Criteria Trends**: 5 individual trend lines (one per criterion)
- **Improvement Rate**: Bar chart showing improvement % per session
- **Convergence Rate**: What % of sessions converge vs hit max iterations

#### Tab 7.3: Model Performance
- **Model Comparison Chart**: Grouped bar chart — avg score by model across sessions
- **Model Usage Distribution**: Pie chart
- **Per-Model Stats Table**: Model, Sessions, Avg Score, Avg Latency, Total Cost, Success Rate
- **Router Performance**: How often smart router picks the right model

#### Tab 7.4: Costs
- **Cumulative Cost Chart**: Area chart showing total spend over time
- **Cost per Session**: Bar chart
- **Cost by Agent**: Stacked bar chart (generator, judge, optimizer)
- **Budget Tracking**: Budget vs actual with alert threshold
- **Projections**: "At current rate, monthly cost ≈ $X.XX"

#### Tab 7.5: Anomalies
- **Anomaly Feed**: Timeline of detected anomalies
  - Performance drops (>1.0 score drop)
  - Prompt length spikes (>2× average)
  - Cost spikes
  - Convergence failures
- Each anomaly card shows: type, severity, timestamp, details, affected session
- **Anomaly Frequency Chart**: Bar chart of anomaly types over time

---

### PAGE 8: Settings (`/settings`)

**Purpose**: Configure all system parameters.

**5 Sub-Tabs**:

#### Tab 8.1: Models
- **Available Models Table**:
  | Model | Provider | Tier | Context Window | Cost (In/Out per 1K) | Status |
  - Each row: toggle available/unavailable
- **Default Model Selection**:
  - Generator model dropdown
  - Judge model dropdown
  - Optimizer model dropdown
- **Model Parameters** (per model):
  - Temperature slider
  - Top P slider
  - Max Tokens slider
  - Frequency Penalty slider

#### Tab 8.2: Optimization
- Max Iterations slider (1-20)
- Convergence Threshold slider (1.0-10.0)
- Rollback Threshold slider
- Performance Plateau Detection toggle
- Plateau Threshold input
- Smart Router toggle + config

#### Tab 8.3: Evaluation Weights
- **5 Weight Sliders** (interactive):
  - Each slider: 0.00 to 1.00, step 0.05
  - Live validation: sum display, error if ≠ 1.0
  - Reset to defaults button
  - Presets: "Balanced", "Accuracy-focused", "Communication-focused", "Custom"
- **Weight Visualization**: 
  - Pie chart / donut chart showing weight distribution
  - Updates live as sliders move

#### Tab 8.4: Runtime
- Dev / Production mode toggle with description of each
- Debug level dropdown: None, Basic, Verbose
- Log retention input (days)
- Output directory configuration

#### Tab 8.5: Integrations
- **LangSmith**:
  - API key input (masked)
  - Project name input
  - Connection test button
  - Status indicator
- **HuggingFace**:
  - API token input (masked)
  - Connection test button
- **OpenAI** (optional):
  - API key input
  - Connection test
- **Anthropic** (optional):
  - API key input
  - Connection test
- **Export/Import Config** button: Download/upload config.yaml

---

### PAGE 9: Question Bank (`/questions`)

**Purpose**: Manage question datasets for optimization.

**Layout**: Filter sidebar + table + detail panel

**Filter Sidebar**:
- Category multi-select (all 15+ categories as checkboxes)
- Difficulty multi-select (easy, medium, hard)
- Has Ground Truth filter (yes/no/all)
- Search text input
- "Reset Filters" button

**Question Table** (main area):
- Columns: ID, Question (truncated), Category (badge), Difficulty (badge), Ground Truth (✅/❌)
- Sortable by any column
- Bulk actions: Delete selected, Export selected
- "Add Question" button (opens modal)
- Pagination or virtual scroll for large sets

**Add/Edit Question Modal**:
- Question text (textarea)
- Category dropdown
- Difficulty dropdown
- Ground truth (textarea)
- Context (optional textarea)
- Metadata JSON editor (optional)
- Save / Cancel buttons

**Import/Export**:
- Import: Drag-drop JSON or CSV file
- Export: Button to download current (filtered) set as JSON/CSV
- Dataset stats: Total questions, category distribution, difficulty distribution

---

### PAGE 10: Session Detail (`/sessions/:id`)

**Purpose**: Deep-dive into a specific past optimization session.

**Layout**: Identical to Results Tab (Phase 3) of the Optimization page, but:
- Loaded from saved session data (API: `GET /api/sessions/:id`)
- Read-only (no live updates)
- Additional header showing session metadata:
  - Session ID
  - Date/time started
  - Duration
  - Model used
  - Number of questions
- "Re-run with same config" button
- "Compare with another session" button (opens session picker modal)

---

## 5. COMPLETE API SPECIFICATION

### Base URL: `http://localhost:8000/api`

### REST Endpoints

#### Optimization
```
POST   /api/optimize/start
  Body: {
    questions: Array<{ question: string, ground_truth?: string, category?: string, difficulty?: string }>,
    initial_prompt: string,
    config: {
      model: string,
      max_iterations: number,
      convergence_threshold: number,
      weights: { correctness: number, clarity: number, reasoning: number, relevance: number, conciseness: number },
      temperature?: number,
      top_p?: number,
      max_tokens?: number,
      smart_router?: boolean
    }
  }
  Response: { session_id: string, status: "started", ws_url: string }

GET    /api/optimize/:session_id/status
  Response: { status: "running" | "completed" | "failed" | "stopped", iteration: number, current_score: number }

POST   /api/optimize/:session_id/stop
  Response: { status: "stopped", results: OptimizationResults }
```

#### Sessions
```
GET    /api/sessions
  Query: ?limit=20&offset=0&sort=date_desc
  Response: { sessions: SessionSummary[], total: number }

GET    /api/sessions/:id
  Response: SessionDetail (full results, all iterations, all evaluations)

DELETE /api/sessions/:id
  Response: { deleted: true }
```

#### Questions
```
GET    /api/questions
  Query: ?category=physics&difficulty=medium&search=newton&limit=20&offset=0
  Response: { questions: Question[], total: number, stats: { categories: Record<string,number>, difficulties: Record<string,number> } }

POST   /api/questions
  Body: { question: string, ground_truth?: string, category: string, difficulty: string, context?: string }
  Response: { id: number, ...question }

PUT    /api/questions/:id
  Body: Partial<Question>
  Response: Question

DELETE /api/questions/:id
  Response: { deleted: true }

POST   /api/questions/import
  Body: FormData (file: JSON/CSV)
  Response: { imported: number, errors: string[] }

GET    /api/questions/export
  Query: ?format=json|csv&category=...&difficulty=...
  Response: File download
```

#### Single Question / Ask
```
POST   /api/ask
  Body: {
    question: string,
    prompt_template?: string,
    ground_truth?: string,
    model?: string,
    auto_route?: boolean
  }
  Response: {
    answer: string,
    explanation: string,
    scores: { correctness: number, clarity: number, reasoning: number, relevance: number, conciseness: number },
    composite_score: number,
    feedback: Record<string, string>,
    suggestions: string[],
    flags: string[],
    metadata: { model: string, tokens_used: number, latency_ms: number, cost_usd: number }
  }
```

#### Model Comparison
```
POST   /api/compare
  Body: {
    question: string,
    prompt_template: string,
    models: string[],
    ground_truth?: string
  }
  Response: {
    results: Array<{
      model: string,
      answer: string,
      explanation: string,
      scores: Scores,
      composite_score: number,
      metadata: { tokens: number, latency_ms: number, cost: number }
    }>,
    ranking: Array<{ model: string, rank: number, score: number }>,
    consistency_score: number,
    summary: string
  }
```

#### Prompt Analysis
```
POST   /api/prompt/analyze
  Body: { prompt: string }
  Response: {
    quality_grade: "A" | "B" | "C" | "D" | "F",
    word_count: number,
    sentence_count: number,
    vagueness_score: number,   // 0-1
    ambiguity_score: number,   // 0-1
    specificity_score: number, // 0-1
    has_question: boolean,
    has_context: boolean,
    has_constraints: boolean,
    detected_intent: "question" | "instruction" | "code" | "conversation",
    suggested_improvements: string[],
    auto_constraints: string[]
  }

POST   /api/prompt/optimize
  Body: { prompt: string, add_constraints?: string[] }
  Response: { original: string, optimized: string, improvements_applied: string[] }
```

#### Smart Router
```
POST   /api/router/predict
  Body: { prompt: string, model?: string }
  Response: {
    complexity: "SIMPLE" | "MODERATE" | "COMPLEX" | "CRITICAL",
    recommended_model: string,
    alternative_models: Array<{ model: string, cost: number, latency: number }>,
    cost_prediction: { prompt_tokens_est: number, response_tokens_est: number, cost_estimate_usd: number, latency_estimate_seconds: number }
  }

GET    /api/router/stats
  Response: {
    total_routings: number,
    total_cost: number,
    per_model: Record<string, { uses: number, avg_score: number, success_rate: number }>
  }
```

#### Analytics
```
GET    /api/analytics/overview
  Response: { total_sessions: number, avg_score: number, best_score: number, total_questions: number, total_cost: number }

GET    /api/analytics/trends
  Query: ?window=7d|30d|90d
  Response: { data_points: Array<{ date: string, avg_score: number, sessions: number, cost: number }>, trend: "improving" | "declining" | "stable" }

GET    /api/analytics/anomalies
  Response: { anomalies: Array<{ type: string, severity: string, timestamp: string, details: string, session_id?: string }> }

GET    /api/analytics/costs
  Query: ?period=day|week|month
  Response: { total: number, by_agent: Record<string,number>, by_model: Record<string,number>, timeline: Array<{ date: string, cost: number }> }
```

#### Models
```
GET    /api/models
  Response: { models: Array<{ id: string, name: string, provider: string, tier: number, context_window: number, cost_input: number, cost_output: number, available: boolean }> }

GET    /api/models/:id/test
  Response: { status: "ok" | "error", latency_ms: number, message?: string }
```

#### Settings
```
GET    /api/settings
  Response: FullConfig

PUT    /api/settings
  Body: Partial<FullConfig>
  Response: FullConfig

POST   /api/settings/test-connection
  Body: { service: "langsmith" | "huggingface" | "openai" | "anthropic", api_key: string }
  Response: { connected: boolean, message: string }
```

### WebSocket Endpoint

```
WS     ws://localhost:8000/ws/optimize/:session_id
```

**Messages from server → client:**
```typescript
// Iteration lifecycle
{ type: "iteration_start", data: { iteration: number, total: number } }
{ type: "generation_started", data: { question_count: number } }
{ type: "generation_progress", data: { completed: number, total: number, current_question: string } }
{ type: "generation_complete", data: { outputs: GeneratedOutput[], duration_ms: number } }
{ type: "evaluation_started", data: {} }
{ type: "evaluation_progress", data: { completed: number, total: number } }
{ type: "evaluation_complete", data: { evaluations: Evaluation[], avg_score: number, scores_by_criterion: Record<string,number> } }
{ type: "optimization_started", data: {} }
{ type: "optimization_complete", data: { new_prompt: string, modifications: string[], rationale: string } }
{ type: "iteration_complete", data: IterationLog }

// Terminal states
{ type: "convergence", data: { final_score: number, iterations: number, reason: string } }
{ type: "max_iterations", data: { final_score: number } }
{ type: "rollback", data: { from_score: number, to_score: number, rolled_back_to_iteration: number } }
{ type: "stopped", data: { reason: "user_cancelled" | "error", message?: string } }
{ type: "error", data: { agent: string, message: string, recoverable: boolean } }

// Final
{ type: "complete", data: OptimizationResults }
```

---

## 6. TYPESCRIPT TYPE DEFINITIONS

```typescript
// ═══════════════════════════════════════════════
// Core Types — Must match Python backend exactly
// ═══════════════════════════════════════════════

// Question
interface Question {
  id: number;
  question: string;
  ground_truth?: string;
  category: QuestionCategory;
  difficulty: Difficulty;
  context?: string;
  metadata?: Record<string, unknown>;
}

type QuestionCategory = 
  | 'computer_science' | 'code_python' | 'code_javascript' | 'code_java'
  | 'code_cpp' | 'code_sql' | 'code_rust' | 'code_debug' | 'code_refactor'
  | 'code_api' | 'code_html_css' | 'physics' | 'biology' | 'mathematics'
  | 'economics' | 'history' | 'earth_science' | 'astronomy' | 'chemistry'
  | 'logic' | 'prompt_quality' | 'relevance_test';

type Difficulty = 'easy' | 'medium' | 'hard';

// Evaluation
interface Scores {
  correctness: number;  // 0-10
  clarity: number;      // 0-10
  reasoning: number;    // 0-10
  relevance: number;    // 0-10
  conciseness: number;  // 0-10
}

interface Evaluation {
  scores: Scores;
  composite_score: number;
  feedback: {
    correctness_reason: string;
    clarity_reason: string;
    reasoning_reason: string;
    relevance_reason: string;
    conciseness_reason: string;
  };
  suggestions: string[];
  flags: string[];  // 'potential_hallucination' | 'off_topic' | 'logical_error' | etc.
  metadata: {
    judge_model: string;
    timestamp: string;
    tokens_used: number;
    confidence: number;
  };
}

// Generation
interface GeneratedOutput {
  question: string;
  answer: string;
  explanation: string;
  confidence: number;
  metadata: {
    model: string;
    tokens_used: number;
    input_tokens: number;
    output_tokens: number;
    latency_ms: number;
    timestamp: string;
  };
}

// Optimization
interface OptimizationConfig {
  model: string;
  max_iterations: number;
  convergence_threshold: number;
  weights: Scores;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  smart_router?: boolean;
}

interface IterationLog {
  iteration: number;
  prompt: string;
  score: number;
  evaluations: Evaluation[];
  generated_outputs: GeneratedOutput[];
  timestamp: string;
  per_question_scores: Record<string, Scores>;
  weak_criteria: string[];
  strong_criteria: string[];
  optimization_modifications: string[];
  duration_seconds: number;
}

interface OptimizationResults {
  session_id: string;
  final_prompt: string;
  initial_score: number;
  final_score: number;
  improvement: number;
  iterations: number;
  converged: boolean;
  convergence_reason?: string;
  performance_history: number[];
  iteration_logs: IterationLog[];
  total_cost: number;
  total_duration_seconds: number;
  config: OptimizationConfig;
}

// Models
interface ModelProfile {
  id: string;
  name: string;
  provider: 'huggingface' | 'openai' | 'anthropic';
  context_window: number;
  cost_input_per_1k: number;
  cost_output_per_1k: number;
  avg_latency_seconds: number;
  quality_tier: 1 | 2 | 3;
  strengths: string[];
  is_available: boolean;
}

interface CostPrediction {
  prompt_tokens_est: number;
  response_tokens_est: number;
  total_tokens_est: number;
  cost_estimate_usd: number;
  latency_estimate_seconds: number;
  complexity: 'SIMPLE' | 'MODERATE' | 'COMPLEX' | 'CRITICAL';
  recommended_model: string;
  alternative_models: Array<{
    model: string;
    cost: number;
    latency: number;
  }>;
}

// Prompt Analysis
interface PromptAnalysis {
  quality_grade: 'A' | 'B' | 'C' | 'D' | 'F';
  word_count: number;
  sentence_count: number;
  vagueness_score: number;    // 0-1
  ambiguity_score: number;    // 0-1
  specificity_score: number;  // 0-1
  has_question: boolean;
  has_context: boolean;
  has_constraints: boolean;
  detected_intent: 'question' | 'instruction' | 'code' | 'conversation';
  suggested_improvements: string[];
  auto_constraints: string[];
}

// Analytics
interface AnalyticsSummary {
  total_sessions: number;
  avg_score: number;
  best_score: number;
  total_questions: number;
  total_cost: number;
}

interface Anomaly {
  type: 'performance_drop' | 'prompt_length_spike' | 'cost_spike' | 'convergence_failure';
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
  details: string;
  session_id?: string;
}

// Smart Router
type PromptComplexity = 'SIMPLE' | 'MODERATE' | 'COMPLEX' | 'CRITICAL';

interface RouterStats {
  total_routings: number;
  total_cost: number;
  per_model: Record<string, {
    uses: number;
    avg_score: number;
    success_rate: number;
  }>;
}

// Model Comparison
interface ComparisonResult {
  model: string;
  answer: string;
  explanation: string;
  scores: Scores;
  composite_score: number;
  metadata: {
    tokens_used: number;
    latency_ms: number;
    cost_usd: number;
  };
}

interface ComparisonReport {
  results: ComparisonResult[];
  ranking: Array<{ model: string; rank: number; score: number }>;
  consistency_score: number;
  summary: string;
}

// Session
interface SessionSummary {
  id: string;
  started_at: string;
  duration_seconds: number;
  questions_count: number;
  initial_score: number;
  final_score: number;
  improvement: number;
  iterations: number;
  converged: boolean;
  model: string;
  total_cost: number;
}

type SessionDetail = SessionSummary & OptimizationResults;
```

---

## 7. COMPONENT BEHAVIOR SPECIFICATIONS

### GlassCard Component
```tsx
interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;        // Enable hover glow effect
  scanEffect?: boolean;   // Enable scanning line overlay
  glow?: boolean;         // Enable border glow
  onClick?: () => void;
}
// Renders: div with glass-card class, optional scan-effect, optional glow-border
// Hover: border transitions to accent/20, shadow transitions to card-hover
```

### ScoreBar Component
```tsx
interface ScoreBarProps {
  label: string;
  score: number;         // 0-10
  maxScore?: number;     // default 10
  showValue?: boolean;   // show number on right
  animate?: boolean;     // animate fill on mount
  size?: 'sm' | 'md' | 'lg';   // height
  colorScheme?: 'score' | 'custom';
}
// Colors: ≥8 → score-excellent (green), ≥6 → score-good, ≥4 → score-average, ≥2 → score-poor, <2 → score-critical
// Animation: width transitions from 0% to (score/max * 100)% with score-fill animation
```

### AnimatedNumber Component
```tsx
interface AnimatedNumberProps {
  value: number;
  duration?: number;     // ms, default 800
  decimals?: number;     // default 1
  prefix?: string;       // e.g., "$"
  suffix?: string;       // e.g., "%"
  colorCode?: boolean;   // color by score range
  className?: string;
}
// Smoothly interpolates from previous value to new value
// Uses requestAnimationFrame for 60fps transitions
```

### ScoreRadar Component
```tsx
interface ScoreRadarProps {
  scores: Scores;
  previousScores?: Scores;   // Show overlay comparison
  size?: number;              // px
  animated?: boolean;
}
// 5-axis radar chart: correctness, clarity, reasoning, relevance, conciseness
// If previousScores provided: show as translucent overlay (red-tinted)
// Current scores shown as filled area (accent-colored)
```

### PromptDisplay Component
```tsx
interface PromptDisplayProps {
  prompt: string;
  previousPrompt?: string;   // For diff view
  showDiff?: boolean;
  maxHeight?: number;
  copyButton?: boolean;
}
// If showDiff + previousPrompt: highlight additions (green bg) and removals (red bg)
// Monospace font, dark background, line numbers
// Copy button in top-right corner
```

### LiveProgress Component
```tsx
// Manages WebSocket connection
// Renders iteration cards as they arrive
// Updates chart in real-time
// Handles all WS message types
// Shows agent activity in dev mode
// Provides stop button
```

---

## 8. STATE MANAGEMENT (Zustand Stores)

### appStore.ts
```typescript
interface AppState {
  // Theme
  isDark: boolean;
  toggleTheme: () => void;

  // Mode
  mode: 'production' | 'developer';
  toggleMode: () => void;

  // Global loading
  isGlobalLoading: boolean;
  setGlobalLoading: (loading: boolean) => void;

  // Notifications
  notifications: Notification[];
  addNotification: (n: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;

  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}
```

### optimizationStore.ts
```typescript
interface OptimizationState {
  // Current run
  isRunning: boolean;
  sessionId: string | null;
  currentIteration: number;
  currentScore: number;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'stopped';

  // Data
  iterations: IterationLog[];
  performanceHistory: number[];
  config: OptimizationConfig | null;

  // Results
  results: OptimizationResults | null;

  // Actions
  startOptimization: (questions: Question[], prompt: string, config: OptimizationConfig) => Promise<void>;
  stopOptimization: () => void;
  addIteration: (log: IterationLog) => void;
  setResults: (results: OptimizationResults) => void;
  reset: () => void;
}
```

### settingsStore.ts
```typescript
interface SettingsState {
  // Models
  generatorModel: string;
  judgeModel: string;
  optimizerModel: string;

  // Optimization
  maxIterations: number;
  convergenceThreshold: number;
  weights: Scores;

  // Advanced
  temperature: number;
  topP: number;
  maxTokens: number;
  smartRouter: boolean;

  // Integrations
  langsmithKey: string;
  huggingfaceToken: string;
  openaiKey: string;
  anthropicKey: string;

  // Actions
  updateSettings: (partial: Partial<SettingsState>) => void;
  loadFromServer: () => Promise<void>;
  saveToServer: () => Promise<void>;
  resetToDefaults: () => void;
}
```

---

## 9. ROUTING CONFIGURATION

```typescript
const routes = [
  { path: '/', element: <LandingPage />, label: 'Home' },
  { path: '/dashboard', element: <DashboardPage />, label: 'Dashboard' },
  { path: '/optimize', element: <OptimizationPage />, label: 'Optimize' },
  { path: '/ask', element: <AskQuestionPage />, label: 'Ask' },
  { path: '/compare', element: <ComparisonPage />, label: 'Compare' },
  { path: '/prompt-analyzer', element: <PromptAnalyzerPage />, label: 'Analyzer' },
  { path: '/analytics', element: <AnalyticsPage />, label: 'Analytics' },
  { path: '/settings', element: <SettingsPage />, label: 'Settings' },
  { path: '/questions', element: <QuestionBankPage />, label: 'Questions' },
  { path: '/sessions/:id', element: <SessionDetailPage />, label: 'Session' },
];
```

**Sidebar Navigation** (always visible except on Landing page):
- Dashboard (grid icon)
- Optimize (zap icon)
- Ask a Question (message-circle icon)
- Compare Models (git-compare icon)
- Prompt Analyzer (search icon)
- Analytics (bar-chart icon)
- Question Bank (database icon)
- Settings (settings icon)
- Divider
- Mode toggle (sun/moon icon)

---

## 10. ANIMATION SPECIFICATIONS (Framer Motion)

### Page Transitions
```typescript
const pageTransition = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
  transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] }
};
```

### Card Entrance (staggered)
```typescript
const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } }
};

const staggerItem = {
  hidden: { opacity: 0, y: 16, scale: 0.97 },
  visible: { 
    opacity: 1, y: 0, scale: 1,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] }
  }
};
```

### Score Bar Fill
```typescript
const scoreBarFill = {
  initial: { width: '0%' },
  animate: { width: `${(score / 10) * 100}%` },
  transition: { duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 0.2 }
};
```

### Number Count-Up
```typescript
// Use useSpring from framer-motion
const springValue = useSpring(0, { stiffness: 80, damping: 20 });
// On value change: springValue.set(newValue)
// Render: useMotionValueEvent to update display
```

### Live Iteration Card Entrance
```typescript
const iterationCardEntrance = {
  initial: { opacity: 0, x: 40, scale: 0.95, filter: 'blur(4px)' },
  animate: { 
    opacity: 1, x: 0, scale: 1, filter: 'blur(0px)',
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] }
  }
};
```

### Chart Data Point Appearance
```typescript
// Each new data point in the performance chart should:
// 1. Appear with a scale animation (0 → 1)
// 2. Have a brief glow effect
// 3. Draw the line segment smoothly from previous point
```

### Hover Effects
```typescript
// Cards: scale(1.02) + border glow + shadow elevation
const cardHover = {
  scale: 1.02,
  boxShadow: '0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,240,255,0.2)',
  transition: { duration: 0.2 }
};

// Buttons: slight Y lift + glow
const buttonHover = {
  y: -2,
  boxShadow: '0 4px 20px rgba(0,240,255,0.3)',
  transition: { duration: 0.15 }
};

// Nav items: bg-surface-4 + left accent bar
```

---

## 11. RESPONSIVE DESIGN

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| `mobile` | <640px | Single column, sidebar becomes bottom nav, simplified charts |
| `tablet` | 640-1024px | 2-column where possible, collapsible sidebar |
| `desktop` | 1024-1440px | Full layout |
| `wide` | >1440px | Extra wide charts, 3-column where beneficial |

**Sidebar**: 
- Desktop: 260px wide, collapsible to 64px (icons only)
- Tablet: Collapsible overlay
- Mobile: Bottom tab bar with 5 most important items

**Charts**: 
- Mobile: Simplified (line charts only, no complex heatmaps)
- Tablet+: Full interactive charts

---

## 12. DARK/LIGHT THEME SYSTEM

- **Default**: Dark theme (the "Observatory" aesthetic)
- **Light theme**: Should NOT be just "invert the colors":
  - Background: Warm off-white (#F5F3EE) with subtle paper texture
  - Cards: White (#FFFFFF) with soft shadows (NOT gray borders)
  - Accent: Deep teal (#0D7377) instead of electric cyan
  - Text: Near-black (#1A1A1A) primary, warm gray (#6B6B6B) secondary
  - Charts: Adjusted for readability on light backgrounds
  - Same distinctive typography
  - Same animations, adjusted glow effects (softer)
- **Toggle**: Smooth 300ms transition between themes using CSS variables

---

## 13. ERROR HANDLING & LOADING STATES

### Loading States
- **Skeleton loaders** matching card shapes (NOT generic spinners)
- **Progress indicators** for long operations (optimization runs)
- **Optimistic UI** for settings changes

### Error States
- **Connection error**: Full-page overlay with retry button
- **API error**: Toast notification with error message + retry action
- **WebSocket disconnect**: Auto-reconnect with countdown display
- **Empty states**: Beautiful illustrations with helpful CTAs (not just "No data")
- **Form validation**: Inline errors with red border + error message below field

### Error Boundary
- Wrap each page in error boundary
- Show friendly error UI with "Report Bug" and "Reload" buttons
- Log errors to console in dev mode

---

## 14. ACCESSIBILITY

- All interactive elements: keyboard navigable (tab order, enter/space activation)
- Score colors: NEVER rely on color alone — always include text labels
- Screen reader: aria-labels on icons, aria-live regions for live updates
- Focus indicators: visible focus rings (accent color, 2px)
- Color contrast: minimum 4.5:1 ratio for text
- Reduced motion: respect `prefers-reduced-motion` media query

---

## 15. PERFORMANCE REQUIREMENTS

- **Lighthouse score**: >90 on all categories
- **First Contentful Paint**: <1.5s
- **Time to Interactive**: <3s
- **Code splitting**: Lazy-load pages with React.lazy + Suspense
- **Image optimization**: WebP format, lazy loading, proper sizing
- **Bundle size**: <200KB initial (gzipped)
- **Chart rendering**: Virtualized for >100 data points
- **WebSocket**: Auto-reconnect with exponential backoff (1s, 2s, 4s, max 30s)
- **Caching**: TanStack Query with stale-while-revalidate (staleTime: 30s for analytics, 5s for live data)

---

## 16. ENVIRONMENT VARIABLES

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_BASE_URL=ws://localhost:8000/ws
VITE_LANGSMITH_BASE_URL=https://api.smith.langchain.com
VITE_APP_NAME=Astra AI
VITE_APP_VERSION=1.0.0
```

---

## 17. BACKEND COMPATIBILITY NOTES

The React frontend MUST be compatible with this Python backend architecture:

1. **FastAPI server** on port 8000
2. **CORS enabled** for `http://localhost:5173` (Vite dev server)
3. **JSON responses** with snake_case keys (frontend converts to camelCase using Axios interceptor)
4. **WebSocket** using FastAPI's WebSocket support
5. **File uploads** using multipart/form-data
6. **Session data** stored in `output/session_YYYYMMDD_HHMMSS/` directories
7. **Config** loaded from `config/config.yaml` — exposed via settings API
8. **Question data** from `questions.json` or `data/sample_questions.json`
9. **HuggingFace Inference API** — free tier models, no GPU needed on client
10. **LangSmith tracing** — optional, configured via environment variables

### Key Backend Files the Frontend Interacts With
| Backend Component | Frontend Interaction |
|---|---|
| `agents/langgraph_orchestrator.py` | Optimization loop — WebSocket + REST |
| `agents/langchain_judge.py` | Evaluation results in API responses |
| `agents/langchain_optimizer.py` | Optimization results + prompt versions |
| `utils/smart_router.py` | Cost prediction + model routing APIs |
| `utils/prompt_engine.py` | Prompt analysis + optimization APIs |
| `utils/analytics.py` | Analytics data APIs |
| `utils/metrics.py` | Metrics calculation (returned in API) |
| `utils/model_selector.py` | Cost tracking APIs |
| `data/data_loader.py` | Question CRUD APIs |
| `config/config.yaml` | Settings API |
| `cli/controller.py` | Reference for all features to replicate in UI |

---

## 18. IMPLEMENTATION PRIORITY ORDER

Build in this sequence:

1. **Design system** (tailwind config, base styles, GlassCard, ScoreBar, AnimatedNumber, Badge)
2. **AppShell** (sidebar, topbar, routing, theme toggle)
3. **Dashboard page** (metric cards, quick actions, recent sessions)
4. **Settings page** (model config, weights, integrations)
5. **Ask Question page** (single question flow, prompt analysis)
6. **Optimization page — Setup tab** (question input, config panel)
7. **Optimization page — Live Progress** (WebSocket, iteration cards, chart)
8. **Optimization page — Results** (all 6 sub-tabs)
9. **Question Bank page** (CRUD, import/export)
10. **Model Comparison page** (multi-model, ranking)
11. **Prompt Analyzer page** (deep analysis)
12. **Analytics Dashboard** (all 5 tabs)
13. **Session Detail page** (reuses Results components)
14. **Landing/Hero page** (cinematic entry point)

---

## 19. QUALITY CHECKLIST

Before considering ANY page complete:
- [ ] Responsive on mobile, tablet, desktop
- [ ] Dark theme looks cinematic, NOT generic
- [ ] Light theme is warm and refined, NOT just inverted
- [ ] All numbers animate on first appearance
- [ ] Score bars animate their fills
- [ ] Cards have hover effects with subtle glow
- [ ] Loading states use skeleton loaders (NOT spinners)
- [ ] Empty states are beautiful (NOT just "No data found")
- [ ] Error states show helpful messages with retry actions
- [ ] Typography uses display font for headings, body font for text, mono for data
- [ ] Colors follow the score-quality mapping consistently
- [ ] Animations respect prefers-reduced-motion
- [ ] No hardcoded colors — all through Tailwind/CSS variables
- [ ] All API calls go through TanStack Query with proper caching
- [ ] WebSocket connections auto-reconnect
- [ ] Forms validate inline with helpful errors
- [ ] No console errors or warnings
- [ ] `<title>` and `<meta>` tags set per page

---

## 20. FINAL DESIGN REMINDERS

> **This is NOT another AI dashboard. This is a command center for an AI that improves itself.**

The design must communicate:
1. **Intelligence**: The system is watching, learning, adapting
2. **Precision**: Data-dense but organized, every number matters
3. **Power**: This is a serious tool for serious work
4. **Beauty**: Dark, cinematic, atmospheric — not sterile or clinical
5. **Motion**: Alive, breathing, responding — not static

Typography rule: **Font weights should vary dramatically**. Display headings at 800 weight, body at 400, data labels at 500 in mono. This contrast creates hierarchy without relying on size alone.

Color rule: **One accent color owns the interface**. Everything else is grayscale. Accent appears on: active nav items, score highlights, CTAs, borders on focused cards, chart highlights, and glowing elements.

Space rule: **Breathing room around hero elements, density in data areas**. The hero section should feel expansive. The metrics tables should feel packed with information. This contrast makes both areas more effective.

Animation rule: **Entrance animations are events, not decorations**. Each card sliding in should feel like it's arriving with important data. The stagger delay (50-80ms between siblings) creates rhythm. The ease curve `[0.16, 1, 0.3, 1]` (Expo.out) gives a satisfying snap.

---

*End of Enhanced Frontend Prompt — Astra AI v2.0*
