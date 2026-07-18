/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Scan Results Page
   Shows top-5 AI predictions with confidence bars + bounding boxes
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import storage from '../js/storage.js';
import api from '../js/api.js';
import DrugAssistantPage from './drug-assistant.js';

// Colors per detected pill rank
const BOX_COLORS = ['#10B981', '#6366F1', '#F59E0B', '#EF4444', '#8B5CF6'];

const ScanResultsPage = {
  render() {
    const result = storage.get('last_scan_result');
    if (!result || !result.predictions || result.predictions.length === 0) {
      return `
        <div class="page-header">
          <button class="btn btn-icon btn-secondary" id="back-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
          </button>
          <h1 class="page-title">${i18n.t('results_title')}</h1>
          <div style="width:48px;"></div>
        </div>
        <div class="page-content no-navbar" style="display:flex;align-items:center;justify-content:center;">
          <div class="empty-state">
            <div class="text-4xl mb-4">🔍</div>
            <p class="text-secondary">${i18n.t('no_results')}</p>
            <button class="btn btn-primary mt-4" id="new-scan-btn">${i18n.t('new_scan')}</button>
          </div>
        </div>
      `;
    }

    const predictions = result.predictions;
    const topMatch = predictions[0];
    const otherMatches = predictions.slice(1);

    // Use locally stored Data URL (no CORS) or fall back to backend URL
    const imageUrl = result._local_image
      || (result.image_url
        ? (result.image_url.startsWith('/') ? 'http://localhost:8005' + result.image_url : result.image_url)
        : '');


    return `
      <div class="page-header">
        <button class="btn btn-icon btn-secondary" id="back-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
        </button>
        <h1 class="page-title">${i18n.t('results_title')}</h1>
        <div style="width:48px;"></div>
      </div>

      <div class="page-content no-navbar stagger-children">

        <!-- ── Scanned Image with Bounding Boxes Canvas ── -->
        <div id="image-container" style="position:relative; margin-bottom:20px; border-radius:16px; overflow:hidden; background:#0a0a12; min-height:180px;">
          ${imageUrl ? `
            <img
              id="scan-image"
              src="${imageUrl}"
              alt="Scanned pill"
              style="width:100%; max-height:300px; object-fit:contain; display:block;"
              onerror="this.closest('#image-container').style.display='none';"
            />
            <canvas
              id="bbox-canvas"
              style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none;"
            ></canvas>
          ` : `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:180px;gap:8px;">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" stroke-width="1.5"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>
              <p style="color:var(--color-text-tertiary);font-size:13px;">No image available</p>
            </div>
          `}
        </div>

        <!-- ── Top Match Card ── -->
        ${topMatch ? `
          <div class="card card-glow animate-fade-in-up result-top-card" id="top-result" data-drug-id="${topMatch.drug_id || ''}"
               style="border-left: 4px solid ${BOX_COLORS[0]};">
            <div class="result-badge">
              <span class="badge badge-primary" style="background:${BOX_COLORS[0]}22; color:${BOX_COLORS[0]}; border:1px solid ${BOX_COLORS[0]}55;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                ${i18n.t('top_match')}
              </span>
              ${result.inference_mode === 'llm' ? `<span class="badge" style="margin-inline-start:6px;background:rgba(99,102,241,0.15);color:#818cf8;border:1px solid rgba(99,102,241,0.35);">${i18n.t('source_ai')}</span>` : ''}
            </div>
            <div class="result-drug-info mt-3">
              <h2 class="text-xl font-bold">${i18n.lang === 'ar' ? (topMatch.drug_name_ar || topMatch.drug_name_en) : topMatch.drug_name_en}</h2>
              ${i18n.lang === 'ar' && topMatch.drug_name_en ? `<p class="text-sm text-tertiary">${topMatch.drug_name_en}</p>` : ''}
              ${i18n.lang === 'en' && topMatch.drug_name_ar ? `<p class="text-sm text-tertiary">${topMatch.drug_name_ar}</p>` : ''}
              <div class="flex items-center gap-3 mt-2">
                <span class="badge badge-primary">${topMatch.dosage_form || ''}</span>
                <span class="text-sm text-secondary">${topMatch.strength || ''}</span>
              </div>
            </div>
            <div class="result-confidence mt-4">
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm text-secondary">${i18n.t('confidence')}</span>
                <span class="text-sm font-bold ${this.getConfidenceColor(topMatch.confidence)}">${Math.round(topMatch.confidence * 100)}%</span>
              </div>
              <div class="confidence-bar">
                <div class="confidence-bar-fill" style="--progress: ${topMatch.confidence * 100}%; background: ${this.getConfidenceGradient(topMatch.confidence)};"></div>
              </div>
            </div>
            ${topMatch.drug_id ? `
              <div class="flex gap-2 mt-4">
                <button class="btn btn-primary flex-1" id="view-details-btn" data-drug-id="${topMatch.drug_id}">${i18n.t('drug_details')}</button>
                <button class="btn btn-secondary flex-1" id="add-med-btn" data-drug-id="${topMatch.drug_id}">${i18n.t('add_to_meds')}</button>
              </div>
            ` : `
              <p class="text-xs text-tertiary mt-3">${i18n.t('ai_suggestion_note')}</p>
            `}
          </div>
        ` : ''}

        <!-- ── AI Drug Info (Gemini) for the top match ── -->
        ${topMatch ? `
          <div class="mt-5">
            <h3 class="font-semibold mb-3">${i18n.t('assistant_scan_info_title')}</h3>
            <div id="scan-drug-info"></div>
          </div>
        ` : ''}

        <!-- ── Other Matches ── -->
        ${otherMatches.length > 0 ? `
          <h3 class="font-semibold mt-6 mb-3">${i18n.t('other_matches')}</h3>
          ${otherMatches.map((match, idx) => `
            <div class="card ${match.drug_id ? 'card-interactive' : ''} animate-fade-in-up other-result"
                 data-drug-id="${match.drug_id || ''}"
                 style="animation-delay:${(idx + 1) * 80}ms; border-left: 3px solid ${BOX_COLORS[idx + 1] || BOX_COLORS[4]};">
              <div class="flex items-center gap-3">
                <div class="result-rank" style="background:${(BOX_COLORS[idx + 1] || BOX_COLORS[4])}22; color:${BOX_COLORS[idx + 1] || BOX_COLORS[4]}; border:1px solid ${(BOX_COLORS[idx + 1] || BOX_COLORS[4])}44;">${match.rank}</div>
                <div class="flex-1">
                  <h4 class="font-semibold text-sm">${i18n.lang === 'ar' ? (match.drug_name_ar || match.drug_name_en) : match.drug_name_en}</h4>
                  <p class="text-xs text-tertiary">${match.dosage_form || ''} • ${match.strength || ''}</p>
                </div>
                <span class="text-sm font-semibold ${this.getConfidenceColor(match.confidence)}">${Math.round(match.confidence * 100)}%</span>
              </div>
              <div class="confidence-bar mt-2">
                <div class="confidence-bar-fill" style="--progress: ${match.confidence * 100}%; background: ${this.getConfidenceGradient(match.confidence)};"></div>
              </div>
            </div>
          `).join('')}
        ` : ''}

        <!-- ── New Scan Button ── -->
        <div class="mt-6 mb-4">
          <button class="btn btn-secondary btn-block" id="new-scan-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="12" x2="21" y2="12"/></svg>
            ${i18n.t('new_scan')}
          </button>
        </div>
      </div>
    `;
  },

  mount() {
    document.getElementById('back-btn')?.addEventListener('click', () => router.navigate('/home'));
    document.getElementById('new-scan-btn')?.addEventListener('click', () => router.navigate('/scanner'));

    document.getElementById('view-details-btn')?.addEventListener('click', (e) => {
      const drugId = e.target.dataset.drugId;
      if (drugId) router.navigate('/drug/:id', { id: drugId });
    });

    document.getElementById('add-med-btn')?.addEventListener('click', (e) => {
      const drugId = e.target.dataset.drugId;
      if (drugId) router.navigate('/medications', { addDrugId: drugId });
    });

    // Click on other results → go to drug detail
    document.querySelectorAll('.other-result').forEach(el => {
      el.addEventListener('click', () => {
        const drugId = el.dataset.drugId;
        if (drugId) router.navigate('/drug/:id', { id: drugId });
      });
    });

    // Fetch comprehensive AI drug info for the top match (scan → Gemini).
    const scanResult = storage.get('last_scan_result');
    const topMatch = scanResult?.predictions?.[0];
    if (topMatch) this.loadDrugInfo(topMatch);

    // Draw bounding boxes after image loads
    const img = document.getElementById('scan-image');
    if (img) {
      if (img.complete && img.naturalWidth > 0) {
        this.drawBoundingBoxes();
      } else {
        img.addEventListener('load', () => this.drawBoundingBoxes());
        img.addEventListener('error', () => {
          console.warn('[ScanResults] Could not load scan image for bbox rendering.');
        });
      }
    }
  },

  drawBoundingBoxes() {
    const result = storage.get('last_scan_result');
    const img = document.getElementById('scan-image');
    const canvas = document.getElementById('bbox-canvas');
    if (!result || !img || !canvas) return;

    const predictions = result.predictions || [];
    const hasBboxes = predictions.some(p => p.bbox);
    if (!hasBboxes) return;

    // Match canvas pixel size to the displayed img size
    const displayW = img.offsetWidth;
    const displayH = img.offsetHeight;
    canvas.width = displayW;
    canvas.height = displayH;

    // Original image size from backend (for scaling)
    const origW = result.image_width || img.naturalWidth || displayW;
    const origH = result.image_height || img.naturalHeight || displayH;

    // Because object-fit:contain, compute letterbox offsets
    const scaleX = displayW / origW;
    const scaleY = displayH / origH;
    const scale = Math.min(scaleX, scaleY);
    const offsetX = (displayW - origW * scale) / 2;
    const offsetY = (displayH - origH * scale) / 2;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, displayW, displayH);

    predictions.forEach((pred, idx) => {
      if (!pred.bbox) return;
      const color = BOX_COLORS[idx] || BOX_COLORS[4];
      const { x1, y1, x2, y2 } = pred.bbox;

      const rx = x1 * scale + offsetX;
      const ry = y1 * scale + offsetY;
      const rw = (x2 - x1) * scale;
      const rh = (y2 - y1) * scale;

      // Draw box
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.shadowColor = color;
      ctx.shadowBlur = 8;
      ctx.strokeRect(rx, ry, rw, rh);

      // Fill semi-transparent
      ctx.shadowBlur = 0;
      ctx.fillStyle = color + '22';
      ctx.fillRect(rx, ry, rw, rh);

      // Label background
      const label = `#${pred.rank} ${Math.round(pred.confidence * 100)}%`;
      ctx.font = 'bold 13px Inter, sans-serif';
      const textW = ctx.measureText(label).width + 12;
      const labelY = ry > 22 ? ry - 2 : ry + rh + 20;

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(rx, labelY - 18, textW, 22, 4);
      ctx.fill();

      // Label text
      ctx.fillStyle = '#fff';
      ctx.fillText(label, rx + 6, labelY - 1);
    });
  },

  // Ask Gemini (via the assistant endpoint) for the identified drug's full
  // profile and render it under the top match — so a scan gives the same rich
  // info as a manual search.
  async loadDrugInfo(topMatch) {
    const container = document.getElementById('scan-drug-info');
    if (!container) return;

    const name = (i18n.lang === 'en')
      ? (topMatch.drug_name_en || topMatch.drug_name_ar)
      : (topMatch.drug_name_ar || topMatch.drug_name_en);
    if (!name) { container.closest('.mt-5')?.remove(); return; }

    container.innerHTML = `
      <div class="card text-center" style="padding:var(--space-5);">
        <div class="loading-dots" style="justify-content:center;"><span></span><span></span><span></span></div>
        <p class="text-secondary text-sm mt-3">${i18n.t('assistant_scan_info_loading')}</p>
      </div>`;

    try {
      const info = await api.getDrugInfo(name);

      if (info.is_configured === false) {
        container.innerHTML = `
          <div class="card text-center">
            <p class="text-secondary text-sm mb-3">${i18n.t('assistant_not_configured')}</p>
            <button class="btn btn-primary btn-sm" id="scan-go-ai-settings">${i18n.t('ai_settings')}</button>
          </div>`;
        document.getElementById('scan-go-ai-settings')?.addEventListener('click', () => router.navigate('/ai-settings'));
        return;
      }

      if (!info.recognized) {
        container.innerHTML = `
          <div class="card text-center">
            <div class="text-3xl mb-2">🤔</div>
            <p class="text-secondary text-sm">${i18n.t('assistant_not_recognized')}</p>
          </div>`;
        return;
      }

      // Reuse the assistant's comprehensive renderer.
      container.innerHTML = DrugAssistantPage.renderDrugInfoHtml(info);
    } catch (err) {
      container.innerHTML = `<div class="card text-center"><p class="text-secondary text-sm">${(err && err.message) || i18n.t('error_generic')}</p></div>`;
    }
  },

  getConfidenceColor(conf) {
    if (conf >= 0.8) return 'text-success';
    if (conf >= 0.5) return 'text-warning';
    return 'text-error';
  },

  getConfidenceGradient(conf) {
    if (conf >= 0.8) return 'linear-gradient(90deg, #10B981, #34D399)';
    if (conf >= 0.5) return 'linear-gradient(90deg, #F59E0B, #FBBF24)';
    return 'linear-gradient(90deg, #EF4444, #F87171)';
  },

  unmount() {}
};

export default ScanResultsPage;
