'use client';

import { useEffect, useState } from 'react';
import {
  isGoogleMapsConfigured,
  loadGoogleMaps,
  onGoogleMapsAuthFailure,
} from './googleMaps';

export type MapEngine = 'loading' | 'google' | 'maplibre';

/**
 * Chooses the map engine once per mount:
 *   - real Google Maps when NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is set and loads
 *   - otherwise (no key, key rejected, network blocked) the free OpenFreeMap
 *     dark basemap via MapLibre — the app always gets a real, detailed map.
 */
export function useMapEngine(): MapEngine {
  const [engine, setEngine] = useState<MapEngine>('loading');

  useEffect(() => {
    let cancelled = false;

    const useFallback = () => {
      if (!cancelled) setEngine('maplibre');
    };

    // Google fires this global if the API key is rejected (bad key, missing
    // billing, referrer restriction) — possibly AFTER the script "loaded".
    const unsubscribe = onGoogleMapsAuthFailure(useFallback);

    if (!isGoogleMapsConfigured()) {
      useFallback();
      return unsubscribe;
    }

    loadGoogleMaps()
      .then(() => {
        if (!cancelled) setEngine('google');
      })
      .catch(useFallback);

    // Safety net: never hang forever on a blocked or slow network
    const timer = window.setTimeout(() => {
      setEngine((current) => (current === 'loading' ? 'maplibre' : current));
    }, 12000);

    return () => {
      cancelled = true;
      unsubscribe();
      window.clearTimeout(timer);
    };
  }, []);

  return engine;
}
