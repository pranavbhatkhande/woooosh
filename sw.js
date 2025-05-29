const CACHE_NAME = 'woooosh-cache-v1';
// Define the assets to cache
const ASSETS_TO_CACHE = [
  './woooosh.html',   // Your main app file
  './manifest.json',  // The web app manifest
  './images/icon-192x192.png', // Main icons
  './images/icon-512x512.png'
  // If you had separate CSS or JS files, you'd list them here too.
];

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