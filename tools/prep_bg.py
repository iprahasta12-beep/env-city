import sys
from PIL import Image
import numpy as np
src, out = sys.argv[1], sys.argv[2]
TOPN = int(sys.argv[3]) if len(sys.argv) > 3 else 96
BOTN = int(sys.argv[4]) if len(sys.argv) > 4 else 140
L = Image.open(f"{src}/bg_landscape.png").convert("RGB").resize((1920,1080), Image.LANCZOS)
L.save(f"{out}/bg_landscape.png", optimize=True)
P = Image.open(f"{src}/bg_potrait.png").convert("RGB").resize((1080,1440), Image.LANCZOS)
a = np.asarray(P)
def reflect_band(band, n):
    # band: rows ordered from seam outward; reflect-tile to n rows
    rows=[]; k=0; d=1; i=0
    while len(rows)<n:
        rows.append(band[i])
        i+=d
        if i==len(band): d=-1; i=len(band)-1
        elif i<0: d=1; i=0
    return np.stack(rows)
top_band = a[0:96][::-1]          # clean sidewalk/road rows, seam at row 0
top = reflect_band(a[0:TOPN], 240)[::-1]   # mirror outward from seam
bot = reflect_band(a[1440-BOTN:1440][::-1], 240)
if TOPN < 40:   # thin clean band -> per-column median (no mirrored streaks)
    top = np.repeat(np.median(a[0:TOPN], 0)[None].astype(np.uint8), 240, 0)
    bot = np.repeat(np.median(a[1440-BOTN:1440], 0)[None].astype(np.uint8), 240, 0)
full = np.concatenate([top, a, bot], 0)
Image.fromarray(full).save(f"{out}/bg_portrait.png", optimize=True)
print(full.shape)
