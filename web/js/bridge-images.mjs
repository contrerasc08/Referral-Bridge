// Apply to an existing <img>. The initial src remains visible if a new image fails.
function loadImage(src, timeoutMs = 12000) {
  return new Promise((resolve, reject) => {
    const candidate = new Image();
    const timer = setTimeout(() => finish(new Error('Bridge image load timed out.')), timeoutMs);
    function finish(error) {
      clearTimeout(timer);
      candidate.onload = null;
      candidate.onerror = null;
      if (error) reject(error); else resolve();
    }
    candidate.onload = () => finish();
    candidate.onerror = () => finish(new Error('Bridge image could not be loaded.'));
    candidate.src = src;
  });
}

export function mountBridgeImage(image, {
  clock, assets, now = () => new Date(), intervalMs = 30000,
  onError = () => {}, onPhaseChange = () => {},
}) {
  if (!image || image.tagName !== 'IMG') throw new TypeError('Supply an image element.');
  if (image.closest('picture')) throw new TypeError('Use a standalone img or adapt picture sources for every phase.');
  if (typeof clock !== 'function') throw new TypeError('Supply the shared bridge clock.');
  for (const phase of ['morning', 'afternoon', 'night']) {
    if (!assets?.[phase]?.src || typeof assets[phase].alt !== 'string') {
      throw new TypeError(`Supply src and alt for the ${phase} asset.`);
    }
  }
  let disposed = false, generation = 0, pendingKey = '', appliedKey = '';
  const report = (error) => { try { onError(error); } catch { /* Host error reporting must not affect login. */ } };
  async function refresh() {
    if (disposed) return;
    let state;
    try { state = clock(now()); } catch (error) { report(error); return; }
    const asset = assets[state.phase];
    const key = `${state.phase}:${asset.src}`;
    if (key === appliedKey) {
      if (pendingKey && pendingKey !== key) { generation++; pendingKey = ''; }
      return;
    }
    if (key === pendingKey) return;
    const ticket = ++generation;
    pendingKey = key;
    try {
      await loadImage(asset.src);
      if (disposed || ticket !== generation) return;
      // A stale responsive source must not override the new phase's src.
      image.removeAttribute('srcset');
      image.removeAttribute('sizes');
      image.src = asset.src;
      image.alt = asset.alt;
      image.dataset.bridgePhase = state.phase;
      appliedKey = key;
      pendingKey = '';
      if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches && image.animate) {
        image.animate([{ opacity: .8 }, { opacity: 1 }], { duration: 450 });
      }
      try { onPhaseChange(state); } catch (error) { report(error); }
    } catch (error) {
      if (disposed || ticket !== generation) return;
      pendingKey = '';
      report(error); // Keep the last successful image; retry on the next refresh.
    }
  }
  const resume = () => { if (!document.hidden) void refresh(); };
  document.addEventListener('visibilitychange', resume);
  window.addEventListener('focus', resume);
  window.addEventListener('pageshow', resume);
  const timer = setInterval(resume, Math.max(1000, intervalMs));
  void refresh();
  return {
    refresh,
    destroy() {
      disposed = true; generation++;
      clearInterval(timer);
      document.removeEventListener('visibilitychange', resume);
      window.removeEventListener('focus', resume);
      window.removeEventListener('pageshow', resume);
    },
  };
}
