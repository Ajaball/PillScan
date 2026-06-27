/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Scanner Page
   Camera-based pill scanning with WebRTC
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import toast from '../components/toast.js';

const ScannerPage = {
  stream: null,
  videoEl: null,

  render() {
    return `
      <div class="scanner-screen">
        <div class="scanner-header">
          <button class="btn btn-icon" id="scanner-back" style="background:rgba(0,0,0,0.4);backdrop-filter:blur(8px);border-radius:50%;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
          </button>
          <h1 class="scanner-title">${i18n.t('scanner_title')}</h1>
          <div style="width:48px;"></div>
        </div>

        <div class="scanner-viewport">
          <video id="camera-video" autoplay playsinline muted></video>
          <canvas id="camera-canvas" class="hidden"></canvas>

          <!-- Scan frame overlay -->
          <div class="scan-frame">
            <div class="scan-corner top-left"></div>
            <div class="scan-corner top-right"></div>
            <div class="scan-corner bottom-left"></div>
            <div class="scan-corner bottom-right"></div>
            <div class="scan-line"></div>
          </div>

          <!-- Hint text -->
          <div class="scanner-hint">
            <p>${i18n.t('scanner_hint')}</p>
          </div>

          <!-- Camera error state -->
          <div class="camera-error hidden" id="camera-error">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" stroke-width="1.5" stroke-linecap="round">
              <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
              <circle cx="12" cy="13" r="4"/>
              <line x1="1" y1="1" x2="23" y2="23" stroke="var(--color-error)"/>
            </svg>
            <p class="text-secondary mt-3">${i18n.t('camera_permission')}</p>
            <button class="btn btn-primary btn-sm mt-3" id="retry-camera">${i18n.t('retry')}</button>
          </div>
        </div>

        <div class="scanner-controls">
          <!-- Upload from gallery -->
          <label class="btn btn-icon btn-secondary scanner-control-btn" for="file-input">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          </label>
          <input type="file" id="file-input" accept="image/*" class="hidden">

          <!-- Capture button -->
          <button class="scanner-capture-btn" id="capture-btn">
            <span class="capture-ring"></span>
            <span class="capture-dot"></span>
          </button>

          <!-- Placeholder for symmetry -->
          <div class="scanner-control-btn" style="visibility:hidden;width:48px;"></div>
        </div>

        <!-- Loading overlay -->
        <div class="scanner-loading hidden" id="scanner-loading">
          <div class="scanner-loading-content">
            <div class="loading-dots">
              <span></span><span></span><span></span>
            </div>
            <p class="mt-3">${i18n.t('scanning')}</p>
          </div>
        </div>
      </div>
    `;
  },

  async mount() {
    this.videoEl = document.getElementById('camera-video');

    document.getElementById('scanner-back')?.addEventListener('click', () => router.back());
    document.getElementById('capture-btn')?.addEventListener('click', () => this.capture());
    document.getElementById('retry-camera')?.addEventListener('click', () => this.startCamera());

    // File upload
    document.getElementById('file-input')?.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) this.processImage(file);
    });

    // Start camera
    await this.startCamera();
  },

  async startCamera() {
    document.getElementById('camera-error')?.classList.add('hidden');

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      if (this.videoEl) {
        this.videoEl.srcObject = this.stream;
      }
    } catch (error) {
      console.error('Camera error:', error);
      document.getElementById('camera-error')?.classList.remove('hidden');
    }
  },

  capture() {
    if (!this.videoEl || !this.stream) {
      toast.warning(i18n.t('camera_error'));
      return;
    }

    // Haptic feedback
    if (navigator.vibrate) navigator.vibrate(50);

    const canvas = document.getElementById('camera-canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = this.videoEl.videoWidth;
    canvas.height = this.videoEl.videoHeight;
    ctx.drawImage(this.videoEl, 0, 0);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], 'pill-scan.jpg', { type: 'image/jpeg' });
        this.processImage(file);
      }
    }, 'image/jpeg', 0.9);
  },

  async processImage(imageFile) {
    const loading = document.getElementById('scanner-loading');
    loading?.classList.remove('hidden');

    try {
      // Read image as Data URL so results page can show it without CORS issues
      const imageDataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsDataURL(imageFile);
      });

      const result = await api.scanPill(imageFile);

      // Store result + local image data URL for the results page
      result._local_image = imageDataUrl;
      storage.set('last_scan_result', result);

      // Navigate to results
      router.navigate('/scan-results', { id: result.scan_id });
    } catch (error) {
      toast.error(error.message || i18n.t('error_generic'));
    } finally {
      loading?.classList.add('hidden');
    }
  },

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
  },

  unmount() {
    this.stopCamera();
  }
};

// Import storage for processImage
import storage from '../js/storage.js';

export default ScannerPage;
