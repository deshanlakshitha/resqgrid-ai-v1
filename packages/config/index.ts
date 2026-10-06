/**
 * ResQGrid AI — Shared Configuration Constants
 *
 * Central configuration values used by both frontend and backend.
 */

export const SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical'] as const;

export const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

export const INCIDENT_TYPES = [
  'flood', 'fire', 'landslide', 'earthquake',
  'accident', 'medical', 'hazmat', 'infrastructure', 'other',
] as const;

export const RESOURCE_TYPES = [
  'ambulance', 'fire_truck', 'rescue_boat', 'helicopter',
  'rescue_team', 'medical_team', 'shelter', 'generator',
  'supply_truck', 'drone', 'other',
] as const;

export const USER_ROLES = ['citizen', 'responder', 'dispatcher', 'admin'] as const;

export const PRIORITY_WEIGHTS = {
  life_risk: 0.30,
  medical_urgency: 0.20,
  people_at_risk: 0.15,
  environmental_risk: 0.15,
  time_sensitivity: 0.10,
  evidence_confidence: 0.10,
} as const;

export const API_VERSION = 'v1';
export const DEFAULT_MAP_CENTER = { latitude: 1.3521, longitude: 103.8198 };
export const DEFAULT_MAP_ZOOM = 12;
