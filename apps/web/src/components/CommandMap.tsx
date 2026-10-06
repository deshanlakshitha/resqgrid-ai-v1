'use client';

import { useEffect, useRef } from 'react';

interface Props {
  selectedIncidentId: string | null;
}

export function CommandMap({ selectedIncidentId }: Props) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<any>(null);

  useEffect(() => {
    if (!mapContainer.current || mapInstance.current) return;

    const initMap = async () => {
      const maplibregl = await import('maplibre-gl');

      mapInstance.current = new maplibregl.Map({
        container: mapContainer.current!,
        style: process.env.NEXT_PUBLIC_MAP_STYLE_URL || 'https://demotiles.maplibre.org/style.json',
        center: [103.8198, 1.3521], // Default: Singapore area
        zoom: 12,
      });

      mapInstance.current.addControl(new maplibregl.NavigationControl(), 'top-right');
    };

    initMap();

    return () => {
      mapInstance.current?.remove();
      mapInstance.current = null;
    };
  }, []);

  return (
    <div ref={mapContainer} className="w-full h-full">
      <div className="absolute top-4 left-4 bg-command-panel/90 backdrop-blur rounded-lg px-4 py-2 text-xs text-gray-400 z-10">
        Interactive Map — Incidents and Resources displayed as markers
      </div>
    </div>
  );
}
