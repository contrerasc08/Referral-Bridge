// Checks the SunCalc wiring against real dates, and the photo lifecycle in a
// small fake browser: missing files, reduced motion, tab return and cleanup.
import test from 'node:test';
import assert from 'node:assert/strict';

// ---- a tiny fake browser ----
const listeners = { window: new Map(), document: new Map() };
const on = (m) => (t, f) => { if (!m.has(t)) m.set(t, new Set()); m.get(t).add(f); };
const off = (m) => (t, f) => m.get(t)?.delete(f);
const count = () => [...listeners.window.values(), ...listeners.document.values()].reduce((n, s) => n + s.size, 0);
const fire = (m, t) => [...(m.get(t) || [])].forEach((f) => f());
let reducedMotion = false;
const available = new Set();
globalThis.window = { addEventListener: on(listeners.window), removeEventListener: off(listeners.window),
  matchMedia: () => ({ matches: reducedMotion }) };
globalThis.document = { hidden: false, addEventListener: on(listeners.document), removeEventListener: off(listeners.document) };
globalThis.Image = class { set src(v) { setTimeout(() => (available.has(v) ? this.onload?.() : this.onerror?.()), 0); } };
const settle = () => new Promise((r) => setTimeout(r, 5));
function fakeImg() {
  return { tagName: 'IMG', src: '', alt: '', dataset: {}, animated: 0, closest: () => null,
    removeAttribute() {}, animate() { this.animated++; } };
}

const { getTimes } = await import('../web/js/vendor/suncalc.js');
const { createBridgeClock } = await import('../web/js/bridge-clock.mjs');
const { mountBridgeImage } = await import('../web/js/bridge-images.mjs');
const { trackDaypart, startBridgeScene } = await import('../web/js/bridge-scene.mjs');

const ny = (d) => d.toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour: 'numeric', minute: '2-digit', hourCycle: 'h23' });
const minutes = (d) => { const [h, m] = ny(d).split(':').map(Number); return h * 60 + m; };
const near = (d, hhmm, tol = 3) => { const [h, m] = hhmm.split(':').map(Number); return Math.abs(minutes(d) - (h * 60 + m)) <= tol; };

test('SunCalc gives the published New York sunrise and sunset on the solstices', () => {
  const clock = createBridgeClock(getTimes);
  const june = clock(new Date('2026-06-21T16:00:00Z'));
  assert.ok(near(june.sunrise, '5:25'), ny(june.sunrise));
  assert.ok(near(june.sunset, '20:31'), ny(june.sunset));
  const dec = clock(new Date('2026-12-21T17:00:00Z'));
  assert.ok(near(dec.sunrise, '7:17'), ny(dec.sunrise));
  assert.ok(near(dec.sunset, '16:32'), ny(dec.sunset));
});

test('SunCalc follows both daylight saving changes on the wall clock', () => {
  const clock = createBridgeClock(getTimes);
  const rise = (iso) => minutes(clock(new Date(iso)).sunrise);
  // Clocks spring forward on March 8: sunrise jumps about an hour later.
  assert.ok(Math.abs(rise('2026-03-08T17:00:00Z') - rise('2026-03-07T17:00:00Z') - 58) <= 3);
  // Clocks fall back on November 1: sunrise jumps about an hour earlier.
  assert.ok(Math.abs(rise('2026-10-31T17:00:00Z') - rise('2026-11-01T17:00:00Z') - 59) <= 3);
});

test('a visitor in another time zone sees the New York phase', () => {
  const clock = createBridgeClock(getTimes);
  // 10:00 in Tokyo on Nov 7 is 20:00 on Nov 6 in New York: night.
  assert.equal(clock(new Date('2026-11-07T10:00:00+09:00')).phase, 'night');
  // 23:00 in London on Nov 6 is 18:00 in New York, after sunset: night.
  assert.equal(clock(new Date('2026-11-06T23:00:00Z')).phase, 'night');
  // 15:00 UTC is 10:00 in New York: morning.
  assert.equal(clock(new Date('2026-11-06T15:00:00Z')).phase, 'morning');
});

const assets = {
  morning: { src: 'm.webp', alt: 'morning' }, afternoon: { src: 'a.webp', alt: 'afternoon' }, night: { src: 'n.webp', alt: 'night' },
};

test('a missing photo keeps the last good one, and nothing loads over the fallback until one works', async () => {
  available.clear(); available.add('a.webp');
  let phase = 'night';
  const img = fakeImg();
  const errors = [];
  const h = mountBridgeImage(img, { clock: () => ({ phase }), assets, intervalMs: 1e6, onError: (e) => errors.push(e) });
  await settle();
  assert.equal(img.src, '', 'no photo yet, so the drawn bridge stays');
  phase = 'afternoon'; await h.refresh();
  assert.equal(img.src, 'a.webp'); assert.equal(img.dataset.bridgePhase, 'afternoon');
  phase = 'night'; await h.refresh();
  assert.equal(img.src, 'a.webp', 'night photo is missing, so the afternoon one stays');
  assert.ok(errors.length >= 2);
  available.add('n.webp'); await h.refresh();
  assert.equal(img.src, 'n.webp', 'retries and recovers once the file exists');
  h.destroy();
});

test('reduced motion skips the fade', async () => {
  available.clear(); available.add('a.webp');
  for (const rm of [false, true]) {
    reducedMotion = rm;
    const img = fakeImg();
    const h = mountBridgeImage(img, { clock: () => ({ phase: 'afternoon' }), assets, intervalMs: 1e6 });
    await settle();
    assert.equal(img.animated, rm ? 0 : 1);
    h.destroy();
  }
  reducedMotion = false;
});

test('returning to the tab updates the photo, and cleanup removes every listener', async () => {
  available.clear(); available.add('a.webp'); available.add('n.webp');
  const before = count();
  let phase = 'afternoon';
  const img = fakeImg();
  const h = mountBridgeImage(img, { clock: () => ({ phase }), assets, intervalMs: 1e6 });
  await settle();
  phase = 'night';
  document.hidden = true; fire(listeners.document, 'visibilitychange'); await settle();
  assert.equal(img.src, 'a.webp', 'no work while the tab is hidden');
  document.hidden = false; fire(listeners.document, 'visibilitychange'); await settle();
  assert.equal(img.src, 'n.webp');
  h.destroy();
  assert.equal(count(), before);
  phase = 'afternoon'; await h.refresh();
  assert.equal(img.src, 'n.webp', 'nothing changes after cleanup');
});

test('the fallback tint follows the clock and keeps its last value if sunlight data fails', () => {
  const root = { dataset: {} };
  let state = { phase: 'morning' };
  const t = trackDaypart(root, { readClock: () => { if (!state) throw new RangeError('no sun'); return state; }, intervalMs: 1e6 });
  assert.equal(root.dataset.daypart, 'morning');
  state = { phase: 'night' }; fire(listeners.window, 'focus');
  assert.equal(root.dataset.daypart, 'night');
  state = null; t.update();
  assert.equal(root.dataset.daypart, 'night');
  t.destroy();
});

test('startBridgeScene cleans up both the tint and the photo', async () => {
  globalThis.document.documentElement = { dataset: {} };
  available.clear();
  const before = count();
  const s = startBridgeScene(fakeImg(), assets, { intervalMs: 1e6 });
  assert.ok(count() > before);
  await settle();
  s.destroy();
  assert.equal(count(), before);
});
