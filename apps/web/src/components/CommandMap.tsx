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
  critical: '#dc2626',
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
        center: [103.8198, 1.3521], // Singapore (matches seed data)
        zoom: 11,
      });

      map.addControl(new maplibregl.NavigationControl(), 'top-right');
      map.on('load', () => {
        readyRef.current = true;
        // Force a marker sync after load
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

  // Remove all markers and re-add them (simple, reliable sync on data change)
  useEffect(() => {
    const maplibregl = maplibreRef.current;
    const map = mapRef.current;
    if (!maplibregl || !map || !readyRef.current) return;

    const sync = () => {
      // Clear existing markers
      for (const marker of markersRef.current.values()) {
        marker.remove();
      }
      markersRef.current.clear();

      const markers = markersRef.current;

      // Hazards: orange triangles (rendered as rotated squares)
      for (const hazard of hazards) {
        if (hazard.status && hazard.status !== 'ACTIVE' && hazard.status !== 'MONITORING') continue;
        const el = document.createElement('div');
        el.style.cssText = `
          width: 14px; height: 14px;
          background: transparent; border: 2px solid #f97316;
          transform: rotate(45deg); border-radius: 2px;
          box-shadow: 0 0 6px #f97316; cursor: pointer; opacity: 0.85;
        `;
        el.title = `Hazard: ${hazard.title}`;

        const popup = new maplibregl.Popup({ offset: 24 }).setHTML(
          `<div style="color:#111;font-size:12px;max-width:220px;">
            <strong>${hazard.title}</strong><br/>
            <span style="color:#ea580c;font-weight:600;text-transform:uppercase;">${hazard.hazard_type}</span>
            · severity: ${hazard.severity}<br/>
            ${hazard.radius_meters ? `Radius: ${hazard.radius_meters}m` : ''}
          </div>`
        );

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([hazard.longitude, hazard.latitude])
          .setPopup(popup)
          .addTo(map);
        markers.set(`hazard-${hazard.id}`, marker);
      }

      // Resources: small colored circles
      for (const resource of resources) {
        const color = RESOURCE_COLORS[resource.status] ?? '#6b7280';
        const el = document.createElement('div');
        el.style.cssText = `
          width: 12px; height: 12px; border-radius: 3px;
          background: ${color}; border: 1.5px solid white;
          box-shadow: 0 0 4px ${color}; cursor: pointer; opacity: 0.9;
        `;
        el.title = `${resource.name} (${resource.status})`;

        const popup = new maplibregl.Popup({ offset: 24 }).setHTML(
          `<div style="color:#111;font-size:12px;max-width:220px;">
            <strong>${resource.name}</strong><br/>
            <span style="color:${color};font-weight:600;">${resource.resource_type}</span>
            · ${resource.status}<br/>
            ${resource.organization ? `${resource.organization}<br/>` : ''}
            ${resource.capacity ? `Capacity: ${resource.capacity}` : ''}
          </div>`
        );

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([resource.longitude, resource.latitude])
          .setPopup(popup)
          .addTo(map);
        markers.set(`resource-${resource.id}`, marker);
      }

      // Incidents: larger severity-colored circles (on top)
      for (const incident of incidents) {
        const color = incidentColor(incident.severity);
        const isSelected = incident.id === selectedIncidentId;

        const el = document.createElement('div');
        el.style.cssText = `
          width: ${isSelected ? 24 : 18}px; height: ${isSelected ? 24 : 18}px;
          border-radius: 50%;
          background: ${color}; border: ${isSelected ? 3 : 2}px solid white;
          box-shadow: 0 0 ${isSelected ? 14 : 6}px ${color};
          cursor: pointer; z-index: ${isSelected ? 2 : 1};
        `;
        el.title = incident.title;
        el.addEventListener('click', (e) => {
          e.stopPropagation();
          onSelectRef.current(incident.id);
        });

        const popup = new maplibregl.Popup({ offset: 24 }).setHTML(
          `<div style="color:#111;font-size:12px;max-width:240px;">
            <strong>${incident.title}</strong><br/>
            <span style="color:${color};font-weight:600;text-transform:uppercase;">${incident.severity}</span>
            · ${incident.incident_type}<br/>
            Status: ${incident.status} · Priority: ${incident.priority_score?.toFixed(1) ?? 'N/A'}<br/>
            ${incident.people_at_risk ? `People at risk: ${incident.people_at_risk}` : ''}
          </div>`
        );

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([incident.longitude, incident.latitude])
          .setPopup(popup)
          .addTo(map);
        markers.set(`incident-${incident.id}`, marker);
      }
    };

    sync();

    // Re-sync once the map fires ready (in case data arrived before load)
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
    <div ref={mapContainer} className="w-full h-full">
      <div className="absolute top-4 left-4 bg-command-panel/90 backdrop-blur rounded-lg px-4 py-2 text-xs text-gray-300 z-10 pointer-events-none">
        <span className="inline-flex items-center gap-1.5 mr-3">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Incidents
        </span>
        <span className="inline-flex items-center gap-1.5 mr-3">
          <span className="w-2.5 h-2.5 rounded-sm bg-green-500" /> Available resources
        </span>
        <span className="inline-flex items-center gap-1.5 mr-3">
          <span className="w-2.5 h-2.5 rounded-sm bg-blue-500" /> Deployed
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 bg-transparent border-2 border-orange-500 rotate-45" /> Hazards
        </span>
      </div>
    </div>
  );
}
