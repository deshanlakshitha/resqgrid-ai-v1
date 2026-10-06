'use client';

import { useState } from 'react';
import { incidentAPI } from '@/lib/api';

const INCIDENT_TYPES = [
  'flood', 'fire', 'landslide', 'earthquake', 'accident', 'medical', 'hazmat', 'infrastructure', 'other',
];

interface Props {
  onClose: () => void;
  onCreated: (incidentId: string) => void;
}

export function ReportIncidentModal({ onClose, onCreated }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [incidentType, setIncidentType] = useState('fire');
  const [latitude, setLatitude] = useState('1.3521');
  const [longitude, setLongitude] = useState('103.8198');
  const [peopleAtRisk, setPeopleAtRisk] = useState('');
  const [medicalNeed, setMedicalNeed] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await incidentAPI.create({
        title,
        description,
        incident_type: incidentType,
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        people_at_risk: peopleAtRisk ? parseInt(peopleAtRisk, 10) : undefined,
        medical_need: medicalNeed,
      });
      onCreated(data.id);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to create incident');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-command-panel border border-command-border rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-command-border">
          <h2 className="text-base font-semibold">Report New Incident</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="bg-red-900/40 border border-red-700 rounded-lg px-3 py-2 text-sm text-red-300">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Title *</label>
            <input
              required
              minLength={1}
              maxLength={500}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Building fire at Central Market"
              className="w-full bg-command-bg border border-command-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-command-accent"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Description *</label>
            <textarea
              required
              minLength={1}
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is happening? How many people are affected?"
              className="w-full bg-command-bg border border-command-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-command-accent resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Type</label>
              <select
                value={incidentType}
                onChange={(e) => setIncidentType(e.target.value)}
                className="w-full bg-command-bg border border-command-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-command-accent"
              >
                {INCIDENT_TYPES.map((t) => (
                  <option key={t} value={t}>{t.toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">People at Risk</label>
              <input
                type="number"
                min={0}
                value={peopleAtRisk}
                onChange={(e) => setPeopleAtRisk(e.target.value)}
                placeholder="0"
                className="w-full bg-command-bg border border-command-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-command-accent"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Latitude *</label>
              <input
                required
                type="number"
                step="any"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                className="w-full bg-command-bg border border-command-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-command-accent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Longitude *</label>
              <input
                required
                type="number"
                step="any"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                className="w-full bg-command-bg border border-command-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-command-accent"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={medicalNeed}
              onChange={(e) => setMedicalNeed(e.target.checked)}
              className="w-4 h-4 accent-blue-500"
            />
            <span className="text-gray-300">Medical assistance needed (injuries reported)</span>
          </label>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-command-accent hover:opacity-90 rounded-lg text-sm font-semibold disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Submit Report'}
          </button>
        </form>
      </div>
    </div>
  );
}
