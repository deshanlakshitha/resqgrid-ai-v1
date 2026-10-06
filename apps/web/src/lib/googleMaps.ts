/**
 * Google Maps JavaScript API loader (singleton).
 *
 * Usage:
 *   - Set NEXT_PUBLIC_GOOGLE_MAPS_API_KEY in apps/web/.env.local
 *   - Call loadGoogleMaps() — resolves with the google.maps namespace
 *   - onGoogleMapsAuthFailure(cb) fires if the key/billing/referrer config
 *     rejects the request, so callers can gracefully fall back to the free
 *     OpenFreeMap basemap instead of showing a broken gray map.
 */

type GoogleMaps = typeof google.maps;

let loadPromise: Promise<GoogleMaps> | null = null;
let authFailed = false;
const authFailureListeners = new Set<() => void>();

declare global {
  interface Window {
    gm_authFailure?: () => void;
  }
}

export function isGoogleMapsConfigured(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY);
}

export function hasGoogleMapsAuthFailed(): boolean {
  return authFailed;
}

/** Subscribe to key-rejection events. Returns an unsubscribe function. */
export function onGoogleMapsAuthFailure(listener: () => void): () => void {
  authFailureListeners.add(listener);
  return () => {
    authFailureListeners.delete(listener);
  };
}

export function loadGoogleMaps(): Promise<GoogleMaps> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Google Maps can only load in the browser'));
  }
  if (loadPromise) return loadPromise;

  loadPromise = new Promise<GoogleMaps>((resolve, reject) => {
    const existing = (window as unknown as { google?: { maps?: GoogleMaps } }).google?.maps;
    if (existing) {
      resolve(existing);
      return;
    }

    const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    if (!key) {
      loadPromise = null;
      reject(new Error('NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is not set'));
      return;
    }

    // Register the auth-failure hook BEFORE the script loads — Google calls
    // this global when the key, billing, or referrer config is rejected.
    window.gm_authFailure = () => {
      authFailed = true;
      authFailureListeners.forEach((cb) => cb());
    };

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&loading=async`;
    script.async = true;
    script.onload = () => {
      const maps = (window as unknown as { google?: { maps?: GoogleMaps } }).google?.maps;
      if (maps) {
        resolve(maps);
      } else {
        loadPromise = null;
        reject(new Error('Google Maps script loaded but the maps namespace is missing'));
      }
    };
    script.onerror = () => {
      loadPromise = null;
      reject(new Error('Failed to load the Google Maps script'));
    };
    document.head.appendChild(script);
  });

  return loadPromise;
}
