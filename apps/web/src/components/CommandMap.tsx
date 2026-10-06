'use client';

import { Loader2 } from 'lucide-react';
import { useMapEngine } from '@/lib/useMapEngine';
import { GoogleCommandMap } from './map/GoogleCommandMap';
import { MapLibreCommandMap } from './map/MapLibreCommandMap';
import type { CommandMapProps } from './map/types';

/**
 * Command center map — real Google Maps when NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
 * is configured, otherwise the free OpenFreeMap dark basemap via MapLibre.
 * Both engines render identical markers, popups, and interactions.
 */
export function CommandMap(props: CommandMapProps) {
  const engine = useMapEngine();

  return (
    <div className="relative w-full h-full">
      {engine === 'google' && <GoogleCommandMap {...props} />}
      {engine === 'maplibre' && <MapLibreCommandMap {...props} />}
      {engine === 'loading' && (
        <div className="absolute inset-0 bg-grid-pattern bg-grid flex items-center justify-center">
          <div className="flex items-center gap-2 text-slate-500 text-xs">
            <Loader2 className="w-4 h-4 animate-spin" />
            Initializing live map…
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute top-3 left-3 bg-command-panel/90 backdrop-blur-md rounded-xl px-4 py-3 text-[11px] border border-command-border shadow-panel z-10 pointer-events-none">
        <p className="text-[9px] font-semibold uppercase tracking-widest text-slate-500 mb-2">
          Live Map
        </p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-glow-red" /> Incidents
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-sm bg-green-500" /> Resources
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-sm bg-blue-500" /> Deployed
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 bg-transparent border-2 border-orange-500 rotate-45 rounded-[2px]" /> Hazards
          </span>
        </div>
      </div>

      {/* Map stats */}
      <div className="absolute bottom-3 left-3 flex gap-2 z-10 pointer-events-none">
        <span className="bg-command-panel/90 backdrop-blur-md rounded-lg px-3 py-1.5 text-[11px] text-slate-400 border border-command-border tabular-nums">
          <b className="text-slate-200">{props.incidents.length}</b> incidents ·{' '}
          <b className="text-slate-200">{props.resources.length}</b> resources ·{' '}
          <b className="text-slate-200">{props.hazards.length}</b> hazards
        </span>
      </div>
    </div>
  );
}
