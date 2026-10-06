'use client';

import { useMemo, useState } from 'react';
import {
  Waves, Flame, Mountain, Activity, Car, HeartPulse, Biohazard, Building2,
  AlertTriangle, Inbox, type LucideIcon,
} from 'lucide-react';
import type { Incident } from '@/lib/api';
import { cn, severityColor, severityDot, timeAgo } from '@/lib/utils';

interface Props {
  incidents: Incident[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'critical', label: 'Critical' },
  { key: 'high', label: 'High' },
  { key: 'medium', label: 'Medium' },
  { key: 'low', label: 'Low' },
] as const;

const TYPE_ICONS: Record<string, LucideIcon> = {
  flood: Waves,
  fire: Flame,
  landslide: Mountain,
  earthquake: Activity,
  accident: Car,
  medical: HeartPulse,
  hazmat: Biohazard,
  infrastructure: Building2,
  other: AlertTriangle,
};

const TYPE_COLORS: Record<string, string> = {
  flood: 'text-blue-400 bg-blue-500/10 border-blue-500/25',
  fire: 'text-red-400 bg-red-500/10 border-red-500/25',
  landslide: 'text-amber-400 bg-amber-500/10 border-amber-500/25',
  earthquake: 'text-violet-400 bg-violet-500/10 border-violet-500/25',
  accident: 'text-orange-400 bg-orange-500/10 border-orange-500/25',
  medical: 'text-pink-400 bg-pink-500/10 border-pink-500/25',
  hazmat: 'text-lime-400 bg-lime-500/10 border-lime-500/25',
  infrastructure: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/25',
  other: 'text-slate-400 bg-slate-500/10 border-slate-500/25',
};

export function IncidentQueue({ incidents, selectedId, onSelect }: Props) {
  const [filter, setFilter] = useState<string>('all');

  const sorted = useMemo(() => {
    const filtered =
      filter === 'all' ? incidents : incidents.filter((i) => i.severity?.toLowerCase() === filter);
    const rank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
    return [...filtered].sort((a, b) => {
      // Priority score first, then severity, then newest
      const pd = (b.priority_score ?? -1) - (a.priority_score ?? -1);
      if (pd !== 0) return pd;
      const sd = (rank[a.severity?.toLowerCase() ?? ''] ?? 9) - (rank[b.severity?.toLowerCase() ?? ''] ?? 9);
      if (sd !== 0) return sd;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
  }, [incidents, filter]);

  return (
    <div className="p-3 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 px-1">
        <h2 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-60" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
          </span>
          Incident Queue
        </h2>
        <span className="text-xs font-semibold text-slate-300 tabular-nums px-2 py-0.5 rounded-md bg-command-raised border border-command-border">
          {incidents.length}
        </span>
      </div>

      {/* Severity filters */}
      <div className="flex gap-1 mb-3 p-1 bg-command-bg/70 rounded-lg border border-command-border">
        {FILTERS.map((f) => {
          const count =
            f.key === 'all'
              ? incidents.length
              : incidents.filter((i) => i.severity?.toLowerCase() === f.key).length;
          const active = filter === f.key;
          return (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={cn(
                'flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-[11px] font-medium transition-all',
                active
                  ? 'bg-command-raised text-white shadow-inner-line border border-command-borderhover'
                  : 'text-slate-500 hover:text-slate-300 border border-transparent'
              )}
            >
              {f.label}
              {count > 0 && (
                <span
                  className={cn(
                    'tabular-nums px-1 rounded text-[10px]',
                    active ? 'bg-blue-500/20 text-blue-300' : 'bg-command-raised text-slate-500'
                  )}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto space-y-2 -mx-1 px-1">
        {sorted.map((incident, idx) => {
          const TypeIcon = TYPE_ICONS[incident.incident_type?.toLowerCase()] ?? AlertTriangle;
          const typeColor = TYPE_COLORS[incident.incident_type?.toLowerCase()] ?? TYPE_COLORS.other;
          const selected = selectedId === incident.id;
          const score = incident.priority_score;

          return (
            <button
              key={incident.id}
              onClick={() => onSelect(incident.id)}
              className={cn(
                'group relative w-full text-left p-3 rounded-xl border transition-all animate-fade-in',
                selected
                  ? 'border-blue-500/60 bg-blue-500/8 shadow-glow-blue'
                  : 'border-command-borderhover/70 bg-command-panel/60 hover:border-slate-500 hover:bg-command-raised/70'
              )}
              style={{ animationDelay: `${Math.min(idx * 30, 300)}ms` }}
            >
              {/* Selected accent bar */}
              {selected && (
                <span className="absolute left-0 top-3 bottom-3 w-0.5 rounded-full bg-gradient-to-b from-blue-400 to-blue-600" />
              )}

              {/* Row 1: icon + severity + priority */}
              <div className="flex items-center gap-2 mb-2">
                <span
                  className={cn(
                    'w-7 h-7 rounded-lg border flex items-center justify-center shrink-0',
                    typeColor
                  )}
                >
                  <TypeIcon className="w-3.5 h-3.5" />
                </span>
                <span
                  className={cn(
                    'text-[10px] font-bold px-2 py-0.5 rounded-md tracking-wide',
                    severityColor(incident.severity)
                  )}
                >
                  {incident.severity?.toUpperCase()}
                </span>
                <span className="ml-auto flex items-center gap-1.5">
                  {score != null ? (
                    <>
                      <span className="text-[10px] text-slate-500">PRIORITY</span>
                      <span
                        className={cn(
                          'text-sm font-bold tabular-nums',
                          score >= 75
                            ? 'text-red-400'
                            : score >= 50
                              ? 'text-orange-400'
                              : score >= 25
                                ? 'text-yellow-400'
                                : 'text-green-400'
                        )}
                      >
                        {score.toFixed(0)}
                      </span>
                    </>
                  ) : (
                    <span className="text-[10px] text-slate-600 font-medium border border-dashed border-slate-700 rounded px-1.5 py-0.5">
                      NOT SCORED
                    </span>
                  )}
                </span>
              </div>

              {/* Row 2: title */}
              <p className="text-sm font-semibold leading-snug line-clamp-2 text-slate-200 group-hover:text-white transition-colors">
                {incident.title}
              </p>

              {/* Row 3: meta */}
              <div className="flex items-center gap-2 mt-2 text-[11px] text-slate-500">
                <span className="capitalize">{incident.incident_type}</span>
                <span className="w-1 h-1 rounded-full bg-slate-600" />
                <span className="capitalize">{incident.status?.replace('_', ' ')}</span>
                <span className="w-1 h-1 rounded-full bg-slate-600" />
                <span className="ml-auto tabular-nums">{timeAgo(incident.created_at)}</span>
              </div>

              {/* Priority bar */}
              {score != null && (
                <div className="mt-2 h-1 rounded-full bg-command-bg overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-500',
                      score >= 75
                        ? 'bg-gradient-to-r from-red-600 to-red-400'
                        : score >= 50
                          ? 'bg-gradient-to-r from-orange-600 to-orange-400'
                          : score >= 25
                            ? 'bg-gradient-to-r from-yellow-600 to-yellow-400'
                            : 'bg-gradient-to-r from-green-600 to-green-400'
                    )}
                    style={{ width: `${score}%` }}
                  />
                </div>
              )}
            </button>
          );
        })}

        {/* Empty state */}
        {sorted.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-in">
            <div className="w-14 h-14 rounded-2xl bg-command-raised border border-command-border flex items-center justify-center mb-4">
              <Inbox className="w-6 h-6 text-slate-600" />
            </div>
            <p className="text-sm font-medium text-slate-400">
              {incidents.length === 0 ? 'No incidents reported' : 'Nothing at this severity'}
            </p>
            <p className="text-xs text-slate-600 mt-1">
              {incidents.length === 0
                ? 'New reports will appear here in real time'
                : 'Try a different filter'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
