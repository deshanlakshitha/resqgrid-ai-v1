'use client';

import { useMemo, useState } from 'react';
import type { Incident } from '@/lib/api';
import { severityColor, formatDate } from '@/lib/utils';

interface Props {
  incidents: Incident[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const FILTERS = ['all', 'critical', 'high', 'medium', 'low'] as const;

export function IncidentQueue({ incidents, selectedId, onSelect }: Props) {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('all');

  const sorted = useMemo(() => {
    const filtered = filter === 'all' ? incidents : incidents.filter((i) => i.severity === filter);
    return [...filtered].sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0));
  }, [incidents, filter]);

  return (
    <div className="p-3">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-2">
        Incident Queue ({incidents.length})
      </h2>

      {/* Severity filter */}
      <div className="flex gap-1 mb-3">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-2 py-1 rounded text-xs capitalize transition-colors ${
              filter === f
                ? 'bg-command-accent text-white font-medium'
                : 'bg-command-bg text-gray-400 hover:text-gray-200'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {sorted.map((incident) => (
          <button
            key={incident.id}
            onClick={() => onSelect(incident.id)}
            className={`w-full text-left p-3 rounded-lg border transition-all ${
              selectedId === incident.id
                ? 'border-command-accent bg-command-accent/10'
                : 'border-command-border hover:border-gray-500'
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-xs px-2 py-0.5 rounded font-medium ${severityColor(incident.severity)}`}>
                {incident.severity.toUpperCase()}
              </span>
              <span className="text-xs text-gray-400">
                Score: {incident.priority_score?.toFixed(1) ?? 'N/A'}
              </span>
            </div>
            <p className="text-sm font-medium truncate">{incident.title}</p>
            <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
              <span>{incident.incident_type}</span>
              <span>·</span>
              <span className="capitalize">{incident.status.replace('_', ' ')}</span>
              <span>·</span>
              <span>{formatDate(incident.created_at)}</span>
            </div>
          </button>
        ))}
        {sorted.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-8">
            {incidents.length === 0 ? 'No incidents reported' : 'No incidents at this severity'}
          </p>
        )}
      </div>
    </div>
  );
}
