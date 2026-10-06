/**
 * Shared map constants and styling used by both map engines
 * (real Google Maps + MapLibre/OpenFreeMap fallback).
 */

export const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

export const RESOURCE_COLORS: Record<string, string> = {
  AVAILABLE: '#22c55e',
  DEPLOYED: '#3b82f6',
  IN_TRANSIT: '#60a5fa',
  MAINTENANCE: '#6b7280',
  OFFLINE: '#4b5563',
};

export const HAZARD_COLOR = '#f97316';

export const DEFAULT_CENTER = { lat: 1.3521, lng: 103.8198 };
export const DEFAULT_ZOOM = 11.5;

/** Free, keyless, Google-Maps-style basemap used when no Google key is set. */
export const FALLBACK_MAP_STYLE_URL = 'https://tiles.openfreemap.org/styles/liberty';

export function incidentColor(severity: string | null | undefined): string {
  return SEVERITY_COLORS[(severity ?? '').toLowerCase()] ?? '#6b7280';
}

export function resourceColor(status: string | null | undefined): string {
  return RESOURCE_COLORS[status ?? ''] ?? '#6b7280';
}

export function esc(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** Google Maps dark "command center" style matching the app palette. */
export const GOOGLE_MAP_DARK_STYLE: google.maps.MapTypeStyle[] = [
  { elementType: 'geometry', stylers: [{ color: '#101a2e' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#080c16' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#7d8ea8' }] },
  { featureType: 'administrative', elementType: 'geometry', stylers: [{ color: '#1e293b' }] },
  { featureType: 'administrative.country', elementType: 'geometry.stroke', stylers: [{ color: '#334155' }] },
  { featureType: 'administrative.country', elementType: 'labels.text.fill', stylers: [{ color: '#94a3b8' }] },
  { featureType: 'administrative.locality', elementType: 'labels.text.fill', stylers: [{ color: '#94a3b8' }] },
  { featureType: 'administrative.neighborhood', elementType: 'labels.text.fill', stylers: [{ color: '#64748b' }] },
  { featureType: 'poi', elementType: 'labels.text.fill', stylers: [{ color: '#64748b' }] },
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#13241d' }] },
  { featureType: 'poi.park', elementType: 'labels.text.fill', stylers: [{ color: '#4d7260' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#1c2740' }] },
  { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#141d31' }] },
  { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#64748b' }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#2c3a58' }] },
  { featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: '#243050' }] },
  { featureType: 'road.highway', elementType: 'labels.text.fill', stylers: [{ color: '#94a3b8' }] },
  { featureType: 'transit', elementType: 'geometry', stylers: [{ color: '#1e293b' }] },
  { featureType: 'transit.station', elementType: 'labels.text.fill', stylers: [{ color: '#64748b' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0a1120' }] },
  { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#3d5a7d' }] },
];

/** SVG symbol paths drawn in a -1..1 box; Google scales them via `scale` (px). */
export const SQUARE_PATH = 'M -1 -1 L 1 -1 L 1 1 L -1 1 Z';
export const DIAMOND_PATH = 'M 0 -1 L 1 0 L 0 1 L -1 0 Z';
