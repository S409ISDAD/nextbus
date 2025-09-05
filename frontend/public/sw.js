import manifest from "./manifest.json";

const CACHE_NAME = "pwa-cache-v1";
const OFFLINE_URL = "/offline.html";

self.addEventListener("install", event => {
    const assetsToCache = [OFFLINE_URL];

    // Add JS, CSS, and assets for offline.html from manifest
    const offlineAssets = manifest["offline.html"];
    if (offlineAssets) {
        if (offlineAssets.file) assetsToCache.push("/" + offlineAssets.file);
        if (offlineAssets.css) assetsToCache.push(...offlineAssets.css.map(f => "/" + f));
        if (offlineAssets.assets) assetsToCache.push(...offlineAssets.assets.map(f => "/" + f));
    }

    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(assetsToCache))
    );
    self.skipWaiting();
});

self.addEventListener("activate", event => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", event => {
    if (event.request.mode === "navigate") {
        event.respondWith(
            fetch(event.request).catch(() =>
                caches.open(CACHE_NAME).then(cache => cache.match(OFFLINE_URL))
            )
        );
    } else {
        event.respondWith(
            caches.match(event.request).then(cached => {
                return (
                    cached ||
                    fetch(event.request).then(response => {
                        if (
                            response &&
                            response.status === 200 &&
                            event.request.url.startsWith(self.location.origin)
                        ) {
                            const cloned = response.clone();
                            caches.open(CACHE_NAME).then(cache =>
                                cache.put(event.request, cloned)
                            );
                        }
                        return response;
                    }).catch(() => cached)
                );
            })
        );
    }
});