import type { Incident, Resource } from '@/lib/api';
import { HAZARD_COLOR, esc, incidentColor, resourceColor } from '@/lib/mapConfig';
import type { Hazard } from './types';

/** Dark-themed info popup content shared by both map engines. */

export function hazardHtml(hazard: Hazard): string {
  return `<div style="font-size:12px;max-width:220px;">
    <div style="font-weight:700;margin-bottom:2px;">${esc(hazard.title)}</div>
    <div style="color:${HAZARD_COLOR};font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:0.05em;">${esc(hazard.hazard_type)}</div>
    <div style="color:#64748b;margin-top:3px;">
      severity: ${esc(hazard.severity)}${hazard.radius_meters ? ` · radius ${hazard.radius_meters}m` : ''}
    </div>
  </div>`;
}

export function resourceHtml(resource: Resource): string {
  const color = resourceColor(resource.status);
  return `<div style="font-size:12px;max-width:230px;">
    <div style="font-weight:700;">${esc(resource.name)}</div>
    <div style="color:${color};font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:0.05em;">${esc(resource.resource_type)} · ${esc(resource.status)}</div>
    ${resource.organization ? `<div style="color:#64748b;margin-top:2px;">${esc(resource.organization)}</div>` : ''}
    ${resource.capacity ? `<div style="color:#64748b;">capacity: ${resource.capacity}</div>` : ''}
  </div>`;
}

export function incidentHtml(incident: Incident): string {
  const color = incidentColor(incident.severity);
  return `<div style="font-size:12px;max-width:240px;">
    <div style="font-weight:700;margin-bottom:2px;">${esc(incident.title)}</div>
    <div style="color:${color};font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:0.05em;">${esc(incident.severity)} · ${esc(incident.incident_type)}</div>
    <div style="color:#64748b;margin-top:3px;">
      ${esc(incident.status)} · priority ${incident.priority_score != null ? incident.priority_score.toFixed(0) : 'N/A'}
    </div>
    ${incident.people_at_risk ? `<div style="color:#94a3b8;">${incident.people_at_risk} people at risk</div>` : ''}
  </div>`;
}
