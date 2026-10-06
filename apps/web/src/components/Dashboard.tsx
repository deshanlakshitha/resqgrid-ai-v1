'use client';

import { useState } from 'react';
import { IncidentQueue } from './IncidentQueue';
import { CommandMap } from './CommandMap';
import { DetailPanel } from './DetailPanel';
import { KPIBar } from './KPIBar';

export function Dashboard() {
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Top: KPI Bar */}
      <KPIBar />

      {/* Main Content: 3-column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Incident Queue */}
        <aside className="w-80 border-r border-command-border overflow-y-auto">
          <IncidentQueue
            selectedId={selectedIncidentId}
            onSelect={setSelectedIncidentId}
          />
        </aside>

        {/* Center: Map */}
        <main className="flex-1 relative">
          <CommandMap selectedIncidentId={selectedIncidentId} />
        </main>

        {/* Right: Detail Panel */}
        <aside className="w-96 border-l border-command-border overflow-y-auto">
          <DetailPanel incidentId={selectedIncidentId} />
        </aside>
      </div>
    </div>
  );
}
