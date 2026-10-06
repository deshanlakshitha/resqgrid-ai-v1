import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function severityColor(severity: string): string {
  switch (severity?.toLowerCase()) {
    case 'critical': return 'bg-red-500/15 text-red-400 border border-red-500/40';
    case 'high': return 'bg-orange-500/15 text-orange-400 border border-orange-500/40';
    case 'medium': return 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/40';
    case 'low': return 'bg-green-500/15 text-green-400 border border-green-500/40';
    default: return 'bg-gray-500/15 text-gray-400 border border-gray-500/40';
  }
}

export function severityDot(severity: string): string {
  switch (severity?.toLowerCase()) {
    case 'critical': return 'bg-red-500 shadow-glow-red';
    case 'high': return 'bg-orange-500';
    case 'medium': return 'bg-yellow-500';
    case 'low': return 'bg-green-500';
    default: return 'bg-gray-500';
  }
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function timeAgo(date: string): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function priorityLabel(score: number | null): string {
  if (score === null) return 'N/A';
  if (score >= 75) return 'Critical';
  if (score >= 50) return 'High';
  if (score >= 25) return 'Medium';
  return 'Low';
}

export function priorityColor(score: number | null): string {
  if (score === null) return 'text-gray-500';
  if (score >= 75) return 'text-red-400';
  if (score >= 50) return 'text-orange-400';
  if (score >= 25) return 'text-yellow-400';
  return 'text-green-400';
}

// Incident type display config: label + lucide icon name
export const INCIDENT_TYPE_META: Record<string, { label: string; icon: string }> = {
  flood: { label: 'Flood', icon: 'waves' },
  fire: { label: 'Fire', icon: 'flame' },
  landslide: { label: 'Landslide', icon: 'mountain' },
  earthquake: { label: 'Earthquake', icon: 'activity' },
  accident: { label: 'Accident', icon: 'car' },
  medical: { label: 'Medical', icon: 'heart-pulse' },
  hazmat: { label: 'Hazmat', icon: 'biohazard' },
  infrastructure: { label: 'Infrastructure', icon: 'building' },
  other: { label: 'Other', icon: 'alert-triangle' },
};

export function incidentTypeLabel(type: string): string {
  return INCIDENT_TYPE_META[type?.toLowerCase()]?.label ?? type;
}
