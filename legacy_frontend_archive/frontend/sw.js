/* ============================================
   SignalSafe Campus – Service Worker
   Robust caching, instant cache-purging, and secure routing
   ============================================ */

const CACHE_NAME = 'signalsafe-v2';
const STATIC_ASSETS = [
    '/static/css/styles.css',
    '/static/js/auth.js',
    '/static/js/app.js',
    '/static/js/i18n.js',
    '/static/js/camera.js',
    '/static/js/screenshot.js',
    '/static/js/qrcode.js',
    '/static/js/url.js',
    '/manifest.json',
];

// Install: Cache static assets and activate immediately
self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
});

// Activate: Delete ALL legacy kavach-* and outdated caches immediately
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        console.log('[SW] Purging old cache:', key);
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: Secure network-first for all navigation and API requests
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // 1. API calls: NEVER cached (network-only)
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                return new Response(
                    JSON.stringify({ error: 'SignalSafe API unreachable or offline.' }),
                    { status: 503, headers: { 'Content-Type': 'application/json' } }
                );
            })
        );
        return;
    }

    // 2. HTML navigation requests: ALWAYS network-first, no stale cache
    if (event.request.mode === 'navigate' || event.request.destination === 'document') {
        event.respondWith(
            fetch(event.request, { cache: 'no-store' }).then((response) => {
                return response;
            }).catch(() => {
                return caches.match('/') || new Response('Offline', { status: 503 });
            })
        );
        return;
    }

    // 3. Static assets: Network-first with cache fallback
    event.respondWith(
        fetch(event.request).then((response) => {
            if (response.status === 200) {
                const clone = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
            }
            return response;
        }).catch(() => {
            return caches.match(event.request);
        })
    );
});
