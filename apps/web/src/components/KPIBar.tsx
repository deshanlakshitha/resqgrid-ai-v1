'use client';

import { useEffect, useState } from 'react';
import {
  ShieldCheck, Flame, Users, Truck, Clock, AlertOctagon, Zap,
  LogOut, PlusCircle, WifiOff, Wifi, ChevronUp,
} from 'lucide-react';
import type { AuthUser } from '@/lib/auth';
import { cn } from '@/lib/utils';

interface KPISummary {
  total_incidents: number;
  active_incidents: number;
  critical_incidents: number;
  available_resources: number;
  deployed_resources: number;
  pending_recommendations: number;
  active_assignments: number;
  active_hazards: number;
}

interface Props {
  summary: KPISummary | Record<string, number | null> | null;
  user: AuthUser | null;
  connected: boolean;
  onLogout: () => void;
  onReport: () => void;
}

function useClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return now;
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();
}

export function KPIBar({ summary, user, connected, onLogout, onReport }: Props) {
  const s = summary as KPISummary | null;
  const now = useClock();

  const kpis = [
    { icon: Zap, label: 'Active', value: s?.active_incidents, color: 'text-red-400', ring: 'group-hover:border-red-500/40' },
    { icon: Flame, label: 'Critical', value: s?.critical_incidents, color: 'text-red-500', ring: 'group-hover:border-red-500/40' },
    { icon: Truck, label: 'Resources', value: s?.available_resources, color: 'text-green-400', ring: 'group-hover:border-green-500/40' },
    { icon: Users, label: 'Deployed', value: s?.deployed_resources, color: 'text-blue-400', ring: 'group-hover:border-blue-500/40' },
    { icon: Clock, label: 'Pending', value: s?.pending_recommendations, color: 'text-yellow-400', ring: 'group-hover:border-yellow-500/40' },
    { icon: AlertOctagon, label: 'Hazards', value: s?.active_hazards, color: 'text-orange-400', ring: 'group-hover:border-orange-500/40' },
  ];

  return (
    <header className="relative z-20 bg-command-panel/95 backdrop-blur border-b border-command-border px-5 py-2.5 flex items-center gap-5 shadow-panel">
      {/* Brand */}
      <div className="flex items-center gap-2.5 pr-5 border-r border-command-border">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center shadow-glow-blue shrink-0">
          <ShieldCheck className="w-5 h-5 text-white" />
        </div>
        <div className="hidden sm:block">
          <h1 className="text-[15px] font-bold leading-tight tracking-tight">ResQGrid AI</h1>
          <p className="text-[10px] text-command-muted uppercase tracking-[0.15em] leading-tight">
            Command Center
          </p>
        </div>
      </div>

      {/* KPIs */}
      <div className="flex-1 flex items-center gap-2 overflow-x-auto">
        {kpis.map((kpi) => {
          const has = kpi.value != null;
          return (
            <div
              key={kpi.label}
              className={cn(
                'group flex items-center gap-2.5 px-3 py-1.5 rounded-xl border border-command-border bg-command-bg/60 transition-colors shrink-0',
                kpi.ring
              )}
              title={kpi.label}
            >
              <kpi.icon className={cn('w-4 h-4 shrink-0', kpi.color, !has && 'opacity-40')} />
              <div className="leading-none">
                <span className={cn('text-base font-bold tabular-nums', kpi.color)}>
                  {has ? kpi.value : '—'}
                </span>
                <span className="ml-1.5 text-[11px] text-slate-500">{kpi.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live clock */}
      <div className="hidden xl:flex flex-col items-end leading-tight tabular-nums border-l border-command-border pl-5">
        <span className="text-sm font-semibold">
          {now.toLocaleTimeString(undefined, { hour12: false })}
        </span>
        <span className="text-[10px] text-command-muted uppercase tracking-wider">
          {now.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
        </span>
      </div>

      {/* Connection pill */}
      <div
        className={cn(
          'hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border',
          connected
            ? 'bg-green-500/10 text-green-400 border-green-500/30'
            : 'bg-red-500/10 text-red-400 border-red-500/30 animate-blink'
        )}
        title={connected ? 'Connected to backend' : 'Backend offline'}
      >
        {connected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
        {connected ? 'LIVE' : 'OFFLINE'}
      </div>

      {/* Report button */}
      <button
        onClick={onReport}
        className="flex items-center gap-1.5 px-3.5 py-2 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 rounded-xl text-xs font-semibold shadow-glow-red hover:-translate-y-px active:translate-y-0 transition-all"
      >
        <PlusCircle className="w-4 h-4" />
        <span className="hidden sm:inline">Report Incident</span>
      </button>

      {/* User */}
      {user && (
        <div className="flex items-center gap-3 border-l border-command-border pl-4">
          <div className="hidden lg:flex flex-col items-end leading-tight">
            <p className="text-xs font-semibold">{user.full_name}</p>
            <p className="flex items-center gap-1 text-[10px] text-command-muted uppercase tracking-wider">
              <ChevronUp className="w-2.5 h-2.5 rotate-90 text-blue-400" />
              {user.role}
            </p>
          </div>
          <div className="relative">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-slate-600 to-slate-800 border-2 border-command-borderhover flex items-center justify-center text-xs font-bold text-slate-200">
              {initials(user.full_name)}
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-green-500 border-2 border-command-panel" />
          </div>
          <button
            onClick={onLogout}
            title="Sign out"
            className="p-2 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-command-raised transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      )}
    </header>
  );
}
