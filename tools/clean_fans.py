# Paint out static fan blades in the bg (clean plate) so the Spine blade is the only one.
import sys, json, math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
bgp, plp, layout = sys.argv[1:4]
pl = json.load(open(plp))[layout]
im = Image.open(bgp).convert("RGB"); a = np.asarray(im).astype(float); lum = a.mean(2)
out = im.copy()
for it in pl["items"]:
    if it["skin"] != "fan": continue
    cx, cy = it["x"], it["y"]
    # refine center: centroid of dark pixels in window
    r0 = int(min(70, max(20, 1.4 * it["scale"] * 75)))
    win = lum[cy-r0:cy+r0, cx-r0:cx+r0]
    rs = []
    for ang in np.linspace(0, 2*math.pi, 36, endpoint=False):
        r, run = r0, 0
        while r > 3:
            x, y = int(cx + r*math.cos(ang)), int(cy + r*math.sin(ang))
            run = run + 1 if lum[y, x] < 80 else 0
            if run >= 5: break
            r -= 1
        rs.append(r + 4)
    rs = np.array(rs)
    # center correction from opposite radii
    dx = np.mean([(rs[i] - rs[(i+18) % 36]) * math.cos(2*math.pi*i/36) for i in range(18)])
    dy = np.mean([(rs[i] - rs[(i+18) % 36]) * math.sin(2*math.pi*i/36) for i in range(18)])
    ncx, ncy = (cx + dx, cy + dy) if abs(dx) < 3 and abs(dy) < 3 else (cx, cy)
    R = float(np.median(rs))
    rin = R - 4  # keep the dark rim/ring edge
    # dark disc color sampled near rim
    ring = []
    for ang in np.linspace(0, 2*math.pi, 72, endpoint=False):
        x, y = int(ncx + (R-3)*math.cos(ang)), int(ncy + (R-3)*math.sin(ang)); ring.append(a[y, x])
    col = np.median(np.array(ring), 0)
    col = tuple(int(c) for c in np.minimum(col, 45))
    # radial gradient disc (slightly lighter center), soft edge
    S = 4; size = int(rin*2*S)+4
    disc = Image.new("RGBA", (size, size), (0,0,0,0)); d = ImageDraw.Draw(disc)
    steps = 24
    for k in range(steps):
        rr = rin*S*(1 - k/steps); t = k/steps
        c = tuple(int(col[i] + (60-col[i])*0.35*t*t) for i in range(3))
        d.ellipse([size/2-rr, size/2-rr, size/2+rr, size/2+rr], fill=c+(255,))
    disc = disc.resize((size//S, size//S), Image.LANCZOS)
    out.paste(disc, (int(round(ncx - disc.size[0]/2)), int(round(ncy - disc.size[1]/2))), disc)
    it["x"], it["y"] = int(round(ncx)), int(round(ncy))
    it["_r"] = round(R, 1)
    print(it["name"], (cx, cy), "->", (it["x"], it["y"]), "R", R)
out.save(bgp, optimize=True)
full = json.load(open(plp)); 
for i, it in enumerate(full[layout]["items"]):
    m = [p for p in pl["items"] if p["name"] == it["name"]][0]
    if it["skin"] == "fan":
        it["x"], it["y"] = m["x"], m["y"]
        it["scale"] = round(m.pop("_r") * 2 / 150, 3)  # blade 160px (tip dia ~150) -> fill disc
json.dump(full, open(plp, "w"), indent=1)
