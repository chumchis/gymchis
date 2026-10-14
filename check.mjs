// Self-check for the plan logic in index.html:  node check.mjs
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';

const html = readFileSync(new URL('index.html', import.meta.url), 'utf8');
const src = html.match(/<script id="logic">([\s\S]*?)<\/script>/)[1];
const L = new Function(`${src}; return { setCatalog, makePlan, allowed, alternatives, cleanDays, dayMinutes, parseBackup, mergeHistory };`)();
const cat = JSON.parse(readFileSync(new URL('catalog.json', import.meta.url), 'utf8'));
L.setCatalog(cat);
const byId = Object.fromEntries(cat.map(x => [x.id, x]));

const profiles = [
  { goal: 'tonificar', zones: ['gluteos', 'abdomen'], level: 1, place: 'casa', equip: [], days: 3, minutes: 30, noJump: true },
  { goal: 'grasa', zones: ['gluteos', 'piernas', 'brazos'], level: 2, place: 'casa', equip: ['dumbbell', 'band'], days: 4, minutes: 45, noJump: false },
  { goal: 'musculo', zones: Object.keys({ gluteos: 1, piernas: 1, abdomen: 1, brazos: 1, espalda: 1, pecho: 1, hombros: 1 }), level: 3, place: 'gym', equip: [], days: 6, minutes: 60, noJump: false },
  { goal: 'salud', zones: ['espalda'], level: 1, place: 'casa', equip: [], days: 2, minutes: 20, noJump: true },
  { goal: 'tonificar', zones: ['gluteos', 'piernas', 'abdomen', 'brazos'], level: 1, place: 'casa', equip: ['dumbbell', 'rope'], days: 4, minutes: 30, noJump: false },
  { goal: 'musculo', zones: ['pecho', 'espalda', 'piernas'], level: 4, place: 'gym', equip: [], days: 5, minutes: 60, noJump: false },
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
        assert.ok(!x.x, `${x.id} needs a partner`);
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
  const mains = [1, 2, 3].flatMap(seed => L.makePlan(p, seed).days.flatMap(d => d.items.filter(i => i.k === 'main'))).map(i => byId[i.id]);
  if (p.level >= 3) { // the generator leans to her own level and the one below
    const share = mains.filter(x => x.l >= p.level - 1).length / mains.length;
    assert.ok(share > 0.6, `level ${p.level}: only ${Math.round(share * 100)}% at level ${p.level - 1}+`);
  }
  const gear = p.place === 'casa' ? p.equip.filter(e => e !== 'rope') : [];
  for (const e of gear) { // her gear gets a fair share next to ~450 bodyweight moves (unbalanced, bands would be ~12%)
    const share = mains.filter(x => x.e === e).length / mains.length, fair = 1 / (gear.length + 1);
    assert.ok(share > fair / 2, `${e}: only ${Math.round(share * 100)}% of exercises`);
  }
  if (p.equip.includes('rope') && !p.noJump) {
    const all = L.makePlan(p, 7).days.flatMap(d => d.items.map(i => i.id));
    assert.ok(all.includes('jump-rope'), 'the jump rope gets used');
  }
  assert.ok(mains.some(x => !x.core), 'plans draw from the whole catalog, not only the curated set');
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

// Backups round-trip; a foreign or broken file is refused; junk inside is dropped or clamped.
const prof = profiles[4], plan = L.makePlan(prof, 5);
const hist = [{ at: 1000, dur: 1800, seed: 5, day: 0, title: 'Glúteos', ex: [{ id: 'push-up', s: [{ r: 12, kg: 2.5 }, { r: 10 }] }, { id: 'jump-rope', s: [{ secs: 40 }] }] }];
const back = L.parseBackup(JSON.stringify({ app: 'gymchis', version: 1, profile: { name: 'Ana', ...prof }, plan, history: hist }));
assert.deepEqual(back.history, hist);
assert.deepEqual(back.profile, { name: 'Ana', ...prof });
assert.deepEqual(back.plan.days, plan.days);
assert.equal(back.plan.seed, 5);
assert.equal(L.parseBackup('nope'), null);
assert.equal(L.parseBackup(JSON.stringify({ history: hist })), null);
const junk = L.parseBackup(JSON.stringify({ app: 'gymchis', profile: { ...prof, level: 9 }, plan: { days: 'x' }, history: [
  null, { at: 'x', ex: [] }, { at: 2000, dur: 1e9, title: '<b>'.repeat(40), ex: [{ id: 7, s: [] }, { id: 'push-up', s: [{ r: -3, kg: 'a' }, { secs: 1e6 }] }] },
] }));
assert.equal(junk.profile, null);
assert.equal(junk.plan, null);
assert.equal(junk.history.length, 1);
assert.equal(junk.history[0].dur, 6 * 3600);
assert.equal(junk.history[0].title.length, 60);
assert.deepEqual(junk.history[0].ex, [{ id: 'push-up', s: [{ r: 0 }, { secs: 3600 }] }]);
const merged = L.mergeHistory([{ at: 3, title: 'mine' }, { at: 1 }], [{ at: 3, title: 'theirs' }, { at: 2 }]);
assert.deepEqual(merged.map(h => h.at), [1, 2, 3]);
assert.equal(merged[2].title, 'mine');
console.log('ok');
