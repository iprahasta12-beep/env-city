import sys, os
from PIL import Image, ImageFilter
import numpy as np
src, out = sys.argv[1], sys.argv[2]
bg = Image.open(f"{src}/background.png").convert("RGB")
bg.resize((1920, 1080), Image.LANCZOS).save(f"{out}/bg_landscape.png", optimize=True)

# ---- portrait 1080x1920: whole scene scaled (crop x 0..1640), desert + vertical road extended above/below
S = 1080 / 1640; OY = 650
a = np.asarray(bg)
def reflect_tile(patch, W, H):
    p = np.concatenate([patch, patch[:, ::-1]], 1); p = np.concatenate([p, p[::-1]], 0)
    reps = (H // p.shape[0] + 1, W // p.shape[1] + 1, 1)
    return np.tile(p, reps)[:H, :W]
import cv2, random
patch = a[0:285, 0:245].copy()
R_, B_ = patch[:, :, 0].astype(int), patch[:, :, 2].astype(int)
rockm = (((B_ > 45) | (R_ < 190)) * 255).astype(np.uint8)
rockm = cv2.dilate(rockm, np.ones((7, 7), np.uint8))
clean = cv2.inpaint(np.ascontiguousarray(patch[:, :, ::-1]), rockm, 9, cv2.INPAINT_TELEA)[:, :, ::-1]
clean = cv2.GaussianBlur(clean, (0, 0), 1.2)
ground = reflect_tile(clean, 1080, 1920).astype(np.uint8)
canvas = Image.fromarray(ground)
# rock stamps cut from bg (soft alpha from non-orange mask)
full_R, full_B = a[:, :, 0].astype(int), a[:, :, 2].astype(int)
fm = (((full_B > 45) | (full_R < 190)) * 255).astype(np.uint8)
def stamp(x0, y0, x1, y1):
    im = Image.fromarray(a[y0:y1, x0:x1]); mm = cv2.dilate(fm[y0:y1, x0:x1], np.ones((5, 5), np.uint8))
    mm = cv2.GaussianBlur(mm, (0, 0), 1.0)
    return im, Image.fromarray(mm)
ROCKS = [stamp(100, 70, 172, 132), stamp(36, 18, 92, 66), stamp(205, 196, 262, 245), stamp(1010, 22, 1065, 72),
         stamp(14, 136, 40, 162), stamp(160, 140, 186, 166), stamp(42, 205, 64, 227), stamp(1015, 655, 1075, 705)]
random.seed(7)
for band in ((0, 640), (1280, 1920)):
    placed = 0
    while placed < 26:
        x = random.randint(0, 1050); y = random.randint(band[0], band[1] - 40)
        if 430 < x < 680: continue
        big = random.random() < 0.35
        im, mm = ROCKS[random.randint(0, 3)] if big else ROCKS[random.randint(4, 7)]
        sc = random.uniform(0.55, 0.8)
        im2 = im.resize((max(1, int(im.size[0] * sc)), max(1, int(im.size[1] * sc))), Image.LANCZOS)
        mm2 = mm.resize(im2.size, Image.LANCZOS)
        if 440 < x + im2.size[0] and x < 670: continue
        canvas.paste(im2, (x, y), mm2); placed += 1
# road column: bg x 685..995, y 0..270 reflect-tiled vertically
road = a[0:270, 685:995]
road = np.concatenate([road, road[::-1]], 0)
road = np.tile(road, (int(1920 / (road.shape[0] * S)) + 2, 1, 1))
rw = round(310 * S)
road_img = Image.fromarray(road).resize((rw, round(road.shape[0] * S)), Image.LANCZOS)
rx = round(685 * S)
canvas.paste(road_img.crop((0, 0, rw, 1920)), (rx, 0))
scene = bg.crop((0, 0, 1640, 942)).resize((1080, round(942 * S)), Image.LANCZOS)
mask = Image.new("L", scene.size, 255)
m = np.asarray(mask).copy(); F = 14
for i in range(F): m[i, :] = m[-1 - i, :] = int(255 * (i + 1) / (F + 1))
canvas.paste(scene, (0, OY), Image.fromarray(m))
canvas.save(f"{out}/bg_portrait.png", optimize=True)
print("portrait scene y", OY, OY + scene.size[1], "road x", rx, rx + rw)

# ---- art: trim + resize (texture px = landscape 1920 display px)
def trim(im, thr=10):
    al = np.asarray(im)[:, :, 3]; ys, xs = np.where(al > thr)
    return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
spec = {"fan_blade": 140, "fan_hub": 46, "vent_blade": 72, "turbine_top": 148, "alarm_on": 30, "alarm_glow": 120,
        "awning_top": 400, "awning_flap": 400, "windsock": 290, "smoke_1": 110, "smoke_2": 110, "smoke_3": 110,
        "tree_A": 130, "tree_B": 130, "tree_C": 120, "tumbleweed": 76, "tumbleweed_shadow": 100}
os.makedirs(f"{out}/images", exist_ok=True)
for n, w in spec.items():
    im = trim(Image.open(f"{src}/{n}.png").convert("RGBA"), 40 if n in ("awning_top", "awning_flap", "alarm_on") else 10)
    h = max(1, round(im.size[1] * w / im.size[0]))
    im.resize((w, h), Image.LANCZOS).save(f"{out}/images/{n}.png", optimize=True)
    print(n, im.size, "->", (w, h))
