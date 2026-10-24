/* Clears earlier offline caches and steps aside.
   Starting Strength and the recomp planner both registered this URL.
   Once this script activates, cached pages are deleted and the worker
   unregisters so WOOOOSH loads from the network. */
self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((key) => caches.delete(key)));
    await self.registration.unregister();
    const windows = await self.clients.matchAll({ type: "window" });
    await Promise.all(windows.map((client) => client.navigate(client.url)));
  })());
});
