import sys, os, shutil, json
from PIL import Image
import numpy as np
src, base_img, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
for f in os.listdir(base_img):
    shutil.copy(os.path.join(base_img, f), os.path.join(out, f))
def trim(im, thr=10):
    a = np.asarray(im)[:,:,3]
    ys, xs = np.where(a > thr)
    return im.crop((xs.min(), ys.min(), xs.max()+1, ys.max()+1))
# name: (width, height or None)   — texture px = display px in landscape 1920
spec = {
 "heli_body": (300,None), "heli_shadow": (300,None), "rotor_blade": (230,None), "rotor_blur": (330,None),
 "tail_rotor": (62,None), "tail_rotor_blur": (66,None),
 "bus_body_blue": (190,None), "bus_body_red": (190,None), "bus_shadow": (210,104),
 "antena_tower": (86,None), "dish_left": (34,None), "dish_right": (34,None),
 "flag_red": (104,None), "flag_blue": (104,None), "flag_pole": (30,None),
 "screen_01": (360,150), "screen_02": (360,150), "screen_03": (360,150), "screen_frame": (272,None),
 "scanline": (300,None), "glint_streak": (70,None), "light_dot": (32,None), "light_glow": (128,None),
}
info = {}
for n,(w,h) in spec.items():
    im = Image.open(os.path.join(src, n+".png")).convert("RGBA")
    if n.startswith("screen_0"): im = im.crop(im.getbbox()) if im.getbbox() else im
    else: im = trim(im, 40 if n in ("light_dot","dish_left","dish_right","scanline") else 10)
    oh = h or max(1, round(im.size[1]*w/im.size[0]))
    info[n] = {"src": im.size}
    im = im.resize((w, oh), Image.LANCZOS)
    im.save(os.path.join(out, n+".png"), optimize=True)
    info[n]["out"] = im.size
for k,v in info.items(): print(k, v)

# ---- greenhouse jungle plants (texture px ~1.3x landscape display for scale headroom)
GH = {"palm_leaf_long": ("h", 110), "palm_leaf_short": ("h", 90), "palm_center": ("w", 76), "monstera_leaf_a": ("h", 90),
      "montsera_leaf_b": ("h", 84), "broad_leaf_a": ("h", 98), "broad_leaf_b": ("h", 98), "shrub_round": ("w", 140), "greenhouse": ("w", 330),
      "flower_leaves": ("w", 100), "flower_red_head": ("w", 62), "branch_full_mesh": ("h", 150), "vine_leaf_small": ("h", 36)}
gsrc = os.path.join(os.path.dirname(src.rstrip("/")), "greenhouse")
for n, (k, v) in GH.items():
    im = trim(Image.open(os.path.join(gsrc, n + ".png")).convert("RGBA"), 20)
    w, h = im.size
    size = (v, max(1, round(h * v / w))) if k == "w" else (max(1, round(w * v / h)), v)
    im.resize(size, Image.LANCZOS).save(os.path.join(out, n + ".png"), optimize=True)
