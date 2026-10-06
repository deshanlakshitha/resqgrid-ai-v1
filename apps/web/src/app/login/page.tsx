'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import {
  ShieldCheck, Radar, BrainCircuit, Scale, ClipboardCheck, ArrowRight,
  AlertTriangle, Loader2,
} from 'lucide-react';

const DEMO_ACCOUNTS = [
  { role: 'Dispatcher', email: 'dispatcher@resqgrid.local', password: 'dispatch123' },
  { role: 'Admin', email: 'admin@resqgrid.local', password: 'admin123' },
  { role: 'Responder', email: 'responder1@resqgrid.local', password: 'respond123' },
  { role: 'Citizen', email: 'citizen@resqgrid.local', password: 'citizen123' },
];

const FEATURES = [
  { icon: BrainCircuit, title: 'AI Triage', desc: 'Qwen-powered incident analysis in seconds' },
  { icon: Scale, title: 'Explainable Priority', desc: 'Deterministic weighted scoring, fully auditable' },
  { icon: Radar, title: 'Resource Matching', desc: 'Optimal dispatch recommendations with live ETA' },
  { icon: ClipboardCheck, title: 'Human-Approved', desc: 'Every AI decision needs a human sign-off' },
];

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('dispatcher@resqgrid.local');
  const [password, setPassword] = useState('dispatch123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      router.push('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Login failed. Is the backend running on port 8000?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex bg-command-bg">
      {/* ===== Left: Brand panel ===== */}
      <div className="hidden lg:flex flex-col justify-between w-[46%] p-12 relative overflow-hidden border-r border-command-border">
        {/* Background layers */}
        <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-60" />
        <div className="absolute inset-0 bg-radial-sweep" />
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-blue-600/10 blur-3xl" />
        <div className="absolute bottom-0 -left-32 w-96 h-96 rounded-full bg-red-600/10 blur-3xl" />

        {/* Radar decoration */}
        <div className="absolute right-12 top-1/2 -translate-y-1/2 opacity-40 pointer-events-none">
          <div className="relative w-64 h-64">
            <div className="absolute inset-0 rounded-full border border-blue-500/30" />
            <div className="absolute inset-8 rounded-full border border-blue-500/20" />
            <div className="absolute inset-16 rounded-full border border-blue-500/10" />
            <div className="absolute inset-0 rounded-full bg-[conic-gradient(from_0deg,transparent_0deg,rgba(37,99,235,0.35)_60deg,transparent_90deg)] animate-spin-slow" />
            <div className="absolute top-12 right-16 w-2 h-2 rounded-full bg-red-500 shadow-glow-red animate-blink" />
            <div className="absolute bottom-20 left-14 w-1.5 h-1.5 rounded-full bg-green-500 shadow-glow-green" />
          </div>
        </div>

        {/* Brand */}
        <div className="relative">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center shadow-glow-blue">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">ResQGrid AI</h1>
              <p className="text-xs text-command-muted tracking-widest uppercase">Command Center</p>
            </div>
          </div>
          <h2 className="text-4xl font-bold leading-tight mt-12 max-w-md bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Intelligent Emergency Resource Network
          </h2>
          <p className="text-slate-400 mt-4 max-w-md leading-relaxed">
            When minutes decide lives — AI-assisted triage, explainable priority
            scoring, and human-approved resource dispatch on one live map.
          </p>
        </div>

        {/* Feature list */}
        <div className="relative space-y-5 mt-12 max-w-md">
          {FEATURES.map((f, i) => (
            <div key={f.title} className="flex gap-4 animate-fade-in" style={{ animationDelay: `${i * 120}ms` }}>
              <div className="w-9 h-9 rounded-lg bg-command-raised border border-command-border flex items-center justify-center shrink-0">
                <f.icon className="w-4.5 h-4.5 w-[18px] h-[18px] text-blue-400" />
              </div>
              <div>
                <p className="text-sm font-semibold">{f.title}</p>
                <p className="text-xs text-slate-500 mt-0.5">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Footer note */}
        <div className="relative flex items-center gap-2 text-xs text-slate-600">
          <AlertTriangle className="w-3.5 h-3.5" />
          AI recommends. Humans approve. Every decision is explainable and auditable.
        </div>
      </div>

      {/* ===== Right: Login form ===== */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm animate-slide-up">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8 justify-center">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold">ResQGrid AI</h1>
          </div>

          <h2 className="text-xl font-bold">Welcome back</h2>
          <p className="text-sm text-slate-500 mt-1 mb-8">
            Sign in to access the emergency command center
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/30 rounded-xl px-3.5 py-2.5 text-sm text-red-400 animate-fade-in">
                <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-xs font-medium text-slate-400 mb-1.5">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-command-panel border border-command-borderhover/60 rounded-xl px-3.5 py-2.5 text-sm placeholder:text-slate-600 focus:outline-none focus:border-blue-500/60 focus:ring-2 focus:ring-blue-500/20 transition-all"
                placeholder="you@resqgrid.local"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-medium text-slate-400 mb-1.5">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-command-panel border border-command-borderhover/60 rounded-xl px-3.5 py-2.5 text-sm placeholder:text-slate-600 focus:outline-none focus:border-blue-500/60 focus:ring-2 focus:ring-blue-500/20 transition-all"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 rounded-xl text-sm font-semibold shadow-glow-blue hover:shadow-glow-blue hover:-translate-y-px active:translate-y-0 transition-all disabled:opacity-50 disabled:hover:translate-y-0 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Demo accounts */}
          <div className="mt-8">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-px flex-1 bg-command-border" />
              <span className="text-[11px] font-medium uppercase tracking-wider text-slate-600">
                Demo accounts — click to fill
              </span>
              <div className="h-px flex-1 bg-command-border" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              {DEMO_ACCOUNTS.map((acc) => {
                const active = email === acc.email;
                return (
                  <button
                    key={acc.role}
                    type="button"
                    onClick={() => {
                      setEmail(acc.email);
                      setPassword(acc.password);
                    }}
                    className={`px-3 py-2.5 rounded-xl border text-left transition-all group ${
                      active
                        ? 'border-blue-500/50 bg-blue-500/10'
                        : 'border-command-borderhover/60 hover:border-slate-500 hover:bg-command-raised'
                    }`}
                  >
                    <span className={`block text-xs font-semibold ${active ? 'text-blue-300' : 'text-slate-300'}`}>
                      {acc.role}
                    </span>
                    <span className="block text-[11px] text-slate-600 truncate mt-0.5">
                      {acc.email}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
