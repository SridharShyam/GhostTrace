let currentMode = 'general';
let auditData = null;
let currentRawText = '';
let randomizeSynonyms = true;
let currentUploadedFileName = 'ghosttrace_cleansed.txt';

// DOM Elements
const editor = document.getElementById('editor');
const heatmap = document.getElementById('heatmap');
const reviewQueue = document.getElementById('review-queue');
const fileInput = document.getElementById('file-upload');
const scoreValue = document.getElementById('score-value');
const scoreBadge = document.getElementById('score-badge');
const burstValue = document.getElementById('burst-value');
const burstDesc = document.getElementById('burst-desc');
const entropyValue = document.getElementById('entropy-value');
const passiveDesc = document.getElementById('passive-desc');
const watermarkValue = document.getElementById('watermark-value');
const watermarkDesc = document.getElementById('watermark-desc');
const btnPurgeQuick = document.getElementById('btn-purge-quick');
const btnHumanize = document.getElementById('btn-humanize');
const btnShuffle = document.getElementById('btn-shuffle');
const rhythmBars = document.getElementById('rhythm-bars');
const sentenceCount = document.getElementById('sentence-count');
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
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mode === mode);
  });
  runAudit();
}

function toggleEntropy(val) {
  randomizeSynonyms = val;
  if (auditData?.suggestions) {
    renderReviewQueue();
  }
}

function clearEditor() {
  editor.value = '';
  currentRawText = '';
  runAudit();
  showToast('Editor cleared');
}

// File Upload Handler (.docx, .pdf, .tex, .md, .txt, .zip)
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  currentUploadedFileName = file.name;
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
      if (file.name.endsWith('.tex') || file.name.endsWith('.zip')) {
        setMode('academic');
      } else {
        runAudit();
      }
      showToast(`Loaded ${file.name} successfully`);
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
    reviewQueue.innerHTML = `
      <div class="empty-review-state">
        <div class="empty-review-icon">
          <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
        </div>
        <div class="empty-review-title">Start Writing or Upload Document</div>
        <div class="empty-review-desc">Paste content or drag in any academic paper, essay, or thesis to begin slop audit.</div>
      </div>`;
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
    renderRhythmHistogram();
    renderReviewQueue();
  } catch (err) {
    console.error('Audit failed:', err);
  }
}

function resetMetrics() {
  scoreValue.textContent = '5/5';
  scoreBadge.textContent = 'CLEAN';
  scoreBadge.className = 'stat-chip clean';
  burstValue.textContent = '0.0 σ';
  burstDesc.textContent = 'Natural Pacing';
  entropyValue.textContent = '0.00 bits';
  passiveDesc.textContent = '0.0% Passive Voice';
  watermarkValue.textContent = '0';
  watermarkValue.className = 'stat-value';
  watermarkDesc.textContent = 'Steganography-Free';
  btnPurgeQuick.classList.add('hidden');
  rhythmBars.innerHTML = '';
  sentenceCount.textContent = '0';
  btnHumanize.disabled = true;
  btnShuffle.disabled = true;
}

function renderMetrics() {
  if (!auditData) return;

  // Score
  scoreValue.textContent = `${auditData.score}/5`;
  if (auditData.score === 5) {
    scoreBadge.textContent = 'CLEAN';
    scoreBadge.className = 'stat-chip clean';
  } else if (auditData.score >= 3) {
    scoreBadge.textContent = 'FAIR';
    scoreBadge.className = 'stat-chip fair';
  } else {
    scoreBadge.textContent = 'NEEDS CLEANSE';
    scoreBadge.className = 'stat-chip danger';
  }

  // Burstiness
  const burst = auditData.burstiness || {};
  burstValue.textContent = `${burst.std_dev || 0} σ`;
  burstDesc.textContent = burst.is_monotonous ? '⚠️ Flat AI Cadence (Low Variation)' : '✅ Natural Human Pacing';

  // Entropy & Passive Ratio
  const ent = burst.shannon_entropy !== undefined ? burst.shannon_entropy : 0;
  entropyValue.textContent = `${ent} bits`;
  const pass = burst.passive_ratio !== undefined ? burst.passive_ratio : 0;
  passiveDesc.textContent = `${pass}% Passive Voice`;

  // Watermarks
  const wm = auditData.watermarks || {};
  const totalWm = Object.values(wm).reduce((a, b) => a + b, 0);
  watermarkValue.textContent = `${totalWm}`;
  if (totalWm > 0) {
    watermarkValue.className = 'stat-value danger';
    watermarkDesc.textContent = '⚠️ Steganographic tells detected';
    btnPurgeQuick.classList.remove('hidden');
  } else {
    watermarkValue.className = 'stat-value';
    watermarkDesc.textContent = 'Steganography-Free';
    btnPurgeQuick.classList.add('hidden');
  }

  // Enable/Disable Humanize button
  const hasSuggestions = Object.keys(auditData.suggestions || {}).length > 0;
  btnHumanize.disabled = !hasSuggestions && totalWm === 0;
  btnShuffle.disabled = !hasSuggestions;
}

function renderRhythmHistogram() {
  const burst = auditData?.burstiness || {};
  const lengths = burst.sentence_lengths || [];
  sentenceCount.textContent = lengths.length;

  if (lengths.length === 0) {
    rhythmBars.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem;">No full sentences detected yet.</span>';
    return;
  }

  let html = '';
  lengths.forEach((len, idx) => {
    const heightPx = Math.max(10, Math.min(len * 3.2, 85));
    let cls = 'bar-pill';
    if (len < 10 || len > 22) {
      cls += ' human';
    } else if (burst.is_monotonous && len >= 12 && len <= 16) {
      cls += ' ai';
    }
    html += `
      <div class="bar-col" title="Sentence ${idx + 1}: ${len} words">
        <div class="${cls}" style="height: ${heightPx}px;"></div>
        <span class="bar-num">${len}w</span>
      </div>
    `;
  });

  rhythmBars.innerHTML = html;
}

function renderLiveHeatmap() {
  let safeText = escapeHtml(currentRawText);

  // Red highlights for Vocabulary Slop
  if (auditData?.hits?.vocab) {
    auditData.hits.vocab.forEach(item => {
      const w = item[0];
      const re = new RegExp(`\\b(${escapeRegex(w)}[a-z]*)\\b`, 'gi');
      safeText = safeText.replace(re, '<mark class="slop-tell">$1</mark>');
    });
  }

  // Yellow highlights for Academic Hype
  if (auditData?.hits?.academic_hype) {
    auditData.hits.academic_hype.forEach(item => {
      const w = item[0];
      const re = new RegExp(`\\b(${escapeRegex(w)})\\b`, 'gi');
      safeText = safeText.replace(re, '<mark class="slop-hype">$1</mark>');
    });
  }

  // Purple highlights for Clichés & Narrative Phrases
  if (auditData?.hits?.phrases) {
    auditData.hits.phrases.forEach(item => {
      if (Array.isArray(item) && item.length > 2 && Array.isArray(item[2])) {
        item[2].forEach(m => {
          const re = new RegExp(`(${escapeRegex(m)})`, 'gi');
          safeText = safeText.replace(re, '<mark class="slop-phrase">$1</mark>');
        });
      }
    });
  }

  heatmap.innerHTML = safeText;
}

function renderReviewQueue() {
  const suggestions = auditData?.suggestions || {};
  const entries = Object.entries(suggestions);
  const totalWm = Object.values(auditData?.watermarks || {}).reduce((a, b) => a + b, 0);

  if (entries.length === 0) {
    if (totalWm > 0) {
      reviewQueue.innerHTML = `
        <div class="empty-review-state">
          <div class="empty-review-icon warn">
            <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
          </div>
          <div class="empty-review-title">${totalWm} Invisible Watermarks Detected</div>
          <div class="empty-review-desc">No generic vocabulary tells found, but <strong>${totalWm} hidden zero-width unicode characters</strong> were flagged in this text.</div>
          <button class="btn-purge-empty" onclick="purgeWatermarksDirect()">
            Purge All ${totalWm} Watermarks Now
          </button>
        </div>`;
    } else {
      reviewQueue.innerHTML = `
        <div class="empty-review-state">
          <div class="empty-review-icon">
            <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"></path></svg>
          </div>
          <div class="empty-review-title">Writing is Clean</div>
          <div class="empty-review-desc">No active AI vocabulary tells or steganographic watermarks detected in your current text.</div>
        </div>`;
    }
    return;
  }

  let html = '';
  entries.forEach(([origWord, alternatives], idx) => {
    let chosen = alternatives[0];
    if (randomizeSynonyms && alternatives.length > 1) {
      const randIdx = Math.floor(Math.random() * alternatives.length);
      chosen = alternatives[randIdx];
    }

    html += `
      <div class="sub-card" id="card-${idx}">
        <div class="sub-card-top">
          <label class="sub-checkbox-label">
            <input type="checkbox" id="chk-${idx}" checked>
            <span>Accept replacement</span>
          </label>
          <span class="tag-badge">AI Buzzword</span>
        </div>
        <div class="sub-row">
          <span class="sub-old">${origWord}</span>
          <span class="sub-arrow">➔</span>
          <select class="sub-select" id="select-${idx}">
            ${alternatives.map(alt => `<option value="${alt}" ${alt === chosen ? 'selected' : ''}>${alt}</option>`).join('')}
          </select>
        </div>
      </div>
    `;
  });

  reviewQueue.innerHTML = html;
}

function shuffleCandidateAlternatives() {
  if (!auditData?.suggestions) return;
  const entries = Object.entries(auditData.suggestions);
  entries.forEach(([_, alternatives], idx) => {
    const sel = document.getElementById(`select-${idx}`);
    if (sel && alternatives.length > 1) {
      const current = sel.value;
      const remaining = alternatives.filter(a => a !== current);
      const next = remaining[Math.floor(Math.random() * remaining.length)];
      sel.value = next;
    }
  });
  showToast('🔀 Shuffled synonyms for maximum entropy');
}

function purgeWatermarksDirect() {
  const updated = purgeWatermarks(editor.value);
  editor.value = updated;
  currentRawText = updated;
  runAudit();
  showToast('🛡️ Successfully stripped all zero-width watermarks!');
}

function applyReplacements() {
  const entries = Object.entries(auditData?.suggestions || {});
  let updatedText = currentRawText;
  let appliedCount = 0;

  entries.forEach(([origWord, _], idx) => {
    const chk = document.getElementById(`chk-${idx}`);
    if (chk && chk.checked) {
      const sel = document.getElementById(`select-${idx}`);
      const replacement = sel ? sel.value : null;
      if (replacement) {
        const re = new RegExp(`\\b${escapeRegex(origWord)}\\b`, 'gi');
        updatedText = updatedText.replace(re, (matched) => {
          if (matched === matched.toUpperCase()) return replacement.toUpperCase();
          if (matched[0] === matched[0].toUpperCase()) {
            return replacement.charAt(0).toUpperCase() + replacement.slice(1);
          }
          return replacement;
        });
        appliedCount++;
      }
    }
  });

  // Purge invisible watermarks
  updatedText = purgeWatermarks(updatedText);

  editor.value = updatedText;
  currentRawText = updatedText;
  runAudit();
  showToast(`✨ Humanized ${appliedCount} word(s) and sanitized watermarks!`);
}

function purgeWatermarks(str) {
  return str.replace(/[\u200B\u200C\u200D\uFEFF\u200E\u200F\u00AD]/g, '')
            .replace(/[\u00A0\u2000-\u200A\u202F\u205F\u3000]/g, ' ')
            .replace(/‑/g, '-');
}

function copyToClipboard() {
  const textToCopy = purgeWatermarks(editor.value);
  navigator.clipboard.writeText(textToCopy).then(() => {
    showToast('📋 Sanitized text copied to clipboard!');
  });
}

function downloadCleanedFile() {
  const clean = purgeWatermarks(editor.value);
  let downloadName = 'ghosttrace_cleansed.txt';
  if (currentUploadedFileName && currentUploadedFileName.includes('.')) {
    const parts = currentUploadedFileName.split('.');
    const ext = parts.pop().toLowerCase();
    const base = parts.join('.');
    if (ext === 'tex' || ext === 'zip') {
      downloadName = `${base}_cleansed.tex`;
    } else if (ext === 'md') {
      downloadName = `${base}_cleansed.md`;
    } else {
      downloadName = `${base}_cleansed.txt`;
    }
  }

  const blob = new Blob([clean], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = downloadName;
  a.click();
  showToast(`📥 Downloaded ${downloadName}`);
}

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2800);
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Initial sample audit on load
window.addEventListener('DOMContentLoaded', () => {
  editor.value = "In this study, we delve into a revolutionary approach that provides seamless optimization for next-level performance.";
  currentRawText = editor.value;
  runAudit();
});
