'use client';

import { useEffect, useState } from 'react';
import { incidentAPI } from '@/lib/api';
import { severityColor, formatDate } from '@/lib/utils';

interface Incident {
  id: string;
  title: string;
  severity: string;
  status: string;
  incident_type: string;
  priority_score: number | null;
  created_at: string;
}

interface Props {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function IncidentQueue({ selectedId, onSelect }: Props) {
  const [incidents, setIncidents] = useState<Incident[]>([]);

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const { data } = await incidentAPI.list();
        setIncidents(data);
      } catch {
        // API not available
      }
    };
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 15000);
    return () => clearInterval(interval);
  }, []);

  const sorted = [...incidents].sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0));

  return (
    <div className="p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-3">
        Incident Queue ({incidents.length})
      </h2>
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
              <span>{incident.status}</span>
              <span>·</span>
              <span>{formatDate(incident.created_at)}</span>
            </div>
          </button>
        ))}
        {incidents.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-8">No incidents reported</p>
        )}
      </div>
    </div>
  );
}
