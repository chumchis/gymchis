// Self-check for the plan logic in index.html:  node check.mjs
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';

const html = readFileSync(new URL('index.html', import.meta.url), 'utf8');
const src = html.match(/<script id="logic">([\s\S]*?)<\/script>/)[1];
const L = new Function(`${src}; return { setCatalog, makePlan, allowed, alternatives, cleanDays, dayMinutes };`)();
const cat = JSON.parse(readFileSync(new URL('catalog.json', import.meta.url), 'utf8'));
L.setCatalog(cat);
const byId = Object.fromEntries(cat.map(x => [x.id, x]));

const profiles = [
  { goal: 'tonificar', zones: ['gluteos', 'abdomen'], level: 1, place: 'casa', equip: [], days: 3, minutes: 30, noJump: true },
  { goal: 'grasa', zones: ['gluteos', 'piernas', 'brazos'], level: 2, place: 'casa', equip: ['dumbbell', 'band'], days: 4, minutes: 45, noJump: false },
  { goal: 'musculo', zones: Object.keys({ gluteos: 1, piernas: 1, abdomen: 1, brazos: 1, espalda: 1, pecho: 1, hombros: 1 }), level: 3, place: 'gym', equip: [], days: 6, minutes: 60, noJump: false },
  { goal: 'salud', zones: ['espalda'], level: 1, place: 'casa', equip: [], days: 2, minutes: 20, noJump: true },
];
for (const p of profiles) {
  for (const seed of [1, 2, 3]) {
    const plan = L.makePlan(p, seed);
    assert.equal(plan.days.length, p.days);
    for (const day of plan.days) {
      const ids = day.items.map(i => i.id);
      assert.equal(new Set(ids).size, ids.length, 'no repeats inside a day');
      for (const it of day.items) {
        const x = byId[it.id];
        assert.ok(L.allowed(x, p), `${x.id} not doable for ${p.place}/${p.level}`);
        assert.ok(x.core, `${x.id} is not from the curated set`);
        if (p.noJump) assert.ok(!x.j, `${x.id} jumps`);
        assert.ok(it.secs > 0 || /\d/.test(it.reps), 'every item has reps or seconds');
      }
      const kinds = day.items.map(i => i.k).join(' ');
      assert.match(kinds, /^(warm )+(main )+(cool ?)+$/, `order warm→main→cool: ${kinds}`);
      const mins = L.dayMinutes(day);
      assert.ok(Math.abs(mins - p.minutes) <= Math.max(4, p.minutes * 0.15), `${mins} min planned for ${p.minutes}`);
      const alts = L.alternatives(day.items.find(i => i.k === 'main'), p, day);
      assert.ok(alts.every(x => L.allowed(x, p) && !ids.includes(x.id)), 'swap offers only doable, unused exercises');
    }
  }
  assert.deepEqual(L.makePlan(p, 7).days, L.makePlan(p, 7).days, 'same seed, same plan');
  const cools = L.makePlan(p, 7).days.flatMap(d => d.items.filter(i => i.k === 'cool').map(i => i.id));
  assert.ok(new Set(cools).size > 2 || p.days < 2, `stretches vary across the week: ${cools}`);
}

// Claude output is untrusted: unknown ids dropped, numbers clamped, timed kinds get seconds.
const days = L.cleanDays({ days: [{ title: 'X', items: [
  { id: 'nope' }, { id: 'push-up', sets: 99, reps: '10', rest: -5 }, { id: 'weighted-front-plank', reps: '12' },
] }, { items: [{ id: 'bad' }] }] });
assert.equal(days.length, 1);
assert.deepEqual(days[0].items.map(i => i.id), ['push-up', 'weighted-front-plank']);
assert.equal(days[0].items[0].sets, 6);
assert.equal(days[0].items[0].rest, 0);
assert.ok(days[0].items[1].secs && !days[0].items[1].reps);
assert.equal(L.cleanDays({ days: 'x' }), null);
console.log('ok');
