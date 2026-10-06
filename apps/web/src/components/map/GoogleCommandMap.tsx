'use client';

import { useEffect, useRef } from 'react';
import {
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  DIAMOND_PATH,
  GOOGLE_MAP_DARK_STYLE,
  HAZARD_COLOR,
  SQUARE_PATH,
  incidentColor,
  resourceColor,
} from '@/lib/mapConfig';
import { hazardHtml, incidentHtml, resourceHtml } from './popupHtml';
import type { CommandMapProps } from './types';

/**
 * Real Google Maps engine for the command center.
 * Mounted only when a valid NEXT_PUBLIC_GOOGLE_MAPS_API_KEY has loaded.
 */
export function GoogleCommandMap({
  incidents,
  resources,
  hazards,
  selectedIncidentId,
  onSelect,
}: CommandMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const infoWindowRef = useRef<google.maps.InfoWindow | null>(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  // ---- Initialize once ----
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    if (typeof google === 'undefined' || !google.maps) return;

    const map = new google.maps.Map(containerRef.current, {
      center: DEFAULT_CENTER,
      zoom: Math.round(DEFAULT_ZOOM),
      styles: GOOGLE_MAP_DARK_STYLE,
      backgroundColor: '#080c16',
      disableDefaultUI: true,
      zoomControl: true,
      fullscreenControl: true,
      gestureHandling: 'greedy',
      clickableIcons: false,
      minZoom: 3,
    });

    infoWindowRef.current = new google.maps.InfoWindow({ maxWidth: 260 });
    mapRef.current = map;

    return () => {
      markersRef.current.forEach((m) => m.setMap(null));
      markersRef.current = [];
      infoWindowRef.current?.close();
      infoWindowRef.current = null;
      mapRef.current = null;
    };
  }, []);

  // ---- Rebuild markers whenever data or selection changes ----
  useEffect(() => {
    const map = mapRef.current;
    const info = infoWindowRef.current;
    if (!map || !info) return;

    const attachPopup = (marker: google.maps.Marker, html: string) => {
      marker.addListener('click', () => {
        info.setContent(html);
        info.open({ map, anchor: marker });
      });
    };

    // Clear previous markers + close any open popup
    info.close();
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];
    const markers = markersRef.current;

    // ---- Hazards (orange outline diamonds, bottom layer) ----
    for (const hazard of hazards) {
      if (hazard.status && hazard.status !== 'ACTIVE' && hazard.status !== 'MONITORING') continue;
      const marker = new google.maps.Marker({
        position: { lat: hazard.latitude, lng: hazard.longitude },
        map,
        title: `Hazard: ${hazard.title}`,
        zIndex: 1,
        icon: {
          path: DIAMOND_PATH,
          scale: 8,
          fillColor: 'rgba(0,0,0,0)',
          fillOpacity: 0,
          strokeColor: HAZARD_COLOR,
          strokeOpacity: 0.9,
          strokeWeight: 2,
        },
      });
      attachPopup(marker, hazardHtml(hazard));
      markers.push(marker);
    }

    // ---- Resources (status-colored squares, middle layer) ----
    for (const resource of resources) {
      const color = resourceColor(resource.status);
      const marker = new google.maps.Marker({
        position: { lat: resource.latitude, lng: resource.longitude },
        map,
        title: `${resource.name} (${resource.status})`,
        zIndex: 2,
        icon: {
          path: SQUARE_PATH,
          scale: 6,
          fillColor: color,
          fillOpacity: 0.95,
          strokeColor: '#ffffff',
          strokeOpacity: 0.9,
          strokeWeight: 1.5,
        },
      });
      attachPopup(marker, resourceHtml(resource));
      markers.push(marker);
    }

    // ---- Incidents (severity-colored circles, top layer) ----
    for (const incident of incidents) {
      const color = incidentColor(incident.severity);
      const isSelected = incident.id === selectedIncidentId;
      const isCritical = incident.severity?.toLowerCase() === 'critical';
      const size = isSelected ? 26 : 19;

      // Glow halo behind critical / selected incidents
      if (isCritical || isSelected) {
        markers.push(
          new google.maps.Marker({
            position: { lat: incident.latitude, lng: incident.longitude },
            map,
            clickable: false,
            zIndex: 9,
            icon: {
              path: google.maps.SymbolPath.CIRCLE,
              scale: size,
              fillColor: color,
              fillOpacity: 0.15,
              strokeColor: color,
              strokeOpacity: 0.55,
              strokeWeight: 1.5,
            },
          })
        );
      }

      const marker = new google.maps.Marker({
        position: { lat: incident.latitude, lng: incident.longitude },
        map,
        title: incident.title,
        zIndex: isSelected ? 100 : 10,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: size / 2,
          fillColor: color,
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: isSelected ? 3 : 2,
        },
      });
      marker.addListener('click', () => onSelectRef.current(incident.id));
      attachPopup(marker, incidentHtml(incident));
      markers.push(marker);
    }
  }, [incidents, resources, hazards, selectedIncidentId]);

  // ---- Pan to the selected incident ----
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedIncidentId) return;
    const incident = incidents.find((i) => i.id === selectedIncidentId);
    if (!incident) return;
    map.panTo({ lat: incident.latitude, lng: incident.longitude });
    if ((map.getZoom() ?? 0) < 13) {
      window.setTimeout(() => mapRef.current?.setZoom(14), 300);
    }
  }, [selectedIncidentId, incidents]);

  return <div ref={containerRef} className="w-full h-full" />;
}
