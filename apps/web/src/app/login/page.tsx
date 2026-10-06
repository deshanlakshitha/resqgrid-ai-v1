'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';

const DEMO_ACCOUNTS = [
  { role: 'Dispatcher', email: 'dispatcher@resqgrid.local', password: 'dispatch123' },
  { role: 'Admin', email: 'admin@resqgrid.local', password: 'admin123' },
  { role: 'Responder', email: 'responder1@resqgrid.local', password: 'respond123' },
  { role: 'Citizen', email: 'citizen@resqgrid.local', password: 'citizen123' },
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
    <main className="min-h-screen flex items-center justify-center bg-command-bg p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            <h1 className="text-3xl font-bold tracking-wide text-command-text">ResQGrid AI</h1>
          </div>
          <p className="text-sm text-gray-400">Intelligent Emergency Resource Network</p>
        </div>

        {/* Login Card */}
        <form
          onSubmit={handleSubmit}
          className="bg-command-panel border border-command-border rounded-xl p-6 space-y-4"
        >
          <h2 className="text-lg font-semibold">Sign in to Command Center</h2>

          {error && (
            <div className="bg-red-900/40 border border-red-700 rounded-lg px-3 py-2 text-sm text-red-300">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-xs font-medium text-gray-400 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-command-bg border border-command-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-command-accent"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-xs font-medium text-gray-400 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-command-bg border border-command-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-command-accent"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-command-accent hover:opacity-90 rounded-lg text-sm font-semibold disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Demo Accounts */}
        <div className="mt-4 bg-command-panel/50 border border-command-border rounded-xl p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
            Demo Accounts (click to fill)
          </p>
          <div className="grid grid-cols-2 gap-2">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.role}
                type="button"
                onClick={() => {
                  setEmail(acc.email);
                  setPassword(acc.password);
                }}
                className={`px-3 py-2 rounded-lg border text-xs text-left transition-all ${
                  email === acc.email
                    ? 'border-command-accent bg-command-accent/10'
                    : 'border-command-border hover:border-gray-500'
                }`}
              >
                <span className="block font-semibold">{acc.role}</span>
                <span className="block text-gray-500 truncate">{acc.email}</span>
              </button>
            ))}
          </div>
        </div>

        <p className="text-center text-xs text-gray-500 mt-4">
          AI recommends. Humans approve. Every decision is auditable.
        </p>
      </div>
    </main>
  );
}
