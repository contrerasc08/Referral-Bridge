/*
 * Bridge images: shows the morning, afternoon or night image for a scene and
 * keeps it current. Checks on arrival, when the tab becomes visible again,
 * at each sunrise, noon and sunset, and once a minute as a safety net.
 *
 * Markup: <img data-bridge-scene="home" ...> with sources registered below.
 * A new image is preloaded first; if it fails, the last good image stays.
 */
(function (root) {
  'use strict';

  function BridgeImages(clock, scenes, opts) {
    this.clock = clock;
    this.scenes = scenes;
    this.opts = opts || {};
    this.current = {};   // element -> src currently shown
    this.timer = null;
  }

  BridgeImages.prototype.apply = function (now) {
    var self = this, info = this.clock.phaseAt(now);
    var doc = this.opts.document || root.document;
    if (doc && doc.documentElement) doc.documentElement.setAttribute('data-daypart', info.phase);
    var els = doc ? doc.querySelectorAll('[data-bridge-scene]') : [];
    Array.prototype.forEach.call(els, function (el) {
      var scene = self.scenes[el.getAttribute('data-bridge-scene')];
      if (!scene || !scene[info.phase]) return;
      var want = scene[info.phase];
      if (el.getAttribute('data-bridge-src') === want.src) return;
      self.load(el, want);
    });
    this.schedule(info);
    return info;
  };

  BridgeImages.prototype.load = function (el, want) {
    var Img = this.opts.Image || root.Image;
    var probe = new Img();
    probe.onload = function () {
      el.src = want.src;
      if (want.alt) el.alt = want.alt;
      el.setAttribute('data-bridge-src', want.src);
      el.classList && el.classList.add('is-loaded');
    };
    probe.onerror = function () {
      // Keep whatever was showing. Mark it so the fallback art can show
      // when no image has ever loaded.
      if (!el.getAttribute('data-bridge-src')) el.classList && el.classList.add('is-missing');
    };
    probe.src = want.src;
  };

  BridgeImages.prototype.schedule = function (info) {
    var self = this;
    clearTimeout(this.timer);
    var wait = Math.max(1000, Math.min(info.nextChange - Date.now() + 1000, 60000));
    this.timer = setTimeout(function () { self.apply(); }, wait);
  };

  BridgeImages.prototype.start = function () {
    var self = this, doc = this.opts.document || root.document;
    this.apply();
    if (doc) doc.addEventListener('visibilitychange', function () {
      if (doc.visibilityState === 'visible') self.apply();
    });
    return this;
  };

  if (typeof module === 'object' && module.exports) module.exports = BridgeImages;
  root.BridgeImages = BridgeImages;
})(typeof globalThis !== 'undefined' ? globalThis : this);
