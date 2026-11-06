// Shared Eastern-time clock. Supply SunCalc.getTimes (see integration example).
export const TIME_ZONE = 'America/New_York';
const formatter = new Intl.DateTimeFormat('en-US', {
  timeZone: TIME_ZONE, calendar: 'gregory', numberingSystem: 'latn',
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
});

export function easternParts(date = new Date()) {
  if (!(date instanceof Date) || !Number.isFinite(date.getTime())) {
    throw new TypeError('A valid Date is required.');
  }
  return Object.fromEntries(formatter.formatToParts(date)
    .filter(({ type }) => type !== 'literal')
    .map(({ type, value }) => [type, Number(value)]));
}

export function easternOffsetMinutes(date) {
  const p = easternParts(date);
  const wallClock = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  return (wallClock - Math.floor(date.getTime() / 1000) * 1000) / 60000;
}

export function phaseAt(date, { sunrise, sunset }) {
  const p = easternParts(date);
  if (!(sunrise instanceof Date) || !(sunset instanceof Date)
    || !Number.isFinite(+sunrise) || !Number.isFinite(+sunset) || sunrise >= sunset) {
    throw new RangeError('Valid sunrise and sunset times are required.');
  }
  if (date < sunrise || date >= sunset) return 'night';
  return p.hour < 12 ? 'morning' : 'afternoon';
}

export function createBridgeClock(getTimes, {
  latitude = 40.8517, longitude = -73.9527,
} = {}) {
  if (typeof getTimes !== 'function') throw new TypeError('Supply a sunlight calculator.');
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)
    || Math.abs(latitude) > 90 || Math.abs(longitude) > 180) {
    throw new RangeError('Invalid bridge coordinates.');
  }
  let cache;
  return function readClock(date = new Date()) {
    const p = easternParts(date);
    const key = `${p.year}-${p.month}-${p.day}`;
    if (!cache || cache.key !== key) {
      // 17:00 UTC is midday in New York in both summer and winter. This
      // selects the correct Eastern calendar day, even for a visitor abroad.
      const anchor = new Date(Date.UTC(p.year, p.month - 1, p.day, 17));
      const times = getTimes(anchor, latitude, longitude, 0, easternOffsetMinutes(anchor));
      phaseAt(date, times); // Reject missing/invalid events instead of inventing a fixed sunset.
      cache = { key, sunrise: times.sunrise, sunset: times.sunset };
    }
    return { phase: phaseAt(date, cache), sunrise: cache.sunrise,
      sunset: cache.sunset, easternDate: key, timeZone: TIME_ZONE };
  };
}
