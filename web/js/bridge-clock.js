/*
 * Bridge clock: decides whether it is morning, afternoon or night at the
 * George Washington Bridge, in New York time, for every visitor.
 *
 *   Morning:   sunrise until 12:00 noon
 *   Afternoon: 12:00 noon until sunset
 *   Night:     sunset until the next sunrise
 *
 * Sunrise and sunset follow the NOAA solar equations for the bridge's
 * location, so they shift with the seasons. All wall-clock math goes through
 * Intl with America/New_York, which also handles daylight saving time.
 */
(function (root) {
  'use strict';

  var GWB = { lat: 40.8517, lon: -73.9527 };
  var ZONE = 'America/New_York';
  var RAD = Math.PI / 180;
  var DAY_MS = 86400000;
  var J1970 = 2440588, J2000 = 2451545;
  var SUN_ALTITUDE = -0.833; // upper limb on the horizon, with refraction

  function toJulian(ms) { return ms / DAY_MS - 0.5 + J1970; }
  function fromJulian(j) { return (j + 0.5 - J1970) * DAY_MS; }

  // Sunrise and sunset (UTC milliseconds) for the solar day nearest `ms`.
  function sunTimes(ms, lat, lon) {
    lat = lat == null ? GWB.lat : lat;
    lon = lon == null ? GWB.lon : lon;
    var lw = -lon * RAD, phi = lat * RAD;
    var d = toJulian(ms) - J2000;
    var n = Math.round(d - 0.0009 - lw / (2 * Math.PI));
    var ds = 0.0009 + lw / (2 * Math.PI) + n;
    var M = RAD * (357.5291 + 0.98560028 * ds);
    var C = RAD * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
    var L = M + C + RAD * 102.9372 + Math.PI;
    var dec = Math.asin(Math.sin(L) * Math.sin(RAD * 23.4397));
    var Jnoon = J2000 + ds + 0.0053 * Math.sin(M) - 0.0069 * Math.sin(2 * L);
    var cosW = (Math.sin(SUN_ALTITUDE * RAD) - Math.sin(phi) * Math.sin(dec)) / (Math.cos(phi) * Math.cos(dec));
    var w = Math.acos(Math.max(-1, Math.min(1, cosW)));
    var Jset = J2000 + 0.0009 + (w + lw) / (2 * Math.PI) + n + 0.0053 * Math.sin(M) - 0.0069 * Math.sin(2 * L);
    var Jrise = Jnoon - (Jset - Jnoon);
    return { sunrise: fromJulian(Jrise), sunset: fromJulian(Jset) };
  }

  var partsFmt = null;
  function nyParts(ms) {
    if (!partsFmt) {
      partsFmt = new Intl.DateTimeFormat('en-US', {
        timeZone: ZONE, hourCycle: 'h23',
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    }
    var out = {};
    partsFmt.formatToParts(new Date(ms)).forEach(function (p) { out[p.type] = p.value; });
    return {
      y: +out.year, m: +out.month, d: +out.day,
      h: +out.hour % 24, min: +out.minute, s: +out.second
    };
  }

  // UTC milliseconds of a New York wall-clock time on a given date.
  function nyWallTime(y, m, d, h, min) {
    var guess = Date.UTC(y, m - 1, d, h, min || 0);
    for (var i = 0; i < 3; i++) {
      var p = nyParts(guess);
      var seen = Date.UTC(p.y, p.m - 1, p.d, p.h, p.min);
      var want = Date.UTC(y, m - 1, d, h, min || 0);
      if (seen === want) break;
      guess += want - seen;
    }
    return guess;
  }

  // Everything the page needs to know about "now" at the bridge.
  function phaseAt(now) {
    now = now == null ? Date.now() : +now;
    var p = nyParts(now);
    var noonNY = nyWallTime(p.y, p.m, p.d, 12, 0);
    var today = sunTimes(noonNY);
    var phase, nextChange;
    if (now < today.sunrise) {
      phase = 'night'; nextChange = today.sunrise;
    } else if (now < noonNY) {
      phase = 'morning'; nextChange = noonNY;
    } else if (now < today.sunset) {
      phase = 'afternoon'; nextChange = today.sunset;
    } else {
      phase = 'night';
      nextChange = sunTimes(noonNY + DAY_MS).sunrise;
    }
    return {
      phase: phase,
      sunrise: today.sunrise,
      sunset: today.sunset,
      noon: noonNY,
      nextChange: nextChange
    };
  }

  var api = { phaseAt: phaseAt, sunTimes: sunTimes, nyParts: nyParts, nyWallTime: nyWallTime, GWB: GWB, ZONE: ZONE };
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.BridgeClock = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
