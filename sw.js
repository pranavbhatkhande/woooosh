const CACHE_NAME = 'woooosh-cache-v7';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './images/icon-192x192.png',
  './images/icon-512x512.png'
];

self.addEventListener('install', event => {
  console.log('[SW] Install event triggered. Attempting to cache assets for CACHE_NAME:', CACHE_NAME);
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Cache opened successfully. Caching core assets:', ASSETS_TO_CACHE);
        return cache.addAll(ASSETS_TO_CACHE)
          .then(() => {
            console.log('[SW] All assets in ASSETS_TO_CACHE were successfully cached.');
          })
          .catch(error => {
            console.error('[SW] CRITICAL ERROR: cache.addAll() FAILED during install!', error);
            console.error('[SW] Failed to cache one or more of these assets:', ASSETS_TO_CACHE);
            throw error;
          });
      })
      .catch(error => {
        console.error('[SW] CRITICAL ERROR: caches.open() FAILED during install for CACHE_NAME:', CACHE_NAME, error);
        throw error;
      })
  );
});

self.addEventListener('activate', event => {
  console.log('[SW] Activate event triggered. Current CACHE_NAME:', CACHE_NAME);
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Clearing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Old caches cleared. Claiming clients.');
      return self.clients.claim();
    })
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

  // For index.html: always check network first for updates, then cache and serve
  if (event.request.url.includes('index.html')) {
    event.respondWith(
      fetch(event.request).then(networkResponse => {
        const responseClone = networkResponse.clone();
        // Cache the fresh copy for offline use
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, responseClone);
        });
        return networkResponse;
      }).catch(() => {
        // Network failed — fall back to cached version
        return caches.match(event.request);
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
