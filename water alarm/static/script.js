// ---------------------------------------------------------------
// AquaSentry front end
// Polls /api/status on an interval and drives every visual element.
// No frameworks — plain DOM + SVG attribute updates.
// ---------------------------------------------------------------

const TANK_TOP = 18;
const TANK_BOTTOM = 308;
const TANK_INNER_HEIGHT = TANK_BOTTOM - TANK_TOP; // 290
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 86;      // ~540.35

const el = {
  statusPill: document.getElementById('statusPill'),
  statusText: document.getElementById('statusText'),
  alarmBanner: document.getElementById('alarmBanner'),
  alarmBannerText: document.getElementById('alarmBannerText'),
  waterBody: document.getElementById('waterBody'),
  waterWave: document.getElementById('waterWave'),
  highLine: document.getElementById('highLine'),
  lowLine: document.getElementById('lowLine'),
  levelCm: document.getElementById('levelCm'),
  tankHeight: document.getElementById('tankHeight'),
  gaugeFill: document.getElementById('gaugeFill'),
  levelPercent: document.getElementById('levelPercent'),
  trendText: document.getElementById('trendText'),
  volumeLiters: document.getElementById('volumeLiters'),
  distanceCm: document.getElementById('distanceCm'),
  lastUpdated: document.getElementById('lastUpdated'),
  lowSlider: document.getElementById('lowSlider'),
  highSlider: document.getElementById('highSlider'),
  lowVal: document.getElementById('lowVal'),
  highVal: document.getElementById('highVal'),
  modeButtons: document.getElementById('modeButtons'),
  logList: document.getElementById('logList'),
  clock: document.getElementById('clock'),
};

let audioCtx = null;
let lastStatus = 'NORMAL';
let userIsEditingThresholds = false;

function beep() {
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'square';
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.06, audioCtx.currentTime);
    osc.connect(gain).connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.15);
  } catch (e) { /* audio not available until user interacts with page */ }
}

function yForPercent(pct) {
  return TANK_BOTTOM - (pct / 100) * TANK_INNER_HEIGHT;
}

function renderTank(percent) {
  const y = yForPercent(percent);
  const height = TANK_BOTTOM - y;
  el.waterBody.setAttribute('y', y);
  el.waterBody.setAttribute('height', Math.max(0, height));

  const wavePath =
    `M18,${y} Q 55,${y - 6} 92,${y} T 166,${y} T 202,${y} V320 H18 Z`;
  el.waterWave.setAttribute('d', wavePath);
}

function renderGuideLines(low, high) {
  const highY = yForPercent(high);
  const lowY = yForPercent(low);
  el.highLine.setAttribute('y1', highY);
  el.highLine.setAttribute('y2', highY);
  el.lowLine.setAttribute('y1', lowY);
  el.lowLine.setAttribute('y2', lowY);
}

function renderGauge(percent, status) {
  const offset = GAUGE_CIRCUMFERENCE * (1 - percent / 100);
  el.gaugeFill.style.strokeDashoffset = offset;
  const color = status === 'NORMAL' ? '#5eead4' : '#ef4a52';
  el.gaugeFill.style.stroke = color;
}

function renderLog(entries) {
  if (!entries || entries.length === 0) {
    el.logList.innerHTML = '<li class="log-empty">No events yet.</li>';
    return;
  }
  el.logList.innerHTML = entries.map(e => `
    <li data-level="${e.level}">
      <span class="log-time">${e.time}</span>
      <span>${e.message}</span>
    </li>
  `).join('');
}

function applyStatus(status) {
  el.statusPill.dataset.status = status;
  el.statusText.textContent = status.replace('_', ' ');

  const inAlarm = status === 'LOW_ALARM' || status === 'HIGH_ALARM';
  el.alarmBanner.classList.toggle('active', inAlarm);
  if (inAlarm) {
    el.alarmBannerText.textContent =
      status === 'LOW_ALARM' ? '⚠ LOW WATER LEVEL — ALARM ACTIVE' : '⚠ TANK OVERFLOW RISK — ALARM ACTIVE';
  }

  if (inAlarm && lastStatus !== status) beep();
  lastStatus = status;
}

async function poll() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();

    renderTank(data.level_percent);
    renderGauge(data.level_percent, data.status);
    applyStatus(data.status);

    el.levelPercent.innerHTML = `${data.level_percent.toFixed(1)}<span>%</span>`;
    el.trendText.textContent = data.trend;
    el.volumeLiters.textContent = `${data.volume_liters.toFixed(1)} L`;
    el.distanceCm.textContent = `${data.distance_cm.toFixed(1)} cm`;
    el.lastUpdated.textContent = data.last_updated || '--:--:--';
    el.levelCm.textContent = data.level_cm.toFixed(1);
    el.tankHeight.textContent = data.tank_height_cm;

    if (!userIsEditingThresholds) {
      el.lowSlider.value = data.low_threshold;
      el.highSlider.value = data.high_threshold;
      el.lowVal.textContent = Math.round(data.low_threshold);
      el.highVal.textContent = Math.round(data.high_threshold);
    }
    renderGuideLines(data.low_threshold, data.high_threshold);
    renderLog(data.alarm_log);
  } catch (err) {
    console.error('poll failed', err);
  }
}

// ---------------- Controls ----------------
let thresholdDebounce = null;
function sendThresholds() {
  clearTimeout(thresholdDebounce);
  thresholdDebounce = setTimeout(() => {
    fetch('/api/thresholds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ low: el.lowSlider.value, high: el.highSlider.value }),
    });
  }, 250);
}

[el.lowSlider, el.highSlider].forEach(slider => {
  slider.addEventListener('input', () => {
    userIsEditingThresholds = true;
    el.lowVal.textContent = el.lowSlider.value;
    el.highVal.textContent = el.highSlider.value;
    renderGuideLines(Number(el.lowSlider.value), Number(el.highSlider.value));
    sendThresholds();
  });
  slider.addEventListener('change', () => { userIsEditingThresholds = false; });
});

el.modeButtons.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-mode]');
  if (!btn) return;
  [...el.modeButtons.children].forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  fetch('/api/mode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode: btn.dataset.mode }),
  });
});

// ---------------- Clock ----------------
function tickClock() {
  el.clock.textContent = new Date().toLocaleTimeString();
}
setInterval(tickClock, 1000);
tickClock();

// ---------------- Boot ----------------
poll();
setInterval(poll, 1500);
