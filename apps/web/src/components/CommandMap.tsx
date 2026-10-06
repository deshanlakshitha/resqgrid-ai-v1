'use client';

import { useEffect, useRef } from 'react';
import type { Incident, Resource } from '@/lib/api';

interface Hazard {
  id: string;
  hazard_type: string;
  title: string;
  status: string;
  latitude: number;
  longitude: number;
  radius_meters?: number | null;
  severity: string;
}

interface Props {
  incidents: Incident[];
  resources: Resource[];
  hazards: Hazard[];
  selectedIncidentId: string | null;
  onSelect: (id: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

const RESOURCE_COLORS: Record<string, string> = {
  AVAILABLE: '#22c55e',
  DEPLOYED: '#3b82f6',
  IN_TRANSIT: '#60a5fa',
  MAINTENANCE: '#6b7280',
  OFFLINE: '#4b5563',
};

function incidentColor(severity: string): string {
  return SEVERITY_COLORS[severity?.toLowerCase()] ?? '#6b7280';
}

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function CommandMap({
  incidents,
  resources,
  hazards,
  selectedIncidentId,
  onSelect,
}: Props) {
  const mapContainer = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const maplibreRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const markersRef = useRef<Map<string, any>>(new Map());
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const readyRef = useRef(false);

  // Initialize map once
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    let cancelled = false;

    const initMap = async () => {
      const maplibregl = (await import('maplibre-gl')).default;
      if (cancelled || !mapContainer.current) return;
      maplibreRef.current = maplibregl;

      const map = new maplibregl.Map({
        container: mapContainer.current,
        style:
          process.env.NEXT_PUBLIC_MAP_STYLE_URL ||
          'https://demotiles.maplibre.org/style.json',
        center: [103.8198, 1.3521],
        zoom: 11.5,
        attributionControl: { compact: true },
      });

      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');
      map.on('load', () => {
        readyRef.current = true;
        window.dispatchEvent(new Event('map-ready'));
      });

      mapRef.current = map;
    };

    initMap();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
      markersRef.current.clear();
      readyRef.current = false;
    };
  }, []);

  // Rebuild markers when data changes (simple + reliable)
  useEffect(() => {
    const maplibregl = maplibreRef.current;
    const map = mapRef.current;
    if (!maplibregl || !map || !readyRef.current) return;

    const sync = () => {
      for (const marker of markersRef.current.values()) {
        marker.remove();
      }
      markersRef.current.clear();

      const markers = markersRef.current;

      // ---- Hazards ----
      for (const hazard of hazards) {
        if (hazard.status && hazard.status !== 'ACTIVE' && hazard.status !== 'MONITORING') continue;
        const el = document.createElement('div');
        el.style.cssText = `
          width: 13px; height: 13px;
          background: transparent; border: 2px solid #f97316;
          transform: rotate(45deg); border-radius: 3px;
          box-shadow: 0 0 8px rgba(249,115,22,0.7); cursor: pointer; opacity: 0.9;
        `;
        el.title = `Hazard: ${hazard.title}`;

        const popup = new maplibregl.Popup({ offset: 24 }).setHTML(
          `<div style="font-size:12px;max-width:220px;">
            <div style="font-weight:700;margin-bottom:2px;">${esc(hazard.title)}</div>
            <div style="color:#fb923c;font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:0.05em;">${esc(hazard.hazard_type)}</div>
            <div style="color:#64748b;margin-top:3px;">
              severity: ${esc(hazard.severity)}${hazard.radius_meters ? ` · radius ${hazard.radius_meters}m` : ''}
            </div>
          </div>`
        );

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([hazard.longitude, hazard.latitude])
          .setPopup(popup)
          .addTo(map);
        markers.set(`hazard-${hazard.id}`, marker);
      }

      // ---- Resources ----
      for (const resource of resources) {
        const color = RESOURCE_COLORS[resource.status] ?? '#6b7280';
        const el = document.createElement('div');
        el.style.cssText = `
          width: 11px; height: 11px; border-radius: 3px;
          background: ${color}; border: 1.5px solid rgba(255,255,255,0.9);
          box-shadow: 0 0 5px ${color}aa; cursor: pointer; opacity: 0.95;
        `;
        el.title = `${resource.name} (${resource.status})`;

        const popup = new maplibregl.Popup({ offset: 20 }).setHTML(
          `<div style="font-size:12px;max-width:230px;">
            <div style="font-weight:700;">${esc(resource.name)}</div>
            <div style="color:${color};font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:0.05em;">${esc(resource.resource_type)} · ${esc(resource.status)}</div>
            ${resource.organization ? `<div style="color:#64748b;margin-top:2px;">${esc(resource.organization)}</div>` : ''}
            ${resource.capacity ? `<div style="color:#64748b;">capacity: ${resource.capacity}</div>` : ''}
          </div>`
        );

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([resource.longitude, resource.latitude])
          .setPopup(popup)
          .addTo(map);
        markers.set(`resource-${resource.id}`, marker);
      }

      // ---- Incidents (on top) ----
      for (const incident of incidents) {
        const color = incidentColor(incident.severity);
        const isSelected = incident.id === selectedIncidentId;
        const isCritical = incident.severity?.toLowerCase() === 'critical';
        const size = isSelected ? 26 : 19;

        const wrapper = document.createElement('div');
        wrapper.style.cssText = 'position:relative;cursor:pointer;';
        wrapper.title = incident.title;

        // Pulse ring for critical / selected
        if (isCritical || isSelected) {
          const ring = document.createElement('div');
          ring.style.cssText = `
            position:absolute; inset:-6px; border-radius:50%;
            border: 2px solid ${color}; opacity:0.6;
            animation: pulse-ring 1.8s cubic-bezier(0.4,0,0.6,1) infinite;
          `;
          wrapper.appendChild(ring);
        }

        const dot = document.createElement('div');
        dot.style.cssText = `
          position:relative; width:${size}px; height:${size}px; border-radius:50%;
          background:${color}; border:${isSelected ? 3 : 2}px solid #fff;
          box-shadow: 0 0 ${isSelected ? 16 : 8}px ${color};
          ${isSelected ? 'z-index:10;' : ''}
        `;
        wrapper.appendChild(dot);

        wrapper.addEventListener('click', (e) => {
          e.stopPropagation();
          onSelectRef.current(incident.id);
        });

        const popup = new maplibregl.Popup({ offset: 26 }).setHTML(
          `<div style="font-size:12px;max-width:240px;">
            <div style="font-weight:700;margin-bottom:2px;">${esc(incident.title)}</div>
            <div style="color:${color};font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:0.05em;">${esc(incident.severity)} · ${esc(incident.incident_type)}</div>
            <div style="color:#64748b;margin-top:3px;">
              ${esc(incident.status)} · priority ${incident.priority_score != null ? incident.priority_score.toFixed(0) : 'N/A'}
            </div>
            ${incident.people_at_risk ? `<div style="color:#94a3b8;">${incident.people_at_risk} people at risk</div>` : ''}
          </div>`
        );

        const marker = new maplibregl.Marker({ element: wrapper })
          .setLngLat([incident.longitude, incident.latitude])
          .setPopup(popup)
          .addTo(map);
        markers.set(`incident-${incident.id}`, marker);
      }
    };

    sync();

    const onReady = () => sync();
    window.addEventListener('map-ready', onReady);
    return () => window.removeEventListener('map-ready', onReady);
  }, [incidents, resources, hazards, selectedIncidentId]);

  // Fly to selected incident
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current || !selectedIncidentId) return;
    const incident = incidents.find((i) => i.id === selectedIncidentId);
    if (incident) {
      map.flyTo({ center: [incident.longitude, incident.latitude], zoom: 14, duration: 1200 });
    }
  }, [selectedIncidentId, incidents]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Legend */}
      <div className="absolute top-3 left-3 bg-command-panel/90 backdrop-blur-md rounded-xl px-4 py-3 text-[11px] border border-command-border shadow-panel z-10 pointer-events-none">
        <p className="text-[9px] font-semibold uppercase tracking-widest text-slate-500 mb-2">
          Live Map
        </p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-glow-red" /> Incidents
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-sm bg-green-500" /> Resources
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-sm bg-blue-500" /> Deployed
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 bg-transparent border-2 border-orange-500 rotate-45 rounded-[2px]" /> Hazards
          </span>
        </div>
      </div>

      {/* Map stats */}
      <div className="absolute bottom-3 left-3 flex gap-2 z-10 pointer-events-none">
        <span className="bg-command-panel/90 backdrop-blur-md rounded-lg px-3 py-1.5 text-[11px] text-slate-400 border border-command-border tabular-nums">
          <b className="text-slate-200">{incidents.length}</b> incidents ·{' '}
          <b className="text-slate-200">{resources.length}</b> resources ·{' '}
          <b className="text-slate-200">{hazards.length}</b> hazards
        </span>
      </div>
    </div>
  );
}
