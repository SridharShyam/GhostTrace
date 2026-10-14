let currentMode = 'general';
let auditData = null;
let currentRawText = '';

// DOM Elements
const editor = document.getElementById('editor');
const heatmap = document.getElementById('heatmap');
const reviewQueue = document.getElementById('review-queue');
const fileInput = document.getElementById('file-upload');
const scoreValue = document.getElementById('score-value');
const scoreBadge = document.getElementById('score-badge');
const burstValue = document.getElementById('burst-value');
const burstDesc = document.getElementById('burst-desc');
const densityValue = document.getElementById('density-value');
const watermarkValue = document.getElementById('watermark-value');
const watermarkDesc = document.getElementById('watermark-desc');
const toast = document.getElementById('toast');

// Debounce timer for live typing
let debounceTimer;

editor.addEventListener('input', () => {
  currentRawText = editor.value;
  syncScroll();
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    runAudit();
  }, 250);
});

editor.addEventListener('scroll', syncScroll);

function syncScroll() {
  heatmap.scrollTop = editor.scrollTop;
  heatmap.scrollLeft = editor.scrollLeft;
}

function setMode(mode) {
  currentMode = mode;
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mode === mode);
  });
  runAudit();
}

// File Upload Handler (.docx, .pdf, .tex, .md, .txt)
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.text) {
      editor.value = data.text;
      currentRawText = data.text;
      if (file.name.endsWith('.tex')) {
        setMode('academic');
      } else {
        runAudit();
      }
      showToast(`Loaded ${file.name}`);
    } else if (data.error) {
      alert(`Error reading file: ${data.error}`);
    }
  } catch (err) {
    alert(`File upload failed: ${err.message}`);
  }
});

// Run Audit API
async function runAudit() {
  if (!currentRawText.trim()) {
    heatmap.innerHTML = '';
    reviewQueue.innerHTML = '<div class="empty-state"><div class="empty-icon">✨</div><p>Type or paste your text to begin detection.</p></div>';
    resetMetrics();
    return;
  }

  try {
    const res = await fetch('/api/audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: currentRawText, mode: currentMode })
    });
    auditData = await res.json();
    renderLiveHeatmap();
    renderMetrics();
    renderReviewQueue();
  } catch (err) {
    console.error('Audit failed:', err);
  }
}

function resetMetrics() {
  scoreValue.textContent = '5/5';
  scoreBadge.textContent = 'CLEAN';
  scoreBadge.style.color = '#10b981';
  burstValue.textContent = '0.0 σ';
  burstDesc.textContent = 'Natural Pacing';
  densityValue.textContent = '0%';
  watermarkValue.textContent = '0';
  watermarkDesc.textContent = 'No steganography';
}

function renderMetrics() {
  if (!auditData) return;

  scoreValue.textContent = `${auditData.score}/5`;
  if (auditData.score === 5) {
    scoreBadge.textContent = 'CLEAN';
    scoreBadge.style.color = '#10b981';
  } else if (auditData.score >= 3) {
    scoreBadge.textContent = 'FAIR';
    scoreBadge.style.color = '#f59e0b';
  } else {
    scoreBadge.textContent = 'NEEDS CLEANSE';
    scoreBadge.style.color = '#ef4444';
  }

  // Burstiness
  const burst = auditData.burstiness || {};
  burstValue.textContent = `${burst.std_dev || 0} σ`;
  burstDesc.textContent = burst.is_monotonous ? '⚠️ Flat AI Cadence' : '✅ Natural Pacing';

  // Density
  const totalTells = (auditData.hits.vocab?.length || 0) + (auditData.hits.phrases?.length || 0);
  const words = auditData.word_count || 1;
  const pct = ((totalTells / words) * 100).toFixed(1);
  densityValue.textContent = `${pct}%`;

  // Watermarks
  const wm = auditData.watermarks || {};
  const totalWm = Object.values(wm).reduce((a, b) => a + b, 0);
  watermarkValue.textContent = `${totalWm}`;
  watermarkDesc.textContent = totalWm > 0 ? '⚠️ Zero-width tells found' : '✅ Purged';
}

function renderLiveHeatmap() {
  let safeText = escapeHtml(currentRawText);

  // Highlight vocabulary in red
  if (auditData?.hits?.vocab) {
    auditData.hits.vocab.forEach(item => {
      const w = item[0];
      const re = new RegExp(`\\b(${escapeRegex(w)}[a-z]*)\\b`, 'gi');
      safeText = safeText.replace(re, '<mark class="slop-tell">$1</mark>');
    });
  }

  // Highlight academic hype in yellow
  if (auditData?.hits?.academic_hype) {
    auditData.hits.academic_hype.forEach(item => {
      const w = item[0];
      const re = new RegExp(`\\b(${escapeRegex(w)})\\b`, 'gi');
      safeText = safeText.replace(re, '<mark class="slop-hype">$1</mark>');
    });
  }

  heatmap.innerHTML = safeText;
}

function renderReviewQueue() {
  const suggestions = auditData?.suggestions || {};
  const entries = Object.entries(suggestions);

  if (entries.length === 0) {
    reviewQueue.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🎉</div>
        <p>No vocabulary tells detected. Your text has passed the check!</p>
      </div>`;
    return;
  }

  let html = '';
  entries.forEach(([origWord, alternatives], idx) => {
    html += `
      <div class="diff-card" id="card-${idx}">
        <div class="diff-header">
          <span class="tell-badge">AI Vocabulary Tell</span>
          <label class="confirm-wrapper">
            <input type="checkbox" class="confirm-checkbox" id="chk-${idx}" checked>
            <span>Accept replacement</span>
          </label>
        </div>
        <div class="replacement-row">
          <span class="word-old">${origWord}</span>
          <span class="word-arrow">➔</span>
          <select class="word-new-select" id="select-${idx}">
            ${alternatives.map(alt => `<option value="${alt}">${alt}</option>`).join('')}
          </select>
        </div>
      </div>
    `;
  });

  reviewQueue.innerHTML = html;
}

// User Confirmation: Apply selected replacements
function applyReplacements() {
  if (!auditData?.suggestions) return;

  const entries = Object.entries(auditData.suggestions);
  let updatedText = currentRawText;
  let appliedCount = 0;

  entries.forEach(([origWord, _], idx) => {
    const chk = document.getElementById(`chk-${idx}`);
    if (chk && chk.checked) {
      const sel = document.getElementById(`select-${idx}`);
      const replacement = sel.value;
      const re = new RegExp(`\\b${escapeRegex(origWord)}\\b`, 'gi');
      updatedText = updatedText.replace(re, (matched) => {
        if (matched === matched.toUpperCase()) return replacement.toUpperCase();
        if (matched[0] === matched[0].toUpperCase()) return replacement.charAt(0).toUpperCase() + replacement.slice(1);
        return replacement;
      });
      appliedCount++;
    }
  });

  // Also purge zero-width characters and unusual spaces
  updatedText = purgeWatermarks(updatedText);

  editor.value = updatedText;
  currentRawText = updatedText;
  runAudit();
  showToast(`Applied ${appliedCount} confirmed replacement(s) and sanitized watermarks!`);
}

function purgeWatermarks(str) {
  // Strip zero-width chars and non-breaking spaces
  return str.replace(/[\u200B\u200C\u200D\uFEFF\u200E\u200F\u00AD]/g, '')
            .replace(/[\u00A0\u2000-\u200A\u202F\u205F\u3000]/g, ' ')
            .replace(/‑/g, '-');
}

function copyToClipboard() {
  const textToCopy = purgeWatermarks(editor.value);
  navigator.clipboard.writeText(textToCopy).then(() => {
    showToast('Cleaned text copied to clipboard!');
  });
}

function downloadCleanedFile() {
  const text = purgeWatermarks(editor.value);
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'ghosttrace_cleansed.txt';
  a.click();
  showToast('Downloaded cleansed file');
}

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2500);
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Initial sample audit
window.addEventListener('DOMContentLoaded', () => {
  editor.value = "In this study, we delve into a revolutionary approach that provides seamless optimization for next-level performance.";
  currentRawText = editor.value;
  runAudit();
});
