/**
 * ResQGrid AI — Shared TypeScript Type Definitions
 *
 * These types mirror the Pydantic schemas in the backend.
 * Keep them in sync when changing API contracts.
 */

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export type IncidentStatus =
  | 'reported' | 'triaged' | 'prioritized' | 'assigned'
  | 'in_progress' | 'resolved' | 'closed' | 'false_alarm';

export type IncidentType =
  | 'flood' | 'fire' | 'landslide' | 'earthquake'
  | 'accident' | 'medical' | 'hazmat' | 'infrastructure' | 'other';

export type ResourceType =
  | 'ambulance' | 'fire_truck' | 'rescue_boat' | 'helicopter'
  | 'rescue_team' | 'medical_team' | 'shelter' | 'generator'
  | 'supply_truck' | 'drone' | 'other';

export type ResourceStatus = 'available' | 'deployed' | 'in_transit' | 'maintenance' | 'offline';

export type UserRole = 'citizen' | 'responder' | 'dispatcher' | 'admin';

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  organization?: string;
  is_active: boolean;
  created_at: string;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  incident_type: IncidentType;
  severity: Severity;
  status: IncidentStatus;
  latitude: number;
  longitude: number;
  address?: string;
  people_at_risk?: number;
  vulnerable_people?: number;
  injuries_reported?: number;
  medical_need: boolean;
  triage_data?: TriageOutput;
  triage_confidence?: number;
  priority_score?: number;
  priority_components?: Record<string, number>;
  immediate_needs?: string[];
  evidence_quality?: number;
  reporter_name?: string;
  created_at: string;
  updated_at: string;
}

export interface TriageOutput {
  incident_type?: string;
  severity: Severity;
  people_at_risk?: number;
  vulnerable_people?: number;
  medical_need: boolean;
  immediate_needs: string[];
  evidence_quality: number;
  confidence: number;
  reason_codes: string[];
}

export interface Resource {
  id: string;
  name: string;
  resource_type: ResourceType;
  status: ResourceStatus;
  latitude: number;
  longitude: number;
  base_address?: string;
  capacity?: number;
  capabilities?: string[];
  organization?: string;
  contact_name?: string;
  max_range_km?: number;
  created_at: string;
}

export interface Recommendation {
  id: string;
  incident_id: string;
  resource_id: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  confidence: number;
  estimated_eta_minutes?: number;
  compatibility_reasons?: string[];
  constraints?: string[];
  alternatives?: string[];
  human_approval_required: boolean;
  created_at: string;
}

export interface Assignment {
  id: string;
  incident_id: string;
  resource_id: string;
  responder_id?: string;
  status: string;
  dispatched_at?: string;
  accepted_at?: string;
  arrived_at?: string;
  completed_at?: string;
  notes?: string;
  created_at: string;
}

export interface Hazard {
  id: string;
  hazard_type: string;
  title: string;
  description?: string;
  status: string;
  latitude: number;
  longitude: number;
  radius_meters?: number;
  severity: string;
  affected_routes?: string[];
  created_at: string;
}

export interface DashboardSummary {
  total_incidents: number;
  active_incidents: number;
  critical_incidents: number;
  available_resources: number;
  deployed_resources: number;
  pending_recommendations: number;
  active_assignments: number;
  active_hazards: number;
  avg_response_time_minutes?: number;
}
