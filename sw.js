const CACHE_NAME = 'woooosh-cache-v8';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './images/icon-192x192.png',
  './images/icon-512x512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS_TO_CACHE))
      .then(() => self.skipWaiting())
      .catch(error => {
        console.error('[SW] cache.addAll() failed during install:', error);
        throw error;
      })
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => Promise.all(
      cacheNames.map(cacheName => {
        if (cacheName !== CACHE_NAME) {
          return caches.delete(cacheName);
        }
      })
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') {
    return;
  }
  // Never cache sync API requests — they must always hit the network
  if (event.request.url.includes('/sync/')) return;
  // Never cache version.json — it's used to detect app updates
  if (event.request.url.includes('/version.json')) return;

  // Navigations (opening the app, including the installed PWA launching at
  // start_url "/") MUST be network-first. Matching only URLs that contain
  // "index.html" misses the root path, which left installed apps pinned to
  // a stale cached copy forever.
  if (event.request.mode === 'navigate' || event.request.url.includes('index.html')) {
    event.respondWith(
      fetch(event.request).then(networkResponse => {
        const responseClone = networkResponse.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, responseClone);
        });
        return networkResponse;
      }).catch(() => {
        // Offline — fall back to the cached app shell
        return caches.match(event.request).then(hit => hit || caches.match('./index.html'));
      })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request).then(networkResponse => {
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
            return networkResponse;
          }
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            })
            .catch(err => {
              console.error('[SW] Failed to cache network response for:', event.request.url, err);
            });
          return networkResponse;
        }).catch(error => {
          console.error('[SW] Network fetch failed for:', event.request.url, error);
        });
      })
  );
});
