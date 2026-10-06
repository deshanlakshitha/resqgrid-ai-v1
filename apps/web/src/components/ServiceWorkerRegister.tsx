'use client';

import { useEffect } from 'react';

export function ServiceWorkerRegister() {
  useEffect(() => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return;

    navigator.serviceWorker
      .register('/sw.js')
      .then((reg) => {
        // eslint-disable-next-line no-console
        console.log('ResQGrid AI service worker registered:', reg.scope);
      })
      .catch((err) => {
        // eslint-disable-next-line no-console
        console.error('Service worker registration failed:', err);
      });
  }, []);

  return null;
}
