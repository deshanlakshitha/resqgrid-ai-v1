'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  incidentAPI,
  recommendationAPI,
  type Incident,
  type Resource,
  type Recommendation,
} from '@/lib/api';
import { severityColor, formatDate, priorityLabel } from '@/lib/utils';

interface Props {
  incident: Incident | null;
  resources: Resource[];
  onChanged: () => Promise<void> | void;
}

export function DetailPanel({ incident, resources, onChanged }: Props) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const incidentId = incident?.id ?? null;

  // Load existing recommendations whenever a new incident is selected
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

  if (!incident) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-full text-gray-500 text-sm gap-2">
        <svg
          className="w-10 h-10 text-gray-600"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
          />
        </svg>
        <p>Select an incident to view details</p>
        <p className="text-xs text-gray-600">Click a marker on the map or an item in the queue</p>
      </div>
    );
  }

  const refreshIncident = async () => {
    await onChanged();
  };

  const runAction = async (name: string, action: () => Promise<void>) => {
    setLoadingAction(name);
    setError('');
    setSuccess('');
    try {
      await action();
      await refreshIncident();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : `Action failed: ${name}`);
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
      setSuccess('Recommendation approved (human decision logged)');
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

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className={`text-xs px-2 py-0.5 rounded font-medium ${severityColor(incident.severity)}`}>
            {incident.severity.toUpperCase()}
          </span>
          <span className="text-xs text-gray-400 capitalize">
            {incident.status.replace('_', ' ')}
          </span>
          {pendingCount > 0 && (
            <span className="text-xs px-2 py-0.5 rounded font-medium bg-yellow-500/20 text-yellow-400 border border-yellow-600/40">
              {pendingCount} pending approval
            </span>
          )}
        </div>
        <h2 className="text-lg font-bold leading-snug">{incident.title}</h2>
        <p className="text-sm text-gray-400 mt-1">{incident.description}</p>
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-red-900/40 border border-red-700 rounded-lg px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-900/40 border border-green-700 rounded-lg px-3 py-2 text-sm text-green-300">
          {success}
        </div>
      )}

      {/* Meta */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-command-bg rounded-lg p-2.5">
          <span className="text-gray-500">Type</span>
          <p className="font-medium uppercase">{incident.incident_type}</p>
        </div>
        <div className="bg-command-bg rounded-lg p-2.5">
          <span className="text-gray-500">Priority Score</span>
          <p className="font-medium">
            {incident.priority_score?.toFixed(1) ?? 'N/A'}{' '}
            <span className="text-gray-400">
              ({priorityLabel(incident.priority_score ?? null)})
            </span>
          </p>
        </div>
        <div className="bg-command-bg rounded-lg p-2.5">
          <span className="text-gray-500">People at Risk</span>
          <p className="font-medium">{incident.people_at_risk ?? 'Unknown'}</p>
        </div>
        <div className="bg-command-bg rounded-lg p-2.5">
          <span className="text-gray-500">Medical Need</span>
          <p className="font-medium">{incident.medical_need ? 'Yes' : 'No'}</p>
        </div>
      </div>

      {/* AI Triage Data */}
      {triage && (
        <div className="bg-command-bg rounded-lg p-3">
          <h3 className="text-xs font-semibold uppercase text-gray-400 mb-2">
            AI Triage Result
          </h3>
          <div className="text-xs space-y-1.5">
            <div className="flex justify-between">
              <span className="text-gray-500">Confidence</span>
              <span className="font-medium">
                {incident.triage_confidence != null
                  ? `${(incident.triage_confidence * 100).toFixed(0)}%`
                  : 'N/A'}
              </span>
            </div>
            {triage.reason_codes && (
              <div>
                <span className="text-gray-500">Reason codes</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {(triage.reason_codes as string[]).map((code) => (
                    <span
                      key={code}
                      className="px-1.5 py-0.5 bg-blue-900/40 text-blue-300 rounded text-[10px]"
                    >
                      {code}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {incident.immediate_needs && incident.immediate_needs.length > 0 && (
              <div>
                <span className="text-gray-500">Immediate needs</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {incident.immediate_needs.map((need) => (
                    <span
                      key={need}
                      className="px-1.5 py-0.5 bg-red-900/40 text-red-300 rounded text-[10px]"
                    >
                      {need}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Priority breakdown */}
      {incident.priority_components && (
        <div className="bg-command-bg rounded-lg p-3">
          <h3 className="text-xs font-semibold uppercase text-gray-400 mb-2">
            Priority Breakdown (explainable)
          </h3>
          <div className="space-y-1.5">
            {Object.entries(incident.priority_components).map(([key, value]) => (
              <div key={key}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span className="text-gray-400 capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="text-gray-300">{(value as number).toFixed(1)}</span>
                </div>
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-command-accent rounded-full"
                    style={{ width: `${Math.min(100, (value as number) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col gap-2">
        <button
          onClick={handleTriage}
          disabled={loadingAction !== null}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loadingAction === 'triage' ? 'Running AI Triage...' : '🤖 Run AI Triage'}
        </button>
        <button
          onClick={handlePriority}
          disabled={loadingAction !== null}
          className="w-full py-2 px-4 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loadingAction === 'priority' ? 'Calculating...' : '⚖️ Calculate Priority'}
        </button>
        <button
          onClick={handleRecommend}
          disabled={loadingAction !== null}
          className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loadingAction === 'recommend' ? 'Matching Resources...' : '🎯 Get Recommendations'}
        </button>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold uppercase text-gray-400">
            AI Recommendations ({recommendations.length}) — Human approval required
          </h3>
          {recommendations.map((rec) => {
            const resource = resourceById(rec.resource_id);
            const isBusy = loadingAction === `approve-${rec.id}` || loadingAction === `reject-${rec.id}`;
            return (
              <div
                key={rec.id}
                className={`rounded-lg p-3 text-xs border ${
                  rec.status === 'PENDING'
                    ? 'bg-command-bg border-yellow-600/40'
                    : rec.status === 'APPROVED'
                      ? 'bg-green-950/40 border-green-700/50'
                      : 'bg-red-950/30 border-red-800/40'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-sm">
                      {resource?.name ?? 'Unknown resource'}
                      <span className="text-gray-400 font-normal">
                        {' '}
                        ({resource?.resource_type ?? '?'})
                      </span>
                    </p>
                    <p className="text-gray-400 mt-0.5">
                      Confidence: <span className="text-gray-200">{(rec.confidence * 100).toFixed(0)}%</span>
                      {rec.estimated_eta_minutes != null && (
                        <> · ETA: <span className="text-gray-200">{rec.estimated_eta_minutes.toFixed(1)} min</span></>
                      )}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                      rec.status === 'PENDING'
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : rec.status === 'APPROVED'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {rec.status}
                  </span>
                </div>

                {rec.compatibility_reasons && rec.compatibility_reasons.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {rec.compatibility_reasons.map((reason) => (
                      <span
                        key={reason}
                        className="px-1.5 py-0.5 bg-gray-700/60 text-gray-300 rounded text-[10px]"
                      >
                        {reason}
                      </span>
                    ))}
                  </div>
                )}

                {rec.reasoning && (
                  <p className="text-gray-500 mt-2 italic">&ldquo;{rec.reasoning}&rdquo;</p>
                )}

                {rec.status === 'PENDING' && (
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => handleApprove(rec)}
                      disabled={isBusy}
                      className="flex-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded font-medium disabled:opacity-50"
                    >
                      {loadingAction === `approve-${rec.id}` ? 'Approving...' : '✓ Approve & Dispatch'}
                    </button>
                    <button
                      onClick={() => handleReject(rec)}
                      disabled={isBusy}
                      className="flex-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded font-medium disabled:opacity-50"
                    >
                      {loadingAction === `reject-${rec.id}` ? 'Rejecting...' : '✕ Reject'}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Timestamps */}
      <div className="text-xs text-gray-500 border-t border-command-border pt-3 space-y-0.5">
        <p>Reported by: {incident.reporter_name ?? 'Unknown'}</p>
        <p>Created: {formatDate(incident.created_at)}</p>
        <p>Updated: {formatDate(incident.updated_at)}</p>
      </div>
    </div>
  );
}
