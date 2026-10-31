# Shared Spine 4.2 JSON helpers. Call init(J, img_dir) first.
import os, math
from PIL import Image
bones = slots = skins = anims = None
IMG = None
def init(J, img_dir):
    global bones, slots, skins, anims, IMG
    bones, slots, skins, anims = J["bones"], J["slots"], J["skins"], J["animations"]
    IMG = lambda n: Image.open(os.path.join(img_dir, n + ".png")).size

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

