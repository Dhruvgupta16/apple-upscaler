// =========================================================================
// APPLICATION DEFAULT SETTINGS & STATE
// =========================================================================
const DEFAULT_SETTINGS = {
  smart_dynamic_range: true,
  contrast: 1.060,
  gamma: 1.040,
  saturation: 1.150,
  sharpness: 0.600,
  brightness: 0.005,
  exposure: 0.0,
  temp: 0.0,
  tint: 0.0,
  denoise: 3.0,
  grain: 0.0,
  deband: true,
  edge_clean: true,
  deinterlace: false,
  resolution: "1080p",
  framing: "4:3 Pillarbox",
  audio_mode: "copy",
  sub_mode: "copy",
  export_fmt: "mkv",
  photo_fmt: "png",
  gpu: "nvenc_hevc",
  cq: 20,
  trim_enabled: false,
  trim_in: "00:00:00",
  trim_out: "00:00:00",
  lut_mode: "none",
  lut_intensity: 1.0,
  ai_model: "realesr-animevideov3",
  delete_original: false,
  lift_r: 0.0, lift_g: 0.0, lift_b: 0.0, lift_master: 0.0,
  gamma_r: 0.0, gamma_g: 0.0, gamma_b: 0.0, gamma_master: 0.0,
  gain_r: 0.0, gain_g: 0.0, gain_b: 0.0, gain_master: 0.0,
  crt_scanlines: false,
  crt_intensity: 0.65,
  crt_curve: false,
  vhs_mode: false,
  vhs_tape_speed: "lp",
  vhs_chroma_loss: 0.05,
  vhs_chroma_vert_blend: true,
  vhs_sharpen_enabled: true,
  vhs_sharpen: 0.50,
  vhs_sharpen_freq: 1.0,
  head_switching: true,
  head_switching_height: 16,
  head_switching_shift: 80,
  head_switching_jitter: 0.05,
  vhs_edge_wave_enabled: true,
  vhs_edge_wave: 0.5,
  vhs_edge_wave_speed: 4.0,
  vhs_ringing: true,
  vhs_ringing_freq: 0.45,
  vhs_ringing_power: 4,
  vhs_chroma_noise: true,
  vhs_chroma_noise_intensity: 25,
  vhs_composite_noise: true,
  vhs_composite_noise_intensity: 15,
  line_darken: 0.0,
  cel_deflicker: false,
  audio_eq: false
};

const ICONS = {
  check: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  undo: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>`,
  redo: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.13-9.36L23 10"></path></svg>`,
  clipboard: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>`,
  download: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`,
  sparkles: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path></svg>`,
  wand: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m15 4 6 6-10 10H5v-6l10-10z"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L20 7l-3-3 1.5-1.5z"></path></svg>`,
  play: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`,
  pause: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>`,
  info: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
};

let state = {
  queue: [],
  activeIndex: -1,
  currentSec: 0,
  curtainPct: 50,
  settings: JSON.parse(JSON.stringify(DEFAULT_SETTINGS)),
  viewMode: 'split',
  zoomLevel: 1.0,
  isPlaying: false,
  playInterval: null,
  isEncoding: false,
  debounceTimer: null,
  activeWheel: null,
  isCurtainDragging: false,
  isZoomed: false,
  auditionCards: [],
  pendingAISettings: null
};

// =========================================================================
// INITIALIZATION (DUAL HOOK TO PREVENT WEBVIEW READY RACE CONDITION)
// =========================================================================
async function startApp() {
  try {
    let init = await window.pywebview.api.get_initial_state();
    state.queue = init.queue || [];
    state.activeIndex = init.active_index;
    
    if (init.branding) {
      const appNameEl = document.getElementById('lblAppName');
      if (appNameEl && init.branding.app_name) appNameEl.innerText = init.branding.app_name;
      const appEditionEl = document.getElementById('lblAppEdition');
      if (appEditionEl) {
        if (init.branding.app_edition) appEditionEl.innerText = init.branding.app_edition;
        else appEditionEl.style.display = 'none';
      }
    }

    setupCurtainDivider();
    setupKeyboardShortcuts();
    setupHistoryInteractionListeners();
    updateBatchQueueUI();
    updateFolderNav();
    updateUndoRedoButtonsState();

    if (state.activeIndex >= 0 && state.queue.length > 0) {
      await selectMedia(state.activeIndex);
    } else {
      let loader = document.getElementById('frameLoader');
      if (loader) loader.style.display = 'none';
      document.getElementById('emptyViewport').style.display = 'flex';
      document.getElementById('canvasBounds').style.display = 'none';
      document.getElementById('viewModePill').style.display = 'none';
      document.getElementById('canvasHud').style.display = 'none';
      document.getElementById('folderNavGroup').style.display = 'none';
    }
  } catch (err) {
    console.error("Initialization error:", err);
    let loader = document.getElementById('frameLoader');
    if (loader) loader.style.display = 'none';
  }
}

if (window.pywebview && window.pywebview.api) {
  startApp();
} else {
  window.addEventListener('pywebviewready', startApp);
}

function showToast(msg, icon = 'check') {
  let t = document.getElementById('toastMsg');
  let text = document.getElementById('toastText');
  let iconContainer = document.getElementById('toastIcon');
  if (!t || !text) return;
  let cleanMsg = msg.replace(/^[\uD800-\uDBFF\uDC00-\uDFFF\u2000-\u3300]\s*/, '').trim();
  text.innerText = cleanMsg;
  if (iconContainer) iconContainer.innerHTML = ICONS[icon] || ICONS.check;
  t.classList.add('show');
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => t.classList.remove('show'), 2600);
}

// =========================================================================
// FOLDER NAVIGATION (SWITCH VIDEOS IN ACTIVE FOLDER)
// =========================================================================
function updateFolderNav() {
  let group = document.getElementById('folderNavGroup');
  let counter = document.getElementById('lblNavCounter');
  let sel = document.getElementById('selActiveMedia');
  if (state.queue && state.queue.length > 0) {
    if (group) group.style.display = 'flex';
    if (counter) counter.innerText = `${state.activeIndex + 1} / ${state.queue.length}`;
    if (sel) {
      sel.innerHTML = state.queue.map((item, idx) => `
        <option value="${idx}" ${idx === state.activeIndex ? 'selected' : ''}>${idx + 1}. ${item.filename || item.name}</option>
      `).join('');
    }
  } else {
    if (group) group.style.display = 'none';
  }
}

// =========================================================================
// UNDO / REDO HISTORY ENGINE (CTRL+Z & CTRL+Y)
// =========================================================================
let historyUndoStack = [];
let historyRedoStack = [];
let preInteractionSettings = null;

function pushHistory(desc) {
  historyUndoStack.push({
    desc: desc,
    settings: JSON.parse(JSON.stringify(state.settings))
  });
  if (historyUndoStack.length > 50) historyUndoStack.shift();
  historyRedoStack = [];
  updateUndoRedoButtonsState();
}

function updateUndoRedoButtonsState() {
  const u = document.getElementById('btnUndo');
  const r = document.getElementById('btnRedo');
  if (u) {
    u.style.opacity = historyUndoStack.length > 0 ? '1' : '0.45';
    u.style.pointerEvents = historyUndoStack.length > 0 ? 'auto' : 'none';
  }
  if (r) {
    r.style.opacity = historyRedoStack.length > 0 ? '1' : '0.45';
    r.style.pointerEvents = historyRedoStack.length > 0 ? 'auto' : 'none';
  }
}

function setupHistoryInteractionListeners() {
  document.addEventListener('pointerdown', (e) => {
    if (e.target && (e.target.matches('input[type="range"]') || e.target.closest('.color-wheel-pad') || e.target.closest('.wheel-disc-inner'))) {
      if (!preInteractionSettings) {
        preInteractionSettings = JSON.parse(JSON.stringify(state.settings));
      }
    }
  }, true);

  document.addEventListener('pointerup', (e) => {
    if (preInteractionSettings) {
      let changed = false;
      for (let k in preInteractionSettings) {
        if (preInteractionSettings[k] !== state.settings[k]) {
          changed = true;
          break;
        }
      }
      if (changed) {
        historyUndoStack.push({
          desc: "Adjust Controls",
          settings: preInteractionSettings
        });
        if (historyUndoStack.length > 50) historyUndoStack.shift();
        historyRedoStack = [];
        updateUndoRedoButtonsState();
      }
      preInteractionSettings = null;
    }
  }, true);
}

function undo() {
  if (historyUndoStack.length === 0) {
    showToast("Already at default state — nothing to undo");
    return;
  }
  historyRedoStack.push({
    desc: "Redo",
    settings: JSON.parse(JSON.stringify(state.settings))
  });
  const prev = historyUndoStack.pop();
  for (let k in prev.settings) state.settings[k] = prev.settings[k];
  syncAllInputsFromSettings();
  updateLiveGPUGrade();
  refreshFrame();
  updateUndoRedoButtonsState();
  showToast(`Undid: ${prev.desc}`, 'undo');
}

function redo() {
  if (historyRedoStack.length === 0) {
    showToast("Nothing to redo", 'info');
    return;
  }
  historyUndoStack.push({
    desc: "Undo",
    settings: JSON.parse(JSON.stringify(state.settings))
  });
  const nxt = historyRedoStack.pop();
  for (let k in nxt.settings) state.settings[k] = nxt.settings[k];
  syncAllInputsFromSettings();
  updateLiveGPUGrade();
  refreshFrame();
  updateUndoRedoButtonsState();
  showToast(`Redid: ${nxt.desc}`, 'redo');
}

function syncAllInputsFromSettings() {
  const s = state.settings;
  const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
  const setText = (id, t) => { const el = document.getElementById(id); if (el) el.innerText = t; };

  setVal('slContrast', s.contrast);
  setText('valContrast', s.contrast.toFixed(2));
  setVal('slBrightness', s.brightness);
  setText('valBrightness', s.brightness.toFixed(3));
  setVal('slGamma', s.gamma);
  setText('valGamma', s.gamma.toFixed(2));
  setVal('slSaturation', s.saturation);
  setText('valSaturation', s.saturation.toFixed(2));
  setVal('slExposure', s.exposure);
  setText('valExposure', `${s.exposure > 0 ? '+' : ''}${s.exposure.toFixed(1)} EV`);
  setVal('slTemp', s.temp);
  setText('valTemp', s.temp);
  setVal('slTint', s.tint);
  setText('valTint', s.tint);
  setVal('slDenoise', s.denoise);
  setText('valDenoise', s.denoise.toFixed(1));
  setVal('slSharpness', s.sharpness);
  setText('valSharpness', s.sharpness.toFixed(2));
  setVal('slGrain', s.grain || 0.0);
  setText('valGrain', (s.grain || 0.0).toFixed(2));
  setVal('slLineDarken', s.line_darken || 0.0);
  setText('valLineDarken', (s.line_darken || 0.0).toFixed(2));

  // CRT Scanlines & Screen Curve
  if (document.getElementById('chkCrtScanlines')) {
    document.getElementById('chkCrtScanlines').checked = !!s.crt_scanlines;
    const crt = document.getElementById('crtOverlay');
    if (crt) crt.style.display = s.crt_scanlines ? 'block' : 'none';
  }
  setVal('slCrtIntensity', s.crt_intensity || 0.70);
  setText('valCrtIntensity', `${Math.round((s.crt_intensity || 0.70) * 100)}%`);

  if (document.getElementById('chkCrtCurve')) {
    document.getElementById('chkCrtCurve').checked = !!s.crt_curve;
    const b = document.getElementById('canvasBounds');
    if (b) {
      if (s.crt_curve) b.classList.add('crt-curved');
      else b.classList.remove('crt-curved');
    }
  }

  // Dedicated VHS Studio Controls (Authentic NTSC-RS DSP)
  if (document.getElementById('chkVhsMaster')) {
    document.getElementById('chkVhsMaster').checked = !!s.vhs_mode;
  }
  setVal('selVhsSpeed', s.vhs_tape_speed || 'lp');
  let cLoss = s.vhs_chroma_loss !== undefined ? s.vhs_chroma_loss : 0.0025;
  setVal('slVhsChromaLoss', cLoss);
  setText('valVhsChromaLoss', `${cLoss.toFixed(4)}%`);
  if (document.getElementById('chkVhsVertBlend')) {
    document.getElementById('chkVhsVertBlend').checked = s.vhs_chroma_vert_blend !== false;
  }

  // Sharpening
  if (document.getElementById('chkVhsSharpen')) {
    document.getElementById('chkVhsSharpen').checked = s.vhs_sharpen_enabled !== false;
  }
  setVal('slVhsSharpen', s.vhs_sharpen !== undefined ? s.vhs_sharpen : 0.25);
  setText('valVhsSharpen', (s.vhs_sharpen !== undefined ? s.vhs_sharpen : 0.25).toFixed(2));
  setVal('slVhsSharpenFreq', s.vhs_sharpen_freq !== undefined ? s.vhs_sharpen_freq : 1.0);
  setText('valVhsSharpenFreq', (s.vhs_sharpen_freq !== undefined ? s.vhs_sharpen_freq : 1.0).toFixed(2));

  // Head Switching & Tracking
  if (document.getElementById('chkHeadSwitching')) {
    document.getElementById('chkHeadSwitching').checked = s.head_switching !== false;
  }
  setVal('slHeadHeight', s.head_switching_height !== undefined ? s.head_switching_height : 8);
  setText('valHeadHeight', `${s.head_switching_height !== undefined ? s.head_switching_height : 8} lines`);
  setVal('slHeadShift', s.head_switching_shift !== undefined ? s.head_switching_shift : 72);
  setText('valHeadShift', `${s.head_switching_shift !== undefined ? s.head_switching_shift : 72} px`);
  setVal('slHeadJitter', s.head_switching_jitter !== undefined ? s.head_switching_jitter : 0.03);
  setText('valHeadJitter', (s.head_switching_jitter !== undefined ? s.head_switching_jitter : 0.03).toFixed(2));

  // Edge Wave
  if (document.getElementById('chkVhsEdgeWave')) {
    document.getElementById('chkVhsEdgeWave').checked = s.vhs_edge_wave_enabled !== false;
  }
  setVal('slVhsEdgeWave', s.vhs_edge_wave !== undefined ? s.vhs_edge_wave : 0.5);
  setText('valVhsEdgeWave', (s.vhs_edge_wave !== undefined ? s.vhs_edge_wave : 0.5).toFixed(2));
  setVal('slVhsEdgeWaveSpeed', s.vhs_edge_wave_speed !== undefined ? s.vhs_edge_wave_speed : 4.0);
  setText('valVhsEdgeWaveSpeed', (s.vhs_edge_wave_speed !== undefined ? s.vhs_edge_wave_speed : 4.0).toFixed(2));

  // Ringing
  if (document.getElementById('chkVhsRinging')) {
    document.getElementById('chkVhsRinging').checked = s.vhs_ringing !== false;
  }
  setVal('slVhsRingingFreq', s.vhs_ringing_freq !== undefined ? s.vhs_ringing_freq : 0.45);
  setText('valVhsRingingFreq', (s.vhs_ringing_freq !== undefined ? s.vhs_ringing_freq : 0.45).toFixed(2));
  setVal('slVhsRingingPower', s.vhs_ringing_power !== undefined ? s.vhs_ringing_power : 4);
  setText('valVhsRingingPower', (s.vhs_ringing_power !== undefined ? s.vhs_ringing_power : 4));

  // Noise
  if (document.getElementById('chkVhsChromaNoise')) {
    document.getElementById('chkVhsChromaNoise').checked = s.vhs_chroma_noise !== false;
  }
  let cNoisePct = Math.round((s.vhs_chroma_noise_intensity !== undefined ? s.vhs_chroma_noise_intensity : 0.10) * 100);
  setVal('slVhsChromaNoise', cNoisePct);
  setText('valVhsChromaNoise', `${cNoisePct}%`);

  if (document.getElementById('chkVhsCompNoise')) {
    document.getElementById('chkVhsCompNoise').checked = s.vhs_composite_noise !== false;
  }
  let compNoisePct = Math.round((s.vhs_composite_noise_intensity !== undefined ? s.vhs_composite_noise_intensity : 0.05) * 100);
  setVal('slVhsCompNoise', compNoisePct);
  setText('valVhsCompNoise', `${compNoisePct}%`);

  // Checkboxes
  if (document.getElementById('chkSmartDynamicRange')) {
    document.getElementById('chkSmartDynamicRange').checked = s.smart_dynamic_range !== false;
  }
  if (document.getElementById('chkCelDeflicker')) {
    document.getElementById('chkCelDeflicker').checked = !!s.cel_deflicker;
  }
  if (document.getElementById('chkAudioEQ')) {
    document.getElementById('chkAudioEQ').checked = !!s.audio_eq;
  }

  // Color Wheels indicator pucks
  updateWheelPositionsFromSettings();
  updateUndoRedoButtonsState();
}

// =========================================================================
// UNIVERSAL & INDIVIDUAL PARAMETER RESET
// =========================================================================
function formatParamName(key) {
  const names = {
    smart_dynamic_range: "Smart Dynamic Range Protection",
    exposure: "Exposure Compensation",
    contrast: "Dynamic Contrast",
    saturation: "Color Saturation",
    gamma: "Shadow De-Fog (Gamma)",
    brightness: "Black Pedestal Floor",
    temp: "Color Temperature",
    tint: "Color Tint",
    sharpness: "AMD CAS Line Sharpening",
    denoise: "Spatial Denoise",
    grain: "Film Grain",
    line_darken: "Cel Line Darkening",
    crt_intensity: "Scanline Intensity",
    vhs_chroma_loss: "Chroma Loss",
    vhs_sharpen: "Sharpen Intensity",
    vhs_sharpen_freq: "Peaking Frequency",
    head_switching_height: "Head Switching Height",
    head_switching_shift: "Horizontal Shift",
    head_switching_jitter: "Mid-Line Jitter",
    vhs_edge_wave: "Edge Wave Intensity",
    vhs_edge_wave_speed: "Flutter Speed",
    vhs_ringing_freq: "Ringing Frequency",
    vhs_ringing_power: "Ringing Power",
    vhs_chroma_noise_intensity: "Chroma Noise",
    vhs_composite_noise_intensity: "Composite Noise",
    lut_intensity: "LUT Intensity"
  };
  return names[key] || key.replace(/_/g, ' ').toUpperCase();
}

function syncSingleInput(key) {
  const s = state.settings;
  const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
  const setText = (id, t) => { const el = document.getElementById(id); if (el) el.innerText = t; };

  switch (key) {
    case 'exposure':
      setVal('slExposure', s.exposure);
      setText('valExposure', `${s.exposure > 0 ? '+' : ''}${s.exposure.toFixed(1)} EV`);
      break;
    case 'contrast':
      setVal('slContrast', s.contrast);
      setText('valContrast', s.contrast.toFixed(2));
      break;
    case 'saturation':
      setVal('slSaturation', s.saturation);
      setText('valSaturation', s.saturation.toFixed(2));
      break;
    case 'gamma':
      setVal('slGamma', s.gamma);
      setText('valGamma', s.gamma.toFixed(2));
      break;
    case 'brightness':
      setVal('slBrightness', s.brightness);
      setText('valBrightness', s.brightness.toFixed(3));
      break;
    case 'temp':
      setVal('slTemp', s.temp);
      setText('valTemp', s.temp);
      break;
    case 'sharpness':
      setVal('slSharpness', s.sharpness);
      setText('valSharpness', s.sharpness.toFixed(2));
      break;
    case 'denoise':
      setVal('slDenoise', s.denoise);
      setText('valDenoise', s.denoise.toFixed(1));
      break;
    case 'grain':
      setVal('slGrain', s.grain);
      setText('valGrain', s.grain.toFixed(2));
      break;
    case 'crt_intensity':
      setVal('slCrtIntensity', s.crt_intensity);
      setText('valCrtIntensity', `${Math.round(s.crt_intensity * 100)}%`);
      break;
    case 'vhs_chroma_loss':
      setVal('slVhsChromaLoss', s.vhs_chroma_loss);
      setText('valVhsChromaLoss', `${s.vhs_chroma_loss}%`);
      break;
    case 'vhs_sharpen':
      setVal('slVhsSharpen', s.vhs_sharpen);
      setText('valVhsSharpen', s.vhs_sharpen.toFixed(2));
      break;
    case 'head_switching_height':
      setVal('slHeadHeight', s.head_switching_height);
      setText('valHeadHeight', `${s.head_switching_height} lines`);
      break;
    case 'head_switching_shift':
      setVal('slHeadShift', s.head_switching_shift);
      setText('valHeadShift', `${s.head_switching_shift} px`);
      break;
    default:
      syncAllInputsFromSettings();
      break;
  }
}

function resetSingleParam(key) {
  if (DEFAULT_SETTINGS[key] === undefined) return;
  pushHistory(`Reset ${formatParamName(key)}`);
  state.settings[key] = DEFAULT_SETTINGS[key];
  syncSingleInput(key);
  updateLiveGPUGrade();
  showToast(`Reset ${formatParamName(key)} to default`, 'undo');
  refreshFrame();
}

function resetCategoryDefaults(catName) {
  const catMap = {
    color: ['smart_dynamic_range', 'exposure', 'contrast', 'saturation', 'gamma', 'brightness', 'temp', 'sharpness'],
    wheels: ['lift_r', 'lift_g', 'lift_b', 'lift_master', 'gamma_r', 'gamma_g', 'gamma_b', 'gamma_master', 'gain_r', 'gain_g', 'gain_b', 'gain_master'],
    vhs: ['vhs_mode', 'vhs_tape_speed', 'vhs_chroma_loss', 'vhs_chroma_vert_blend', 'vhs_sharpen_enabled', 'vhs_sharpen', 'vhs_sharpen_freq', 'head_switching', 'head_switching_height', 'head_switching_shift', 'head_switching_jitter', 'vhs_edge_wave_enabled', 'vhs_edge_wave', 'vhs_edge_wave_speed', 'vhs_ringing', 'vhs_ringing_freq', 'vhs_ringing_power', 'vhs_chroma_noise', 'vhs_chroma_noise_intensity', 'vhs_composite_noise', 'vhs_composite_noise_intensity'],
    crt: ['crt_scanlines', 'crt_intensity', 'crt_curve'],
    restoration: ['denoise', 'grain', 'deband', 'edge_clean', 'line_darken', 'cel_deflicker'],
    geometry: ['framing', 'resolution']
  };
  const keys = catMap[catName];
  if (!keys) return;
  pushHistory(`Reset ${catName.toUpperCase()} Defaults`);
  keys.forEach(k => {
    if (DEFAULT_SETTINGS[k] !== undefined) state.settings[k] = DEFAULT_SETTINGS[k];
  });
  syncAllInputsFromSettings();
  updateLiveGPUGrade();
  showToast(`Reset ${catName} section to default`, 'undo');
  refreshFrame();
}

function onToggleSmartDynamicRange(checked) {
  pushHistory(checked ? "Enable Smart Dynamic Range Protection" : "Disable Smart Dynamic Range Protection");
  state.settings.smart_dynamic_range = checked;
  showToast(checked ? "Smart Night/Day dynamic range protection active" : "Dynamic range protection disabled", "sparkles");
  refreshFrame();
}

function resetAllDefaults() {
  pushHistory("Reset All Pipeline Defaults");
  for (let k in DEFAULT_SETTINGS) {
    state.settings[k] = DEFAULT_SETTINGS[k];
  }
  syncAllInputsFromSettings();
  updateLiveGPUGrade();
  showToast("Restored all pipeline settings to defaults", 'undo');
  refreshFrame();
}

async function prevMedia() {
  if (state.queue.length <= 1) {
    showToast("Single media in active queue");
    return;
  }
  let nextIdx = state.activeIndex - 1;
  if (nextIdx < 0) nextIdx = state.queue.length - 1;
  await selectMedia(nextIdx);
  showToast(`Switched: ${state.queue[nextIdx].filename}`);
}

async function nextMedia() {
  if (state.queue.length <= 1) {
    showToast("Single media in active queue");
    return;
  }
  let nextIdx = (state.activeIndex + 1) % state.queue.length;
  await selectMedia(nextIdx);
  showToast(`Switched: ${state.queue[nextIdx].filename}`);
}

function setupKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    // Shortcuts for Undo & Redo (Ctrl+Z and Ctrl+Y / Ctrl+Shift+Z)
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
      e.preventDefault();
      undo();
      return;
    }
    if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'y' || (e.key.toLowerCase() === 'z' && e.shiftKey))) {
      e.preventDefault();
      redo();
      return;
    }

    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === '[' || (e.altKey && e.key === 'ArrowLeft')) {
      prevMedia();
    } else if (e.key === ']' || (e.altKey && e.key === 'ArrowRight')) {
      nextMedia();
    } else if (e.key === 'f' || e.key === 'F11') {
      toggleFullscreen();
    }
  });
}

async function selectMedia(idx) {
  if (idx < 0 || !state.queue || idx >= state.queue.length) return;
  state.activeIndex = idx;
  try {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.select_queue_item(idx);
    }
  } catch (e) {
    console.error("select_queue_item error:", e);
  }
  let item = state.queue[idx];
  if (!item) return;

  document.getElementById('emptyViewport').style.display = 'none';
  document.getElementById('canvasBounds').style.display = 'inline-flex';
  document.getElementById('viewModePill').style.display = 'flex';
  document.getElementById('canvasHud').style.display = 'flex';

  document.getElementById('lblVideoName').innerText = item.filename || item.name;
  document.getElementById('lblFileSize').innerText = `${item.size_mb} MB`;
  document.getElementById('lblMediaTypeBadge').innerText = item.is_image ? 'Active Photo' : 'Active Video';
  document.getElementById('valMetaRes').innerText = `${item.width}x${item.height} (${item.dar || '16:9'})`;
  document.getElementById('valMetaCodec').innerText = `${(item.video_codec || 'unknown').toUpperCase()} / ${item.fps} fps`;

  updateFolderNav();
  updateResolutionTags();

  let scrubber = document.getElementById('timelineScrubber');
  let jumps = document.getElementById('quickJumps');
  let trimCard = document.getElementById('cardTrimControls');

  if (item.is_image) {
    if (scrubber) scrubber.style.display = 'none';
    if (jumps) jumps.style.display = 'none';
    if (trimCard) trimCard.style.display = 'none';
    document.getElementById('lblTimeline').innerText = 'Photo Mode - Single Frame Canvas';
    document.getElementById('lblExportBtn').innerText = 'Export Remastered Photo';
    state.currentSec = 0;
  } else {
    if (scrubber) scrubber.style.display = 'block';
    if (jumps) jumps.style.display = 'flex';
    if (trimCard) trimCard.style.display = 'flex';
    document.getElementById('lblExportBtn').innerText = 'Export Remastered Media';
    
    let dur = Math.max(1, Math.floor(item.duration));
    if (scrubber) {
      scrubber.min = 0;
      scrubber.max = dur;
      let defSec = dur > 60 ? Math.floor(Math.min(dur * 0.1, 45)) : Math.floor(dur / 4);
      scrubber.value = defSec;
      state.currentSec = defSec;
    }
    updateTimeReadout();
  }

  updateBatchQueueUI();
  await refreshFrame();
}

function updateResolutionTags() {
  let item = state.queue[state.activeIndex];
  if (!item) return;
  document.getElementById('tabOriginal').innerText = `Source (${item.height}p)`;
  document.getElementById('tabRemaster').innerText = `Remastered (${state.settings.resolution})`;
  document.getElementById('tagSource').innerText = `Source (${item.height}p)`;
  document.getElementById('tagRemaster').innerText = `Remastered (${state.settings.resolution})`;
}

function formatSec(s) {
  s = Math.floor(s || 0);
  let h = Math.floor(s / 3600);
  let m = Math.floor((s % 3600) / 60);
  let sec = s % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
  return `${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
}

function updateTimeReadout() {
  let dur = state.queue[state.activeIndex]?.duration || 0;
  document.getElementById('lblTimeline').innerText = `${formatSec(state.currentSec)} / ${formatSec(dur)}`;
}

function onScrubInput(val) {
  state.currentSec = parseInt(val);
  updateTimeReadout();
}

function onScrubCommit(val) {
  state.currentSec = parseInt(val);
  refreshFrame();
}

function jumpPercent(pct) {
  let dur = state.queue[state.activeIndex]?.duration || 0;
  if (dur <= 0) return;
  state.currentSec = Math.floor(dur * pct);
  document.getElementById('timelineScrubber').value = state.currentSec;
  updateTimeReadout();
  refreshFrame();
}

function stepTime(delta) {
  let dur = state.queue[state.activeIndex]?.duration || 0;
  state.currentSec = Math.max(0, Math.min(dur, state.currentSec + delta));
  document.getElementById('timelineScrubber').value = state.currentSec;
  updateTimeReadout();
  refreshFrame();
}

// =========================================================================
// REAL-TIME 60FPS GPU VIEWPORT SHADING (ZERO LAG DURING DRAGGING)
// =========================================================================
function updateLiveGPUGrade() {
  const imgAfter = document.getElementById('imgAfter');
  if (!imgAfter) return;

  const s = state.settings;
  const expMult = Math.pow(2, s.exposure);
  const brightPct = Math.round((1.0 + (s.brightness * 1.5)) * expMult * 100);
  const contPct = Math.round(s.contrast * 100);
  const satPct = Math.round(s.saturation * 100);

  const matrix = document.getElementById('feGradeMatrix');
  if (matrix) {
    let r_gain = (1.0 + s.gain_r + s.gain_master);
    let g_gain = (1.0 + s.gain_g + s.gain_master);
    let b_gain = (1.0 + s.gain_b + s.gain_master);

    let r_off = (s.lift_r + s.lift_master + (s.temp * 0.004));
    let g_off = (s.lift_g + s.lift_master - (s.tint * 0.004));
    let b_off = (s.lift_b + s.lift_master - (s.temp * 0.004));

    matrix.setAttribute('values', `
      ${r_gain.toFixed(3)} 0 0 0 ${r_off.toFixed(3)}
      0 ${g_gain.toFixed(3)} 0 0 ${g_off.toFixed(3)}
      0 0 ${b_gain.toFixed(3)} 0 ${b_off.toFixed(3)}
      0 0 0 1 0
    `.trim());
  }

  let filterStr = `contrast(${contPct}%) saturate(${satPct}%) brightness(${brightPct}%) url(#liveGrade)`;
  imgAfter.style.filter = filterStr;
}

// =========================================================================
// RETRO CRT & AUTHENTIC NTSC VHS SIMULATION (INTERACTIVE GPU TOGGLES)
// =========================================================================
function onToggleCRTScanlines(checked) {
  pushHistory(checked ? "Enable Trinitron CRT Scanlines" : "Disable CRT Scanlines");
  state.settings.crt_scanlines = checked;
  const overlay = document.getElementById('crtOverlay');
  if (overlay) overlay.style.display = checked ? 'block' : 'none';
  showToast(checked ? "Trinitron CRT Phosphor Triads active" : "CRT Scanlines disabled");
  refreshFrame();
}

function onCrtIntensityChange(val) {
  val = parseFloat(val);
  state.settings.crt_intensity = val;
  const lbl = document.getElementById('valCrtIntensity');
  if (lbl) lbl.innerText = `${Math.round(val * 100)}%`;
  const overlay = document.getElementById('crtOverlay');
  if (overlay) overlay.style.opacity = (val * 1.5).toString();
}

function onToggleCRTCurve(checked) {
  pushHistory(checked ? "Enable Curved Tube Monitor" : "Disable Curved Monitor");
  state.settings.crt_curve = checked;
  const bounds = document.getElementById('canvasBounds');
  if (bounds) {
    if (checked) bounds.classList.add('crt-curved');
    else bounds.classList.remove('crt-curved');
  }
  showToast(checked ? "Curved glass tube monitor enabled" : "Flat canvas enabled");
}

// =========================================================================
// AUTHENTIC NTSC-RS VHS STUDIO ENGINE CONTROLS
// =========================================================================
function onToggleVHSMode(checked) {
  pushHistory(checked ? "Enable Physical NTSC VHS DSP" : "Disable VHS Mode");
  state.settings.vhs_mode = checked;
  showToast(checked ? "Authentic NTSC VHS Tape DSP active" : "VHS Tape Mode disabled");
  refreshFrame();
}

function onVhsSpeedChange(val) {
  pushHistory(`VHS Speed: ${val.toUpperCase()}`);
  state.settings.vhs_tape_speed = val;
  showToast(`VHS Tape Speed: ${val.toUpperCase()}`);
  refreshFrame();
}

function onVhsChromaLossChange(val) {
  let v = parseFloat(val);
  state.settings.vhs_chroma_loss = v;
  const lbl = document.getElementById('valVhsChromaLoss');
  if (lbl) lbl.innerText = `${v.toFixed(2)}%`;
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onToggleVhsVertBlend(checked) {
  pushHistory(checked ? "Enable Chroma Vertical Blend" : "Disable Chroma Vertical Blend");
  state.settings.vhs_chroma_vert_blend = checked;
  refreshFrame();
}

function onToggleVhsSharpen(checked) {
  pushHistory(checked ? "Enable Luma Peaking Sharpen" : "Disable Sharpening");
  state.settings.vhs_sharpen_enabled = checked;
  refreshFrame();
}

function onVhsSharpenChange(val) {
  let v = parseFloat(val);
  state.settings.vhs_sharpen = v;
  const lbl = document.getElementById('valVhsSharpen');
  if (lbl) lbl.innerText = v.toFixed(2);
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onVhsSharpenFreqChange(val) {
  let v = parseFloat(val);
  state.settings.vhs_sharpen_freq = v;
  const lbl = document.getElementById('valVhsSharpenFreq');
  if (lbl) lbl.innerText = v.toFixed(2);
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onToggleHeadSwitching(checked) {
  pushHistory(checked ? "Enable Head-Switching Tracking" : "Disable Head-Switching");
  state.settings.head_switching = checked;
  refreshFrame();
}

function onHeadHeightChange(val) {
  let v = parseInt(val);
  state.settings.head_switching_height = v;
  const lbl = document.getElementById('valHeadHeight');
  if (lbl) lbl.innerText = `${v} lines`;
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onHeadShiftChange(val) {
  let v = parseInt(val);
  state.settings.head_switching_shift = v;
  const lbl = document.getElementById('valHeadShift');
  if (lbl) lbl.innerText = `${v} px`;
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onHeadJitterChange(val) {
  let v = parseFloat(val);
  state.settings.head_switching_jitter = v;
  const lbl = document.getElementById('valHeadJitter');
  if (lbl) lbl.innerText = v.toFixed(2);
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onToggleVhsEdgeWave(checked) {
  pushHistory(checked ? "Enable Tape Edge Wave" : "Disable Edge Wave");
  state.settings.vhs_edge_wave_enabled = checked;
  refreshFrame();
}

function onVhsEdgeWaveChange(val) {
  let v = parseFloat(val);
  state.settings.vhs_edge_wave = v;
  const lbl = document.getElementById('valVhsEdgeWave');
  if (lbl) lbl.innerText = v.toFixed(2);
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onVhsEdgeWaveSpeedChange(val) {
  let v = parseFloat(val);
  state.settings.vhs_edge_wave_speed = v;
  const lbl = document.getElementById('valVhsEdgeWaveSpeed');
  if (lbl) lbl.innerText = v.toFixed(2);
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onToggleVhsRinging(checked) {
  pushHistory(checked ? "Enable Luma Ringing" : "Disable Ringing");
  state.settings.vhs_ringing = checked;
  refreshFrame();
}

function onVhsRingingFreqChange(val) {
  let v = parseFloat(val);
  state.settings.vhs_ringing_freq = v;
  const lbl = document.getElementById('valVhsRingingFreq');
  if (lbl) lbl.innerText = v.toFixed(2);
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onVhsRingingPowerChange(val) {
  let v = parseInt(val);
  state.settings.vhs_ringing_power = v;
  const lbl = document.getElementById('valVhsRingingPower');
  if (lbl) lbl.innerText = v;
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onToggleVhsChromaNoise(checked) {
  pushHistory(checked ? "Enable Chroma Noise" : "Disable Chroma Noise");
  state.settings.vhs_chroma_noise = checked;
  refreshFrame();
}

function onVhsChromaNoiseChange(val) {
  let v = parseInt(val);
  state.settings.vhs_chroma_noise_intensity = v / 100.0;
  const lbl = document.getElementById('valVhsChromaNoise');
  if (lbl) lbl.innerText = `${v}%`;
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onToggleVhsCompNoise(checked) {
  pushHistory(checked ? "Enable Composite Noise" : "Disable Composite Noise");
  state.settings.vhs_composite_noise = checked;
  refreshFrame();
}

function onVhsCompNoiseChange(val) {
  let v = parseInt(val);
  state.settings.vhs_composite_noise_intensity = v / 100.0;
  const lbl = document.getElementById('valVhsCompNoise');
  if (lbl) lbl.innerText = `${v}%`;
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => { refreshFrame(); }, 120);
}

function onToggleAudioEQ(checked) {
  pushHistory(checked ? "Enable Dialogue Clarity EQ" : "Disable Dialogue Clarity EQ");
  state.settings.audio_eq = checked;
  showToast(checked ? "Audio dialogue presence & hiss filter active" : "Audio filter disabled");
}

// =========================================================================
// FRAME RENDERING (HIGH-PRECISION BACKGROUND SYNC)
// =========================================================================
async function refreshFrame() {
  if (state.activeIndex < 0) return;
  
  let loader = document.getElementById('frameLoader');
  if (loader) {
    loader.style.display = 'flex';
    document.getElementById('lblLoaderText').innerText = `Processing frame...`;
  }

  try {
    if (state.viewMode === 'ab_compare') {
      let res = await window.pywebview.api.get_ab_model_comparison(state.currentSec, state.settings);
      if (res && res.model_a && res.model_b) {
        let imgB = document.getElementById('imgBefore');
        let imgA = document.getElementById('imgAfter');
        imgB.src = res.model_b;
        imgA.src = res.model_a;
        imgB.style.display = 'block';
        imgA.style.display = 'block';
        imgB.style.opacity = '1';
        imgA.style.opacity = '1';
        imgA.style.filter = 'none';
        document.getElementById('tagSource').innerText = res.name_b;
        document.getElementById('tagRemaster').innerText = res.name_a;
        document.getElementById('lblFrameTech').innerText = "A/B Neural vs Traditional Scaler Compare";
        document.getElementById('canvasBounds').style.display = 'inline-flex';
        document.getElementById('curtainDivider').style.display = 'block';
        document.getElementById('tagSource').style.display = 'block';
        document.getElementById('tagRemaster').style.display = 'block';
      }
      return;
    }

    let res = await window.pywebview.api.extract_preview_frames(state.currentSec, state.settings);
    if (res && res.before && res.after) {
      let imgB = document.getElementById('imgBefore');
      let imgA = document.getElementById('imgAfter');
      imgB.src = res.before;
      imgA.src = res.after;
      imgB.style.display = 'block';
      imgA.style.display = 'block';
      imgB.style.opacity = '1';
      imgA.style.opacity = '1';
      imgA.style.filter = 'none'; // Ensure CSS live grade does not compound on newly rendered frame
      document.getElementById('canvasBounds').style.display = 'inline-flex';
      
      let isSplit = (state.viewMode === 'split');
      let isRemaster = (state.viewMode === 'remaster');
      let isOriginal = (state.viewMode === 'original');

      const afterClip = document.getElementById('afterClip');
      const divider = document.getElementById('curtainDivider');
      const tagL = document.getElementById('tagSource');
      const tagR = document.getElementById('tagRemaster');

      if (isSplit) {
        afterClip.style.display = 'block';
        divider.style.display = 'block';
        tagL.style.display = 'block';
        tagR.style.display = 'block';
        setCurtainPos(state.curtainPct !== undefined ? state.curtainPct : 50);
      } else if (isRemaster) {
        afterClip.style.display = 'block';
        afterClip.style.clipPath = 'inset(0 0 0 0%)';
        divider.style.display = 'none';
        tagL.style.display = 'none';
        tagR.style.display = 'block';
      } else if (isOriginal) {
        afterClip.style.display = 'none';
        divider.style.display = 'none';
        tagL.style.display = 'block';
        tagR.style.display = 'none';
      }

      let modelTag = state.settings.ai_model.includes('realesr') ? 'Real-ESRGAN AI' : 'Lanczos-3 + CAS';
      document.getElementById('lblFrameTech').innerText = `${res.width}x${res.height} ${modelTag} (${res.timestamp})`;
      updateResolutionTags();
    }
  } catch (err) {
    console.error("refreshFrame error:", err);
  } finally {
    if (loader) loader.style.display = 'none';
  }
}

function onFrameLoaded() {
  let loader = document.getElementById('frameLoader');
  let imgB = document.getElementById('imgBefore');
  let imgA = document.getElementById('imgAfter');
  let div = document.getElementById('curtainDivider');
  let tagL = document.getElementById('tagSource');
  let tagR = document.getElementById('tagRemaster');

  loader.style.display = 'none';
  imgB.style.opacity = '1';
  imgA.style.opacity = '1';
  imgA.style.filter = 'none'; // Clear compound grading filter on loaded frame

  if (state.viewMode === 'split' || state.viewMode === 'ab_compare') {
    div.style.display = 'block';
    setCurtainPos(state.curtainPct !== undefined ? state.curtainPct : 50);
  }
  tagL.style.display = 'block';
  tagR.style.display = 'block';
}

// =========================================================================
// 100% FLUSH CURTAIN DIVIDER (0% TO 100% EDGE TO EDGE)
// =========================================================================
function setCurtainPos(pct) {
  pct = Math.max(0, Math.min(100, pct));
  state.curtainPct = pct;
  const divider = document.getElementById('curtainDivider');
  const afterClip = document.getElementById('afterClip');

  if (divider) divider.style.left = `${pct}%`;
  if (afterClip) afterClip.style.clipPath = `inset(0 0 0 ${pct}%)`;

  // Auto-fade badges if curtain handle approaches them to prevent overlapping/clipping
  const tagL = document.getElementById('tagSource');
  const tagR = document.getElementById('tagRemaster');
  if (tagL) {
    if (pct < 18) {
      tagL.style.opacity = '0';
      tagL.style.transform = 'translateY(6px)';
    } else {
      tagL.style.opacity = '1';
      tagL.style.transform = 'translateY(0)';
    }
  }
  if (tagR) {
    if (pct > 82) {
      tagR.style.opacity = '0';
      tagR.style.transform = 'translateY(6px)';
    } else {
      tagR.style.opacity = '1';
      tagR.style.transform = 'translateY(0)';
    }
  }
}


// =========================================================================
// REAL-TIME PREVIEW PLAYBACK LOOP (SPACEBAR / PLAY BUTTON)
// =========================================================================
function togglePlayback() {
  if (state.activeIndex < 0) return;
  const item = state.queue[state.activeIndex];
  if (item && item.is_image) return;

  state.isPlaying = !state.isPlaying;
  const btn = document.getElementById('btnPlayPause');
  const iconPlay = document.getElementById('iconPlay');
  const iconPause = document.getElementById('iconPause');

  if (state.isPlaying) {
    if (btn) btn.classList.add('playing');
    if (iconPlay) iconPlay.style.display = 'none';
    if (iconPause) iconPause.style.display = 'block';
    showToast("Preview Playback started", "play");

    state.playInterval = setInterval(() => {
      let dur = state.queue[state.activeIndex]?.duration || 100;
      state.currentSec += 1;
      if (state.currentSec >= Math.floor(dur)) {
        state.currentSec = 0;
      }
      const scrubber = document.getElementById('timelineScrubber');
      if (scrubber) scrubber.value = state.currentSec;
      updateTimeReadout();
      refreshFrame();
    }, 1200);
  } else {
    stopPlayback();
  }
}

function stopPlayback() {
  state.isPlaying = false;
  if (state.playInterval) {
    clearInterval(state.playInterval);
    state.playInterval = null;
  }
  const btn = document.getElementById('btnPlayPause');
  const iconPlay = document.getElementById('iconPlay');
  const iconPause = document.getElementById('iconPause');
  if (btn) btn.classList.remove('playing');
  if (iconPlay) iconPlay.style.display = 'block';
  if (iconPause) iconPause.style.display = 'none';
}

// Spacebar key shortcut for Play/Pause
window.addEventListener('keydown', (e) => {
  if (e.code === 'Space' && !e.target.matches('input, textarea, select')) {
    e.preventDefault();
    togglePlayback();
  }
});

// =========================================================================
// INTERACTIVE ZOOM IN / OUT SYSTEM (HUD CONTROLS & WHEEL)
// =========================================================================
function applyZoomLevel() {
  const bounds = document.getElementById('canvasBounds');
  const lbl = document.getElementById('lblZoomLevel');
  if (bounds) {
    bounds.style.transform = `scale(${state.zoomLevel})`;
    bounds.style.transformOrigin = 'center center';
  }
  if (lbl) {
    lbl.innerText = `${Math.round(state.zoomLevel * 100)}%`;
  }
}

function zoomStep(delta) {
  state.zoomLevel = Math.max(0.5, Math.min(3.0, state.zoomLevel + delta));
  applyZoomLevel();
}

function resetZoom() {
  state.zoomLevel = 1.0;
  applyZoomLevel();
  showToast("Viewport Zoom: Fit (100%)");
}

function setupCurtainDivider() {
  const bounds = document.getElementById('canvasBounds');

  const updateFromEvent = (e) => {
    const rect = bounds.getBoundingClientRect();
    if (rect.width <= 0) return;
    let x = e.clientX - rect.left;
    let pct = (x / rect.width) * 100;
    setCurtainPos(pct);
  };

  bounds.addEventListener('mousedown', (e) => {
    if (state.viewMode !== 'split' && state.viewMode !== 'ab_compare') return;
    state.isCurtainDragging = true;
    updateFromEvent(e);
  });

  window.addEventListener('mousemove', (e) => {
    if (!state.isCurtainDragging) return;
    updateFromEvent(e);
  });

  window.addEventListener('mouseup', () => {
    state.isCurtainDragging = false;
  });
}

async function setViewMode(mode) {
  let prevMode = state.viewMode;
  state.viewMode = mode;
  document.querySelectorAll('.tab-pill').forEach(t => t.classList.remove('active'));
  const afterClip = document.getElementById('afterClip');
  const divider = document.getElementById('curtainDivider');
  const loader = document.getElementById('frameLoader');
  const bounds = document.getElementById('canvasBounds');
  const tagL = document.getElementById('tagSource');
  const tagR = document.getElementById('tagRemaster');

  if (bounds) bounds.style.display = 'inline-flex';
  if (loader) loader.style.display = 'none';

  if (mode === 'split') {
    document.getElementById('tabSplit').classList.add('active');
    afterClip.style.display = 'block';
    setCurtainPos(state.curtainPct || 50);
    divider.style.display = 'block';
    tagL.style.display = 'block';
    tagR.style.display = 'block';
    updateResolutionTags();
    if (prevMode === 'ab_compare') {
      await refreshFrame();
    }
  } else if (mode === 'ab_compare') {
    document.getElementById('tabABCompare').classList.add('active');
    afterClip.style.display = 'block';
    setCurtainPos(state.curtainPct || 50);
    divider.style.display = 'block';
    tagL.style.display = 'block';
    tagR.style.display = 'block';
    await refreshFrame();
  } else if (mode === 'original') {
    document.getElementById('tabOriginal').classList.add('active');
    afterClip.style.display = 'none';
    divider.style.display = 'none';
    tagL.style.display = 'block';
    tagR.style.display = 'none';
    if (prevMode === 'ab_compare') {
      await refreshFrame();
    }
  } else if (mode === 'remaster') {
    document.getElementById('tabRemaster').classList.add('active');
    afterClip.style.display = 'block';
    afterClip.style.clipPath = 'inset(0 0 0 0%)';
    divider.style.display = 'none';
    tagL.style.display = 'none';
    tagR.style.display = 'block';
    if (prevMode === 'ab_compare') {
      await refreshFrame();
    }
  }
}

function toggleZoomMode() {
  state.isZoomed = !state.isZoomed;
  const bounds = document.getElementById('canvasBounds');
  const btn = document.getElementById('btnZoomToggle');
  if (state.isZoomed) {
    bounds.classList.add('zoom-100');
    btn.classList.add('active');
    document.getElementById('lblZoom').innerText = 'Fit Canvas';
    showToast("1:1 Pixel Zoom enabled (inspect neural sharpness)");
  } else {
    bounds.classList.remove('zoom-100');
    btn.classList.remove('active');
    document.getElementById('lblZoom').innerText = '1:1 Zoom';
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
  } else {
    document.exitFullscreen().catch(() => {});
  }
}

// =========================================================================
// 3-WAY COLOR WHEELS (ZERO LAG REAL-TIME 60FPS)
// =========================================================================
function startWheelDrag(e, wheelType) {
  e.preventDefault();
  state.activeWheel = wheelType;
  updateWheelPosition(e, wheelType);

  const onMouseMove = (ev) => {
    if (state.activeWheel) {
      updateWheelPosition(ev, state.activeWheel);
      updateLiveGPUGrade();
    }
  };
  const onMouseUp = () => {
    state.activeWheel = null;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
    
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(() => {
      refreshFrame();
    }, 120);
  };
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
}

function updateWheelPosition(e, type) {
  const wheel = document.getElementById(`wheel${type.charAt(0).toUpperCase() + type.slice(1)}`);
  const rect = wheel.getBoundingClientRect();
  const radius = rect.width / 2;
  const cx = rect.left + radius;
  const cy = rect.top + radius;

  let dx = e.clientX - cx;
  let dy = e.clientY - cy;
  let dist = Math.sqrt(dx * dx + dy * dy);

  if (dist > radius - 6) {
    dx = (dx / dist) * (radius - 6);
    dy = (dy / dist) * (radius - 6);
  }

  const puck = document.getElementById(`puck${type.charAt(0).toUpperCase() + type.slice(1)}`);
  puck.style.left = `${radius + dx}px`;
  puck.style.top = `${radius + dy}px`;

  let angle = Math.atan2(dy, dx);
  let mag = Math.min(1.0, dist / radius) * 0.35;

  let r = Math.cos(angle) * mag;
  let g = Math.cos(angle - (2 * Math.PI / 3)) * mag;
  let b = Math.cos(angle + (2 * Math.PI / 3)) * mag;

  state.settings[`${type}_r`] = roundVal(r);
  state.settings[`${type}_g`] = roundVal(g);
  state.settings[`${type}_b`] = roundVal(b);

  const badge = document.getElementById(`lbl${type.charAt(0).toUpperCase() + type.slice(1)}Readout`);
  if (badge) {
    badge.innerText = `R${r >= 0 ? '+' : ''}${Math.round(r*100)} G${g >= 0 ? '+' : ''}${Math.round(g*100)} B${b >= 0 ? '+' : ''}${Math.round(b*100)}`;
  }
}

function onWheelMasterLive(type, val) {
  val = parseFloat(val);
  state.settings[`${type}_master`] = val;
  updateLiveGPUGrade();
  
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => {
    refreshFrame();
  }, 120);
}

function resetSingleWheel(type) {
  state.settings[`${type}_r`] = 0.0;
  state.settings[`${type}_g`] = 0.0;
  state.settings[`${type}_b`] = 0.0;
  state.settings[`${type}_master`] = 0.0;
  const puck = document.getElementById(`puck${type.charAt(0).toUpperCase() + type.slice(1)}`);
  if (puck) { puck.style.left = '50%'; puck.style.top = '50%'; }
  const sl = document.getElementById(`sl${type.charAt(0).toUpperCase() + type.slice(1)}Master`);
  if (sl) sl.value = 0;
  const badge = document.getElementById(`lbl${type.charAt(0).toUpperCase() + type.slice(1)}Readout`);
  if (badge) badge.innerText = "R0 G0 B0";
  updateLiveGPUGrade();
  refreshFrame();
}

function resetColorWheels() {
  pushHistory("Reset 3-Way Color Wheels");
  ['lift', 'gamma', 'gain'].forEach(t => resetSingleWheel(t));
  showToast("Reset 3-way color wheels to neutral");
}

function updateWheelPositionsFromSettings() {
  ['lift', 'gamma', 'gain'].forEach(type => {
    const puck = document.getElementById(`puck${type.charAt(0).toUpperCase() + type.slice(1)}`);
    const wheel = document.getElementById(`wheel${type.charAt(0).toUpperCase() + type.slice(1)}`);
    const badge = document.getElementById(`lbl${type.charAt(0).toUpperCase() + type.slice(1)}Readout`);
    const r = state.settings[`${type}_r`] || 0;
    const g = state.settings[`${type}_g`] || 0;
    const b = state.settings[`${type}_b`] || 0;
    const master = state.settings[`${type}_master`] || 0;
    const slMaster = document.getElementById(`sl${type.charAt(0).toUpperCase() + type.slice(1)}Master`);
    if (slMaster) slMaster.value = master;

    if (badge) {
      badge.innerText = `R${r >= 0 ? '+' : ''}${Math.round(r*100)} G${g >= 0 ? '+' : ''}${Math.round(g*100)} B${b >= 0 ? '+' : ''}${Math.round(b*100)}`;
    }
    if (puck && wheel) {
      const radius = wheel.offsetWidth ? wheel.offsetWidth / 2 : 45;
      if (Math.abs(r) < 0.001 && Math.abs(g) < 0.001 && Math.abs(b) < 0.001) {
        puck.style.left = '50%';
        puck.style.top = '50%';
      } else {
        let dx = (r - (g + b) / 2) * (radius / 0.35);
        let dy = ((g - b) * 0.866) * (radius / 0.35);
        let dist = Math.sqrt(dx * dx + dy * dy);
        if (dist > radius - 6) {
          dx = (dx / dist) * (radius - 6);
          dy = (dy / dist) * (radius - 6);
        }
        puck.style.left = `${radius + dx}px`;
        puck.style.top = `${radius + dy}px`;
      }
    }
  });
}

function roundVal(v) { return Math.round(v * 1000) / 1000; }

// =========================================================================
// SLIDER LIVE 60FPS INTERACTION
// =========================================================================
function onParamChangeLive(key, val, lblId) {
  val = parseFloat(val);
  state.settings[key] = val;
  
  if (lblId) {
    if (key === 'exposure') document.getElementById(lblId).innerText = `${val >= 0 ? '+' : ''}${val.toFixed(2)} EV`;
    else if (key === 'temp' || key === 'tint') document.getElementById(lblId).innerText = `${val > 0 ? '+' : ''}${val}`;
    else if (key === 'lut_intensity') document.getElementById(lblId).innerText = `${Math.round(val * 100)}%`;
    else if (key === 'cq') document.getElementById(lblId).innerText = `${val} (${val <= 18 ? 'Master' : 'High Quality'})`;
    else if (key === 'line_darken') document.getElementById(lblId).innerText = val.toFixed(2);
    else document.getElementById(lblId).innerText = val.toFixed(key === 'brightness' ? 3 : 2);
  }

  updateLiveGPUGrade();

  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => {
    refreshFrame();
  }, 120);
}

function onToggleParam(key, checked) {
  state.settings[key] = checked;
  refreshFrame();
}

// =========================================================================
// QUICK PRESETS
// =========================================================================
function quickApplyPreset(presetId) {
  let presets = {
    apple_master: {"contrast": 1.060, "brightness": 0.005, "gamma": 1.040, "saturation": 1.150, "sharpness": 0.60, "denoise": 2.5, "temp": 0, "exposure": 0.0, "crt_scanlines": false, "vhs_mode": false, "crt_curve": false},
    cel_master: {"contrast": 1.020, "brightness": 0.015, "gamma": 1.050, "saturation": 1.050, "sharpness": 0.50, "denoise": 2.0, "temp": 0, "exposure": 0.0, "crt_scanlines": false, "vhs_mode": false, "crt_curve": false},
    film_35mm: {"contrast": 1.080, "brightness": 0.010, "gamma": 1.080, "saturation": 1.350, "sharpness": 0.50, "denoise": 1.0, "temp": 35, "exposure": 0.05, "crt_scanlines": false, "vhs_mode": false, "crt_curve": false},
    ink_sharp: {"contrast": 1.060, "brightness": 0.010, "gamma": 1.050, "saturation": 1.200, "sharpness": 1.00, "denoise": 3.5, "temp": 0, "exposure": 0.0, "crt_scanlines": false, "vhs_mode": false, "crt_curve": false},
    hdr_pop: {"contrast": 1.100, "brightness": 0.020, "gamma": 1.120, "saturation": 1.650, "sharpness": 0.85, "denoise": 2.5, "temp": 2, "exposure": 0.08, "crt_scanlines": false, "vhs_mode": false, "crt_curve": false},
    retro_crt: {"contrast": 1.060, "brightness": 0.025, "gamma": 1.150, "saturation": 1.300, "sharpness": 0.50, "denoise": 1.5, "temp": 8, "exposure": 0.0, "crt_scanlines": true, "crt_intensity": 0.65, "vhs_mode": false, "crt_curve": true},
    vhs_tape: {"contrast": 1.080, "brightness": 0.015, "gamma": 1.080, "saturation": 1.400, "sharpness": 0.60, "denoise": 1.0, "temp": 6, "exposure": 0.0, "crt_scanlines": false, "vhs_mode": true, "crt_curve": false, "vhs_tape_speed": "lp", "head_switching": true, "head_switching_height": 24, "head_switching_shift": 90, "vhs_edge_wave_enabled": true},
    oled_clean: {"contrast": 1.050, "brightness": 0.025, "gamma": 1.140, "saturation": 1.150, "sharpness": 0.85, "denoise": 3.5, "temp": -28, "exposure": 0.02, "crt_scanlines": false, "vhs_mode": false, "crt_curve": false}
  };

  let p = presets[presetId];
  if (!p) return;

  // Snapshot previous settings for undo
  pushHistory(`Preset: ${presetId.replace('_', ' ').toUpperCase()}`);

  for (let k in p) state.settings[k] = p[k];

  syncAllInputsFromSettings();

  // Highlight active preset chip
  document.querySelectorAll('.chip-preset').forEach(b => b.classList.remove('active'));
  const activeBtn = document.getElementById(`preset_${presetId}`);
  if (activeBtn) activeBtn.classList.add('active');

  updateLiveGPUGrade();
  showToast(`Applied: ${presetId.replace('_', ' ').toUpperCase()}`);
  refreshFrame();
}

// =========================================================================
// AI COLOR MATCHING
// =========================================================================
async function triggerColorMatch() {
  showToast("Select a reference image to transfer color grading...");
  let res = await window.pywebview.api.match_color_from_reference_dialog(state.currentSec);
  if (res && res.success) {
    pushHistory(`AI Color Match: ${res.ref_name || 'Reference'}`);
    state.settings.contrast = res.contrast;
    state.settings.brightness = res.brightness;
    state.settings.saturation = res.saturation;
    state.settings.gain_r = res.gain_r;
    state.settings.gain_g = res.gain_g;
    state.settings.gain_b = res.gain_b;
    state.settings.lift_r = res.lift_r;
    state.settings.lift_g = res.lift_g;
    state.settings.lift_b = res.lift_b;

    syncAllInputsFromSettings();
    updateLiveGPUGrade();
    showToast(`Color matched to '${res.ref_name}'!`);
    refreshFrame();
  }
}

// =========================================================================
// PRESETS: COPY (CLIPBOARD), EXTRACT (FILE), APPLY (SMART CLIPBOARD/FILE)
// =========================================================================
async function copyPresetToClipboard() {
  let payload = {
    apple_upscaler_preset: true,
    version: "2.0",
    name: "Apple Studio Custom Preset",
    settings: JSON.parse(JSON.stringify(state.settings))
  };
  let jsonStr = JSON.stringify(payload, null, 2);
  let ok = false;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(jsonStr);
      ok = true;
    }
  } catch (e) {}

  if (!ok && window.pywebview && window.pywebview.api && window.pywebview.api.copy_text_to_clipboard) {
    ok = await window.pywebview.api.copy_text_to_clipboard(jsonStr);
  }

  showToast("Preset copied to clipboard as text!", "clipboard");
}

async function extractPresetToFile() {
  let payload = {
    apple_upscaler_preset: true,
    version: "2.0",
    name: "Apple Studio Custom Preset",
    settings: JSON.parse(JSON.stringify(state.settings))
  };
  let jsonStr = JSON.stringify(payload, null, 2);
  let fname = await window.pywebview.api.save_preset_dialog(jsonStr);
  if (fname) {
    showToast(`Extracted preset file '${fname}'!`, "download");
  }
}

async function applySmartPreset() {
  let clipboardText = "";
  try {
    if (navigator.clipboard && navigator.clipboard.readText) {
      clipboardText = await navigator.clipboard.readText();
    }
  } catch (e) {}

  if (!clipboardText && window.pywebview && window.pywebview.api && window.pywebview.api.get_clipboard_text) {
    try {
      clipboardText = await window.pywebview.api.get_clipboard_text();
    } catch (e) {}
  }

  // Parse clipboard text if present
  let parsedSettings = null;
  if (clipboardText && clipboardText.trim()) {
    try {
      let data = JSON.parse(clipboardText.trim());
      if (data && typeof data === 'object') {
        if (data.settings && typeof data.settings === 'object') {
          parsedSettings = data.settings;
        } else if (data.contrast !== undefined || data.gamma !== undefined || data.saturation !== undefined) {
          parsedSettings = data;
        }
      }
    } catch (e) {}
  }

  if (parsedSettings) {
    applyAuditionProfile(parsedSettings, "Clipboard Preset");
    showToast("Applied preset from clipboard text!", "check");
    return;
  }

  // Fallback: Open file picker to let user choose preset file
  showToast("No preset on clipboard. Pick preset file from PC...", "info");
  let res = await window.pywebview.api.load_preset_dialog();
  if (res && res.success && res.settings) {
    applyAuditionProfile(res.settings, res.name || "Loaded Preset");
    showToast(`Loaded preset '${res.name}'!`, "check");
  }
}

// =========================================================================
// SMART AI FRAME ANALYSIS & PROBLEM RECOGNITION
// =========================================================================
async function triggerAIAutoEnhance() {
  if (state.activeIndex < 0) {
    showToast("Load a video or photo first.", "info");
    return;
  }
  showToast("AI analyzing frame & detecting anomalies...", "wand");

  let res = await window.pywebview.api.analyze_and_auto_enhance(state.currentSec);
  if (!res || !res.success) {
    showToast(res && res.message ? res.message : "AI analysis failed", "info");
    return;
  }

  // Open AI Diagnostic Modal
  let modal = document.getElementById('aiDiagModal');
  let body = document.getElementById('aiDiagBody');
  if (!modal || !body) {
    if (res.settings) {
      applyAuditionProfile(res.settings, "AI Auto-Enhance");
      showToast(`AI Auto-Enhanced: fixed ${res.problems.length} source issues!`, "wand");
    }
    return;
  }

  state.pendingAISettings = res.settings;

  let problemsHtml = (res.problems || []).map(p => `
    <div class="diag-item problem">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
      <div>${p}</div>
    </div>
  `).join('');

  let enhancementsHtml = (res.enhancements || []).map(e => `
    <div class="diag-item enhancement">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
      <div>${e}</div>
    </div>
  `).join('');

  let m = res.metrics || {};
  body.innerHTML = `
    <div>
      <div class="diag-section-title">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        Identified Anomalies & Deficiencies (${res.problems.length})
      </div>
      <div class="diag-list">${problemsHtml || '<div class="diag-item enhancement">No critical issues detected; source is high-fidelity reference.</div>'}</div>
    </div>

    <div>
      <div class="diag-section-title">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
        AI Calculated Enhancements (${res.enhancements.length})
      </div>
      <div class="diag-list">${enhancementsHtml}</div>
    </div>

    <div>
      <div class="diag-section-title">Source Frame Metrics</div>
      <div class="diag-metrics-row">
        <div class="diag-metric-box">
          <span class="diag-metric-label">Resolution</span>
          <span class="diag-metric-val">${m.resolution || '--'}</span>
        </div>
        <div class="diag-metric-box">
          <span class="diag-metric-label">Mean Luma</span>
          <span class="diag-metric-val">${m.mean_luma || '--'} IRE</span>
        </div>
        <div class="diag-metric-box">
          <span class="diag-metric-label">Saturation</span>
          <span class="diag-metric-val">${Math.round((m.mean_sat || 0) * 100)}%</span>
        </div>
        <div class="diag-metric-box">
          <span class="diag-metric-label">Noise Index</span>
          <span class="diag-metric-val">${m.noise_level || '--'}</span>
        </div>
      </div>
    </div>
  `;

  modal.style.display = 'flex';
}

function applyPendingAIEnhancements() {
  if (state.pendingAISettings) {
    applyAuditionProfile(state.pendingAISettings, "AI Auto-Enhance");
    closeAIDiagModal();
    showToast("Applied AI Calculated Enhancements!", "wand");
  }
}

function closeAIDiagModal() {
  const m = document.getElementById('aiDiagModal');
  if (m) m.style.display = 'none';
}

// =========================================================================
// AUTO SCENE DETECTION
// =========================================================================
async function triggerDetectScenes() {
  let strip = document.getElementById('sceneListStrip');
  strip.innerHTML = '<div style="font-size:11px; color:var(--accent-cyan); display:flex; gap:6px; align-items:center;"><div class="spinner-ring" style="width:14px;height:14px;border-width:2px;"></div> Indexing scene cuts...</div>';
  
  let scenes = await window.pywebview.api.detect_scenes_fast();
  if (scenes && scenes.length) {
    strip.innerHTML = scenes.map(s => `
      <button class="btn-subtle" style="padding:4px 8px; font-size:10px;" onclick="seekToScene(${s.seconds})">
        ${s.name} (${s.timestamp})
      </button>
    `).join('');
    showToast(`Detected ${scenes.length} scene cuts`);
  } else {
    strip.innerHTML = '<div style="font-size:11px; color:var(--text-dim);">No significant scene cuts found</div>';
  }
}

function seekToScene(sec) {
  state.currentSec = sec;
  document.getElementById('timelineScrubber').value = sec;
  updateTimeReadout();
  refreshFrame();
}

// =========================================================================
// BATCH QUEUE
// =========================================================================
function updateBatchQueueUI() {
  let list = document.getElementById('batchQueueList');
  if (!list) return;
  if (!state.queue || !state.queue.length) {
    list.innerHTML = '<div style="color:var(--text-dim); font-size:11px; padding:8px 0;">No media in queue</div>';
    return;
  }
  list.innerHTML = state.queue.map((item, idx) => `
    <div class="queue-row ${idx === state.activeIndex ? 'active' : ''}" style="${idx === state.activeIndex ? 'border-left: 2px solid var(--accent-primary); background: rgba(225, 29, 72, 0.12);' : ''}">
      <input type="checkbox" ${item.selected_for_batch !== false ? 'checked' : ''} onchange="onItemBatchToggle(${idx}, this.checked)" />
      <span class="queue-item-title" onclick="selectMedia(${idx})" style="cursor:pointer; ${idx === state.activeIndex ? 'color: #ffffff; font-weight: 600;' : ''}" title="${item.filename || item.name}">${idx + 1}. ${item.filename || item.name}</span>
      <span class="queue-status-badge ${item.status.toLowerCase()}">${item.status}</span>
    </div>
  `).join('');
}

async function onItemBatchToggle(idx, checked) {
  state.queue[idx].selected_for_batch = checked;
  await window.pywebview.api.toggle_queue_item_batch(idx, checked);
}

async function selectAllBatch(val) {
  state.queue = await window.pywebview.api.select_all_batch(val);
  updateBatchQueueUI();
}

// =========================================================================
// SIDEBAR TABS & PARAMETERS
// =========================================================================
function switchSidebarTab(tabId, btn) {
  document.querySelectorAll('.studio-tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.studio-scroll').forEach(p => p.style.display = 'none');
  btn.classList.add('active');
  document.getElementById(tabId).style.display = 'flex';
}

function setAIModel(model, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => {
    b.classList.remove('active');
    b.style.borderColor = 'transparent';
  });
  btn.classList.add('active');
  btn.style.borderColor = 'var(--accent-primary)';
  state.settings.ai_model = model;
  showToast(`Active Scaler: ${model}`);
  refreshFrame();
}

function setFraming(mode, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.framing = mode;
  refreshFrame();
}

function setResolution(res, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.resolution = res;
  updateResolutionTags();
  refreshFrame();
}

function setLutMode(mode, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.lut_mode = mode;
  refreshFrame();
}

async function triggerBrowseLUT() {
  let fname = await window.pywebview.api.browse_lut_dialog();
  if (fname) {
    let btnCustom = document.getElementById('btnCustomLut');
    btnCustom.style.display = 'block';
    btnCustom.innerText = fname.length > 12 ? fname.substring(0, 10) + '...' : fname;
    setLutMode('custom', btnCustom);
    showToast(`Loaded 3D LUT: ${fname}`);
  }
}

function setExportFormat(fmt, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.export_fmt = fmt;
}

function setGpuMode(mode, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.gpu = mode;
}

function onToggleDeleteOriginal(checked) {
  state.settings.delete_original = checked;
  if (checked) {
    showToast("Warning: Original source file will be deleted after export successfully finishes.");
  }
}

function resetSlidersToDefault() {
  pushHistory("Reset to Calibrated Defaults");
  let defs = {
    contrast: 1.060, brightness: 0.005, gamma: 1.040, saturation: 1.150, sharpness: 0.600,
    exposure: 0.0, temp: 0, tint: 0, denoise: 3.0, grain: 0.0, deband: true, edge_clean: true,
    deinterlace: false, lut_mode: "none", lut_intensity: 1.0, crt_scanlines: false, vhs_mode: false,
    crt_curve: false, vhs_tape_speed: "lp", vhs_chroma_loss: 0.0025, vhs_chroma_vert_blend: true,
    vhs_sharpen_enabled: true, vhs_sharpen: 0.25, vhs_sharpen_freq: 1.0,
    head_switching: true, head_switching_height: 8, head_switching_shift: 72, head_switching_jitter: 0.03,
    vhs_edge_wave_enabled: true, vhs_edge_wave: 0.5, vhs_edge_wave_speed: 4.0,
    vhs_ringing: true, vhs_ringing_freq: 0.45, vhs_ringing_power: 4,
    vhs_chroma_noise: true, vhs_chroma_noise_intensity: 0.10,
    vhs_composite_noise: true, vhs_composite_noise_intensity: 0.05,
    line_darken: 0.0, cel_deflicker: false, audio_eq: false,
    lift_r: 0.0, lift_g: 0.0, lift_b: 0.0, lift_master: 0.0,
    gamma_r: 0.0, gamma_g: 0.0, gamma_b: 0.0, gamma_master: 0.0,
    gain_r: 0.0, gain_g: 0.0, gain_b: 0.0, gain_master: 0.0
  };
  for (let k in defs) state.settings[k] = defs[k];

  // Highlight Apple Master chip
  document.querySelectorAll('.chip-preset').forEach(b => b.classList.remove('active'));
  const activeBtn = document.getElementById('preset_apple_master');
  if (activeBtn) activeBtn.classList.add('active');

  syncAllInputsFromSettings();
  updateLiveGPUGrade();
  showToast("Restored all sliders to calibrated defaults");
  refreshFrame();
}

// =========================================================================
// VISUAL AUDITION MODAL (SUGGEST ENHANCEMENTS - BUG FIXED)
// =========================================================================
async function openAuditionModal() {
  if (state.activeIndex < 0) {
    showToast("Load a video or photo first.");
    return;
  }
  let modal = document.getElementById('auditionModal');
  let grid = document.getElementById('auditionGrid');
  modal.style.display = 'flex';
  
  grid.innerHTML = `
    <div style="grid-column: 1 / -1; display: flex; align-items: center; justify-content: center; height: 260px; color: var(--text-sub); gap: 12px;">
      <div class="spinner-ring"></div>
      <span>Rendering 6 AI remaster treatments...</span>
    </div>
  `;

  let cards = await window.pywebview.api.get_preset_auditions(state.currentSec);
  state.auditionCards = cards || [];
  
  if (cards && cards.length) {
    grid.innerHTML = cards.map((c, idx) => `
      <div class="audition-card" onclick="applyAuditionByIndex(${idx})">
        <div class="audition-thumb-wrap">
          <img class="audition-thumb" src="${c.thumb}" />
        </div>
        <div class="audition-info">
          <div class="audition-name-row">
            <span class="audition-name">${c.name}</span>
            <span class="audition-tag">${c.tag}</span>
          </div>
          <div class="audition-desc">${c.desc}</div>
        </div>
      </div>
    `).join('');
  } else {
    grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-dim); padding: 40px;">Could not render presets on current frame</div>`;
  }
}

function closeAuditionModal() {
  document.getElementById('auditionModal').style.display = 'none';
}

function applyAuditionByIndex(idx) {
  if (!state.auditionCards || !state.auditionCards[idx]) return;
  let card = state.auditionCards[idx];
  applyAuditionProfile(card.settings, card.name);
}

function applyAuditionProfile(settings, name) {
  pushHistory(`Profile: ${name || 'Audition'}`);
  for (let k in settings) state.settings[k] = settings[k];
  syncAllInputsFromSettings();
  closeAuditionModal();
  updateLiveGPUGrade();
  showToast(`Applied '${name}' profile`);
  refreshFrame();
}

// =========================================================================
// TRIMMING & FILE ACTIONS
// =========================================================================
function markInPoint() {
  state.settings.trim_in = formatSec(state.currentSec);
  state.settings.trim_enabled = true;
  document.getElementById('valTrimIn').innerText = state.settings.trim_in;
  showToast(`Marked In Point at ${state.settings.trim_in}`);
}

function markOutPoint() {
  state.settings.trim_out = formatSec(state.currentSec);
  state.settings.trim_enabled = true;
  document.getElementById('valTrimOut').innerText = state.settings.trim_out;
  showToast(`Marked Out Point at ${state.settings.trim_out}`);
}

function resetTrim() {
  state.settings.trim_enabled = false;
  state.settings.trim_in = "00:00:00";
  state.settings.trim_out = "00:00:00";
  document.getElementById('valTrimIn').innerText = "00:00:00";
  document.getElementById('valTrimOut').innerText = "Full Video";
  showToast("Trim points reset to full media");
}

async function triggerAddFiles() {
  try {
    let res = await window.pywebview.api.add_files_dialog();
    if (res && res.queue) {
      state.queue = res.queue;
      state.activeIndex = res.active_index;
      updateBatchQueueUI();
      updateFolderNav();
      if (state.activeIndex >= 0) await selectMedia(state.activeIndex);
      showToast(`Loaded ${res.queue.length} items`);
    }
  } catch (e) {
    console.error("add_files error:", e);
  }
}

async function triggerAddFolder() {
  try {
    let res = await window.pywebview.api.add_folder_dialog();
    if (res && res.queue) {
      state.queue = res.queue;
      state.activeIndex = res.active_index;
      updateBatchQueueUI();
      updateFolderNav();
      if (state.activeIndex >= 0) await selectMedia(state.activeIndex);
      showToast(`Loaded folder with ${res.queue.length} items`);
    }
  } catch (e) {
    console.error("add_folder error:", e);
  }
}

function openOutputDir() {
  window.pywebview.api.open_output_folder();
}

function watchInPotPlayer() {
  let btn = document.getElementById('lblPotPlayerBtn');
  btn.innerText = 'Encoding Sample...';
  showToast("Rendering 30s sample with dual-audio & subtitles...");
  window.pywebview.api.watch_in_potplayer_color_graded(state.currentSec, state.settings, 30);
}

function renderQuickSample(sec) {
  showToast(`Rendering ${sec}s fast test sample...`);
  window.pywebview.api.watch_in_potplayer_color_graded(state.currentSec, state.settings, sec);
}

function onPotPlayerLaunched(ok, msg) {
  document.getElementById('lblPotPlayerBtn').innerText = 'Watch Remastered';
  showToast(msg);
}

// BATCH EXPORT
function toggleExport() {
  if (state.isEncoding) {
    window.pywebview.api.stop_batch_encode();
    document.getElementById('lblExportBtn').innerText = 'Export Remastered Media';
    document.getElementById('btnExportVideo').classList.remove('cancel');
    state.isEncoding = false;
    showToast("Export cancelled");
  } else {
    window.pywebview.api.start_batch_encode(state.settings);
    document.getElementById('lblExportBtn').innerText = 'Cancel Batch Export';
    document.getElementById('btnExportVideo').classList.add('cancel');
    state.isEncoding = true;
    showToast("Batch export started (NVIDIA RTX accelerated)");
  }
}

function onBatchProgress(t) {
  document.getElementById('telSpeed').innerText = `Speed: ${t.fps} fps (${t.multiplier}x)`;
  document.getElementById('telEta').innerText = `ETA: ${t.eta}`;
  document.getElementById('exportProgFill').style.width = `${t.percent}%`;
}

function onFileCompleted(idx, ok) {
  if (state.queue[idx]) {
    state.queue[idx].status = ok ? 'Done' : 'Failed';
    updateBatchQueueUI();
  }
}

function onBatchFinished(success) {
  state.isEncoding = false;
  document.getElementById('lblExportBtn').innerText = 'Export Remastered Media';
  document.getElementById('btnExportVideo').classList.remove('cancel');
  document.getElementById('exportProgFill').style.width = '100%';
  showToast(success ? "Batch export finished successfully!" : "Batch export stopped");
  updateBatchQueueUI();
}