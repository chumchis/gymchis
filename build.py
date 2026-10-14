"""Build catalog.json + img/*.webp for Gymchis from ExerciseGymGifsDB.

catalog.json holds all 1323 exercises. The curated ones (core) feed the plan
generator and carry hand-set names and flags; the rest get flags inferred from
slug and category. On GitHub Pages images load from the jsDelivr CDN. The
Artifact host blocks external images, so only the curated set ships there,
as small animated WebP in img/.

    python3 build.py            # needs gif2webp (brew install webp)

Line format:  slug | display name | flags
flags: 1/2/3/4 level (default 1: principiante, habitual, experto, coach) · t timed hold · j jump/impact · w warm-up
       s cool-down stretch · g needs gym gear (bar, bench, fitball…)
       @equip  overrides the DB equipment
"""
import json, subprocess, sys, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://cdn.jsdelivr.net/gh/JahelCuadrado/ExerciseGymGifsDB@v1.2.0"
HERE = Path(__file__).parent
CACHE = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / ".cache"

CURATED = """
# Glúteos
low-glute-bridge-on-floor | Puente de glúteos |
glute-bridge-march | Puente de glúteos con marcha | 2
single-leg-bridge-with-outstretched-leg | Puente de glúteos a una pierna | 2
glute-bridge-two-legs-on-bench-male | Hip thrust en banco o sofá |
barbell-glute-bridge | Puente de glúteos con barra | 2
barbell-glute-bridge-two-legs-on-bench-male | Hip thrust con barra | 2
resistance-band-hip-thrusts-on-knees-female | Hip thrust de rodillas con banda |
band-hip-lift | Puente de glúteos con banda |
band-pull-through | Pull-through con banda |
band-stiff-leg-deadlift | Peso muerto rumano con banda |
band-step-up | Subida al escalón con banda |
band-bent-over-hip-extension | Patada de glúteo con banda |
band-squat | Sentadilla con banda |
monster-walk | Caminata lateral (monster walk) |
swimmer-kicks-v-2-male | Patadas de nadador |
curtsey-squat | Sentadilla cruzada |
weighted-squat | Sentadilla con disco entre bancos | 2 g
forward-lunge-male | Zancada al frente |
walking-lunge | Zancadas caminando | 2
dumbbell-lunge | Zancada con mancuernas |
dumbbell-rear-lunge | Zancada atrás con mancuernas |
dumbbell-step-up | Subida al escalón con mancuernas |
dumbbell-squat | Sentadilla con mancuernas |
dumbbell-romanian-deadlift | Peso muerto rumano con mancuernas |
dumbbell-single-leg-deadlift | Peso muerto a una pierna | 2
kettlebell-swing | Swing con kettlebell | 2
kettlebell-goblet-squat | Sentadilla goblet con kettlebell |
barbell-full-squat | Sentadilla con barra | 2
barbell-front-squat | Sentadilla frontal con barra | 3
barbell-romanian-deadlift | Peso muerto rumano con barra | 2
barbell-sumo-deadlift | Peso muerto sumo con barra | 2
barbell-deadlift | Peso muerto con barra | 3
barbell-lunge | Zancada con barra | 2
barbell-step-up | Subida al banco con barra | 2
smith-squat | Sentadilla en máquina Smith |
smith-sumo-squat | Sentadilla sumo en Smith |
sled-45-leg-press | Prensa de piernas |
sled-hack-squat | Sentadilla hack | 2
cable-pull-through-with-rope | Pull-through en polea |
cable-standing-hip-extension | Patada de glúteo en polea |
lever-hip-extension-v-2 | Patada de glúteo en máquina |
jump-squat | Sentadilla con salto | 2 j
lunge-with-jump | Zancada con salto | 3 j
march-sit-wall | Sentadilla en pared con marcha | 2 t

# Abductores / aductores
side-hip-abduction | Elevación lateral de pierna en el suelo |
straight-leg-outer-hip-abductor | Abducción de cadera de pie |
resistance-band-seated-hip-abduction | Abducción de cadera con banda |
lever-seated-hip-abduction | Abductores en máquina |
side-bridge-hip-abduction | Plancha lateral con elevación de pierna | 3
side-lying-hip-adduction-male | Aducción de cadera en el suelo |
lever-seated-hip-adduction | Aductores en máquina |
cable-hip-adduction | Aducción de cadera en polea |

# Piernas
quads | Sentadilla búlgara | 2
dumbbell-single-leg-split-squat | Sentadilla búlgara con mancuernas | 2
split-squats | Zancada estática |
band-single-leg-split-squat | Zancada estática con banda |
dumbbell-goblet-squat | Sentadilla goblet con mancuerna |
sissy-squat | Sentadilla sissy | 3
lever-leg-extension | Extensión de cuádriceps en máquina |
resistance-band-leg-extension | Extensión de cuádriceps con banda |
lever-lying-leg-curl | Curl femoral acostado en máquina |
lever-seated-leg-curl | Curl femoral sentado en máquina |
dumbbell-lying-femoral | Curl femoral con mancuerna | 2
dumbbell-stiff-leg-deadlift | Peso muerto piernas rígidas con mancuernas |
barbell-straight-leg-deadlift | Peso muerto piernas rígidas con barra | 2
barbell-good-morning | Buenos días con barra | 2
self-assisted-inverse-leg-curl-on-floor | Curl nórdico asistido | 3
bodyweight-standing-calf-raise | Elevación de talones |
dumbbell-standing-calf-raise | Elevación de talones con mancuernas |
dumbbell-single-leg-calf-raise | Elevación de talones a una pierna | 2
band-single-leg-calf-raise | Elevación de talones con banda |
lever-standing-calf-raise | Gemelos de pie en máquina |
lever-seated-calf-raise | Gemelos sentado en máquina |
sled-calf-press-on-leg-press | Gemelos en prensa |

# Abdomen
crunch-floor | Crunch abdominal |
reverse-crunch | Crunch inverso |
dead-bug | Dead bug |
air-bike | Bicicleta abdominal |
alternate-heel-touchers | Toques de talón alternos |
cross-body-crunch | Crunch cruzado |
oblique-crunches-floor | Crunch oblicuo |
elbow-to-knee | Codo a rodilla |
russian-twist | Giro ruso |
weighted-russian-twist | Giro ruso con peso | 2
seated-leg-raise | Elevación de piernas sentado |
weighted-front-plank | Plancha frontal | t
kneeling-plank-tap-shoulder-male | Plancha de rodillas con toque de hombro |
shoulder-tap | Plancha alta con toque de hombro | 2
front-plank-with-twist | Plancha con giro de cadera | 2
side-bridge-v-2 | Plancha lateral | t
bodyweight-incline-side-plank | Plancha lateral inclinada | t
power-point-plank | Plancha con brazo y pierna | 3
sit-up-v-2 | Abdominal completo | 2
jackknife-sit-up | Navaja (V-up) | 3
lying-leg-raise-flat-bench | Elevación de piernas en banco | 2 g
hanging-leg-raise | Elevación de piernas colgado | 3 g
wheel-rollerout | Rueda abdominal | 3 g
crunch-on-stability-ball | Crunch en fitball | g
band-horizontal-pallof-press | Press Pallof con banda |
dumbbell-side-bend | Inclinación lateral con mancuerna |
cable-kneeling-crunch | Crunch en polea de rodillas |
cable-twist | Giro de torso en polea |
lever-seated-crunch | Crunch en máquina |

# Cardio
jack-jump-male | Jumping jacks | j w
star-jump-male | Saltos de estrella | 2 j
scissor-jumps-male | Saltos de tijera | 2 j
burpee | Burpees | 2 j
jump-rope | Saltar la cuerda | j @rope
skater-hops | Saltos de patinador | 2 j
run | Trote en el sitio | j w
mountain-climber | Escaladores | 2
bear-crawl | Caminata de oso | 2
high-knee-against-wall | Rodillas altas en la pared | w
back-and-forth-step | Pasos adelante y atrás | w
walking-high-knees-lunge | Zancada caminando con rodilla alta | w
walking-on-incline-treadmill | Caminata en cinta inclinada | w
walk-elliptical-cross-trainer | Elíptica | w
stationary-bike-walk | Bicicleta estática | w @machine
walking-on-stepmill | Escaladora | w

# Espalda
band-close-grip-pulldown | Jalón con banda |
resistance-band-seated-straight-back-row | Remo sentado con banda |
band-one-arm-standing-low-row | Remo a una mano con banda |
bodyweight-standing-row-with-towel | Remo con toalla en una baranda |
dumbbell-bent-over-row | Remo inclinado con mancuernas |
dumbbell-one-arm-bent-over-row | Remo a una mano con mancuerna |
dumbbell-incline-row | Remo en banco inclinado |
kettlebell-one-arm-row | Remo a una mano con kettlebell |
lower-back-curl | Extensión lumbar en el suelo |
dumbbell-shrug | Encogimientos con mancuernas |
inverted-row-bent-knees | Remo invertido con rodillas flexionadas | 2 g
inverted-row | Remo invertido | 3 g
band-assisted-pull-up | Dominada asistida con banda | 2 g
assisted-pull-up | Dominada asistida | 2 g
pull-up | Dominada | 3 g
hyperextension | Hiperextensión lumbar | g
cable-pulldown | Jalón al pecho en polea |
lever-front-pulldown | Jalón al pecho en máquina |
cable-straight-arm-pulldown | Pullover en polea |
cable-seated-row | Remo sentado en polea |
lever-seated-row | Remo sentado en máquina |
barbell-bent-over-row | Remo inclinado con barra | 2

# Pecho
push-up-wall | Flexión en la pared |
incline-push-up | Flexión inclinada |
kneeling-push-up-male | Flexión de rodillas |
push-up | Flexión de brazos | 2
wide-hand-push-up | Flexión con manos abiertas | 2
decline-push-up | Flexión declinada | 3
band-bench-press | Press de pecho con banda |
dumbbell-bench-press | Press de pecho con mancuernas |
dumbbell-incline-bench-press | Press inclinado con mancuernas |
dumbbell-fly | Aperturas con mancuernas |
dumbbell-pullover | Pullover con mancuerna |
lever-chest-press | Press de pecho en máquina |
lever-seated-fly | Aperturas en máquina |
cable-standing-fly | Cruce de poleas |
barbell-bench-press | Press de banca con barra | 2
barbell-incline-bench-press | Press inclinado con barra | 2
chest-dip | Fondos en paralelas | 3 g

# Hombros
dumbbell-lateral-raise | Elevaciones laterales |
dumbbell-front-raise | Elevaciones frontales |
dumbbell-seated-shoulder-press | Press de hombros sentado |
dumbbell-standing-overhead-press | Press de hombros de pie |
dumbbell-arnold-press | Press Arnold | 2
dumbbell-rear-fly | Pájaros con mancuernas |
band-shoulder-press | Press de hombros con banda |
band-front-raise | Elevación frontal con banda |
band-reverse-fly | Aperturas posteriores con banda |
band-standing-rear-delt-row | Remo alto con banda |
cable-lateral-raise | Elevación lateral en polea |
lever-shoulder-press | Press de hombros en máquina |
lever-seated-reverse-fly | Aperturas posteriores en máquina |
barbell-seated-overhead-press | Press militar con barra | 2

# Brazos
dumbbell-biceps-curl | Curl de bíceps con mancuernas |
dumbbell-alternate-biceps-curl | Curl alterno con mancuernas |
dumbbell-hammer-curl | Curl martillo |
dumbbell-concentration-curl | Curl concentrado |
dumbbell-incline-curl | Curl en banco inclinado | 2
band-alternating-biceps-curl | Curl de bíceps con banda |
barbell-curl | Curl con barra |
ez-barbell-curl | Curl con barra Z |
cable-curl | Curl en polea |
cable-hammer-curl-with-rope | Curl martillo con cuerda |
lever-preacher-curl | Curl predicador en máquina |
bench-dip-knees-bent | Fondos de tríceps en silla |
triceps-dips-floor | Fondos de tríceps en el suelo |
dumbbell-kickback | Patada de tríceps |
dumbbell-standing-triceps-extension | Extensión de tríceps sobre la cabeza |
dumbbell-lying-triceps-extension | Rompecráneos con mancuernas | 2
band-side-triceps-extension | Extensión de tríceps con banda |
close-grip-push-up | Flexión con agarre cerrado | 2
diamond-push-up | Flexión diamante | 3
cable-pushdown | Jalón de tríceps en polea |
cable-pushdown-with-rope-attachment | Jalón de tríceps con cuerda |
barbell-close-grip-bench-press | Press de banca agarre cerrado | 2

# Movilidad para calentar
squat-to-overhead-reach | Sentadilla con brazos arriba | w
inchworm | Caminata de manos | w
world-greatest-stretch | Estiramiento completo de cadera | w

# Estiramientos para terminar
seated-glute-stretch | Estiramiento de glúteo sentado | s
seated-piriformis-stretch | Estiramiento de piriforme | s
hamstring-stretch | Estiramiento de femoral | s
runners-stretch | Estiramiento del corredor | s
lying-side-quads-stretch | Estiramiento de cuádriceps de lado | s
intermediate-hip-flexor-and-quad-stretch | Estiramiento de flexor de cadera | s
calf-stretch-with-hands-against-wall | Estiramiento de gemelo en la pared | s
butterfly-yoga-pose | Postura de mariposa | s
kneeling-lat-stretch | Estiramiento de dorsal de rodillas | s
behind-head-chest-stretch | Estiramiento de pecho | s
rear-deltoid-stretch | Estiramiento de hombro | s
overhead-triceps-stretch | Estiramiento de tríceps | s
upper-back-stretch | Estiramiento de espalda alta | s
spine-stretch | Estiramiento de columna | s
sphinx | Postura de la esfinge | s
upward-facing-dog | Postura de la cobra | s
neck-side-stretch | Estiramiento lateral de cuello | s
standing-lateral-stretch | Estiramiento lateral de pie | s
"""


def parse(text):
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        slug, name, flags = (p.strip() for p in line.split("|"))
        yield slug, name, flags.split()


# Levels: 1 principiante · 2 habitual · 3 experto · 4 coach.
# Rules match whole slug segments ("pull-up" matches "wide-grip-pull-up", not "pull-through").
COACH = ["planche", "maltese", "muscle-up", "handstand", "front-lever", "back-lever", "flag", "dragon",
         "one-arm-chin-up", "one-hand-pull-up", "single-arm-push-up", "archer", "clap", "impossible",
         "stalder", "snatch", "jerk", "power-clean", "clean-and-press", "kipping", "skin-the-cat",
         "l-pull-up", "gironda", "korean-dips", "ring-dips", "pistol", "weighted-pull-up",
         "weighted-one-hand", "weighted-straight-bar-dip", "weighted-tricep-dips", "weighted-muscle-up",
         "overhead-squat", "jefferson", "zercher", "guillotine", "turkish-get-up", "rope-climb", "l-sit",
         "v-sit", "drop-jump", "depth-jump", "straddle", "elevator", "superman-push-up", "front-lever-reps",
         "double-windmill", "advanced-windmill", "standing-wheel-rollerout", "standing-ab-rollerout",
         "bent-press", "lean-planche", "frog-planche", "full-planche", "one-arm-dip",
         "squat-jerk", "snatch-pull", "back-lever", "drop-push-up", "single-leg-squat-pistol", "kettlebell-pistol-squat"]
EXPERT = ["pull-up", "pull-ups", "chin-up", "chin-ups", "chin", "dip", "dips", "hanging", "captains-chair",
          "rollerout", "body-saw", "decline-push-up", "diamond-push-up", "pike", "inverse-leg-curl",
          "glute-ham-raise", "sissy-squat", "one-leg-squat", "single-leg-squat", "jackknife", "v-up",
          "box-jump", "tuck-jump", "swing", "windmill", "renegade", "thruster", "good-morning",
          "front-squat", "barbell-deadlift", "pendlay", "inverted-row", "spider-crawl", "plyo",
          "clean", "hang-clean", "sledge-hammer", "tire-flip", "wide-grip-pull-up", "deep-push-up",
          "spider-crawl-push-up", "pike-to-cobra-push-up", "battling-ropes", "bear-crawl",
          "shoulder-tap-push-up", "isometric-wipers", "power-point-plank", "side-bridge-hip-abduction",
          "push-up-to-side-plank", "suspended-abdominal-fallout", "hyperextension-on-bench", "lunge-with-jump",
          "jump-squat", "barbell-jump-squat", "skater-hops", "burpee", "jack-burpee", "dumbbell-burpee",
          "bulgarian", "split-squat", "barbell-lunge", "barbell-step-up",
          "weighted-sissy-squat", "squat-on-knees", "cossack", "close-grip-push-up", "side-plank-hip-adduction"]
EASY = ["bench-dip", "bench-dip-knees-bent", "bench-dip-on-floor", "triceps-dips-floor", "three-bench-dip",
        "scapula-dips", "assisted", "band-assisted", "bent-knees", "knees-bent", "kneeling", "on-knees",
        "incline-push-up", "push-up-wall", "wall", "potty-squat-with-support", "dumbbell-hammer-curl"]
BEGINNER_BW = {"crunch", "crunches", "curl", "bridge", "tilt", "heel", "touchers", "calf", "calves", "march",
               "stretch", "pose", "circles", "walk", "walking", "step", "abduction", "adduction",
               "abductor", "adductor", "toe", "touch", "bug", "sphinx", "dog", "hug", "rotation",
               "extension", "hyperextension", "elbow", "twist", "sit", "flutter", "kicks", "lying",
               "seated", "isometric", "squeeze", "grip", "wrist", "finger", "neck", "tap", "otis"}
ISOLATION = {"curl", "curls", "raise", "raises", "fly", "flyes", "kickback", "kickbacks", "extension",
             "shrug", "calf", "wrist", "pronation", "supination", "rotation", "finger", "bend", "twist",
             "rollerer", "circles", "lift", "crunch"}
JUMPS = {"jump", "jumps", "hop", "hops", "burpee", "skip", "plyo", "bound", "jack", "skater", "run"}
HOLDS = {"plank", "hold", "isometric", "stretch", "pose", "squeeze", "carry", "walk", "wipers"}
GEAR = {"bench", "ball", "bosu", "bar", "bars", "ring", "rings", "suspended", "roller", "wheel",
        "parallel", "pull", "chin", "dip", "dips", "hanging", "captains", "box", "stepbox", "rope",
        "stability", "medicine", "tire", "sledge", "board", "staircase", "towel", "chair", "decline", "farmers"}


def has(slug, seqs):
    s = f"-{slug}-"
    return any(f"-{k}-" in s for k in seqs)


def level(e):
    """1 principiante · 2 habitual · 3 experto · 4 coach, from slug, equipment and category."""
    s, eq, cat = e["slug"], e["equipment"], e["category"]
    tok = set(s.split("-"))
    if has(s, COACH):
        return 4
    if cat == "stretching":
        return 1
    if has(s, ["behind-neck"]):  # shoulder-unfriendly; only for people who know what they're doing
        return 3
    if eq in ("lever", "machine", "cable", "sled") and not has(s, ["sledge-hammer", "deadlift", "inverse-leg-curl"]):
        return 2 if tok & {"ball", "bosu", "stability", "one"} and eq == "cable" else 1
    if eq == "band":
        return 2 if has(s, EXPERT) else 1
    if cat == "plyometrics" or (has(s, EXPERT) and (not has(s, EASY) or has(s, ["self-assisted"]))):
        return 3
    if cat == "cardio":
        return 2 if tok & JUMPS else 1
    if eq == "barbell":
        return 1 if tok & {"curl", "shrug", "calf", "wrist"} and not tok & {"lying", "prone"} else 2
    if eq in ("dumbbell", "ez-bar", "smith"):
        if tok & {"ball", "stability", "bosu", "plank", "stork"} and "curl" not in tok or (eq == "ez-bar" and "extension" in tok):
            return 2
        return 1 if tok & ISOLATION and not tok & {"press", "squat", "lunge", "deadlift", "row", "step"} else 2
    if eq == "kettlebell":
        return 2
    if eq == "bodyweight":
        if tok & {"weighted", "mountain", "decline", "farmers"}:
            return 2
        if has(s, EASY):
            return 1 if has(s, ["incline-push-up", "push-up-wall", "kneeling", "wall", "bench-dip-knees-bent",
                                "bench-dip-on-floor", "triceps-dips-floor"]) else 2
        if tok & {"weighted", "suspended", "stability", "bosu", "ball", "medicine", "single", "one",
                  "push", "squat", "lunge", "plank", "raise", "row", "lever", "jump", "sit-up"}:
            return 2
        return 1 if tok & BEGINNER_BW else 2
    return 2


# a jump rope or strap at home; battle ropes need a gym; DB mislabels a few machines and bars
EQUIP_FIX = {"calf-stretch-with-rope": "rope", "reclining-big-toe-pose-with-rope": "rope",
             "standing-hamstring-and-calf-stretch-with-strap": "rope", "battling-ropes": "other",
             "hands-bike": "machine", "run-equipment": "machine", "frankenstein-squat": "barbell"}
# Checked against the animations: fixes where slug-based rules guess wrong.
OVERRIDES = {
    "hands-bike": {"l": 1, "c": 1, "w": 1}, "standing-archer": {"l": 1}, "body-up": {"l": 2},
    "triceps-press": {"l": 2, "g": 1}, "wheel-run": {"l": 2, "j": 1, "c": 1, "g": 0}, "swing-360": {"l": 4, "g": 1},
    "frankenstein-squat": {"l": 3}, "wind-sprints": {"l": 3, "g": 1}, "kick-out-sit": {"t": 1},
    "standing-calves": {"s": 1, "t": 1}, "assisted-prone-hamstring": {"s": 1, "t": 1, "x": 1},
    "assisted-standing-triceps-extension-with-towel": {"x": 1},
}


def load_names():
    """names_es.txt: hand-translated Spanish names for every non-curated exercise."""
    rows = [l.split("|") for l in (HERE / "names_es.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
    return {slug.strip(): name.strip() for slug, name in rows}


NAMES = load_names()


def load_steps():
    """instrucciones_es.txt: technique steps per exercise, blocks of `slug` + one step per line."""
    out = {}
    for block in (HERE / "instrucciones_es.txt").read_text().split("\n\n"):
        lines = [l.strip() for l in block.splitlines() if l.strip() and not l.startswith("#")]
        if lines:
            out[lines[0]] = lines[1:]
    return out


STEPS = load_steps()


def infer(e):
    """Level and flags for a non-curated exercise (heuristic over slug and category)."""
    s, cat = e["slug"], e["category"]
    eq = EQUIP_FIX.get(s, e["equipment"])
    tok = set(s.split("-"))
    lv = level(e)
    jump = cat == "plyometrics" or bool(tok & JUMPS) or has(s, ["jump-rope"])
    row = {"id": s, "n": NAMES[s], "m": e["muscle"], "e": eq, "l": max(lv, 2) if jump else lv,
           "i": e["instructions"], "f": e["file"]}
    flags = {"s": cat == "stretching" or bool(tok & {"stretch", "pose"}) and not tok & {"weighted", "lunge"},
             "c": cat == "cardio",
             "j": jump,
             "t": cat in ("stretching", "cardio") or bool(tok & HOLDS) or has(s, ["wall-sit", "march-sit-wall"]),
             "g": eq in ("bodyweight", "other") and bool(tok & GEAR),
             # partner-assisted stretches: fine to browse, never auto-planned
             "x": s.startswith("assisted-") and (cat == "stretching" or "stretch" in tok)}
    flags["w"] = flags["c"] and not jump and row["l"] <= 2
    flags["x"] = flags["x"] or "throw-down" in s  # a partner pushes the legs down
    row.update({k: 1 for k, v in flags.items() if v})
    row.update(OVERRIDES.get(s, {}))
    return row


def fetch_webp(e):
    gif = CACHE / e["file"]
    out = HERE / "img" / f"{e['slug']}.webp"
    if not gif.exists():
        gif.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(f"{BASE}/{e['file']}", gif)
    if not out.exists():
        subprocess.run(["gif2webp", "-quiet", "-lossy", "-q", "60", "-m", "6", "-mixed",
                        str(gif), "-o", str(out)], check=True)
    return out.stat().st_size


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    src = CACHE / "exercises.json"
    if not src.exists():
        urllib.request.urlretrieve(f"{BASE}/api/es/exercises.json", src)
    db = {e["slug"]: e for e in json.loads(src.read_text())["exercises"]}

    rows, picked = [], []
    for slug, name, flags in parse(CURATED):
        e = db[slug]  # KeyError = typo in CURATED
        f = set(flags)
        row = {"id": slug, "n": name, "m": e["muscle"], "core": 1, "f": e["file"],
               "e": next((x[1:] for x in f if x.startswith("@")), e["equipment"]),
               "l": int(next((x for x in f if x in "1234"), 1)),
               "i": e["instructions"]}
        for k in "tjwsg":
            if k in f:
                row[k] = 1
        if e["category"] == "cardio":
            row["c"] = 1
        rows.append(row)
        picked.append(e)

    assert len(rows) <= 250, "an Artifact publish takes 255 files: page + catalog + images"
    rows += [infer(e) for s, e in db.items() if s not in {r["id"] for r in rows}]
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == len(db), "every DB exercise exactly once"
    assert not set(NAMES) - set(db), f"names_es.txt has unknown slugs: {sorted(set(NAMES) - set(db))}"
    assert not set(NAMES) & {r["id"] for r in rows if r.get("core")}, "curated names live in CURATED"
    dupes = [n for n, c in Counter(r["n"] for r in rows).items() if c > 1]
    assert not dupes, f"two exercises share a name: {dupes}"
    assert set(STEPS) == set(ids), f"instructions missing for {sorted(set(ids) - set(STEPS))[:5]}, unknown {sorted(set(STEPS) - set(ids))[:5]}"
    for r in rows:
        r["i"] = STEPS[r["id"]]
        assert len(r["i"]) >= 2, f"{r['id']}: needs at least two steps"

    (HERE / "img").mkdir(exist_ok=True)
    with ThreadPoolExecutor(8) as pool:
        total = sum(pool.map(fetch_webp, picked))
    (HERE / "catalog.json").write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    print(f"{len(rows)} exercises ({len(picked)} curated), img {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
