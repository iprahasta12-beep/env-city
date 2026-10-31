# win_fx.json — 5 win levels (WIN / CRASH / SMASH / WRECKAGE / TOTAL), each <lvl>_in / _loop / _out. Spine 4.2, all motion = keys.
# Design space 1080 wide, root (0,0) = screen center, y-up. Bone `fx` scale 0.8 resizes everything. Slot `amount` = game number text.
import json, math, os, sys, random
from PIL import Image
import numpy as np
src, out = sys.argv[1:3]
IMGD = os.path.join(out, "images_win"); os.makedirs(IMGD, exist_ok=True)
for f in os.listdir(IMGD): os.remove(os.path.join(IMGD, f))

TEX = {"text_win": 760, "text_crash": 800, "text_smash": 800, "wreckage": 860, "total": 800, "plate_top": 860, "car_hood": 500,
       "engine_block": 400, "tire": 300, "rim": 190, "bracket": 320, "blade": 320, "piston": 240, "chain": 80, "bolt": 120,
       "shard": 160, "debris_round": 180, "brake_disc": 280, "exhaust_pipe": 340, "bumper": 400, "smoke": 380, "smoke_big": 560,
       "explosion_main": 1100, "spark_burst_01": 440, "spark_burst_02": 440, "spark_burst_03": 440, "spark_small": 170}
SIZE = {}
for n, w in TEX.items():
    im = Image.open(os.path.join(src, n + ".png")).convert("RGBA")
    a = np.asarray(im)[:, :, 3]; ys, xs = np.where(a > 20)
    im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    h = round(im.size[1] * w / im.size[0])
    im.resize((w, h), Image.LANCZOS).save(os.path.join(IMGD, n + ".png"), optimize=True)
    SIZE[n] = (w, h)

R = lambda v: round(v, 3)
J = {"skeleton": {"hash": "winfx5", "spine": "4.2.40", "x": -540, "y": -540, "width": 1080, "height": 1080, "images": "./images_win/", "audio": ""},
     "bones": [{"name": "root"}, {"name": "fx", "parent": "root", "scaleX": 0.8, "scaleY": 0.8}, {"name": "amount", "parent": "fx", "y": -265}],
     "slots": [], "skins": [{"name": "default", "attachments": {}}], "animations": {}}
B, S, SK, AN = J["bones"], J["slots"], J["skins"][0]["attachments"], J["animations"]

def bone(name, parent, x=0, y=0, rot=0):
    b = {"name": name, "parent": parent}
    if x: b["x"] = R(x)
    if y: b["y"] = R(y)
    if rot: b["rotation"] = R(rot)
    B.append(b)
def slot(name, b, att, blend=None, color="ffffff00"):
    s = {"name": name, "bone": b, "attachment": att, "color": color}
    if blend: s["blend"] = blend
    S.append(s)
def region(img, w, mirror=False, rot=0, h=None):
    tw, th = SIZE[img]; s = w / tw
    a = {"width": tw, "height": th, "scaleX": R(s * (-1 if mirror else 1)), "scaleY": R((h / th) if h else s)}
    if rot: a["rotation"] = rot
    return a
def K(t, **v):
    d = {"time": R(t)} if t else {}
    d.update({k: R(x) if isinstance(x, (int, float)) else x for k, x in v.items()})
    return d
def eo(t0, a0, t1, a1):      # ease-out bezier, 1 or 2 values
    dt = t1 - t0
    if not isinstance(a0, tuple): return [R(t0 + dt * 0.1), R(a0 + (a1 - a0) * 0.5), R(t0 + dt * 0.45), R(a1)]
    return eo(t0, a0[0], t1, a1[0]) + eo(t0, a0[1], t1, a1[1])
def ei(t0, a0, t1, a1):
    dt = t1 - t0
    if not isinstance(a0, tuple): return [R(t0 + dt * 0.5), R(a0), R(t0 + dt * 0.9), R(a0 + (a1 - a0) * 0.5)]
    return ei(t0, a0[0], t1, a1[0]) + ei(t0, a0[1], t1, a1[1])
def eio(t0, a0, t1, a1):
    dt = t1 - t0
    if not isinstance(a0, tuple): return [R(t0 + dt * 0.4), R(a0), R(t1 - dt * 0.4), R(a1)]
    return eio(t0, a0[0], t1, a1[0]) + eio(t0, a0[1], t1, a1[1])
def sinv(T, amp, ph, n=8, base=0):
    return [(T * k / n, base + amp * math.sin(2 * math.pi * (k / n + ph))) for k in range(n + 1)]

IN_T, LOOP_T, OUT_T = 1.4, 2.0, 0.5

def build_level(lv, main, main_w, parts, smokes, bursts, sparks, explosion=None, shake=14, win_y=-10, main_y=150, win_w=560, smoke_a=0.5):
    """parts: dicts(name,img,x,y,rot,w,from,t0,loop,mirror,parent,z)  smokes: (img,x,y,w,t0)  bursts: (x,y,rot,w,t0,mirror)  sparks: n"""
    rng = random.Random(hash(lv) & 0xffff)
    L, SHK = f"{lv}", f"{lv}_shake"
    bone(L, "fx"); bone(SHK, L)
    A_in, A_loop, A_out = {"bones": {}, "slots": {}}, {"bones": {}, "slots": {}}, {"bones": {}, "slots": {}}
    def add(anim, kind, name, tl, keys): anim[kind].setdefault(name, {})[tl] = keys
    order = []   # (z, slotdef) draw order within level

    # ---------- explosion (back)
    if explosion:
        n = f"{lv}_explosion"; bone(n, SHK, 0, explosion[1]); order.append((0, (n, n, "explosion_main", None)))
        SK.setdefault(n, {})["explosion_main"] = region("explosion_main", explosion[0])
        add(A_in, "bones", n, "scale", [K(0, x=0.2, y=0.2, curve=eo(0, (0.2, 0.2), 0.45, (1.15, 1.15))), K(0.45, x=1.15, y=1.15, curve=eio(0.45, (1.15, 1.15), 0.8, (1, 1))), K(0.8, x=1, y=1)])
        add(A_in, "slots", n, "alpha", [K(0, value=0), K(0.12, value=1), K(0.8, value=1), K(IN_T, value=0.9)])
        add(A_loop, "bones", n, "scale", [K(t, x=1 + v, y=1 + v) for t, v in sinv(LOOP_T, 0.04, 0)])
        add(A_loop, "bones", n, "rotate", [K(t, value=v) for t, v in sinv(LOOP_T, 2, 0.25)])
        add(A_loop, "slots", n, "alpha", [K(t, value=0.85 + v) for t, v in sinv(LOOP_T, 0.08, 0.1)])
        add(A_out, "bones", n, "scale", [K(0, x=1, y=1, curve=eo(0, (1, 1), OUT_T, (1.4, 1.4))), K(OUT_T, x=1.4, y=1.4)])
        add(A_out, "slots", n, "alpha", [K(0, value=0.9), K(0.35, value=0)])
    # ---------- smoke
    for i, (img, x, y, w, t0) in enumerate(smokes):
        n = f"{lv}_smoke{i}"; bone(n, SHK, x, y, rng.uniform(-20, 20)); order.append((1, (n, n, img, None)))
        SK.setdefault(n, {})[img] = region(img, w, mirror=x > 0)
        dx = 40 * (1 if x >= 0 else -1)
        add(A_in, "bones", n, "scale", [K(0, x=0.3, y=0.3), K(t0, x=0.3, y=0.3, curve=eo(t0, (0.3, 0.3), t0 + 0.7, (1, 1))), K(t0 + 0.7, x=1, y=1)])
        add(A_in, "bones", n, "translate", [K(0, x=-dx, y=-10), K(t0, x=-dx, y=-10, curve=eo(t0, (-dx, -10), IN_T, (0, 0))), K(IN_T, x=0, y=0)])
        add(A_in, "slots", n, "alpha", [K(0, value=0), K(t0, value=0), K(t0 + 0.15, value=smoke_a * 1.3), K(IN_T, value=smoke_a)])
        ph = rng.random()
        add(A_loop, "bones", n, "scale", [K(t, x=1 + v, y=1 + v) for t, v in sinv(LOOP_T, 0.07, ph)])
        add(A_loop, "bones", n, "translate", [K(t, x=v * 1.5, y=v) for t, v in sinv(LOOP_T, 8, ph + 0.2)])
        add(A_loop, "slots", n, "alpha", [K(t, value=smoke_a + v) for t, v in sinv(LOOP_T, 0.16 * smoke_a, ph)])
        add(A_out, "bones", n, "scale", [K(0, x=1, y=1), K(OUT_T, x=1.5, y=1.5)])
        add(A_out, "bones", n, "translate", [K(0, x=0, y=0), K(OUT_T, x=dx * 3, y=30)])
        add(A_out, "slots", n, "alpha", [K(0, value=smoke_a), K(0.4, value=0)])
    # ---------- spark bursts (additive, 3-frame flicker)
    for i, (x, y, rot, w, t0, mir) in enumerate(bursts):
        n = f"{lv}_burst{i}"; bone(n, SHK, x, y, rot); order.append((2, (n, n, "spark_burst_01", "additive")))
        SK.setdefault(n, {}).update({f"spark_burst_0{k}": region(f"spark_burst_0{k}", w, mirror=mir) for k in (1, 2, 3)})
        fr = lambda t0_, t1_, st: [K(t, name=f"spark_burst_0{(k + i) % 3 + 1}") for k, t in enumerate(np.arange(t0_, t1_ - 1e-6, st))]
        add(A_in, "slots", n, "attachment", fr(0, IN_T, 0.1))
        add(A_in, "slots", n, "alpha", [K(0, value=0), K(t0, value=0), K(t0 + 0.05, value=1), K(IN_T, value=0.95)])
        add(A_in, "bones", n, "scale", [K(0, x=0, y=0), K(t0, x=0, y=0, curve=eo(t0, (0, 0), t0 + 0.2, (1.25, 1.25))), K(t0 + 0.2, x=1.25, y=1.25, curve=eio(t0 + 0.2, (1.25, 1.25), t0 + 0.4, (1, 1))), K(t0 + 0.4, x=1, y=1)])
        add(A_loop, "slots", n, "attachment", fr(0, LOOP_T, 0.1))
        add(A_loop, "slots", n, "alpha", [K(t, value=0.9 + v) for t, v in sinv(LOOP_T, 0.1, i * 0.3, n=16)])
        add(A_loop, "bones", n, "scale", [K(t, x=1 + v, y=1 + v) for t, v in sinv(LOOP_T, 0.08, i * 0.37, n=16)])
        add(A_out, "slots", n, "alpha", [K(0, value=0.95), K(0.25, value=0)])
        add(A_out, "bones", n, "scale", [K(0, x=1, y=1), K(0.25, x=1.4, y=1.4)])
    # ---------- components
    for p in parts:
        n = f"{lv}_{p['name']}"; par = f"{lv}_{p['parent']}" if p.get("parent") else SHK
        bone(n, par, p.get("x", 0), p.get("y", 0), p.get("rot", 0)); order.append((p.get("z", 3), (n, n, p["img"], None)))
        SK.setdefault(n, {})[p["img"]] = region(p["img"], p["w"], mirror=p.get("mirror", False))
        t0 = p.get("t0", 0.2)
        if p.get("parent"):   # child (rim on tire): only alpha + own spin
            add(A_in, "slots", n, "alpha", [K(0, value=0), K(t0, value=0), K(t0 + 0.08, value=1)])
        else:
            fx_, fy_ = p.get("from", (0, 0))
            if fx_ or fy_:
                add(A_in, "bones", n, "translate", [K(0, x=fx_, y=fy_), K(t0, x=fx_, y=fy_, curve=eo(t0, (fx_, fy_), t0 + 0.35, (-fx_ * 0.04, -fy_ * 0.04))),
                                                    K(t0 + 0.35, x=-fx_ * 0.04, y=-fy_ * 0.04, curve=eio(t0 + 0.35, (-fx_ * 0.04, -fy_ * 0.04), t0 + 0.5, (0, 0))), K(t0 + 0.5, x=0, y=0)])
                rr = p.get("spinin", 120 * (1 if fx_ <= 0 else -1))
                add(A_in, "bones", n, "rotate", [K(0, value=rr), K(t0, value=rr, curve=eo(t0, rr, t0 + 0.4, 0)), K(t0 + 0.4, value=0)])
            else:  # pop
                add(A_in, "bones", n, "scale", [K(0, x=0, y=0), K(t0, x=0, y=0, curve=eo(t0, (0, 0), t0 + 0.18, (1.3, 1.3))), K(t0 + 0.18, x=1.3, y=1.3, curve=eio(t0 + 0.18, (1.3, 1.3), t0 + 0.35, (1, 1))), K(t0 + 0.35, x=1, y=1)])
                add(A_in, "bones", n, "translate", [K(0, x=0, y=-30), K(t0, x=0, y=-30, curve=eo(t0, (0, -30), t0 + 0.35, (0, 0))), K(t0 + 0.35, x=0, y=0)])
            add(A_in, "slots", n, "alpha", [K(0, value=0), K(t0, value=0), K(t0 + 0.08, value=1)])
        ph = rng.random(); loop = p.get("loop", "float")
        if loop == "spin":
            d = p.get("dir", -1)
            add(A_loop, "bones", n, "rotate", [K(LOOP_T * k / 4, value=d * 90 * k) for k in range(5)])
        elif loop == "wobble":
            add(A_loop, "bones", n, "rotate", [K(t, value=v) for t, v in sinv(LOOP_T, 4, ph)])
        if not p.get("parent"):
            add(A_loop, "bones", n, "translate", [K(t, x=0, y=v) for t, v in sinv(LOOP_T, p.get("amp", 7), ph)])
            if loop == "float":
                add(A_loop, "bones", n, "rotate", [K(t, value=v) for t, v in sinv(LOOP_T, 3, ph + 0.25)])
            ox, oy = p.get("x", 0), p.get("y", 0); l = math.hypot(ox, oy) or 1
            add(A_out, "bones", n, "translate", [K(0, x=0, y=0, curve=ei(0, (0, 0), OUT_T, (ox / l * 650, oy / l * 650))), K(OUT_T, x=ox / l * 650, y=oy / l * 650)])
            add(A_out, "bones", n, "rotate", [K(0, value=0), K(OUT_T, value=rng.choice([-1, 1]) * 140)])
        add(A_loop, "slots", n, "alpha", [K(0, value=1), K(LOOP_T, value=1)])
        add(A_out, "slots", n, "alpha", [K(0, value=1), K(0.3, value=1), K(OUT_T, value=0)])
    # ---------- texts
    for key, img, w, y, t0 in (("main", main, main_w, main_y, 0.32), ("win", "text_win", win_w, win_y, 0.62)):
        if img is None: continue
        n = f"{lv}_{key}"; bone(n, SHK, 0, y); order.append((5, (n, n, img, None)))
        SK.setdefault(n, {})[img] = region(img, w)
        if key == "main":
            add(A_in, "bones", n, "scale", [K(0, x=2.4, y=2.4), K(t0, x=2.4, y=2.4, curve=ei(t0, (2.4, 2.4), t0 + 0.16, (0.9, 0.9))), K(t0 + 0.16, x=0.9, y=0.86, curve=eio(t0 + 0.16, (0.9, 0.86), t0 + 0.3, (1, 1))), K(t0 + 0.3, x=1, y=1)])
        else:
            add(A_in, "bones", n, "scale", [K(0, x=0, y=0), K(t0, x=0, y=0, curve=eo(t0, (0, 0), t0 + 0.16, (1.25, 1.25))), K(t0 + 0.16, x=1.25, y=1.25, curve=eio(t0 + 0.16, (1.25, 1.25), t0 + 0.3, (1, 1))), K(t0 + 0.3, x=1, y=1)])
        add(A_in, "slots", n, "alpha", [K(0, value=0), K(t0, value=0), K(t0 + 0.06, value=1)])
        ph = 0 if key == "main" else 0.5
        add(A_loop, "bones", n, "scale", [K(t, x=1 + v, y=1 + v) for t, v in sinv(LOOP_T / 2 if key == "main" else LOOP_T, 0.04, ph)] if key != "main" else
            [K(t, x=1 + abs(v), y=1 + abs(v)) for t, v in sinv(LOOP_T, 0.045, 0, n=8)])
        add(A_loop, "slots", n, "alpha", [K(0, value=1), K(LOOP_T, value=1)])
        add(A_out, "slots", n, "alpha", [K(0, value=1), K(0.3, value=1), K(OUT_T, value=0)])
    # ---------- small sparks (additive): shoot out from center, re-shoot in loop
    for i in range(sparks):
        ang = rng.uniform(0, 360) if lv != "win" else i * 360 / sparks + rng.uniform(-15, 15)
        n = f"{lv}_spark{i}"; bone(n, SHK, 0, 40, ang); order.append((6, (n, n, "spark_small", "additive")))
        sw = rng.uniform(90, 150)
        SK.setdefault(n, {})["spark_small"] = region("spark_small", sw, rot=45)   # art head points down-right -> along +x
        r0, r1 = rng.uniform(120, 220), rng.uniform(380, 560)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))   # translate is in parent space -> along the spark heading
        def shot(t0, dur):
            return ([K(t0, x=r0 * ca, y=r0 * sa), K(t0 + dur, x=r1 * ca, y=r1 * sa)], [K(t0, value=1), K(t0 + dur * 0.6, value=0.9), K(t0 + dur, value=0)])
        t0 = 0.6 + rng.uniform(0, 0.3); dur = rng.uniform(0.35, 0.55)
        tr, al = shot(t0, dur)
        # bone x is along the spark direction because the bone is rotated by ang
        add(A_in, "bones", n, "translate", [K(0, x=r0 * ca, y=r0 * sa)] + tr)
        add(A_in, "slots", n, "alpha", [K(0, value=0), K(t0 - 0.001, value=0)] + al + [K(IN_T, value=0)])
        lt = rng.uniform(0, LOOP_T - dur)
        tr, al = shot(lt, dur)
        add(A_loop, "bones", n, "translate", [K(0, x=r0 * ca, y=r0 * sa)] + tr + [K(LOOP_T, x=r1 * ca, y=r1 * sa)])
        add(A_loop, "slots", n, "alpha", [K(0, value=0), K(max(0.0001, lt - 0.001), value=0)] + al + [K(LOOP_T, value=0)])
        add(A_out, "slots", n, "alpha", [K(0, value=0), K(OUT_T, value=0)])
    # ---------- impact shake + level punch/shrink on out
    sh = []
    for k, t in enumerate(np.arange(0.48, 0.8, 0.04)):
        a = shake * (1 - (t - 0.48) / 0.32)
        sh.append(K(t, x=rng.uniform(-a, a), y=rng.uniform(-a, a)))
    add(A_in, "bones", SHK, "translate", [K(0, x=0, y=0), K(0.47, x=0, y=0)] + sh + [K(0.82, x=0, y=0)])
    if lv == "total":
        add(A_loop, "bones", SHK, "translate", [K(LOOP_T * k / 20, x=(1.5 if k % 2 else -1.5) * (k % 20 != 0), y=(1 if k % 3 else -1) * (k % 20 != 0)) for k in range(21)])
    add(A_out, "bones", L, "scale", [K(0, x=1, y=1, curve=eo(0, (1, 1), 0.12, (1.1, 1.1))), K(0.12, x=1.1, y=1.1, curve=ei(0.12, (1.1, 1.1), OUT_T, (0.2, 0.2))), K(OUT_T, x=0.2, y=0.2)])
    # draw order: stable by z
    for z, (n, b, att, blend) in sorted(order, key=lambda o: o[0]):
        slot(n, b, att, blend)
    AN[f"{lv}_in"], AN[f"{lv}_loop"], AN[f"{lv}_out"] = A_in, A_loop, A_out

def P(name, img, x, y, w, rot=0, frm=None, t0=0.2, loop="float", mirror=False, parent=None, z=3, **kw):
    if frm is None:
        frm = (-900, 0) if x < -150 else (900, 0) if x > 150 else (0, 700 if y > 0 else -700)
    if frm == "pop": frm = (0, 0)
    return dict(name=name, img=img, x=x, y=y, w=w, rot=rot, **{"from": frm}, t0=t0, loop=loop, mirror=mirror, parent=parent, z=z, **kw)

# Layouts traced from the 5 reference comps (ref px, 2000 wide). M() maps ref px -> skeleton units:
# k = scale, (ax, ay) = ref point that lands on skeleton (0, by).
def mapper(k, ay, by, ax=1000):
    return lambda rx, ry: (R((rx - ax) * k), R((ay - ry) * k + by))
def mirror_pair(name, img, M, rx, ry, w, k, rot=0, **kw):
    x, y = M(rx, ry); x2, _ = M(2000 - rx, ry)
    return [P(name + "L", img, x, y, w * k, rot=rot, **kw), P(name + "R", img, x2, y, w * k, rot=-rot, mirror=not kw.pop("mirror", False), **kw)]
def burst_pair(M, rx, ry, w, k, rot, t0):
    x, y = M(rx, ry); x2, _ = M(2000 - rx, ry)
    return [(x, y, rot, w * k, t0, False), (x2, y, -rot, w * k, t0, True)]
def smoke_pair(img, M, rx, ry, w, k, t0):
    x, y = M(rx, ry); x2, _ = M(2000 - rx, ry)
    return [(img, x, y, w * k, t0), (img, x2, y, w * k, t0 + 0.02)]

# ===================================================== WIN  (ref: WIN + smoke column behind + orange bursts L/R)
k = 0.5; M = mapper(k, 800, -20)
_, wy = M(1010, 800)
build_level("win", None, 0, [],
            [],
            burst_pair(M, 330, 560, 640, k, 0, 0.5) + burst_pair(M, 330, 700, 460, k, 25, 0.56), 6,
            win_y=wy, win_w=1450 * k, shake=6)
# ===================================================== CRASH WIN  (ref: CRASH/WIN, exhaust pipes L/R, bursts behind pipes, smoke column, 2 rocks)
k = 0.61; M = mapper(k, 900, -70)
build_level("crash_win", "text_crash", 1050 * k,
            mirror_pair("pipe", "exhaust_pipe", M, 430, 660, 560, k, rot=-12, t0=0.15, loop="wobble", amp=4)
            + mirror_pair("rock", "debris_round", M, 455, 290, 95, k, rot=-30, frm="pop", t0=0.8),
            [],
            burst_pair(M, 400, 380, 640, k, 0, 0.5) + burst_pair(M, 330, 520, 420, k, 20, 0.56), 8,
            main_y=M(995, 590)[1], win_y=M(1035, 900)[1], win_w=830 * k, shake=12)
# ===================================================== SMASH WIN  (ref: plate on top, SMASH/WIN, smoke + bursts L/R, tires bottom L/R, bolts + rocks top)
k = 0.673; M = mapper(k, 690, -70)
build_level("smash_win", "text_smash", 980 * k,
            [P("plate", "plate_top", *M(1000, 250), 880 * k, frm=(0, 700), t0=0.05, z=1.5, amp=3)]
            + mirror_pair("tire", "tire", M, 480, 760, 340, k, t0=0.12, loop="spin", dir=1, z=2.5)
            + [P("rimL", "rim", 0, 0, 205 * k, parent="tireL", t0=0.12, loop="none", z=2.6),
               P("rimR", "rim", 0, 0, 205 * k, parent="tireR", t0=0.12, loop="none", z=2.6)]
            + mirror_pair("bolt", "bolt", M, 445, 65, 120, k, rot=-35, frm="pop", t0=0.78)
            + mirror_pair("rock", "debris_round", M, 430, 180, 100, k, rot=-15, frm="pop", t0=0.86),
            smoke_pair("smoke", M, 390, 400, 420, k, 0.05) + smoke_pair("smoke", M, 430, 620, 320, k, 0.1),
            burst_pair(M, 330, 330, 620, k, 0, 0.5) + burst_pair(M, 400, 560, 480, k, 25, 0.56), 10,
            main_y=M(995, 450)[1], win_y=M(1000, 690)[1], win_w=840 * k, shake=16)
# ===================================================== WRECKAGE WIN  (ref: engine top, brackets L/R, big smoke L/R, bursts radiating, bolts/rocks/shards top corners)
k = 0.555; M = mapper(k, 690, -70)
build_level("wreckage_win", "wreckage", 1370 * k,
            [P("engine", "engine_block", *M(1000, 190), 640 * k, frm=(0, 750), t0=0.05, z=2, loop="wobble", amp=4)]
            + mirror_pair("bracket", "bracket", M, 510, 270, 360, k, rot=-35, t0=0.15, loop="wobble")
            + mirror_pair("bolt", "bolt", M, 300, 60, 95, k, rot=-30, frm="pop", t0=0.78)
            + mirror_pair("rock", "debris_round", M, 430, 95, 115, k, rot=20, frm="pop", t0=0.84)
            + mirror_pair("shard", "shard", M, 290, 155, 80, k, rot=60, frm="pop", t0=0.9),
            smoke_pair("smoke_big", M, 300, 500, 600, k, 0.02) + smoke_pair("smoke", M, 520, 760, 420, k, 0.08),
            burst_pair(M, 560, 170, 620, k, 0, 0.48) + burst_pair(M, 470, 420, 560, k, 15, 0.52) + burst_pair(M, 560, 700, 340, k, 80, 0.56)
            + burst_pair(M, 760, 120, 420, k, -25, 0.6), 14, smoke_a=0.28,
            main_y=M(1000, 440)[1], win_y=M(1000, 690)[1], win_w=770 * k, shake=22)
# ===================================================== TOTAL WIN  (ref: brake disc + chains behind, crossed blades + bumpers, tires L/R, smoke, bursts everywhere, bolts/rocks/shards at sides)
k = 0.83; M = mapper(k, 790, -70)
build_level("total_win", "total", 870 * k,
            [P("disc", "brake_disc", *M(1000, 360), 520 * k, frm=(0, 700), t0=0.05, z=2, loop="spin", amp=3)]
            + mirror_pair("chain", "chain", M, 790, 220, 62, k, rot=35, frm=(0, 600), t0=0.1, loop="wobble", z=1.5)
            + mirror_pair("bumper", "bumper", M, 470, 420, 420, k, rot=-12, t0=0.18, loop="wobble", mirror=True)
            + mirror_pair("blade", "blade", M, 620, 300, 400, k, rot=0, t0=0.24, loop="wobble")
            + mirror_pair("tire", "tire", M, 580, 700, 260, k, t0=0.12, loop="spin", dir=1)
            + [P("rimL", "rim", 0, 0, 155 * k, parent="tireL", t0=0.12, loop="none", z=3.1),
               P("rimR", "rim", 0, 0, 155 * k, parent="tireR", t0=0.12, loop="none", z=3.1)]
            + mirror_pair("bolt", "bolt", M, 310, 640, 90, k, rot=-40, frm="pop", t0=0.8)
            + mirror_pair("shard", "shard", M, 395, 640, 60, k, rot=20, frm="pop", t0=0.86)
            + mirror_pair("rock", "debris_round", M, 330, 705, 90, k, rot=10, frm="pop", t0=0.92),
            smoke_pair("smoke", M, 420, 780, 440, k, 0.05) + smoke_pair("smoke", M, 640, 230, 300, k, 0.1),
            burst_pair(M, 720, 110, 680, k, -30, 0.5), 18, shake=28, explosion=(820, M(1000, 650)[1]), smoke_a=0.28,
            main_y=M(995, 520)[1], win_y=M(1010, 790)[1], win_w=690 * k)

slot("amount", "amount", None, None, "ffffffff"); del S[-1]["attachment"]
json.dump(J, open(os.path.join(out, "win_fx.json"), "w"), indent=1)
print("bones", len(B), "slots", len(S), "anims", list(AN))
