'use client';

import { useEffect, useState } from 'react';
import { incidentAPI, recommendationAPI } from '@/lib/api';
import { severityColor, formatDate, priorityLabel } from '@/lib/utils';

interface Props {
  incidentId: string | null;
}

export function DetailPanel({ incidentId }: Props) {
  const [incident, setIncident] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!incidentId) {
      setIncident(null);
      setRecommendations([]);
      return;
    }

    const fetch = async () => {
      try {
        const { data } = await incidentAPI.get(incidentId);
        setIncident(data);
      } catch {
        setIncident(null);
      }
    };
    fetch();
  }, [incidentId]);

  if (!incidentId) {
    return (
      <div className="p-6 flex items-center justify-center h-full text-gray-500 text-sm">
        Select an incident to view details
      </div>
    );
  }

  if (!incident) {
    return <div className="p-6 text-gray-500 text-sm">Loading...</div>;
  }

  const handleTriage = async () => {
    setLoading(true);
    try {
      await incidentAPI.runTriage(incident.id);
      const { data } = await incidentAPI.get(incident.id);
      setIncident(data);
    } catch (err) {
      console.error('Triage failed:', err);
    }
    setLoading(false);
  };

  const handlePriority = async () => {
    setLoading(true);
    try {
      await incidentAPI.calculatePriority(incident.id);
      const { data } = await incidentAPI.get(incident.id);
      setIncident(data);
    } catch (err) {
      console.error('Priority calculation failed:', err);
    }
    setLoading(false);
  };

  const handleRecommend = async () => {
    setLoading(true);
    try {
      const { data } = await incidentAPI.getRecommendations(incident.id);
      setRecommendations(data);
    } catch (err) {
      console.error('Recommendations failed:', err);
    }
    setLoading(false);
  };

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className={`text-xs px-2 py-0.5 rounded font-medium ${severityColor(incident.severity)}`}>
            {incident.severity.toUpperCase()}
          </span>
          <span className="text-xs text-gray-400">{incident.status}</span>
        </div>
        <h2 className="text-lg font-bold">{incident.title}</h2>
        <p className="text-sm text-gray-400 mt-1">{incident.description}</p>
      </div>

      {/* Meta */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-command-bg rounded p-2">
          <span className="text-gray-500">Type</span>
          <p className="font-medium">{incident.incident_type}</p>
        </div>
        <div className="bg-command-bg rounded p-2">
          <span className="text-gray-500">Priority Score</span>
          <p className="font-medium">{incident.priority_score?.toFixed(1) ?? 'N/A'} ({priorityLabel(incident.priority_score)})</p>
        </div>
        <div className="bg-command-bg rounded p-2">
          <span className="text-gray-500">People at Risk</span>
          <p className="font-medium">{incident.people_at_risk ?? 'Unknown'}</p>
        </div>
        <div className="bg-command-bg rounded p-2">
          <span className="text-gray-500">Medical Need</span>
          <p className="font-medium">{incident.medical_need ? 'Yes' : 'No'}</p>
        </div>
      </div>

      {/* AI Triage Data */}
      {incident.triage_data && (
        <div className="bg-command-bg rounded-lg p-3">
          <h3 className="text-xs font-semibold uppercase text-gray-400 mb-2">AI Triage</h3>
          <div className="text-xs space-y-1">
            <p>Confidence: {(incident.triage_confidence * 100).toFixed(0)}%</p>
            <p>Reason codes: {incident.triage_reason_codes?.join(', ')}</p>
            <p>Immediate needs: {incident.immediate_needs?.join(', ')}</p>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col gap-2">
        <button
          onClick={handleTriage}
          disabled={loading}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Run AI Triage'}
        </button>
        <button
          onClick={handlePriority}
          disabled={loading}
          className="w-full py-2 px-4 bg-purple-600 hover:bg-purple-700 rounded text-sm font-medium disabled:opacity-50"
        >
          Calculate Priority
        </button>
        <button
          onClick={handleRecommend}
          disabled={loading}
          className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 rounded text-sm font-medium disabled:opacity-50"
        >
          Get Recommendations
        </button>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold uppercase text-gray-400">Recommendations</h3>
          {recommendations.map((rec) => (
            <div key={rec.id} className="bg-command-bg rounded-lg p-3 text-xs">
              <p className="font-medium">{rec.resource_name} ({rec.resource_type})</p>
              <p className="text-gray-400">Confidence: {(rec.confidence * 100).toFixed(0)}% · ETA: {rec.estimated_eta_minutes}min</p>
              <p className="text-gray-500 mt-1">{rec.compatibility_reasons?.join(' · ')}</p>
              <div className="flex gap-2 mt-2">
                <button
                  onClick={async () => {
                    await recommendationAPI.approve(rec.id);
                    setRecommendations([]);
                  }}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-xs"
                >
                  Approve
                </button>
                <button
                  onClick={async () => {
                    await recommendationAPI.reject(rec.id, 'Not suitable');
                    setRecommendations([]);
                  }}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-xs"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Timestamps */}
      <div className="text-xs text-gray-500 border-t border-command-border pt-3">
        <p>Created: {formatDate(incident.created_at)}</p>
        <p>Updated: {formatDate(incident.updated_at)}</p>
      </div>
    </div>
  );
}
