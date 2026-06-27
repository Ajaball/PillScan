/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Service Worker
   Cache-first for static assets, Network-first for API calls
   ═══════════════════════════════════════════════════════════════════ */

const CACHE_NAME = 'pillscan-v1';
const API_CACHE = 'pillscan-api-v1';

// Static assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/design-system.css',
  '/css/animations.css',
  '/css/page-styles.css',
  '/js/app.js',
  '/js/api.js',
  '/js/router.js',
  '/js/i18n.js',
  '/js/storage.js',
  '/components/toast.js',
  '/components/navbar.js',
  '/pages/splash.js',
  '/pages/onboarding.js',
  '/pages/login.js',
  '/pages/register.js',
  '/pages/home.js',
  '/pages/scanner.js',
  '/pages/scan-results.js',
  '/pages/drug-details.js',
  '/pages/drug-search.js',
  '/pages/medications.js',
  '/pages/reminders.js',
  '/pages/adherence.js',
  '/pages/profile.js',
  '/manifest.json',
];

// ── Install — Cache static assets ───────────────────────────────────
self.addEventListener('install', (event) => {
  console.log('📦 Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
      .catch(err => console.warn('Cache install failed:', err))
  );
});

// ── Activate — Clean old caches ─────────────────────────────────────
self.addEventListener('activate', (event) => {
  console.log('✅ Service Worker activated');
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME && key !== API_CACHE)
          .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch — Routing strategy ────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // API requests — Network first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(event.request, API_CACHE));
    return;
  }

  // Static assets — Cache first, network fallback
  event.respondWith(cacheFirst(event.request));
});

// ── Strategies ──────────────────────────────────────────────────────

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    // Offline fallback
    return caches.match('/index.html') || new Response('Offline', { status: 503 });
  }
}

async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response(JSON.stringify({ error: 'Offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

// ── Background Sync (future) ────────────────────────────────────────
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-adherence') {
    // Sync queued adherence logs when back online
    console.log('🔄 Background sync: adherence');
  }
});
