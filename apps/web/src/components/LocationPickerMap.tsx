'use client';

import { useEffect, useRef, useState } from 'react';
import { Crosshair, Loader2, MapPin } from 'lucide-react';
import { useMapEngine } from '@/lib/useMapEngine';
import {
  FALLBACK_MAP_STYLE_URL,
  GOOGLE_MAP_DARK_STYLE,
} from '@/lib/mapConfig';

interface Props {
  latitude: number;
  longitude: number;
  onChange: (lat: number, lng: number) => void;
}

/**
 * Interactive location picker: click the map to drop the pin, drag the pin
 * to fine-tune, or hit "My location" to use the browser's GPS position.
 * Real Google Maps when configured, OpenFreeMap fallback otherwise.
 */
export function LocationPickerMap({ latitude, longitude, onChange }: Props) {
  const engine = useMapEngine();
  const [locating, setLocating] = useState(false);

  const handleLocate = () => {
    if (!('geolocation' in navigator)) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        onChange(pos.coords.latitude, pos.coords.longitude);
        setLocating(false);
      },
      () => setLocating(false),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  return (
    <div className="relative w-full h-56 rounded-xl overflow-hidden border border-command-borderhover/60 bg-command-bg">
      {engine === 'google' && (
        <GooglePicker latitude={latitude} longitude={longitude} onChange={onChange} />
      )}
      {engine === 'maplibre' && (
        <MapLibrePicker latitude={latitude} longitude={longitude} onChange={onChange} />
      )}
      {engine === 'loading' && (
        <div className="absolute inset-0 bg-grid-pattern bg-grid flex items-center justify-center">
          <div className="flex items-center gap-2 text-slate-500 text-xs">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading map…
          </div>
        </div>
      )}

      {/* Hint chip */}
      <div className="absolute top-2.5 left-2.5 z-10 pointer-events-none flex items-center gap-1.5 bg-command-panel/95 backdrop-blur border border-command-border rounded-lg px-2.5 py-1.5 text-[11px] text-slate-400 shadow-panel">
        <MapPin className="w-3.5 h-3.5 text-red-400" />
        Click the map or drag the pin
      </div>

      {/* GPS button */}
      <button
        type="button"
        onClick={handleLocate}
        className="absolute top-2.5 right-2.5 z-10 flex items-center gap-1.5 bg-command-panel/95 backdrop-blur border border-command-border rounded-lg px-2.5 py-1.5 text-[11px] font-medium text-slate-300 hover:text-white hover:border-blue-500/50 transition-colors shadow-panel"
      >
        {locating ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Crosshair className="w-3.5 h-3.5" />
        )}
        My location
      </button>
    </div>
  );
}

/** ---- Real Google Maps picker ---- */
function GooglePicker({ latitude, longitude, onChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const markerRef = useRef<google.maps.Marker | null>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    if (typeof google === 'undefined' || !google.maps) return;

    const map = new google.maps.Map(containerRef.current, {
      center: { lat: latitude, lng: longitude },
      zoom: 14,
      styles: GOOGLE_MAP_DARK_STYLE,
      backgroundColor: '#080c16',
      disableDefaultUI: true,
      zoomControl: true,
      gestureHandling: 'greedy',
      draggableCursor: 'crosshair',
      clickableIcons: false,
    });

    // Classic red Google pin — instantly readable "drop a pin" UX
    const marker = new google.maps.Marker({
      position: { lat: latitude, lng: longitude },
      map,
      draggable: true,
      title: 'Incident location',
      zIndex: 100,
    });

    marker.addListener('dragend', () => {
      const pos = marker.getPosition();
      if (pos) onChangeRef.current(pos.lat(), pos.lng());
    });
    map.addListener('click', (e: google.maps.MapMouseEvent) => {
      if (e.latLng) onChangeRef.current(e.latLng.lat(), e.latLng.lng());
    });

    mapRef.current = map;
    markerRef.current = marker;

    return () => {
      marker.setMap(null);
      markerRef.current = null;
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Follow external coordinate changes (inputs, GPS)
  useEffect(() => {
    const map = mapRef.current;
    const marker = markerRef.current;
    if (!map || !marker) return;
    const pos = marker.getPosition();
    if (!pos) return;
    if (Math.abs(pos.lat() - latitude) > 1e-9 || Math.abs(pos.lng() - longitude) > 1e-9) {
      const next = { lat: latitude, lng: longitude };
      marker.setPosition(next);
      map.panTo(next);
    }
  }, [latitude, longitude]);

  return <div ref={containerRef} className="w-full h-full" />;
}

/** ---- MapLibre (OpenFreeMap) picker ---- */
function MapLibrePicker({ latitude, longitude, onChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const markerRef = useRef<any>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    let cancelled = false;

    const init = async () => {
      const maplibregl = (await import('maplibre-gl')).default;
      if (cancelled || !containerRef.current) return;

      const map = new maplibregl.Map({
        container: containerRef.current,
        style: process.env.NEXT_PUBLIC_MAP_STYLE_URL || FALLBACK_MAP_STYLE_URL,
        center: [longitude, latitude],
        zoom: 13,
        attributionControl: { compact: true },
      });
      map.getCanvas().style.cursor = 'crosshair';

      const marker = new maplibregl.Marker({ draggable: true, color: '#ef4444' })
        .setLngLat([longitude, latitude])
        .addTo(map);

      marker.on('dragend', () => {
        const ll = marker.getLngLat();
        onChangeRef.current(ll.lat, ll.lng);
      });
      map.on('click', (e) => {
        onChangeRef.current(e.lngLat.lat, e.lngLat.lng);
      });

      mapRef.current = map;
      markerRef.current = marker;
    };

    init();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Follow external coordinate changes (inputs, GPS)
  useEffect(() => {
    const map = mapRef.current;
    const marker = markerRef.current;
    if (!map || !marker) return;
    const current = marker.getLngLat();
    if (Math.abs(current.lat - latitude) > 1e-9 || Math.abs(current.lng - longitude) > 1e-9) {
      marker.setLngLat([longitude, latitude]);
      map.panTo([longitude, latitude], { duration: 600 });
    }
  }, [latitude, longitude]);

  return <div ref={containerRef} className="w-full h-full" />;
}
