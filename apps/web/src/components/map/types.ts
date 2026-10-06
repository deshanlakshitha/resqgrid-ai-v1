import type { Incident, Resource } from '@/lib/api';

export interface Hazard {
  id: string;
  hazard_type: string;
  title: string;
  status: string;
  latitude: number;
  longitude: number;
  radius_meters?: number | null;
  severity: string;
}

export interface CommandMapProps {
  incidents: Incident[];
  resources: Resource[];
  hazards: Hazard[];
  selectedIncidentId: string | null;
  onSelect: (id: string) => void;
}
