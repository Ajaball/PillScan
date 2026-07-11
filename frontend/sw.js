/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Service Worker
   Network-first for HTML & API, Stale-while-revalidate for assets
   ═══════════════════════════════════════════════════════════════════ */

const VERSION = 'v3';
const CACHE_NAME = `pillscan-${VERSION}`;
const API_CACHE = `pillscan-api-${VERSION}`;
const FONT_CACHE = `pillscan-fonts-${VERSION}`;

// Static assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.ico',
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
  '/assets/icons/icon-96.png',
  '/assets/icons/icon-192.png',
  '/assets/icons/icon-512.png',
  '/assets/icons/icon-maskable-192.png',
  '/assets/icons/icon-maskable-512.png',
  '/assets/icons/apple-touch-icon.png',
];

// ── Install — Cache static assets ───────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      // cache: 'reload' bypasses the HTTP cache so a new SW never
      // pre-caches stale copies of the app files
      .then(cache => cache.addAll(STATIC_ASSETS.map(url => new Request(url, { cache: 'reload' }))))
      .then(() => self.skipWaiting())
      .catch(err => console.warn('Cache install failed:', err))
  );
});

// ── Activate — Clean old caches ─────────────────────────────────────
self.addEventListener('activate', (event) => {
  const KEEP = [CACHE_NAME, API_CACHE, FONT_CACHE];
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => !KEEP.includes(key)).map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch — Routing strategy ────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Google Fonts — cache-first (immutable files)
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(cacheFirst(request, FONT_CACHE));
    return;
  }

  // Other cross-origin requests — let the browser handle them
  if (url.origin !== self.location.origin) return;

  // API requests — network first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request, API_CACHE));
    return;
  }

  // Navigations (HTML shell) — network first so updates reach users
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request, CACHE_NAME, '/index.html'));
    return;
  }

  // Static assets — stale-while-revalidate: fast load, silent refresh
  event.respondWith(staleWhileRevalidate(request, CACHE_NAME));
});

// ── Strategies ──────────────────────────────────────────────────────

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return offlineResponse();
  }
}

async function networkFirst(request, cacheName, fallbackUrl) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (fallbackUrl) {
      const fallback = await caches.match(fallbackUrl);
      if (fallback) return fallback;
    }
    return offlineResponse(request);
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cached = await caches.match(request);

  const networkUpdate = fetch(request)
    .then(async (response) => {
      if (response.ok) {
        const cache = await caches.open(cacheName);
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => null);

  if (cached) return cached;
  const fresh = await networkUpdate;
  return fresh || offlineResponse(request);
}

function offlineResponse(request) {
  const wantsJSON = request && request.headers.get('accept')?.includes('application/json');
  if (wantsJSON) {
    return new Response(JSON.stringify({ error: 'Offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  return new Response('Offline', { status: 503 });
}

// ── Background Sync (future) ────────────────────────────────────────
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-adherence') {
    // Sync queued adherence logs when back online
  }
});

// ── Allow the page to trigger immediate activation ──────────────────
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});
