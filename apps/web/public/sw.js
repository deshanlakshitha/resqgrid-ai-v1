const CACHE_NAME = 'resqgrid-ai-v2-security';
const SHELL_ASSETS = [
  '/',
  '/login',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/manifest.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Skip non-GET requests and API calls
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin ||
      url.pathname.startsWith('/api/') || url.pathname.startsWith('/uploads/') ||
      event.request.headers.has('Authorization')) {
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).then((response) => {
      if (response.ok) {
        const copy = response.clone();
        event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy)));
      }
      return response;
    }).catch(async () => (await caches.match(event.request)) || Response.error()));
    return;
  }
  if (!url.pathname.startsWith('/_next/static/') && !SHELL_ASSETS.includes(url.pathname)) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      return (
        cached ||
        fetch(event.request)
          .then((response) => {
            if (response.ok && response.type === 'basic') {
              const clone = response.clone();
              event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone)));
            }
            return response;
          })
          .catch(() => cached || Response.error())
      );
    })
  );
});
