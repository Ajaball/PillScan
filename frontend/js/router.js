/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — SPA Router
   Hash-based client-side routing with auth guards and transitions
   ═══════════════════════════════════════════════════════════════════ */

import storage from './storage.js';

class Router {
  constructor() {
    this.routes = {};
    this.currentPage = null;
    this.currentPath = '';
    this.containerEl = null;
    this.navbarEl = null;
    this.onNavigate = null;
  }

  /** Initialize router with DOM container */
  init(containerId = 'page-container') {
    this.containerEl = document.getElementById(containerId);
    this.navbarEl = document.getElementById('bottom-navbar');

    // Listen for hash changes
    window.addEventListener('hashchange', () => this.handleRoute());

    // Handle initial route
    this.handleRoute();
  }

  /** Register a route */
  register(path, pageModule, options = {}) {
    this.routes[path] = { module: pageModule, ...options };
  }

  /** Navigate to a path */
  navigate(path, params = {}) {
    // Build hash with params
    let hash = path;
    if (params.id) {
      hash = path.replace(':id', params.id);
    }
    // Store params for the page to access
    this._params = params;
    window.location.hash = hash;
  }

  /** Go back */
  back() {
    window.history.back();
  }

  /** Get current route params */
  getParams() {
    return this._params || {};
  }

  /** Get param from URL hash */
  getHashParam(name) {
    const hash = window.location.hash.slice(1);
    const parts = hash.split('/');
    const route = this.matchRoute(hash);
    if (!route) return null;

    const routeParts = route.path.split('/');
    for (let i = 0; i < routeParts.length; i++) {
      if (routeParts[i] === `:${name}`) {
        return parts[i];
      }
    }
    return null;
  }

  /** Match hash to a registered route */
  matchRoute(hash) {
    // Direct match
    if (this.routes[hash]) {
      return { path: hash, ...this.routes[hash] };
    }

    // Pattern match (e.g., /drug/:id)
    for (const [pattern, route] of Object.entries(this.routes)) {
      const patternParts = pattern.split('/');
      const hashParts = hash.split('/');

      if (patternParts.length !== hashParts.length) continue;

      let match = true;
      const params = {};
      for (let i = 0; i < patternParts.length; i++) {
        if (patternParts[i].startsWith(':')) {
          params[patternParts[i].slice(1)] = hashParts[i];
        } else if (patternParts[i] !== hashParts[i]) {
          match = false;
          break;
        }
      }

      if (match) {
        this._params = { ...this._params, ...params };
        return { path: pattern, ...route };
      }
    }

    return null;
  }

  /** Handle route change */
  async handleRoute() {
    const hash = window.location.hash.slice(1) || this.getDefaultRoute();

    // Find matching route
    const route = this.matchRoute(hash);

    if (!route) {
      // Redirect to default
      this.navigate(this.getDefaultRoute());
      return;
    }

    // Auth guard
    if (route.auth && !storage.isAuthenticated()) {
      this.navigate('/login');
      return;
    }

    // Admin guard (server also enforces the role on every admin endpoint)
    if (route.admin && !storage.isAdmin()) {
      this.navigate('/home');
      return;
    }

    // Guest only (login/register when already authenticated)
    if (route.guest && storage.isAuthenticated()) {
      this.navigate('/home');
      return;
    }

    // Unmount current page
    if (this.currentPage && this.currentPage.unmount) {
      this.currentPage.unmount();
    }

    // Update current path
    this.currentPath = hash;

    // Show/hide navbar
    if (this.navbarEl) {
      if (route.showNavbar !== false && storage.isAuthenticated()) {
        this.navbarEl.classList.remove('hidden');
        this.updateNavbarActive(hash);
      } else {
        this.navbarEl.classList.add('hidden');
      }
    }

    // Render new page
    try {
      const pageModule = route.module;
      this.currentPage = pageModule;

      // Clear container
      this.containerEl.innerHTML = '';

      // Render page HTML
      const html = pageModule.render(this._params || {});
      this.containerEl.innerHTML = `<div class="page page-enter">${html}</div>`;

      // Mount page (attach event listeners)
      if (pageModule.mount) {
        await pageModule.mount(this._params || {});
      }

      // Notify
      if (this.onNavigate) {
        this.onNavigate(hash);
      }
    } catch (error) {
      console.error('Route error:', error);
      this.containerEl.innerHTML = `
        <div class="page flex flex-col items-center justify-center p-6">
          <div class="text-4xl mb-4">⚠️</div>
          <p class="text-secondary text-center">حدث خطأ في تحميل الصفحة</p>
          <button class="btn btn-primary mt-4" onclick="location.reload()">إعادة المحاولة</button>
        </div>
      `;
    }
  }

  /** Get default route based on auth state */
  getDefaultRoute() {
    if (!storage.isOnboardingDone()) return '/splash';
    if (!storage.isAuthenticated()) return '/login';
    return '/home';
  }

  /** Update navbar active state */
  updateNavbarActive(hash) {
    if (!this.navbarEl) return;
    const items = this.navbarEl.querySelectorAll('.nav-item');
    items.forEach(item => {
      const route = item.dataset.route;
      if (hash.startsWith(route)) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }
}

// Singleton
const router = new Router();

export default router;
