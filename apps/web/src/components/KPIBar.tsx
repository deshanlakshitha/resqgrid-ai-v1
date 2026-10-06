'use client';

import { useEffect, useState } from 'react';
import { dashboardAPI } from '@/lib/api';

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

export function KPIBar() {
  const [summary, setSummary] = useState<KPISummary | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const { data } = await dashboardAPI.getSummary();
        setSummary(data);
      } catch {
        // API not available yet
      }
    };
    fetchSummary();
    const interval = setInterval(fetchSummary, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const kpis = [
    { label: 'Active Incidents', value: summary?.active_incidents ?? '—', color: 'text-red-400' },
    { label: 'Critical', value: summary?.critical_incidents ?? '—', color: 'text-red-600' },
    { label: 'Available Resources', value: summary?.available_resources ?? '—', color: 'text-green-400' },
    { label: 'Deployed', value: summary?.deployed_resources ?? '—', color: 'text-blue-400' },
    { label: 'Pending Approvals', value: summary?.pending_recommendations ?? '—', color: 'text-yellow-400' },
    { label: 'Active Hazards', value: summary?.active_hazards ?? '—', color: 'text-orange-400' },
  ];

  return (
    <header className="bg-command-panel border-b border-command-border px-6 py-3 flex items-center gap-8">
      <div className="flex items-center gap-3">
        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
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
    </header>
  );
}
