import test from 'node:test';
import assert from 'node:assert/strict';
import { easternParts, easternOffsetMinutes, phaseAt, createBridgeClock } from '../web/js/bridge-clock.mjs';
const winter = { sunrise: new Date('2026-11-06T06:30:00-05:00'), sunset: new Date('2026-11-06T16:45:00-05:00') };
// Explicit fixtures validate boundary logic, not the astronomical library's accuracy.
test('sunrise, noon and sunset use explicit inclusive/exclusive boundaries', () => {
  for (const [instant, expected] of [
    ['2026-11-06T06:29:59-05:00','night'], ['2026-11-06T06:30:00-05:00','morning'],
    ['2026-11-06T11:59:59-05:00','morning'], ['2026-11-06T12:00:00-05:00','afternoon'],
    ['2026-11-06T16:44:59-05:00','afternoon'], ['2026-11-06T16:45:00-05:00','night'],
  ]) assert.equal(phaseAt(new Date(instant), winter), expected);
});
test('equivalent instants give the same phase for international visitors', () => {
  assert.equal(phaseAt(new Date('2026-11-06T17:00:00Z'),winter),'afternoon');
  assert.equal(phaseAt(new Date('2026-11-07T02:00:00+09:00'),winter),'afternoon');
});
test('UTC midnight still belongs to the preceding New York date', () => {
  const p = easternParts(new Date('2026-11-07T01:00:00Z'));
  assert.equal(p.day,6); assert.equal(p.hour,20);
});
test('Eastern midnight is hour zero, not hour 24', () => {
  assert.equal(easternParts(new Date('2026-11-06T05:00:00Z')).hour,0);
});
test('offset changes at both daylight saving transitions', () => {
  assert.equal(easternOffsetMinutes(new Date('2026-03-08T06:59:59Z')),-300);
  assert.equal(easternOffsetMinutes(new Date('2026-03-08T07:00:00Z')),-240);
  assert.equal(easternOffsetMinutes(new Date('2026-11-01T05:59:59Z')),-240);
  assert.equal(easternOffsetMinutes(new Date('2026-11-01T06:00:00Z')),-300);
});
test('different seasonal sunset fixtures change the evening phase', () => {
  const summer = { sunrise:new Date('2026-07-06T05:30:00-04:00'), sunset:new Date('2026-07-06T20:30:00-04:00') };
  assert.equal(phaseAt(new Date('2026-07-06T18:00:00-04:00'),summer),'afternoon');
  assert.equal(phaseAt(new Date('2026-11-06T18:00:00-05:00'),winter),'night');
});
test('sun calculator uses the Eastern day, caches it and advances at Eastern midnight', () => {
  const calls=[];
  const clock=createBridgeClock((anchor,lat,lon,height,offset) => {
    calls.push({anchor,offset});
    const day=anchor.toISOString().slice(0,10);
    return {sunrise:new Date(`${day}T11:30:00Z`),sunset:new Date(`${day}T21:45:00Z`)};
  });
  assert.equal(clock(new Date('2026-11-07T01:00:00Z')).easternDate,'2026-11-6');
  clock(new Date('2026-11-07T04:59:59Z'));
  assert.equal(calls.length,1);
  clock(new Date('2026-11-07T05:00:00Z'));
  assert.equal(calls.length,2);
  assert.equal(calls[0].anchor.toISOString(),'2026-11-06T17:00:00.000Z');
  assert.equal(calls[1].anchor.toISOString(),'2026-11-07T17:00:00.000Z');
  assert.equal(calls[0].offset,-300);
});
test('DST-transition date is calculated with its midday offset', () => {
  let offset;
  const clock=createBridgeClock((date,lat,lon,height,value) => {
    offset=value;
    return {sunrise:new Date('2026-03-08T11:20:00Z'),sunset:new Date('2026-03-08T22:55:00Z')};
  });
  clock(new Date('2026-03-08T05:30:00Z'));
  assert.equal(offset,-240);
});
test('bad or missing sunlight data fails explicitly', () => {
  assert.throws(()=>phaseAt(new Date(),{sunrise:null,sunset:null}));
  assert.throws(()=>phaseAt(new Date(),{sunrise:winter.sunset,sunset:winter.sunrise}));
  assert.throws(()=>easternParts(new Date('invalid')));
  assert.throws(()=>createBridgeClock(null));
});
