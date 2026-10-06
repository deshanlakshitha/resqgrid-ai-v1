'use client';

import { useCallback, useEffect, useState } from 'react';
import { IncidentQueue } from './IncidentQueue';
import { CommandMap } from './CommandMap';
import { DetailPanel } from './DetailPanel';
import { KPIBar } from './KPIBar';
import { ReportIncidentModal } from './ReportIncidentModal';
import { AssistantChat } from './AssistantChat';
import { incidentAPI, resourceAPI, dashboardAPI, hazardAPI } from '@/lib/api';
import type { Incident, Resource } from '@/lib/api';
import { useAuth } from '@/lib/auth';

export function Dashboard() {
  const { user, logout } = useAuth();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [summary, setSummary] = useState<Record<string, number | null> | null>(null);
  const [hazards, setHazards] = useState<any[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);
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

      {/* Main Content: 3-column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Incident Queue */}
        <aside className="w-80 border-r border-command-border overflow-y-auto">
          <IncidentQueue
            incidents={incidents}
            selectedId={selectedIncidentId}
            onSelect={setSelectedIncidentId}
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
        </main>

        {/* Right: Detail Panel */}
        <aside className="w-96 border-l border-command-border overflow-y-auto">
          <DetailPanel
            incident={selectedIncident}
            resources={resources}
            onChanged={refreshAll}
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
