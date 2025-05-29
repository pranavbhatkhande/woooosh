const CACHE_NAME = 'woooosh-cache-v1'; // If you change assets, consider updating to 'woooosh-cache-v2' etc.
const ASSETS_TO_CACHE = [
  './',                         // This entry is key! It caches the root of your site.
                                // When start_url is "/", this cached version of index.html will be served.
  './index.html',               // It's also good practice to explicitly cache index.html by its name.
                                // This provides robustness.
  './manifest.json',            // Your PWA manifest file.
  './images/icon-192x192.png',  // Your primary PWA icon.
  './images/icon-512x512.png',  // Your larger PWA icon.
];

// ... rest of your sw.js code (install, activate, fetch listeners)

// Install event: Open a cache and add core assets to it.
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('ServiceWorker: Caching app shell and core assets');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .catch(error => {
        console.error('ServiceWorker: Failed to cache assets during install:', error);
      })
  );
});

// Activate event: Clean up old caches.
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('ServiceWorker: Clearing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim(); // Ensure new service worker takes control immediately
});

// Fetch event: Serve requests from cache if available, otherwise fetch from network.
self.addEventListener('fetch', event => {
  // We only want to cache GET requests for our app shell.
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        // Cache hit - return response
        if (cachedResponse) {
          return cachedResponse;
        }

        // Not in cache - fetch from network
        // Optionally, you could add new successful responses to the cache here.
        return fetch(event.request).then(networkResponse => {
          // Check if we received a valid response to cache
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
            return networkResponse; // Don't cache invalid responses
          }

          // Clone the response to cache it, as response body can only be read once
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });
          return networkResponse;
        });
      })
      .catch(error => {
        console.error('ServiceWorker: Fetch error:', error);
        // You could return a fallback offline page here if you had one in cache.
        // For example: return caches.match('./offline.html');
      })
  );
});
