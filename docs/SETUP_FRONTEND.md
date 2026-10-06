# ResQGrid AI — Frontend Setup Guide

This guide covers the Next.js frontend application in detail.

---

## Architecture

The frontend is a Next.js 14 application with:

- **App Router** for page routing
- **TypeScript** for type safety
- **Tailwind CSS** for styling (dark command-center theme)
- **MapLibre GL JS** for interactive maps
- **Zustand** for state management
- **Axios** for HTTP API communication
- **Radix UI** for accessible UI primitives

## Directory Structure

```
apps/web/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout (dark theme)
│   │   ├── page.tsx            # Home page (Dashboard)
│   │   └── globals.css         # Global styles + Tailwind
│   ├── components/
│   │   ├── Dashboard.tsx       # Main 3-column dashboard layout
│   │   ├── KPIBar.tsx          # Top KPI metrics bar
│   │   ├── IncidentQueue.tsx   # Left panel: incident list
│   │   ├── CommandMap.tsx      # Center: MapLibre map
│   │   └── DetailPanel.tsx     # Right panel: incident details
│   ├── lib/
│   │   ├── api.ts              # Axios client + API functions
│   │   └── utils.ts            # Utility functions
│   ├── hooks/                  # Custom React hooks (future)
│   ├── stores/                 # Zustand stores (future)
│   ├── styles/                 # Additional styles (future)
│   └── types/                  # TypeScript types (future)
├── public/                     # Static assets
├── Dockerfile                  # Production Docker build
├── next.config.ts              # Next.js configuration
├── tailwind.config.ts          # Tailwind theme configuration
├── tsconfig.json               # TypeScript configuration
├── postcss.config.js           # PostCSS plugins
└── package.json                # Dependencies and scripts
```

## Step-by-Step Setup

### 1. Install Node.js

Ensure Node.js 18+ is installed:

```bash
node --version    # Should be v18+
npm --version     # Should be v9+
```

### 2. Install Dependencies

```bash
cd apps/web
npm install
```

### 3. Configure Environment

Create `.env.local` in `apps/web/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_MAP_STYLE_URL=https://demotiles.maplibre.org/style.json
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### 4. Start Development Server

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

### 5. Build for Production

```bash
npm run build
npm start
```

### 6. Run Linter

```bash
npm run lint
```

### 7. Run Type Checks

```bash
npm run type-check
```

### 8. Run Tests

```bash
npm test
```

## UI Layout

The command center uses a professional 3-column layout:

```
┌──────────────────────────────────────────────────────┐
│ KPI Bar: Active Incidents | Critical | Resources...  │
├────────┬──────────────────────────────┬──────────────┤
│        │                              │              │
│ Incident│        Map                  │  Incident    │
│ Queue  │   (MapLibre GL JS)           │  Details     │
│        │                              │  & Actions   │
│ Left   │        Center                │  Right       │
│ 320px  │        Flex-1                │  384px       │
│        │                              │              │
├────────┴──────────────────────────────┴──────────────┤
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Severity Visual Hierarchy

- **Critical**: Red (#ef4444) — highest urgency
- **High**: Orange (#f97316) — urgent attention needed
- **Medium**: Yellow (#eab308) — standard priority
- **Low**: Green (#22c55e) — informational

## Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server (hot reload) |
| `npm run build` | Build production bundle |
| `npm start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |
| `npm test` | Run Jest tests |
| `npm run type-check` | TypeScript type checking |

## Adding New Pages

Create new pages using Next.js App Router:

```
src/app/
├── page.tsx                    # / (Dashboard)
├── login/
│   └── page.tsx                # /login
├── incidents/
│   ├── page.tsx                # /incidents
│   └── [id]/
│       └── page.tsx            # /incidents/:id
├── resources/
│   └── page.tsx                # /resources
└── report/
    └── page.tsx                # /report (citizen form)
```

## Map Configuration

The map uses MapLibre GL JS with OpenStreetMap tiles by default. To use a custom tile provider:

```env
NEXT_PUBLIC_MAP_STYLE_URL=https://your-tile-server/style.json
```

## Mobile Responsive

The citizen incident reporting form should be mobile-responsive. The command dashboard is optimized for desktop.
