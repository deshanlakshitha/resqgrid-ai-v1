'use client';

import type { AuthUser } from '@/lib/auth';

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

export function KPIBar({ summary, user, connected, onLogout, onReport }: Props) {
  const s = summary as KPISummary | null;

  const kpis = [
    { label: 'Active Incidents', value: s?.active_incidents ?? '—', color: 'text-red-400' },
    { label: 'Critical', value: s?.critical_incidents ?? '—', color: 'text-red-600' },
    { label: 'Available Resources', value: s?.available_resources ?? '—', color: 'text-green-400' },
    { label: 'Deployed', value: s?.deployed_resources ?? '—', color: 'text-blue-400' },
    { label: 'Pending Approvals', value: s?.pending_recommendations ?? '—', color: 'text-yellow-400' },
    { label: 'Active Hazards', value: s?.active_hazards ?? '—', color: 'text-orange-400' },
  ];

  return (
    <header className="bg-command-panel border-b border-command-border px-6 py-3 flex items-center gap-6">
      <div className="flex items-center gap-3">
        <div
          className={`w-3 h-3 rounded-full animate-pulse ${
            connected ? 'bg-green-500' : 'bg-red-500'
          }`}
          title={connected ? 'Connected to backend' : 'Backend offline'}
        />
        <h1 className="text-lg font-bold tracking-wide">ResQGrid AI</h1>
      </div>

      <div className="flex-1 flex items-center gap-6">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="flex items-center gap-2 text-sm">
            <span className={`${kpi.color} font-bold text-lg`}>{kpi.value}</span>
            <span className="text-gray-400">{kpi.label}</span>
          </div>
        ))}
      </div>

      <button
        onClick={onReport}
        className="px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium"
      >
        + Report Incident
      </button>

      {user && (
        <div className="flex items-center gap-3 border-l border-command-border pl-4">
          <div className="text-right">
            <p className="text-sm font-medium leading-tight">{user.full_name}</p>
            <p className="text-xs text-gray-400 uppercase">{user.role}</p>
          </div>
          <button
            onClick={onLogout}
            className="px-3 py-1.5 border border-command-border hover:border-gray-500 rounded-lg text-xs text-gray-300"
          >
            Logout
          </button>
        </div>
      )}
    </header>
  );
}
