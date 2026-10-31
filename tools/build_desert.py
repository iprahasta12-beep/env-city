# Desert theme: Spine 4.2 skeleton (env.json) + placements.json. All motion = Spine keys.
# Skeleton space y-up; texture px = landscape 1920 display px.
import json, math, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import spine_helpers as H
from spine_helpers import *

base_json, theme_dir = sys.argv[1:3]
img_dir = os.path.join(theme_dir, "images")
BASE = json.load(open(base_json))
FLAG = [s for s in BASE["skins"] if s["name"] == "flag"][0]["attachments"]["flag_cloth"]["flag_cloth"]
UV = FLAG["uvs"]

J = {"skeleton": {"hash": "envdesert", "spine": "4.2.40", "x": -200, "y": -200, "width": 400, "height": 400, "images": "./images/", "audio": ""},
     "bones": [{"name": "root"}], "slots": [], "skins": [{"name": "default", "attachments": {}}], "animations": {}}
H.init(J, img_dir)
IMG = H.IMG
anims = J["animations"]

def mesh(img, vert_fn, name=None):
    tw, th = IMG(img)
    m = {"type": "mesh", "uvs": UV, "triangles": FLAG["triangles"], "hull": FLAG["hull"], "edges": FLAG["edges"],
         "width": tw, "height": th}
    m["vertices"] = [v for k in range(0, len(UV), 2) for v in map(R, vert_fn(UV[k], UV[k + 1]))]
    if name and name != img: m["path"] = img
    return m

def deform_anim(skin_name, slot_name, att_name, T, n, off_fn):
    keys = []
    for k in range(n + 1):
        t = T * k / n
        vs = []
        for i in range(0, len(UV), 2):
            dx, dy = off_fn(UV[i], UV[i + 1], t / T)
            vs += [R(dx), R(dy)]
        keys.append({"time": R(t), "vertices": vs} if k else {"vertices": vs})
    return {skin_name: {slot_name: {att_name: {"deform": keys}}}}

# ============================================================ SPINNERS (fan / vent / turbine)
bone("spin")
slot("spin_blade", "spin", "blade")
slot("spin_hub", "root", "hub")
skin("fan", {"spin_blade": {"blade": region("fan_blade", w=140, path="fan_blade")}, "spin_hub": {"hub": region("fan_hub", w=46, path="fan_hub")}})
skin("vent", {"spin_blade": {"blade": region("vent_blade", w=72, path="vent_blade")}})
skin("turbine", {"spin_blade": {"blade": region("turbine_top", w=148, path="turbine_top")}})
anims["fan_spin"] = {"bones": {"spin": {"rotate": spin_keys(-360, 1.2)}}}
anims["vent_spin"] = {"bones": {"spin": {"rotate": spin_keys(-360, 1.0)}}}
anims["turbine_spin"] = {"bones": {"spin": {"rotate": spin_keys(-360, 3.0, 8)}}}

# ============================================================ ALARM LIGHT
bone("alarm")
bone("alarm_glow", "alarm")
slot("alarm_glow", "alarm_glow", "alarm_glow", "additive", "ff3020ff")
slot("alarm_on", "alarm", "alarm_on")
skin("alarm", {"alarm_glow": {"alarm_glow": region("alarm_glow", w=120)}, "alarm_on": {"alarm_on": region("alarm_on", w=26)}})
blink = [(0, 0), (0.05, 1), (0.5, 1), (0.58, 0), (1, 0)]
anims["alarm_blink"] = {"slots": {"alarm_glow": {"alpha": lin1([(t, v * 0.9) for t, v in blink])}, "alarm_on": {"alpha": lin1(blink)}},
                        "bones": {"alarm_glow": {"scale": keys2([(0, 0.8, 0.8), (0.1, 1.1, 1.1), (0.5, 1.0, 1.0), (1, 0.8, 0.8)])}}}

# ============================================================ AWNING (root = top-center under diner sign)
AW = 380
bone("awning_d")
slot("awning_flap", "awning_d", "awning_flap")
slot("awning_top", "awning_d", "awning_top")
fh = IMG("awning_flap")[1] * AW / IMG("awning_flap")[0]
th_ = IMG("awning_top")[1] * AW / IMG("awning_top")[0]
skin("awning", {"awning_top": {"awning_top": region("awning_top", w=AW, y=-th_ / 2)},
                "awning_flap": {"awning_flap": mesh("awning_flap", lambda u, v: (-AW / 2 + u * AW, -(th_ - 6) - v * fh))}})
def awning_off(u, v, p):
    x = u * AW
    wave = 0.5 + 0.5 * math.sin(2 * math.pi * p - x * 0.045)
    gust = 0.5 + 0.5 * math.sin(2 * math.pi * 2 * p + x * 0.02)
    return (v * v * 1.6 * math.sin(2 * math.pi * p + x * 0.03), -v * v * (1.5 + 5 * wave * gust))
anims["awning_flutter"] = {"attachments": deform_anim("awning", "awning_flap", "awning_flap", 2.0, 16, awning_off)}

# ============================================================ WINDSOCK (root = pole top / sock mouth)
SW = 290; sw, sh = IMG("windsock"); SH = sh * SW / sw
MX, MY = 0.05, 0.25                       # mouth position in uv
AX = ((0.97 - MX) * SW, -(0.85 - MY) * SH); AL = math.hypot(*AX); AX = (AX[0] / AL, AX[1] / AL); NX = (-AX[1], AX[0])
bone("windsock")
slot("windsock", "windsock", "windsock")
skin("windsock", {"windsock": {"windsock": mesh("windsock", lambda u, v: ((u - MX) * SW, (MY - v) * SH))}})
def sock_off(u, v, p):
    px, py = (u - MX) * SW, (MY - v) * SH
    along = max(0, (px * AX[0] + py * AX[1]) / AL)
    w = min(1, along) ** 1.4
    wv = math.sin(2 * math.pi * p - along * 2 * math.pi * 1.1)
    st = 3 * w * math.sin(2 * math.pi * 2 * p)
    off = 7 * w * wv
    return (NX[0] * off + AX[0] * st, NX[1] * off + AX[1] * st)
anims["windsock_wave"] = {"attachments": deform_anim("windsock", "windsock", "windsock", 1.6, 16, sock_off)}

# ============================================================ TREES (gust + leaf flutter)
bone("tree_d")
bone("tree_leaf", "tree_d")
slot("tree_d", "tree_leaf", "tree")
for k, w in (("A", 130), ("B", 130), ("C", 120)):
    skin(f"tree_{k.lower()}", {"tree_d": {"tree": region(f"tree_{k}", w=w, path=f"tree_{k}")}})
anims["tree_gust"] = {"bones": {
    "tree_d": {"translate": keys2([(0, 0, 0), (1.0, 3.5, -1.8), (1.8, -1, 0.5), (2.6, 1.6, -0.8), (3.6, 0, 0), (5, 0, 0)]),
               "rotate": keys1([(0, 0), (1.0, -2.2), (1.8, 0.9), (2.6, -1.1), (3.6, 0.5), (5, 0)]),
               "scale": keys2([(0, 1, 1), (1.0, 1.03, 0.985), (1.8, 0.99, 1.01), (2.6, 1.015, 0.995), (5, 1, 1)])},
    "tree_leaf": {"scale": keys2([(0, 1, 1), (0.25, 1.012, 0.992), (0.5, 1, 1), (0.75, 0.992, 1.012), (1.0, 1, 1),
                                  (1.25, 1.012, 0.992), (1.5, 1, 1), (1.75, 0.992, 1.012), (2.0, 1, 1), (2.25, 1.012, 0.992), (2.5, 1, 1),
                                  (2.75, 0.992, 1.012), (3.0, 1, 1), (3.25, 1.012, 0.992), (3.5, 1, 1), (3.75, 0.992, 1.012), (4.0, 1, 1),
                                  (4.25, 1.012, 0.992), (4.5, 1, 1), (4.75, 0.992, 1.012), (5.0, 1, 1)])}}}

# ============================================================ PUFFS (smoke / dust) — 4 puffs, keys offset per puff
NP = 4
bone("puffs")
for i in range(NP): bone(f"puff_{i}", "puffs")
SM = ["smoke_1", "smoke_3", "smoke_2", "smoke_1"]
for i in range(NP): slot(f"smoke_{i}", f"puff_{i}", SM[i], None, "efe7ddff")
for i in range(NP): slot(f"dust_{i}", f"puff_{i}", SM[i], None, "f5a050ff")
skin("smoke", {f"smoke_{i}": {SM[i]: region(SM[i], w=110)} for i in range(NP)})
skin("dust", {f"dust_{i}": {SM[i]: region(SM[i], w=110)} for i in range(NP)})
def puff_anim(prefix, T, travel, rise, s0, s1, amax, rot, steps=24):
    bones_, slots_ = {}, {}
    for i in range(NP):
        off = i / NP
        ts = sorted(set([T * k / steps for k in range(steps + 1)] + [T * (1 - off) - 1e-3, T * (1 - off)] if off else [T * k / steps for k in range(steps + 1)]))
        ts = [t for t in ts if 0 <= t <= T]
        tr, sc, al, ro = [], [], [], []
        for t in ts:
            u = (t / T + off) % 1.0
            if abs(t - (T * (1 - off) - 1e-3)) < 1e-6: u = 0.9999
            a = (u / 0.15) if u < 0.15 else (1 - (u - 0.15) / 0.85) ** 1.3
            s = s0 + (s1 - s0) * u
            def K(d): return dict({"time": R(t)} if t else {}, **d)
            tr.append(K({"x": R(travel * u), "y": R(-rise * u + 6 * math.sin(u * 6.28 + i))}))
            sc.append(K({"x": R(s), "y": R(s)}))
            al.append(K({"value": R(a * amax)}))
            ro.append(K({"value": R(rot * u + i * 70)}))
        bones_[f"puff_{i}"] = {"translate": tr, "scale": sc, "rotate": ro}
        slots_[f"{prefix}_{i}"] = {"alpha": al}
    return {"bones": bones_, "slots": slots_}
anims["smoke_flow"] = puff_anim("smoke", 3.2, 130, 60, 0.35, 1.6, 0.9, 40)
anims["dust_drift"] = puff_anim("dust", 6.0, 700, 40, 1.4, 2.6, 0.32, 25)

# ============================================================ TUMBLEWEED (root = start point, rolls +x 2100px)
bone("tw")
bone("tw_shadow", "tw")
bone("tw_hop", "tw")
bone("tw_ball", "tw_hop")
slot("tw_shadow", "tw_shadow", "tumbleweed_shadow", None, "ffffffb3")
slot("tumbleweed", "tw_ball", "tumbleweed")
skin("tumbleweed", {"tw_shadow": {"tumbleweed_shadow": region("tumbleweed_shadow", w=96, h=34)}, "tumbleweed": {"tumbleweed": region("tumbleweed", w=72)}})
TT, TR_, DIST = 10.0, 8.0, 2100
tr, hop, hs, rot, sh_t, sh_s, sh_a, ball_a = [], [], [], [], [], [], [], []
n = 80
for k in range(n + 1):
    t = TR_ * k / n
    x = DIST * t / TR_
    yw = 22 * math.sin(2 * math.pi * 1.5 * t / TR_)
    hp = abs(math.sin(math.pi * 9 * t / TR_))
    T0 = {"time": R(t)} if t else {}
    tr.append(dict(T0, x=R(x), y=0))
    hop.append(dict(T0, x=0, y=R(yw + hp * 12)))
    hs.append(dict(T0, x=R(1 + hp * 0.15), y=R(1 + hp * 0.15)))
    rot.append(dict(T0, value=R(-x / 36 * 57.2958)))
    sh_t.append(dict(T0, x=R(6 + hp * 8), y=R(yw - 10 - hp * 4)))
    sh_s.append(dict(T0, x=R(1 - hp * 0.18), y=R(1 - hp * 0.18)))
    sh_a.append(dict(T0, value=R(0.7 - hp * 0.3)))
    ball_a.append(dict(T0, value=1))
tr.append({"time": TT, "x": DIST, "y": 0})
for lst, last in ((sh_a, 0), (ball_a, 0)):
    lst[-1]["curve"] = "stepped"; lst.append({"time": R(TR_ + 0.001), "value": 0}); lst.append({"time": TT, "value": 0})
anims["tumbleweed_roll"] = {"bones": {"tw": {"translate": tr}, "tw_hop": {"translate": hop, "scale": hs}, "tw_ball": {"rotate": rot},
                                      "tw_shadow": {"translate": sh_t, "scale": sh_s}},
                            "slots": {"tumbleweed": {"alpha": ball_a}, "tw_shadow": {"alpha": sh_a}}}

json.dump(J, open(os.path.join(theme_dir, "env.json"), "w"), indent=1)
print("bones", len(J["bones"]), "slots", len(J["slots"]), "skins", len(J["skins"]), "anims", list(anims))

# ============================================================ PLACEMENTS
KL = 1920 / 1670
KP, OY = 1080 / 1640, 650
def it(name, skin_, anim, x, y, scale=1.0, **kw):
    return dict(name=name, skin=skin_, anim=anim, x=x, y=y, scale=scale, **kw)
SRC = [  # source-px coords (1670x942), scale at landscape
    ("Tree TL 1", "tree_b", "tree_gust", 40, 30, 0.62), ("Tree TL 2", "tree_a", "tree_gust", 115, 250, 0.6),
    ("Tree TR 1", "tree_c", "tree_gust", 1630, 40, 0.62), ("Tree TR 2", "tree_a", "tree_gust", 1040, 250, 0.5),
    ("Tree BL 1", "tree_c", "tree_gust", 40, 600, 0.6), ("Tree BL 2", "tree_b", "tree_gust", 150, 890, 0.66),
    ("Tree BL 3", "tree_a", "tree_gust", 560, 900, 0.6),
    ("Tree BR 1", "tree_b", "tree_gust", 1060, 860, 0.62), ("Tree BR 2", "tree_c", "tree_gust", 1630, 900, 0.6),
    ("Tree BR 3", "tree_a", "tree_gust", 1620, 560, 0.55),
    ("Turbine", "turbine", "turbine_spin", 187, 637, 0.9),
    ("Shop fan", "fan", "fan_spin", 335, 655, 0.8),
    ("Diner fan L", "fan", "fan_spin", 1243, 140, 0.9),
    ("Diner fan R", "fan", "fan_spin", 1495, 141, 0.86, {"flipX": True}),
    ("Vent top", "vent", "vent_spin", 432, 115, 0.6),
    ("Vent bottom", "vent", "vent_spin", 1333, 702, 0.92, {"flipX": True}),
    ("Awning diner", "awning", "awning_flutter", 1352, 262, 1.0),
    ("Alarm shop", "alarm", "alarm_blink", 610, 679, 1.0, {"random": False}),
    ("Windsock", "windsock", "windsock_wave", 22, 718, 0.78),
    ("Smoke diner", "smoke", "smoke_flow", 1446, 40, 1.0),
    ("Smoke shop", "smoke", "smoke_flow", 390, 556, 0.75),
    ("Dust road", "dust", "dust_drift", -120, 420, 1.0),
    ("Tumbleweed", "tumbleweed", "tumbleweed_roll", -100, 455, 1.0, {"random": False}),
]
def conv(k, ox, oy, smul):
    out = []
    for row in SRC:
        name, sk, an, x, y, s = row[:6]; kw = row[6] if len(row) > 6 else {}
        out.append(it(name, sk, an, round(x * k + ox), round(y * k + oy), round(s * smul, 3), **kw))
    return out
land = conv(KL, 0, 0, 1)
port = conv(KP, 0, OY, KP / KL)
# portrait: extra desert life in the extended bands (no buildings there)
import random
random.seed(3)
for i, (x, y, sk) in enumerate([(90, 120, "tree_a"), (330, 260, "tree_c"), (800, 90, "tree_b"), (980, 330, "tree_a"), (200, 470, "tree_b"),
                                (860, 520, "tree_c"), (120, 1420, "tree_c"), (360, 1600, "tree_a"), (760, 1450, "tree_b"),
                                (990, 1700, "tree_a"), (180, 1820, "tree_b"), (850, 1860, "tree_c")]):
    port.insert(0, it(f"Tree band {i + 1}", sk, "tree_gust", x, y, round(random.uniform(0.5, 0.65), 2)))
port += [it("Tumbleweed vertical", "tumbleweed", "tumbleweed_roll", 553, -100, 0.75, rotation=90, timeScale=0.8),
         it("Dust vertical", "dust", "dust_drift", 553, -150, 0.7, rotation=90)]
doc = {"_readme": "Coordinates = background pixels (top-left origin). List order = draw order. Fields: name, skin, anim, x, y, scale, scaleY, rotation(deg, clockwise), flipX, timeScale, random.",
       "skeleton": "env.json", "atlas": "env.atlas",
       "landscape": {"background": "bg_landscape.png", "width": 1920, "height": 1080, "items": land},
       "portrait": {"background": "bg_portrait.png", "width": 1080, "height": 1920, "items": port}}
json.dump(doc, open(os.path.join(theme_dir, "placements.json"), "w"), indent=1)
print(len(land), len(port))
