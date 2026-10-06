'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  BrainCircuit, Scale, Target, Check, X, Loader2, MapPin, Users, Stethoscope,
  Sparkles, History, AlertTriangle, CheckCircle2, XCircle, MousePointerClick,
} from 'lucide-react';
import {
  incidentAPI,
  recommendationAPI,
  type Incident,
  type Resource,
  type Recommendation,
} from '@/lib/api';
import { cn, severityColor, formatDate, priorityLabel } from '@/lib/utils';

interface Props {
  incident: Incident | null;
  resources: Resource[];
  onChanged: () => Promise<void> | void;
}

const WEIGHT_LABELS: Record<string, string> = {
  life_risk: 'Life Risk',
  medical_urgency: 'Medical Urgency',
  people_at_risk: 'People at Risk',
  environmental_risk: 'Environmental Risk',
  time_sensitivity: 'Time Sensitivity',
  evidence_confidence: 'Evidence Confidence',
};

function PriorityGauge({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score));
  const color = score >= 75 ? '#ef4444' : score >= 50 ? '#f97316' : score >= 25 ? '#eab308' : '#22c55e';
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="relative w-24 h-24 shrink-0">
      <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
          style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold tabular-nums" style={{ color }}>
          {score.toFixed(0)}
        </span>
        <span className="text-[9px] text-slate-500 uppercase tracking-wider">/ 100</span>
      </div>
    </div>
  );
}

function Section({ icon: Icon, title, children, accent }: {
  icon: React.ElementType;
  title: string;
  children: React.ReactNode;
  accent?: string;
}) {
  return (
    <div className="rounded-xl border border-command-borderhover/70 bg-command-panel/60 overflow-hidden">
      <div className="flex items-center gap-2 px-3.5 py-2.5 border-b border-command-border bg-command-bg/40">
        <Icon className={cn('w-3.5 h-3.5', accent ?? 'text-slate-400')} />
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{title}</h3>
      </div>
      <div className="p-3.5">{children}</div>
    </div>
  );
}

function Meta({ icon: Icon, label, value, valueClass }: {
  icon: React.ElementType;
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-xl border border-command-borderhover/70 bg-command-panel/60 p-3">
      <div className="flex items-center gap-1.5 text-slate-500 mb-1">
        <Icon className="w-3 h-3" />
        <span className="text-[10px] uppercase tracking-wider font-medium">{label}</span>
      </div>
      <p className={cn('text-sm font-semibold', valueClass)}>{value}</p>
    </div>
  );
}

export function DetailPanel({ incident, resources, onChanged }: Props) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const incidentId = incident?.id ?? null;

  const loadRecommendations = useCallback(async (id: string) => {
    try {
      const { data } = await recommendationAPI.list({ incident_id: id });
      setRecommendations(data);
    } catch {
      setRecommendations([]);
    }
  }, []);

  useEffect(() => {
    setError('');
    setSuccess('');
    if (incidentId) {
      loadRecommendations(incidentId);
    } else {
      setRecommendations([]);
    }
  }, [incidentId, loadRecommendations]);

  // Auto-dismiss success message
  useEffect(() => {
    if (success) {
      const t = setTimeout(() => setSuccess(''), 4000);
      return () => clearTimeout(t);
    }
  }, [success]);

  if (!incident) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8 gap-3">
        <div className="w-16 h-16 rounded-2xl bg-command-raised border border-command-border flex items-center justify-center">
          <MousePointerClick className="w-7 h-7 text-slate-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-slate-400">No incident selected</p>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
            Click a card in the queue or a marker on the map to open the full workflow
          </p>
        </div>
      </div>
    );
  }

  const runAction = async (name: string, action: () => Promise<void>) => {
    setLoadingAction(name);
    setError('');
    setSuccess('');
    try {
      await action();
      await onChanged();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : `Action failed. Please try again.`);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleTriage = () =>
    runAction('triage', async () => {
      await incidentAPI.runTriage(incident.id);
      setSuccess('AI triage completed');
    });

  const handlePriority = () =>
    runAction('priority', async () => {
      await incidentAPI.calculatePriority(incident.id);
      setSuccess('Priority score calculated');
    });

  const handleRecommend = () =>
    runAction('recommend', async () => {
      await incidentAPI.getRecommendations(incident.id);
      await loadRecommendations(incident.id);
      setSuccess('Resource recommendations generated');
    });

  const handleApprove = (rec: Recommendation) =>
    runAction(`approve-${rec.id}`, async () => {
      await recommendationAPI.approve(rec.id);
      await loadRecommendations(incident.id);
      setSuccess('Approved — dispatch decision logged to audit trail');
    });

  const handleReject = (rec: Recommendation) =>
    runAction(`reject-${rec.id}`, async () => {
      await recommendationAPI.reject(rec.id, 'Not suitable');
      await loadRecommendations(incident.id);
      setSuccess('Recommendation rejected');
    });

  const resourceById = (id: string) => resources.find((r) => r.id === id);
  const triage = incident.triage_data as Record<string, any> | null;
  const pendingCount = recommendations.filter((r) => r.status === 'PENDING').length;
  const hasScore = incident.priority_score != null;

  const actions = [
    {
      key: 'triage',
      label: 'Run AI Triage',
      icon: BrainCircuit,
      gradient: 'from-violet-600 to-violet-500',
      glow: 'shadow-glow-blue',
      handler: handleTriage,
      hint: 'AI analyzes the report',
    },
    {
      key: 'priority',
      label: 'Calculate Priority',
      icon: Scale,
      gradient: 'from-purple-600 to-fuchsia-500',
      glow: 'shadow-glow-blue',
      handler: handlePriority,
      hint: 'Deterministic weighted score',
    },
    {
      key: 'recommend',
      label: 'Get Recommendations',
      icon: Target,
      gradient: 'from-emerald-600 to-emerald-500',
      glow: 'shadow-glow-green',
      handler: handleRecommend,
      hint: 'Match nearby resources',
    },
  ];

  return (
    <div className="p-3.5 space-y-3.5 animate-fade-in">
      {/* ===== Header ===== */}
      <div className="rounded-xl border border-command-borderhover/70 bg-gradient-to-b from-command-raised to-command-panel p-4">
        <div className="flex items-center gap-2 mb-2.5">
          <span className={cn('text-[10px] font-bold px-2 py-0.5 rounded-md tracking-wider', severityColor(incident.severity))}>
            {incident.severity?.toUpperCase()}
          </span>
          <span className="text-[11px] px-2 py-0.5 rounded-md bg-command-bg text-slate-400 border border-command-border capitalize">
            {incident.status?.replace('_', ' ')}
          </span>
          {pendingCount > 0 && (
            <span className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded-md bg-yellow-500/15 text-yellow-400 border border-yellow-500/40 animate-blink">
              {pendingCount} PENDING
            </span>
          )}
        </div>
        <h2 className="text-base font-bold leading-snug">{incident.title}</h2>
        <p className="text-[13px] text-slate-400 mt-1.5 leading-relaxed">{incident.description}</p>
        {incident.address && (
          <p className="flex items-center gap-1.5 text-xs text-slate-500 mt-2">
            <MapPin className="w-3.5 h-3.5" />
            {incident.address}
          </p>
        )}
      </div>

      {/* ===== Alerts ===== */}
      {error && (
        <div className="flex items-start gap-2.5 bg-red-500/10 border border-red-500/30 rounded-xl px-3.5 py-2.5 text-sm text-red-400 animate-fade-in">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-start gap-2.5 bg-green-500/10 border border-green-500/30 rounded-xl px-3.5 py-2.5 text-sm text-green-400 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
          {success}
        </div>
      )}

      {/* ===== Priority gauge + quick meta ===== */}
      <div className="flex gap-3.5">
        {hasScore ? (
          <div className="flex flex-col items-center rounded-xl border border-command-borderhover/70 bg-command-panel/60 p-3 shrink-0">
            <PriorityGauge score={incident.priority_score!} />
            <span
              className={cn(
                'mt-1.5 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded',
                incident.priority_score! >= 75
                  ? 'text-red-400'
                  : incident.priority_score! >= 50
                    ? 'text-orange-400'
                    : incident.priority_score! >= 25
                      ? 'text-yellow-400'
                      : 'text-green-400'
              )}
            >
              {priorityLabel(incident.priority_score ?? null)}
            </span>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-command-panel/40 p-4 w-24 shrink-0">
            <Scale className="w-6 h-6 text-slate-700 mb-1" />
            <span className="text-[9px] text-slate-600 uppercase tracking-wider text-center leading-tight">
              No score yet
            </span>
          </div>
        )}

        <div className="grid grid-cols-1 gap-2 flex-1">
          <Meta icon={Users} label="People at Risk" value={String(incident.people_at_risk ?? 'Unknown')} />
          <Meta
            icon={Stethoscope}
            label="Medical Need"
            value={incident.medical_need ? 'Yes' : 'No'}
            valueClass={incident.medical_need ? 'text-red-400' : undefined}
          />
        </div>
      </div>

      {/* ===== AI Triage Result ===== */}
      {triage && (
        <Section icon={Sparkles} title="AI Triage Result" accent="text-violet-400">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Model Confidence</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-1.5 rounded-full bg-command-bg overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-violet-600 to-violet-400 rounded-full"
                    style={{ width: `${(incident.triage_confidence ?? 0) * 100}%` }}
                  />
                </div>
                <span className="text-xs font-bold text-violet-300 tabular-nums">
                  {incident.triage_confidence != null ? `${(incident.triage_confidence * 100).toFixed(0)}%` : '—'}
                </span>
              </div>
            </div>

            {triage.reason_codes && (triage.reason_codes as string[]).length > 0 && (
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Reason Codes</p>
                <div className="flex flex-wrap gap-1.5">
                  {(triage.reason_codes as string[]).map((code) => (
                    <span key={code} className="px-2 py-0.5 bg-blue-500/10 text-blue-300 border border-blue-500/25 rounded-md text-[10px] font-mono">
                      {code}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {incident.immediate_needs && incident.immediate_needs.length > 0 && (
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Immediate Needs</p>
                <div className="flex flex-wrap gap-1.5">
                  {incident.immediate_needs.map((need) => (
                    <span key={need} className="px-2 py-0.5 bg-red-500/10 text-red-300 border border-red-500/25 rounded-md text-[10px] font-medium">
                      {need}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* ===== Priority Breakdown ===== */}
      {incident.priority_components && (
        <Section icon={Scale} title="Priority Breakdown" accent="text-purple-400">
          <div className="space-y-2.5">
            {Object.entries(incident.priority_components).map(([key, value]) => (
              <div key={key}>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-400">{WEIGHT_LABELS[key] ?? key.replace(/_/g, ' ')}</span>
                  <span className="text-slate-300 font-semibold tabular-nums">
                    {(value as number).toFixed(1)}
                  </span>
                </div>
                <div className="h-1.5 bg-command-bg rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-600 to-fuchsia-400 rounded-full transition-all duration-700"
                    style={{ width: `${Math.min(100, (value as number) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
            <p className="text-[10px] text-slate-600 leading-relaxed pt-1 border-t border-command-border">
              Deterministic weighted sum — same input always produces the same score. Fully auditable.
            </p>
          </div>
        </Section>
      )}

      {/* ===== Action Buttons ===== */}
      <div className="grid grid-cols-3 gap-2">
        {actions.map((a) => {
          const busy = loadingAction === a.key;
          const disabled = loadingAction !== null;
          return (
            <button
              key={a.key}
              onClick={a.handler}
              disabled={disabled}
              title={a.hint}
              className={cn(
                'group flex flex-col items-center gap-1.5 py-3 px-2 rounded-xl text-[11px] font-semibold transition-all',
                'bg-gradient-to-b hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-40 disabled:hover:translate-y-0 disabled:pointer-events-auto cursor-pointer',
                a.gradient
              )}
            >
              {busy ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <a.icon className="w-5 h-5 transition-transform group-hover:scale-110" />
              )}
              <span className="text-center leading-tight">
                {busy ? 'Working…' : a.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* ===== Recommendations ===== */}
      {recommendations.length > 0 && (
        <Section icon={Target} title={`Recommendations — Human Approval Required`} accent="text-emerald-400">
          <div className="space-y-2.5">
            {recommendations.map((rec) => {
              const resource = resourceById(rec.resource_id);
              const isBusy =
                loadingAction === `approve-${rec.id}` || loadingAction === `reject-${rec.id}`;
              const approved = rec.status === 'APPROVED';
              const rejected = rec.status === 'REJECTED';

              return (
                <div
                  key={rec.id}
                  className={cn(
                    'rounded-xl border p-3 transition-all',
                    rec.status === 'PENDING'
                      ? 'border-yellow-500/30 bg-yellow-500/[0.04]'
                      : approved
                        ? 'border-green-500/30 bg-green-500/[0.04]'
                        : 'border-red-500/25 bg-red-500/[0.03]'
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate">
                        {resource?.name ?? 'Unknown resource'}
                      </p>
                      <p className="text-[11px] text-slate-500">
                        {resource?.resource_type ?? '—'}
                        {resource?.organization ? ` · ${resource.organization}` : ''}
                      </p>
                    </div>
                    <span
                      className={cn(
                        'shrink-0 text-[9px] font-bold px-2 py-1 rounded-md tracking-wider flex items-center gap-1',
                        rec.status === 'PENDING'
                          ? 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30'
                          : approved
                            ? 'bg-green-500/15 text-green-400 border border-green-500/30'
                            : 'bg-red-500/15 text-red-400 border border-red-500/30'
                      )}
                    >
                      {rec.status === 'PENDING' && <History className="w-3 h-3" />}
                      {rec.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 mt-2.5 text-[11px]">
                    <span className="flex items-center gap-1.5">
                      <span className="text-slate-500">Confidence</span>
                      <span className="font-bold text-emerald-400 tabular-nums">
                        {(rec.confidence * 100).toFixed(0)}%
                      </span>
                    </span>
                    {rec.estimated_eta_minutes != null && (
                      <span className="flex items-center gap-1.5">
                        <span className="text-slate-500">ETA</span>
                        <span className="font-bold text-blue-400 tabular-nums">
                          {rec.estimated_eta_minutes.toFixed(0)} min
                        </span>
                      </span>
                    )}
                  </div>

                  {rec.compatibility_reasons && rec.compatibility_reasons.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {rec.compatibility_reasons.slice(0, 4).map((reason) => (
                        <span
                          key={reason}
                          className="px-1.5 py-0.5 bg-command-raised text-slate-400 border border-command-border rounded text-[10px]"
                        >
                          {reason}
                        </span>
                      ))}
                    </div>
                  )}

                  {rec.status === 'PENDING' ? (
                    <div className="grid grid-cols-2 gap-2 mt-3">
                      <button
                        onClick={() => handleApprove(rec)}
                        disabled={isBusy}
                        className="flex items-center justify-center gap-1.5 px-3 py-2 bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-500 hover:to-emerald-400 rounded-lg text-xs font-semibold transition-all hover:-translate-y-px active:translate-y-0 disabled:opacity-50"
                      >
                        {loadingAction === `approve-${rec.id}` ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Check className="w-3.5 h-3.5" />
                        )}
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(rec)}
                        disabled={isBusy}
                        className="flex items-center justify-center gap-1.5 px-3 py-2 bg-command-raised border border-red-500/40 text-red-400 hover:bg-red-500/10 rounded-lg text-xs font-semibold transition-all disabled:opacity-50"
                      >
                        {loadingAction === `reject-${rec.id}` ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <X className="w-3.5 h-3.5" />
                        )}
                        Reject
                      </button>
                    </div>
                  ) : (
                    <div
                      className={cn(
                        'flex items-center gap-1.5 mt-2.5 text-[11px] font-medium',
                        approved ? 'text-green-400' : 'text-red-400'
                      )}
                    >
                      {approved ? (
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5" />
                      )}
                      {approved ? 'Human-approved decision logged' : 'Rejected by operator'}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {/* ===== Footer meta ===== */}
      <div className="text-[11px] text-slate-600 border-t border-command-border pt-3 flex items-center justify-between">
        <span>Reported by {incident.reporter_name ?? 'Unknown'}</span>
        <span className="tabular-nums">{formatDate(incident.created_at)}</span>
      </div>
    </div>
  );
}
