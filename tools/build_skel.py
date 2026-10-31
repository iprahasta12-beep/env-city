# Build small_city env.json = base env.json (city skins) + new skins.
# All motion is Spine keys. Coordinates: Spine bone space (y-up), px = landscape 1920 display px.
import json, math, sys, os, copy
from PIL import Image

base_json, img_dir, out_json = sys.argv[1:4]
J = json.load(open(base_json))
J["skeleton"]["hash"] = "envsmallcity"
IMG = lambda n: Image.open(os.path.join(img_dir, n + ".png")).size

bones, slots, skins, anims = J["bones"], J["slots"], J["skins"], J["animations"]

def bone(name, parent="root", **kw):
    bones.append({"name": name, "parent": parent, **kw})

def slot(name, b, att=None, blend=None, color=None):
    s = {"name": name, "bone": b}
    if att: s["attachment"] = att
    if blend: s["blend"] = blend
    if color: s["color"] = color
    slots.append(s)

def region(img, w=None, h=None, x=0, y=0, rot=0, path=None):
    """Region attachment; width/height = texture size, display size via scaleX/scaleY."""
    tw, th = IMG(img)
    a = {"x": round(x, 2), "y": round(y, 2), "width": tw, "height": th}
    if path: a["path"] = path
    if rot: a["rotation"] = rot
    sx = w / tw if w else None
    sy = h / th if h else None
    if sx is None: sx = sy or 1
    if sy is None: sy = sx
    if abs(sx - 1) > 1e-4: a["scaleX"] = round(sx, 4)
    if abs(sy - 1) > 1e-4: a["scaleY"] = round(sy, 4)
    return a

def skin(name, att):
    skins.append({"name": name, "attachments": att})

def clip(end, w, h, x=0, y=0):
    return {"type": "clipping", "end": end, "vertexCount": 4,
            "vertices": [x - w/2, y - h/2, x + w/2, y - h/2, x + w/2, y + h/2, x - w/2, y + h/2],
            "color": "ce3a3aff"}

R = lambda v: round(v, 4)
def ease1(t0, v0, t1, v1, k=0.4):
    dt = t1 - t0
    return [R(t0 + dt * k), R(v0), R(t1 - dt * k), R(v1)]
def ease2(t0, a0, t1, a1, k=0.4):  # translate / scale (x,y)
    return ease1(t0, a0[0], t1, a1[0], k) + ease1(t0, a0[1], t1, a1[1], k)

def keys1(pts, ease=True, k=0.4):
    """pts: [(t,v)] -> value timeline with ease-in-out curves."""
    out = []
    for i, (t, v) in enumerate(pts):
        e = {"time": R(t), "value": R(v)} if t else {"value": R(v)}
        if ease and i < len(pts) - 1 and pts[i + 1][1] != v:
            e["curve"] = ease1(t, v, pts[i + 1][0], pts[i + 1][1], k)
        out.append(e)
    return out

def keys2(pts, ease=True, k=0.4):
    out = []
    for i, (t, x, y) in enumerate(pts):
        e = {"time": R(t), "x": R(x), "y": R(y)} if t else {"x": R(x), "y": R(y)}
        if ease and i < len(pts) - 1 and (pts[i + 1][1], pts[i + 1][2]) != (x, y):
            n = pts[i + 1]
            e["curve"] = ease2(t, (x, y), n[0], (n[1], n[2]), k)
        out.append(e)
    return out

def easein2(t0, a0, t1, a1):
    return [R(t0 + (t1 - t0) * 0.42), R(a0[0]), R(t1), R(a1[0]), R(t0 + (t1 - t0) * 0.42), R(a0[1]), R(t1), R(a1[1])]
def easeout2(t0, a0, t1, a1):
    return [R(t0), R(a0[0]), R(t0 + (t1 - t0) * 0.58), R(a1[0]), R(t0), R(a0[1]), R(t0 + (t1 - t0) * 0.58), R(a1[1])]

def lin1(pts):
    return [({"time": R(t), "value": R(v)} if t else {"value": R(v)}) for t, v in pts]

def stepped1(pts):
    out = []
    for t, v in pts:
        e = {"time": R(t), "value": R(v)} if t else {"value": R(v)}
        e["curve"] = "stepped"
        out.append(e)
    return out

def att_keys(pts):
    return [({"time": R(t), "name": n} if t else {"name": n}) for t, n in pts]

def spin_keys(total_deg, dur, n=4):
    return [({"time": R(dur * i / n), "value": R(total_deg * i / n)} if i else {"value": 0}) for i in range(n + 1)]

# ---------------------------------------------------------------- colors
COL = {"red": "ff3b30", "orange": "ffa424", "white": "fff1c4", "green": "4dff7a", "blue": "45b4ff"}

# ================================================================ 1. LIGHT (single)
bone("light")
bone("light_glow", "light")
for c, hexc in COL.items():
    slot(f"light_glow_{c}", "light_glow", "light_glow", "additive", hexc + "ff")
for c, hexc in COL.items():
    slot(f"light_dot_{c}", "light", "light_dot", "additive" if c != "white" else None, hexc + "ff")
for c in COL:
    skin(f"light_{c}", {
        f"light_glow_{c}": {"light_glow": region("light_glow", w=58)},
        f"light_dot_{c}": {"light_dot": region("light_dot", w=13)},
    })
def light_anim(alpha_fn_keys, glow_scale=None, stepped=False):
    sl = {}
    for c in COL:
        for kind in ("glow", "dot"):
            sl[f"light_{kind}_{c}"] = {"alpha": stepped1(alpha_fn_keys) if stepped else keys1(alpha_fn_keys)}
    a = {"slots": sl}
    if glow_scale:
        a["bones"] = {"light_glow": {"scale": keys2(glow_scale)}}
    return a
anims["light_blink"] = light_anim([(0, 1), (0.5, 0.12), (1, 1)], stepped=True)
anims["light_pulse"] = light_anim([(0, 0.35), (1, 1), (2, 0.35)],
                                  [(0, 0.8, 0.8), (1, 1.15, 1.15), (2, 0.8, 0.8)])
anims["light_flicker"] = light_anim([(0, 1), (0.08, 0.3), (0.16, 1), (0.9, 1), (0.98, 0.5), (1.06, 1), (2.4, 1)], stepped=True)

# ================================================================ chase helper (multi-light rigs)
def chase_alpha(i, n, dur, lo=0.18, tail=3.0):
    pts = []
    for k in range(n + 1):
        d = (k - i) % n
        a = max(lo, 1 - d / tail) if d < tail else lo
        pts.append((dur * k / n, a))
    return lin1(pts)

# ================================================================ 2. HELIPAD RING (12 orange lights, chase)
RING_N, RING_R = 12, 152
bone("ring")
for i in range(RING_N):
    ang = math.pi / 2 - 2 * math.pi * i / RING_N   # start top, clockwise
    bone(f"ring_{i}", "ring", x=R(RING_R * math.cos(ang)), y=R(RING_R * math.sin(ang)))
for i in range(RING_N):
    slot(f"ring_glow_{i}", f"ring_{i}", "light_glow", "additive", COL["orange"] + "ff")
for i in range(RING_N):
    slot(f"ring_dot_{i}", f"ring_{i}", "light_dot", "additive", COL["orange"] + "ff")
ra = {}
for i in range(RING_N):
    ra[f"ring_glow_{i}"] = {"light_glow": region("light_glow", w=46)}
    ra[f"ring_dot_{i}"] = {"light_dot": region("light_dot", w=11)}
skin("helipad_ring", ra)
anims["ring_chase"] = {"slots": {**{f"ring_glow_{i}": {"alpha": chase_alpha(i, RING_N, 1.8)} for i in range(RING_N)},
                                 **{f"ring_dot_{i}": {"alpha": chase_alpha(i, RING_N, 1.8, lo=0.35)} for i in range(RING_N)}}}

# ================================================================ 3. LAMP ROW (canopy lamps, root = leftmost lamp)
LAMP_N, LAMP_DX = 8, 62
bone("lamps")
for i in range(LAMP_N):
    bone(f"lamp_{i}", "lamps", x=i * LAMP_DX)
for i in range(LAMP_N):
    slot(f"lamp_glow_{i}", f"lamp_{i}", "light_glow", "additive", COL["white"] + "ff")
for i in range(LAMP_N):
    slot(f"lamp_dot_{i}", f"lamp_{i}", "light_dot", "additive", COL["white"] + "ff")
for n in (8, 6):
    la = {}
    for i in range(n):
        la[f"lamp_glow_{i}"] = {"light_glow": region("light_glow", w=60)}
        la[f"lamp_dot_{i}"] = {"light_dot": region("light_dot", w=12)}
    skin(f"lamp_row{n}", la)
anims["lamp_chase"] = {"slots": {**{f"lamp_glow_{i}": {"alpha": chase_alpha(i, LAMP_N, 2.4, lo=0.3, tail=3)} for i in range(LAMP_N)},
                                 **{f"lamp_dot_{i}": {"alpha": chase_alpha(i, LAMP_N, 2.4, lo=0.5, tail=3)} for i in range(LAMP_N)}}}
anims["lamp_pulse"] = {"slots": {**{f"lamp_glow_{i}": {"alpha": keys1([(0, 0.45), (1.2, 1), (2.4, 0.45)])} for i in range(LAMP_N)},
                                 **{f"lamp_dot_{i}": {"alpha": keys1([(0, 0.6), (1.2, 1), (2.4, 0.6)])} for i in range(LAMP_N)}}}

# ================================================================ 4. GLINT (clip = panel, streak sweeps)
bone("glint")
bone("glint_streak", "glint", rotation=-8)
slot("glint_clip", "glint", "clip")
slot("glint_streak", "glint_streak", "glint_streak", "additive", "ffffffff")
GLINTS = {  # skin: (w, h) of glass panel
    "glint_square": (62, 62), "glint_wide": (114, 58), "glint_canopy": (438, 68),
    "glint_canopy_short": (204, 56), "glint_small": (86, 44), "glint_tiny": (64, 36),
}
for n, (w, h) in GLINTS.items():
    sh = h * 1.9
    skin(n, {"glint_clip": {"clip": clip("glint_streak", w, h)},
             "glint_streak": {"glint_streak": region("glint_streak", h=sh)}})
def glint_anim(rng, sweep, total):
    return {"bones": {"glint_streak": {"translate": [
                {"x": -rng, "y": 0, "curve": ease2(0, (-rng, 0), sweep, (rng, 0), 0.25)},
                {"time": sweep, "x": rng, "y": 0, "curve": "stepped"},
                {"time": total, "x": -rng, "y": 0}]}},
            "slots": {"glint_streak": {"alpha": [{"value": 0.9}, {"time": total, "value": 0.9}]}}}
anims["glint_sweep"] = glint_anim(270, 1.3, 5.0)
anims["glint_sweep_small"] = glint_anim(85, 0.7, 4.0)

# ================================================================ 5. BILLBOARD (3 screens crossfade + scanline, clipped)
bone("billboard")
bone("bb_screens", "billboard")
bone("bb_scan", "billboard")
slot("bb_clip", "billboard", "clip")
for i in (1, 2, 3):
    slot(f"bb_screen{i}", "bb_screens", f"screen_0{i}")
slot("bb_scan", "bb_scan", "scanline", "additive", "ffffff66")
slot("bb_frame", "billboard", "screen_frame")
for n, (cw, ch, sw, frame) in {"billboard": (242, 104, 262, True), "billboard_square": (148, 150, 376, False)}.items():
    a = {"bb_clip": {"clip": clip("bb_scan", cw, ch)}}
    for i in (1, 2, 3):
        a[f"bb_screen{i}"] = {f"screen_0{i}": region(f"screen_0{i}", w=sw, h=sw / 2.4)}
    a["bb_scan"] = {"scanline": region("scanline", w=cw + 20, h=6)}
    if frame:
        a["bb_frame"] = {"screen_frame": region("screen_frame", w=cw + 26, h=ch + 16)}
    skin(n, a)
T = 7.5
anims["billboard_cycle"] = {
    "slots": {
        "bb_screen1": {"alpha": [{"value": 1}, {"time": T, "value": 1}]},
        "bb_screen2": {"alpha": keys1([(0, 0), (2.0, 0), (2.5, 1), (7.0, 1), (7.5, 0)])},
        "bb_screen3": {"alpha": keys1([(0, 0), (4.5, 0), (5.0, 1), (7.0, 1), (7.5, 0)])},
        "bb_scan": {"alpha": keys1([(0, 0.25), (1.25, 0.5), (2.5, 0.25), (3.75, 0.5), (5.0, 0.25), (6.25, 0.5), (7.5, 0.25)])},
    },
    "bones": {
        "bb_scan": {"translate": [{"x": 0, "y": 60}, {"time": 2.5, "x": 0, "y": -60, "curve": "stepped"}, {"time": 2.5001, "x": 0, "y": 60},
                                  {"time": 5.0, "x": 0, "y": -60, "curve": "stepped"}, {"time": 5.0001, "x": 0, "y": 60}, {"time": 7.5, "x": 0, "y": -60}]},
        "bb_screens": {"translate": keys2([(0, 6, 0), (3.75, -6, 0), (7.5, 6, 0)]),
                       "scale": keys2([(0, 1, 1), (3.75, 1.04, 1.04), (7.5, 1, 1)])},
    },
}

# ================================================================ 6. BUS (front = -x)
bone("bus")
bone("bus_body", "bus")
slot("bus_shadow", "bus", "bus_shadow", None, "ffffffb3")
slot("bus_body", "bus_body", "bus_body")
for c in ("blue", "red"):
    skin(f"bus_{c}", {"bus_shadow": {"bus_shadow": region("bus_shadow", w=206, h=86, x=5, y=-6)},
                      "bus_body": {"bus_body": region(f"bus_body_{c}", w=190, path=f"bus_body_{c}")}})
def shake(t0, t1, step=0.2, amp=0.7):
    pts, t, s = [], t0, 1
    while t < t1 - 1e-6:
        pts.append((t, 0, s * amp)); s = -s; t += step
    pts.append((t1, 0, pts[0][2]))
    return pts
anims["bus_idle"] = {"bones": {"bus_body": {"translate": keys2([(0, 0, 0.7), (0.2, 0, -0.7), (0.4, 0, 0.7)]),
                                            "scale": keys2([(0, 1, 1), (0.2, 1.004, 1.012), (0.4, 1, 1)])}}}
anims["bus_drive_out"] = {
    "bones": {"bus": {"translate": [{"x": 0, "y": 0, "curve": easein2(0, (0, 0), 2, (-300, 0))}, {"time": 2, "x": -300, "y": 0}]},
              "bus_body": {"translate": keys2(shake(0, 2, 0.1, 0.5), ease=False)}},
    "slots": {"bus_body": {"alpha": keys1([(0, 1), (1.1, 1), (2, 0)])},
              "bus_shadow": {"alpha": keys1([(0, 0.7), (1.1, 0.7), (2, 0)])}}}
anims["bus_drive_in"] = {
    "bones": {"bus": {"translate": [{"x": 300, "y": 0, "curve": easeout2(0, (300, 0), 2, (0, 0))}, {"time": 2, "x": 0, "y": 0}]},
              "bus_body": {"translate": keys2(shake(0, 2, 0.1, 0.5), ease=False)}},
    "slots": {"bus_body": {"alpha": keys1([(0, 0), (0.9, 1), (2, 1)])},
              "bus_shadow": {"alpha": keys1([(0, 0), (0.9, 0.7), (2, 0.7)])}}}
# cycle 12s: idle 0-4 · out 4-6 · gone 6-8 · in 8-10 · idle 10-12
anims["bus_cycle"] = {
    "bones": {"bus": {"translate": [{"x": 0, "y": 0, "curve": "stepped"}, {"time": 4, "x": 0, "y": 0, "curve": easein2(4, (0, 0), 6, (-300, 0))},
                                    {"time": 6, "x": -300, "y": 0, "curve": "stepped"}, {"time": 8, "x": 300, "y": 0, "curve": easeout2(8, (300, 0), 10, (0, 0))},
                                    {"time": 10, "x": 0, "y": 0}, {"time": 12, "x": 0, "y": 0}]},
              "bus_body": {"translate": keys2(shake(0, 12, 0.2, 0.6), ease=False)}},
    "slots": {"bus_body": {"alpha": keys1([(0, 1), (5.1, 1), (6, 0), (8, 0), (8.9, 1), (12, 1)])},
              "bus_shadow": {"alpha": keys1([(0, 0.7), (5.1, 0.7), (6, 0), (8, 0), (8.9, 0.7), (12, 0.7)])}}}

# ================================================================ 7. HELICOPTER (root = main rotor hub)
bone("heli")
bone("heli_shadow", "heli", x=10, y=-12)
bone("heli_lift", "heli")
bone("heli_body", "heli_lift")
bone("heli_tail_rotor", "heli_body", x=171, y=0)
bone("heli_rotor", "heli_lift")
slot("heli_shadow", "heli_shadow", "heli_shadow", None, "ffffff8c")
slot("heli_body", "heli_body", "heli_body")
slot("heli_tail_rotor", "heli_tail_rotor", "tail_rotor")
slot("heli_rotor", "heli_rotor", "rotor_blade")
skin("helicopter", {
    "heli_shadow": {"heli_shadow": region("heli_shadow", w=380, x=65)},
    "heli_body": {"heli_body": region("heli_body", w=300, x=46)},
    "heli_tail_rotor": {"tail_rotor": region("tail_rotor", w=58), "tail_rotor_blur": region("tail_rotor_blur", w=64)},
    "heli_rotor": {"rotor_blade": region("rotor_blade", w=230), "rotor_blur": region("rotor_blur", w=326)},
})
def omega_keys(omega_pts, dur, step=0.05, total_round=360):
    """Integrate angular speed (deg/s, piecewise-linear in time) -> rotate keys; total snapped to multiple of 360."""
    def w(t):
        for (t0, w0), (t1, w1) in zip(omega_pts, omega_pts[1:]):
            if t0 <= t <= t1: return w0 + (w1 - w0) * (t - t0) / (t1 - t0) if t1 > t0 else w1
        return omega_pts[-1][1]
    n = int(round(dur / step)); ang = [0.0]
    for i in range(n):
        t = i * step; ang.append(ang[-1] + (w(t) + 4 * w(t + step / 2) + w(t + step)) / 6 * step)
    tot = ang[-1]; snap = round(tot / total_round) * total_round or total_round
    return [({"time": R(i * step), "value": R(-a * snap / tot)} if i else {"value": 0}) for i, a in enumerate(ang)]
anims["heli_idle"] = {"bones": {"heli_rotor": {"rotate": spin_keys(-360, 1.6)},
                                "heli_tail_rotor": {"rotate": spin_keys(-720, 1.6)},
                                "heli_body": {"scale": keys2([(0, 1, 1), (0.8, 1.004, 1.004), (1.6, 1, 1)])}}}
anims["heli_spin_fast"] = {
    "slots": {"heli_rotor": {"attachment": att_keys([(0, "rotor_blur")])}, "heli_tail_rotor": {"attachment": att_keys([(0, "tail_rotor_blur")])}},
    "bones": {"heli_rotor": {"rotate": spin_keys(-360, 0.3)}, "heli_tail_rotor": {"rotate": spin_keys(-720, 0.3)},
              "heli_body": {"translate": keys2([(0, 0, 0.6), (0.1, 0.4, -0.5), (0.2, -0.4, 0.3), (0.3, 0, 0.6)], ease=False)}}}
# takeoff 4s one-shot: spin up 0-1.6 (blur at 1.2), lift 1.6-4
anims["heli_takeoff"] = {
    "slots": {"heli_rotor": {"attachment": att_keys([(0, "rotor_blade"), (1.2, "rotor_blur")])},
              "heli_tail_rotor": {"attachment": att_keys([(0, "tail_rotor"), (1.2, "tail_rotor_blur")])},
              "heli_shadow": {"alpha": keys1([(0, 0.55), (1.6, 0.55), (4, 0.18)])}},
    "bones": {"heli_rotor": {"rotate": omega_keys([(0, 225), (1.4, 1200), (4, 1200)], 4)},
              "heli_tail_rotor": {"rotate": omega_keys([(0, 450), (1.4, 2400), (4, 2400)], 4)},
              "heli_lift": {"scale": keys2([(0, 1, 1), (1.6, 1, 1), (4, 1.35, 1.35)], k=0.45)},
              "heli_shadow": {"translate": keys2([(0, 10, -12), (1.6, 10, -12), (4, 70, -80)], k=0.45),
                              "scale": keys2([(0, 1, 1), (1.6, 1, 1), (4, 0.8, 0.8)])}}}
anims["heli_land"] = {
    "slots": {"heli_rotor": {"attachment": att_keys([(0, "rotor_blur"), (3.0, "rotor_blade")])},
              "heli_tail_rotor": {"attachment": att_keys([(0, "tail_rotor_blur"), (3.0, "tail_rotor")])},
              "heli_shadow": {"alpha": keys1([(0, 0.18), (2.4, 0.55)])}},
    "bones": {"heli_rotor": {"rotate": omega_keys([(0, 1200), (2.4, 1200), (4, 225)], 4)},
              "heli_tail_rotor": {"rotate": omega_keys([(0, 2400), (2.4, 2400), (4, 450)], 4)},
              "heli_lift": {"scale": keys2([(0, 1.35, 1.35), (2.4, 1, 1)], k=0.45)},
              "heli_shadow": {"translate": keys2([(0, 70, -80), (2.4, 10, -12)], k=0.45), "scale": keys2([(0, 0.8, 0.8), (2.4, 1, 1)])}}}
# heli_cycle: idle 0-20 (rotor spins up 18-20) · 20 lift + turn · 23 fly away · 27-47 gone (20s) · 47 fly back
# · 51 turn to pad · 52.5 descend · 54.5 rotor spin-down · 56 loop
HC = 56
S0, L0, F0, G0, G1, B1, D0, D1 = 18, 20, 23, 27, 47, 51, 52.5, 54.5
FLY = (760, 560)       # skeleton units (y-up): away to upper-right (off frame)
FX, FY = FLY
anims["heli_cycle"] = {
    "slots": {"heli_rotor": {"attachment": att_keys([(0, "rotor_blade"), (19.4, "rotor_blur"), (55.2, "rotor_blade")])},
              "heli_tail_rotor": {"attachment": att_keys([(0, "tail_rotor"), (19.4, "tail_rotor_blur"), (55.2, "tail_rotor")])},
              "heli_shadow": {"alpha": keys1([(0, 0.55), (L0, 0.55), (F0, 0.2), (F0 + 2, 0), (B1 - 2, 0), (B1, 0.2), (D1, 0.55), (HC, 0.55)])},
              "heli_body": {"alpha": [{"value": 1, "curve": "stepped"}, {"time": G0, "value": 0, "curve": "stepped"}, {"time": G1, "value": 1}]},
              "heli_rotor": {"alpha": [{"value": 1, "curve": "stepped"}, {"time": G0, "value": 0, "curve": "stepped"}, {"time": G1, "value": 1}]},
              "heli_tail_rotor": {"alpha": [{"value": 1, "curve": "stepped"}, {"time": G0, "value": 0, "curve": "stepped"}, {"time": G1, "value": 1}]}},
    "bones": {
        "heli_rotor": {"rotate": omega_keys([(0, 0), (S0, 0), (19.6, 1200), (D1, 1200), (HC, 0)], HC, step=0.1)},
        "heli_tail_rotor": {"rotate": omega_keys([(0, 0), (S0, 0), (19.6, 2400), (D1, 2400), (HC, 0)], HC, step=0.1)},
        "heli_lift": {
            "scale": keys2([(0, 1, 1), (L0, 1, 1), (F0, 1.35, 1.35), (G0, 1.6, 1.6), (G1, 1.6, 1.6), (B1, 1.35, 1.35), (D0, 1.35, 1.35), (D1, 1, 1), (HC, 1, 1)], k=0.45),
            "translate": [{"x": 0, "y": 0, "curve": "stepped"}, {"time": F0, "x": 0, "y": 0, "curve": easein2(F0, (0, 0), G0, FLY)},
                          {"time": G0, "x": FX, "y": FY, "curve": "stepped"}, {"time": G1, "x": FX, "y": FY, "curve": easeout2(G1, FLY, B1, (0, 0))},
                          {"time": B1, "x": 0, "y": 0}, {"time": HC, "x": 0, "y": 0}],
            "rotate": [{"value": 0, "curve": "stepped"}, {"time": L0 + 0.5, "value": 0, "curve": ease1(L0 + 0.5, 0, F0, -143.6)},
                       {"time": F0, "value": -143.6, "curve": "stepped"}, {"time": G1 - 0.01, "value": -143.6, "curve": "stepped"},
                       {"time": G1, "value": 36.4, "curve": "stepped"}, {"time": B1, "value": 36.4, "curve": ease1(B1, 36.4, D0, 0)},
                       {"time": D0, "value": 0}, {"time": HC, "value": 0}]},
        "heli_shadow": {
            "translate": [{"x": 10, "y": -12, "curve": "stepped"}, {"time": L0, "x": 10, "y": -12, "curve": ease2(L0, (10, -12), F0, (70, -80), 0.45)},
                          {"time": F0, "x": 70, "y": -80, "curve": easein2(F0, (70, -80), G0, (70 + FX, -80 + FY))},
                          {"time": G0, "x": 70 + FX, "y": -80 + FY, "curve": "stepped"},
                          {"time": G1, "x": 70 + FX, "y": -80 + FY, "curve": easeout2(G1, (70 + FX, -80 + FY), B1, (70, -80))},
                          {"time": B1, "x": 70, "y": -80, "curve": "stepped"}, {"time": D0, "x": 70, "y": -80, "curve": ease2(D0, (70, -80), D1, (10, -12), 0.45)},
                          {"time": D1, "x": 10, "y": -12}, {"time": HC, "x": 10, "y": -12}],
            "scale": keys2([(0, 1, 1), (L0, 1, 1), (F0, 0.8, 0.8), (D0, 0.8, 0.8), (D1, 1, 1), (HC, 1, 1)]),
            "rotate": [{"value": 0, "curve": "stepped"}, {"time": L0 + 0.5, "value": 0, "curve": ease1(L0 + 0.5, 0, F0, -143.6)},
                       {"time": F0, "value": -143.6, "curve": "stepped"}, {"time": G1, "value": 36.4, "curve": "stepped"},
                       {"time": B1, "value": 36.4, "curve": ease1(B1, 36.4, D0, 0)}, {"time": D0, "value": 0}, {"time": HC, "value": 0}]},
        "heli_body": {"translate": keys2([(0, 0, 0), (19.5, 0, 0), (19.6, 0.5, 0.4), (19.7, -0.4, -0.3), (19.8, 0, 0), (HC, 0, 0)], ease=False)},
    }}
anims["bus_static"] = {"bones": {"bus": {"translate": [{"x": 0, "y": 0}, {"time": 1, "x": 0, "y": 0}]}}}

# ================================================================ 8. ANTENNA (tower + 2 dishes + beacon)
bone("antenna")
bone("dish_l", "antenna", x=-22, y=4)
bone("dish_r", "antenna", x=22, y=4)
bone("antenna_beacon", "antenna", y=2)
bone("antenna_beacon_glow", "antenna_beacon")
slot("antena_tower", "antenna", "antena_tower")
slot("dish_left", "dish_l", "dish_left")
slot("dish_right", "dish_r", "dish_right")
slot("antenna_glow", "antenna_beacon_glow", "light_glow", "additive", COL["red"] + "ff")
slot("antenna_dot", "antenna_beacon", "light_dot", "additive", COL["red"] + "ff")
skin("antenna", {
    "antena_tower": {"antena_tower": region("antena_tower", w=86)},
    "dish_left": {"dish_left": region("dish_left", w=34, x=-12)},     # pivot = mount (right edge)
    "dish_right": {"dish_right": region("dish_right", w=34, x=12)},   # pivot = mount (left edge)
    "antenna_glow": {"light_glow": region("light_glow", w=62)},
    "antenna_dot": {"light_dot": region("light_dot", w=12)},
})
blink3 = [(0, 1), (0.5, 0.1), (1, 1), (1.5, 0.1), (2, 1), (2.5, 0.1), (3, 1)]
anims["antenna_idle"] = {
    "bones": {"dish_l": {"rotate": keys1([(0, -4), (1.5, 4), (3, -4)])},
              "dish_r": {"rotate": keys1([(0, 3), (1.5, -3), (3, 3)])},
              "antenna_beacon_glow": {"scale": keys2([(0, 1.1, 1.1), (0.5, 0.8, 0.8), (1, 1.1, 1.1), (1.5, 0.8, 0.8), (2, 1.1, 1.1), (2.5, 0.8, 0.8), (3, 1.1, 1.1)])}},
    "slots": {"antenna_glow": {"alpha": stepped1(blink3)}, "antenna_dot": {"alpha": stepped1(blink3)}}}

# ================================================================ 9. LONG FLAG (mesh wave, root = pole center)
bone("flag_long")
slot("flag_long_cloth", "flag_long", "flag_long")
slot("flag_pole", "flag_long", "flag_pole")
COLS_, ROWS_ = 8, 3
BASE_FLAG = [x for x in J["skins"] if x["name"] == "flag"][0]["attachments"]["flag_cloth"]["flag_cloth"]
def grid_mesh2(w, h, x0=2):
    m = {"type": "mesh", "uvs": BASE_FLAG["uvs"], "triangles": BASE_FLAG["triangles"], "hull": BASE_FLAG["hull"]}
    uv = BASE_FLAG["uvs"]
    m["vertices"] = [v for k in range(0, len(uv), 2) for v in (R(x0 + uv[k] * w), R(h / 2 - uv[k + 1] * h))]
    if "edges" in BASE_FLAG: m["edges"] = BASE_FLAG["edges"]
    return m
def grid_mesh(w, h, x0=2):
    xs = [x0 + w * i / COLS_ for i in range(COLS_ + 1)]
    ys = [h / 2 - h * j / ROWS_ for j in range(ROWS_ + 1)]
    verts, uvs = [], []
    for j in range(ROWS_ + 1):
        for i in range(COLS_ + 1):
            verts += [R(xs[i]), R(ys[j])]; uvs += [R(i / COLS_), R(j / ROWS_)]
    tris = []
    for j in range(ROWS_):
        for i in range(COLS_):
            a = j * (COLS_ + 1) + i; b = a + 1; c = a + COLS_ + 1; d = c + 1
            tris += [a, b, d, a, d, c]
    hull = 2 * (COLS_ + ROWS_)
    return {"type": "mesh", "uvs": uvs, "triangles": tris, "vertices": verts, "hull": hull}, xs, ys
# hull must list boundary vertices first in Spine; we skip hull edges by giving hull=0-equivalent: use full count edges off
FW = 104
for c in ("red", "blue"):
    m = grid_mesh2(FW, IMG(f"flag_{c}")[1] * FW / IMG(f"flag_{c}")[0])
    tw, th = IMG(f"flag_{c}")
    m["width"], m["height"], m["path"] = tw, th, f"flag_{c}"
    skin(f"flag_long_{c}", {"flag_long_cloth": {"flag_long": m},
                            "flag_pole": {"flag_pole": region("flag_pole", w=28)}})
def flag_deform(t, T, w, h):
    vs = []
    lam = w * 0.9
    uv = BASE_FLAG["uvs"]
    for k in range(0, len(uv), 2):
            u = uv[k]
            ph = 2 * math.pi * (t / T) - 2 * math.pi * (u * w) / lam
            dy = 3.6 * u ** 0.8 * math.sin(ph)
            dx = -2.2 * u * (1 - math.cos(ph)) * 0.5
            vs += [R(dx), R(dy)]
    return vs
FT, FN = 1.4, 12
fa = {}
for c in ("red", "blue"):
    th = IMG(f"flag_{c}")[1]
    fa[f"flag_long_{c}"] = {"flag_long_cloth": {"flag_long": {"deform": [
        ({"time": R(FT * k / FN), "vertices": flag_deform(FT * k / FN, FT, FW, th)} if k else {"vertices": flag_deform(0, FT, FW, th)})
        for k in range(FN + 1)]}}}
anims["flag_long_wave"] = {"attachments": fa}

exec(open(os.path.join(os.path.dirname(__file__), "jungle.py")).read())

json.dump(J, open(out_json, "w"), indent=1)
print("bones", len(bones), "slots", len(slots), "skins", len(skins), "anims", len(anims))
