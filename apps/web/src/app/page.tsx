'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { Dashboard } from '@/components/Dashboard';

function BootScreen({ message }: { message: string }) {
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-command-bg relative overflow-hidden">
      <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-40" />
      <div className="absolute inset-0 bg-radial-sweep" />
      <div className="relative flex flex-col items-center gap-5 animate-fade-in">
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center shadow-glow-blue">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <span className="absolute -inset-3 rounded-3xl border border-blue-500/20 animate-pulse-ring" />
        </div>
        <div className="text-center">
          <h1 className="text-lg font-bold tracking-tight">ResQGrid AI</h1>
          <p className="text-xs text-slate-500 mt-1">{message}</p>
        </div>
        <div className="flex gap-1.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-bounce"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const { user, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && !user) {
      router.replace('/login');
    }
  }, [ready, user, router]);

  if (!ready) {
    return <BootScreen message="Restoring session…" />;
  }

  if (!user) {
    return <BootScreen message="Redirecting to login…" />;
  }

  return <Dashboard />;
}
