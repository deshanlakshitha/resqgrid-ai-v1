'use client';

import { useEffect, useRef, useState } from 'react';
import {
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  FALLBACK_MAP_STYLE_URL,
  HAZARD_COLOR,
  incidentColor,
  resourceColor,
} from '@/lib/mapConfig';
import { hazardHtml, incidentHtml, resourceHtml } from './popupHtml';
import type { CommandMapProps } from './types';

/**
 * MapLibre engine (free OpenFreeMap basemap) for the command center.
 * Mounted when no Google Maps API key is configured (or it was rejected).
 */
export function MapLibreCommandMap({
  incidents,
  resources,
  hazards,
  selectedIncidentId,
  onSelect,
}: CommandMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const maplibreRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const markersRef = useRef<Map<string, any>>(new Map());
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const [mapReady, setMapReady] = useState(false);

  // ---- Initialize once ----
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    let cancelled = false;

    const initMap = async () => {
      const maplibregl = (await import('maplibre-gl')).default;
      if (cancelled || !containerRef.current) return;
      maplibreRef.current = maplibregl;

      const map = new maplibregl.Map({
        container: containerRef.current,
        style: process.env.NEXT_PUBLIC_MAP_STYLE_URL || FALLBACK_MAP_STYLE_URL,
        center: [DEFAULT_CENTER.lng, DEFAULT_CENTER.lat],
        zoom: DEFAULT_ZOOM,
        attributionControl: { compact: true },
      });

      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');
      map.on('load', () => setMapReady(true));

      mapRef.current = map;
    };

    initMap();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
      markersRef.current.clear();
      setMapReady(false);
    };
  }, []);

  // ---- Rebuild markers whenever data or selection changes ----
  useEffect(() => {
    const maplibregl = maplibreRef.current;
    const map = mapRef.current;
    if (!maplibregl || !map || !mapReady) return;

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
        background: transparent; border: 2px solid ${HAZARD_COLOR};
        transform: rotate(45deg); border-radius: 3px;
        box-shadow: 0 0 8px rgba(249,115,22,0.7); cursor: pointer; opacity: 0.9;
      `;
      el.title = `Hazard: ${hazard.title}`;

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([hazard.longitude, hazard.latitude])
        .setPopup(new maplibregl.Popup({ offset: 24 }).setHTML(hazardHtml(hazard)))
        .addTo(map);
      markers.set(`hazard-${hazard.id}`, marker);
    }

    // ---- Resources ----
    for (const resource of resources) {
      const color = resourceColor(resource.status);
      const el = document.createElement('div');
      el.style.cssText = `
        width: 11px; height: 11px; border-radius: 3px;
        background: ${color}; border: 1.5px solid rgba(255,255,255,0.9);
        box-shadow: 0 0 5px ${color}aa; cursor: pointer; opacity: 0.95;
      `;
      el.title = `${resource.name} (${resource.status})`;

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([resource.longitude, resource.latitude])
        .setPopup(new maplibregl.Popup({ offset: 20 }).setHTML(resourceHtml(resource)))
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

      const marker = new maplibregl.Marker({ element: wrapper })
        .setLngLat([incident.longitude, incident.latitude])
        .setPopup(new maplibregl.Popup({ offset: 26 }).setHTML(incidentHtml(incident)))
        .addTo(map);
      markers.set(`incident-${incident.id}`, marker);
    }
  }, [incidents, resources, hazards, selectedIncidentId, mapReady]);

  // ---- Fly to the selected incident ----
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !selectedIncidentId) return;
    const incident = incidents.find((i) => i.id === selectedIncidentId);
    if (incident) {
      map.flyTo({ center: [incident.longitude, incident.latitude], zoom: 14, duration: 1200 });
    }
  }, [selectedIncidentId, incidents, mapReady]);

  return <div ref={containerRef} className="w-full h-full" />;
}
