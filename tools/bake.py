import json, base64, os, sys, re
root = sys.argv[1]
LABELS = {"urban": "Urban", "city": "City", "desert": "Desert"}
def url(p): return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()
def pages(atlas): return [l.strip() for l in atlas.splitlines() if re.search(r"\.(png|jpe?g|webp)$", l.strip(), re.I)]
D = {"themes": {}}
for tid in ["desert", "urban", "city"]:
    d = os.path.join(root, "themes", tid)
    at = open(os.path.join(d, "env.atlas")).read(); pl = json.load(open(os.path.join(d, "placements.json")))
    imgs = {n: url(os.path.join(d, n)) for n in pages(at) + [pl[k]["background"] for k in ("landscape", "portrait")]}
    D["themes"][tid] = {"label": LABELS[tid], "skeleton": open(os.path.join(d, "env.json")).read(), "atlas": at, "placements": pl, "images": imgs}
d = os.path.join(root, "win_fx"); at = open(os.path.join(d, "win_fx.atlas")).read()
D["fx"] = {"skeleton": open(os.path.join(d, "win_fx.json")).read(), "atlas": at, "images": {n: url(os.path.join(d, n)) for n in pages(at)}}
open(os.path.join(root, "preview", "data.js"), "w").write("// AUTO-GENERATED preview data\nwindow.ENV_DATA = " + json.dumps(D) + ";\n")
print(os.path.getsize(os.path.join(root, "preview", "data.js")) // 1024, "KB")
