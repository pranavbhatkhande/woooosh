// In sw.js
const CACHE_NAME = 'woooosh-cache-v3'; // <-- IMPORTANT: Increment the cache version!
const ASSETS_TO_CACHE = [
  './',                         // For start_url: "/"
  './index.html',               // Explicit cache for index.html
  './manifest.json',
  './images/icon-192x192.png',  // Ensure this exact path and filename exists
  './images/icon-512x512.png'   // Ensure this exact path and filename exists
  // If you added an apple-touch-icon, ensure its path is here too, e.g. './images/apple-touch-icon.png'
];

self.addEventListener('install', event => {
  console.log('[SW] Install event triggered. Attempting to cache assets for CACHE_NAME:', CACHE_NAME);
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Cache opened successfully. Caching core assets:', ASSETS_TO_CACHE);
        return cache.addAll(ASSETS_TO_CACHE) // This is the critical operation
          .then(() => {
            console.log('[SW] All assets in ASSETS_TO_CACHE were successfully cached.');
          })
          .catch(error => {
            // THIS IS THE MOST IMPORTANT LOG IF THINGS GO WRONG
            console.error('[SW] CRITICAL ERROR: cache.addAll() FAILED during install!', error);
            console.error('[SW] Failed to cache one or more of these assets:', ASSETS_TO_CACHE);
            // The error object above often indicates which URL failed.
            // Throwing an error here signals that the SW installation failed, which is correct
            // if critical assets cannot be cached.
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
      return self.clients.claim(); // Ensure new SW takes control immediately
    })
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') {
    return; // Only handle GET requests
  }
  // Optional: uncomment for very verbose fetch logging during testing
  // console.log('[SW] Fetch event for:', event.request.url, 'Mode:', event.request.mode);

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          // console.log('[SW] Serving from cache:', event.request.url);
          return cachedResponse;
        }
        // console.log('[SW] Not in cache, fetching from network:', event.request.url);
        return fetch(event.request).then(networkResponse => {
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
            // console.log('[SW] Invalid network response, not caching:', event.request.url, 'Status:', networkResponse ? networkResponse.status : 'unknown');
            return networkResponse;
          }
          // console.log('[SW] Valid network response, attempting to cache:', event.request.url);
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
              // console.log('[SW] Successfully cached network response for:', event.request.url);
            })
            .catch(err => {
              console.error('[SW] Failed to cache network response for:', event.request.url, err);
            });
          return networkResponse;
        }).catch(error => {
          console.error('[SW] Network fetch failed for:', event.request.url, error);
          // Optionally return a generic offline fallback page if one is cached
          // For example: return caches.match('./offline.html');
        });
      })
  );
});
