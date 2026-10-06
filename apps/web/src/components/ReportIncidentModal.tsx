'use client';

import { useState } from 'react';
import {
  Waves, Flame, Mountain, Activity, Car, HeartPulse, Biohazard, Building2,
  AlertTriangle, X, Loader2, MapPin, Users, type LucideIcon,
} from 'lucide-react';
import { incidentAPI } from '@/lib/api';
import { cn } from '@/lib/utils';
import { LocationPickerMap } from './LocationPickerMap';

const INCIDENT_TYPES: { key: string; icon: LucideIcon }[] = [
  { key: 'flood', icon: Waves },
  { key: 'fire', icon: Flame },
  { key: 'landslide', icon: Mountain },
  { key: 'earthquake', icon: Activity },
  { key: 'accident', icon: Car },
  { key: 'medical', icon: HeartPulse },
  { key: 'hazmat', icon: Biohazard },
  { key: 'infrastructure', icon: Building2 },
  { key: 'other', icon: AlertTriangle },
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

  const inputCls =
    'w-full bg-command-bg border border-command-borderhover/60 rounded-xl px-3.5 py-2.5 text-sm placeholder:text-slate-600 focus:outline-none focus:border-blue-500/60 focus:ring-2 focus:ring-blue-500/20 transition-all';

  // Coordinates for the map picker (fall back to Singapore center while empty)
  const latNum = parseFloat(latitude);
  const lngNum = parseFloat(longitude);
  const pickerLat = Number.isFinite(latNum) ? latNum : 1.3521;
  const pickerLng = Number.isFinite(lngNum) ? lngNum : 103.8198;

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-command-panel border border-command-borderhover rounded-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto shadow-panel animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 border-b border-command-border bg-command-panel/95 backdrop-blur rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-red-600 to-red-800 flex items-center justify-center shadow-glow-red">
              <AlertTriangle className="w-4.5 h-4.5 w-[18px] h-[18px] text-white" />
            </div>
            <div>
              <h2 className="text-base font-bold leading-tight">Report New Incident</h2>
              <p className="text-[11px] text-slate-500">Goes live to all dispatchers instantly</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-command-raised transition-colors"
            aria-label="Close"
          >
            <X className="w-4.5 h-4.5 w-[18px] h-[18px]" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {error && (
            <div className="flex items-start gap-2.5 bg-red-500/10 border border-red-500/30 rounded-xl px-3.5 py-2.5 text-sm text-red-400 animate-fade-in">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              {error}
            </div>
          )}

          {/* Incident type selector */}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Incident Type
            </label>
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
              {INCIDENT_TYPES.map(({ key, icon: Icon }) => {
                const active = incidentType === key;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setIncidentType(key)}
                    className={cn(
                      'flex flex-col items-center gap-1 py-2.5 rounded-xl border text-[10px] font-medium capitalize transition-all',
                      active
                        ? 'border-blue-500/60 bg-blue-500/10 text-blue-300 shadow-glow-blue'
                        : 'border-command-borderhover/60 text-slate-500 hover:border-slate-500 hover:text-slate-300'
                    )}
                  >
                    <Icon className={cn('w-5 h-5', active && 'scale-110 transition-transform')} />
                    {key}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              required
              minLength={1}
              maxLength={500}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Building fire at Central Market"
              className={inputCls}
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Description <span className="text-red-400">*</span>
            </label>
            <textarea
              required
              minLength={1}
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is happening? How many people are affected? Any visible hazards?"
              className={cn(inputCls, 'resize-none')}
            />
          </div>

          {/* Location — pick on the map or type exact coordinates */}
          <div>
            <label className="flex items-center gap-1.5 text-xs font-medium text-slate-400 mb-2">
              <MapPin className="w-3.5 h-3.5" />
              Location <span className="text-red-400">*</span>
            </label>
            <LocationPickerMap
              latitude={pickerLat}
              longitude={pickerLng}
              onChange={(lat, lng) => {
                setLatitude(lat.toFixed(6));
                setLongitude(lng.toFixed(6));
              }}
            />
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div>
                <span className="block text-[10px] text-slate-600 mb-1">Latitude</span>
                <input
                  required
                  type="number"
                  step="any"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  className={cn(inputCls, 'tabular-nums')}
                />
              </div>
              <div>
                <span className="block text-[10px] text-slate-600 mb-1">Longitude</span>
                <input
                  required
                  type="number"
                  step="any"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  className={cn(inputCls, 'tabular-nums')}
                />
              </div>
            </div>
            <p className="text-[10px] text-slate-600 mt-1.5">
              Click the map, drag the pin, or use “My location” — fine-tune the coordinates below if needed.
            </p>
          </div>

          {/* People + medical */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="flex items-center gap-1.5 text-xs font-medium text-slate-400 mb-1.5">
                <Users className="w-3.5 h-3.5" />
                People at Risk
              </label>
              <input
                type="number"
                min={0}
                value={peopleAtRisk}
                onChange={(e) => setPeopleAtRisk(e.target.value)}
                placeholder="0"
                className={cn(inputCls, 'tabular-nums')}
              />
            </div>
            <label className="flex items-center gap-2.5 rounded-xl border border-command-borderhover/60 bg-command-bg px-3.5 py-2.5 cursor-pointer hover:border-slate-500 transition-colors">
              <input
                type="checkbox"
                checked={medicalNeed}
                onChange={(e) => setMedicalNeed(e.target.checked)}
                className="w-4 h-4 rounded"
              />
              <span className="text-sm text-slate-300 leading-tight">
                Medical need
                <span className="block text-[10px] text-slate-600">Injuries reported on scene</span>
              </span>
            </label>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 rounded-xl text-sm font-bold shadow-glow-red hover:-translate-y-px active:translate-y-0 transition-all disabled:opacity-50 disabled:hover:translate-y-0 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Submitting…
              </>
            ) : (
              'Submit Report'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
