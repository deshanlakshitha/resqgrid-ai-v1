'use client';

import { useCallback, useEffect, useState } from 'react';
import { ListFilter, X } from 'lucide-react';
import { IncidentQueue } from './IncidentQueue';
import { CommandMap } from './CommandMap';
import { DetailPanel } from './DetailPanel';
import { KPIBar } from './KPIBar';
import { ReportIncidentModal } from './ReportIncidentModal';
import { AssistantChat } from './AssistantChat';
import { incidentAPI, resourceAPI, dashboardAPI, hazardAPI } from '@/lib/api';
import type { Incident, Resource } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { cn } from '@/lib/utils';

export function Dashboard() {
  const { user, logout } = useAuth();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [summary, setSummary] = useState<Record<string, number | null> | null>(null);
  const [hazards, setHazards] = useState<any[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [showQueue, setShowQueue] = useState(false);
  const [connected, setConnected] = useState(true);

  // Central data refresh — called on mount, on interval, and after every action
  const refreshAll = useCallback(async () => {
    try {
      const [incRes, resRes, sumRes, hazRes] = await Promise.all([
        incidentAPI.list({ page_size: 200 }),
        resourceAPI.list(),
        dashboardAPI.getSummary().catch(() => null),
        hazardAPI.list().catch(() => null),
      ]);
      setIncidents(incRes.data);
      setResources(resRes.data);
      if (sumRes) setSummary(sumRes.data);
      if (hazRes) setHazards(hazRes.data);
      setConnected(true);
    } catch {
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 15000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  const selectedIncident = incidents.find((i) => i.id === selectedIncidentId) ?? null;

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Top: KPI Bar */}
      <KPIBar
        summary={summary}
        user={user}
        connected={connected}
        onLogout={logout}
        onReport={() => setShowReportModal(true)}
      />

      {/* Main Content: 3-column layout on desktop, map-first on mobile */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Mobile backdrop behind the queue drawer */}
        {showQueue && (
          <div
            className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
            onClick={() => setShowQueue(false)}
          />
        )}

        {/* Left: Incident Queue — slide-in drawer on mobile, sidebar on desktop */}
        <aside
          className={cn(
            'z-40 border-r border-command-border bg-command-panel overflow-y-auto',
            'fixed inset-y-0 left-0 w-[85%] max-w-sm transition-transform duration-300 ease-in-out',
            'lg:static lg:w-80 lg:translate-x-0',
            showQueue ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <button
            onClick={() => setShowQueue(false)}
            className="lg:hidden absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-command-bg/80 border border-command-border text-slate-400 hover:text-slate-200"
            title="Close queue"
          >
            <X className="w-4 h-4" />
          </button>
          <IncidentQueue
            incidents={incidents}
            selectedId={selectedIncidentId}
            onSelect={(id) => {
              setSelectedIncidentId(id);
              setShowQueue(false);
            }}
          />
        </aside>

        {/* Center: Map */}
        <main className="flex-1 relative">
          <CommandMap
            incidents={incidents}
            resources={resources}
            hazards={hazards}
            selectedIncidentId={selectedIncidentId}
            onSelect={setSelectedIncidentId}
          />
          {/* Mobile: floating button to open the incident queue */}
          <button
            onClick={() => setShowQueue(true)}
            className="lg:hidden absolute bottom-14 left-3 z-10 flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-command-panel/95 backdrop-blur-md border border-command-border shadow-panel text-xs font-semibold text-slate-200 active:scale-95 transition-transform"
          >
            <ListFilter className="w-4 h-4 text-blue-400" />
            Queue
            <span className="px-1.5 py-0.5 rounded-md bg-blue-500/15 text-blue-400 border border-blue-500/30 tabular-nums">
              {incidents.length}
            </span>
          </button>
        </main>

        {/* Right: Detail Panel — full-screen overlay on mobile, sidebar on desktop */}
        <aside
          className={cn(
            'z-40 border-command-border bg-command-panel overflow-y-auto lg:bg-transparent',
            selectedIncident
              ? 'fixed inset-0 lg:static lg:inset-auto lg:w-96 lg:border-l'
              : 'hidden lg:block lg:w-96 lg:border-l'
          )}
        >
          <DetailPanel
            incident={selectedIncident}
            resources={resources}
            onChanged={refreshAll}
            onClose={() => setSelectedIncidentId(null)}
          />
        </aside>
      </div>

      {/* Report Incident Modal */}
      {showReportModal && (
        <ReportIncidentModal
          onClose={() => setShowReportModal(false)}
          onCreated={(id) => {
            setShowReportModal(false);
            setSelectedIncidentId(id);
            refreshAll();
          }}
        />
      )}

      {/* AI Command Assistant */}
      <AssistantChat />
    </div>
  );
}
