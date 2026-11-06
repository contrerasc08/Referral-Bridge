// Wires the shared bridge clock (SunCalc + New York time) to a bridge photo.
// The same file is used by the EcoBridge site and the Referral Bridge sign-in page.
import { getTimes } from './vendor/suncalc.js';
import { createBridgeClock } from './bridge-clock.mjs';
import { mountBridgeImage } from './bridge-images.mjs';

export const clock = createBridgeClock(getTimes);

// Sets data-daypart on <html> so the drawn fallback bridge is tinted for the
// time of day, even before (or without) a photo. If the sunlight calculation
// fails, the last tint stays rather than guessing a sunset.
export function trackDaypart(root = document.documentElement, {
  readClock = clock, now = () => new Date(), intervalMs = 30000,
} = {}) {
  const update = () => {
    if (document.hidden) return;
    try { root.dataset.daypart = readClock(now()).phase; } catch { /* keep the last tint */ }
  };
  document.addEventListener('visibilitychange', update);
  window.addEventListener('focus', update);
  window.addEventListener('pageshow', update);
  const timer = setInterval(update, Math.max(1000, intervalMs));
  update();
  return {
    update,
    destroy() {
      clearInterval(timer);
      document.removeEventListener('visibilitychange', update);
      window.removeEventListener('focus', update);
      window.removeEventListener('pageshow', update);
    },
  };
}

// Starts both the tint and the photo for one <img>. Call destroy() to stop.
export function startBridgeScene(image, assets, options = {}) {
  const tint = trackDaypart(document.documentElement, options);
  const photo = mountBridgeImage(image, { clock, ...options, assets });
  return { refresh: photo.refresh, destroy() { tint.destroy(); photo.destroy(); } };
}
