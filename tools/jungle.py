# Jungle plants for the city greenhouse (TR roof). exec'd inside build_skel.py (shares helpers + J).
# Plan: jungle_plants_spine.xlsx. All motion = Spine keys. Leaves: image points up (stem at bottom) -> attachment rotation -90
# so the leaf points along its bone (+x), base at bone origin.

def leaf(img, length, x0=0, sx=1.0, path=None):
    tw, th = IMG(img)
    s = length / th
    a = {"x": R(x0 + length / 2), "y": 0, "rotation": -90, "width": tw, "height": th, "scaleX": R(s * sx), "scaleY": R(s)}
    if path: a["path"] = path
    return a

def sin_keys(amp, T, phase=0.0, base=0.0, n=12):
    return lin1([(T * k / n, base + amp * math.sin(2 * math.pi * (k / n + phase))) for k in range(n + 1)])
def sin_keys2(ampx, ampy, T, phase=0.0, n=12):
    return [dict({"time": R(T * k / n)} if k else {}, x=R(1 + ampx * math.sin(2 * math.pi * (k / n + phase))),
                 y=R(1 + ampy * math.sin(2 * math.pi * (k / n + phase)))) for k in range(n + 1)]

# ---- grid mesh with hull first (for weighted bone-chain meshes)
def grid_topology(C, N):
    loop = [(0, j) for j in range(N + 1)] + [(i, N) for i in range(1, C + 1)] + [(C, j) for j in range(N - 1, -1, -1)] + [(i, 0) for i in range(C - 1, 0, -1)]
    inner = [(i, j) for j in range(1, N) for i in range(1, C)]
    order = loop + inner
    idx = {p: k for k, p in enumerate(order)}
    tris = []
    for j in range(N):
        for i in range(C):
            a, b, c, d = idx[(i, j)], idx[(i + 1, j)], idx[(i, j + 1)], idx[(i + 1, j + 1)]
            tris += [a, b, d, a, d, c]
    hull = len(loop)
    edges = []
    for k in range(hull): edges += [k * 2, ((k + 1) % hull) * 2]
    return order, tris, hull, edges

def bone_index(name):
    return next(i for i, b in enumerate(J["bones"]) if b["name"] == name)

def chain_mesh(img, length, width, chain, C=2, N=8):
    """Weighted mesh along a bone chain (bones colinear in setup, each seg = length/len(chain))."""
    tw, th = IMG(img)
    order, tris, hull, edges = grid_topology(C, N)
    seg = length / len(chain)
    bi = [bone_index(b) for b in chain]
    uvs, verts = [], []
    for (i, j) in order:
        u, v = i / C, j / N
        uvs += [R(u), R(v)]
        s = (1 - v) * length; y = -(u - 0.5) * width
        k = min(int(s // seg), len(chain) - 1); f = (s - k * seg) / seg
        if k == len(chain) - 1: ws = [(k, 1.0)]
        else: ws = [(k, 1 - f), (k + 1, f)]
        ws = [(kk, w) for kk, w in ws if w > 1e-4]
        verts.append(len(ws))
        for kk, w in ws: verts += [bi[kk], R(s - kk * seg), R(y), R(w)]
    return {"type": "mesh", "path": img, "uvs": uvs, "triangles": tris, "vertices": verts, "hull": hull, "edges": edges,
            "width": tw, "height": th}

# ======================================================== 1. PALM (star burst)
NL = 6
bone("j_palm")
for i in range(NL): bone(f"j_palm_{i}", "j_palm", rotation=R(i * 60 + 15))
for i in range(NL): slot(f"j_palm_leaf_{i}", f"j_palm_{i}", "leaf", None, "ffffffff" if i % 2 else "dceed2ff")
slot("j_palm_center", "j_palm", "palm_center")
pa = {f"j_palm_leaf_{i}": {"leaf": leaf("palm_leaf_long" if i % 2 == 0 else "palm_leaf_short", 82 if i % 2 == 0 else 64, x0=6,
                                         path="palm_leaf_long" if i % 2 == 0 else "palm_leaf_short")} for i in range(NL)}
pa["j_palm_center"] = {"palm_center": region("palm_center", w=58)}
skin("palm", pa)
anims["palm_sway"] = {"bones": {"j_palm": {"rotate": sin_keys(3, 3.5)},
                                **{f"j_palm_{i}": {"rotate": sin_keys(2, 3.5, phase=i / NL, base=0)} for i in range(NL)}}}
# gust: wind toward +x (screen right). Leaf at angle a bends toward wind: delta = -sin(a)*k
def gust_rot(a, k):  # timeline values are offsets from setup rotation
    d = -math.sin(math.radians(a)) * k
    return [{"value": 0, "curve": ease1(0, 0, 0.35, d)}, {"time": 0.35, "value": R(d), "curve": ease1(0.35, d, 1.2, 0)}, {"time": 1.2, "value": 0}]
anims["palm_gust"] = {"bones": {**{f"j_palm_{i}": {"rotate": gust_rot(i * 60 + 15, 12),
                                                    "scale": keys2([(0, 1, 1), (0.35, 1 - 0.08 * max(0, -math.cos(math.radians(i * 60 + 15))), 1), (1.2, 1, 1)])}
                                   for i in range(NL)},
                                "j_palm": {"translate": keys2([(0, 0, 0), (0.35, 3, 0), (1.2, 0, 0)])}}}

# ======================================================== 2. MONSTERA (4 leaves, back copies darker)
MA = [10, 100, 195, 285]
bone("j_mon")
for i, a in enumerate(MA): bone(f"j_mon_{i}", "j_mon", rotation=a)
for i in range(4): slot(f"j_mon_leaf_{i}", f"j_mon_{i}", "leaf", None, "a9c49cff" if i < 2 else "ffffffff")
skin("monstera", {f"j_mon_leaf_{i}": {"leaf": leaf("monstera_leaf_a" if i % 2 == 0 else "montsera_leaf_b", 66 if i < 2 else 58, x0=4,
                                                    path="monstera_leaf_a" if i % 2 == 0 else "montsera_leaf_b")} for i in range(4)})
anims["monstera_sway"] = {"bones": {f"j_mon_{i}": {"rotate": sin_keys(2, 2.5, phase=-i * 0.2 / 2.5, base=0),
                                                     "scale": sin_keys2(-0.03, 0, 2.5, phase=-i * 0.2 / 2.5)} for i, a in enumerate(MA)}}

# ======================================================== 3. FERN (7 fronds, 2-bone chain each, weighted mesh bends)
NF = 7; FL = 58
bone("j_fern")
for i in range(NF):
    bone(f"j_fern_{i}", "j_fern", rotation=R(i * 360 / NF))
    bone(f"j_fern_{i}_tip", f"j_fern_{i}", x=FL / 2)
for i in range(NF): slot(f"j_fern_frond_{i}", f"j_fern_{i}", "frond", None, "d8ffb8ff" if i % 2 else "b8e8a0ff")
fw = FL * IMG("palm_leaf_short")[0] / IMG("palm_leaf_short")[1] * 0.42
skin("fern", {f"j_fern_frond_{i}": {"frond": chain_mesh("palm_leaf_short", FL, fw, [f"j_fern_{i}", f"j_fern_{i}_tip"], C=2, N=6)} for i in range(NF)})
anims["fern_flutter"] = {"bones": {**{f"j_fern_{i}": {"rotate": sin_keys(2, 1.5, phase=i / NF, base=0)} for i in range(NF)},
                                   **{f"j_fern_{i}_tip": {"rotate": sin_keys(5, 1.5, phase=i / NF - 0.12)} for i in range(NF)}}}

# ======================================================== 4. BROAD LEAF (philodendron / elephant ear)
BA = [(0, "broad_leaf_b", 70), (85, "broad_leaf_a", 62), (175, "broad_leaf_b", 66), (265, "broad_leaf_a", 74)]
bone("j_broad")
for i, (a, _, _) in enumerate(BA): bone(f"j_broad_{i}", "j_broad", rotation=a)
order_ = sorted(range(len(BA)), key=lambda i: BA[i][2])          # bigger leaf on top
for i in order_: slot(f"j_broad_leaf_{i}", f"j_broad_{i}", "leaf")
skin("broad_leaf", {f"j_broad_leaf_{i}": {"leaf": leaf(img, ln, x0=3, path=img)} for i, (a, img, ln) in enumerate(BA)})
anims["broad_sway"] = {"bones": {f"j_broad_{i}": {"rotate": sin_keys(2, 3, phase=i * 0.21, base=0),
                                                   "scale": sin_keys2(-0.02, 0, 3, phase=i * 0.21 + 0.25)} for i, (a, _, _) in enumerate(BA)}}

# ======================================================== 5. SHRUB (1 bone, 3 tint skins)
bone("j_shrub")
SH = {"dark": "8fb380ff", "mid": "c9e2bcff", "light": "ffffffff"}
for k, c in SH.items(): slot(f"j_shrub_{k}", "j_shrub", "shrub_round", None, c)
for k in SH: skin(f"shrub_{k}", {f"j_shrub_{k}": {"shrub_round": region("shrub_round", w=62)}})
anims["shrub_breathe"] = {"bones": {"j_shrub": {"scale": keys2([(0, 1, 1), (1.5, 1.03, 1.03), (3, 1, 1)]),
                                                "rotate": keys1([(0, -1), (1.5, 1), (3, -1)])}}}

# ======================================================== 6. RED FLOWER (leaves + flower head)
bone("j_flower")
bone("j_flower_head", "j_flower")
slot("j_flower_leaves", "j_flower", "flower_leaves")
slot("j_flower_head", "j_flower_head", "flower_red_head")
skin("red_flower", {"j_flower_leaves": {"flower_leaves": region("flower_leaves", w=78)},
                    "j_flower_head": {"flower_red_head": region("flower_red_head", w=46)}})
anims["flower_bob"] = {"bones": {"j_flower": {"rotate": keys1([(0, -2), (1, 2), (2, -2)])},
                                 "j_flower_head": {"scale": keys2([(0, 1, 1), (0.6, 1.08, 1.08), (1.6, 1, 1), (2, 1, 1)]),
                                                   "rotate": keys1([(0, 0), (0.5, 4), (1.5, -4), (2, 0)])}}}
anims["flower_bloom"] = {"bones": {"j_flower_head": {"scale": [{"x": 0, "y": 0, "curve": easeout2(0, (0, 0), 0.4, (1.1, 1.1))},
                                                               {"time": 0.4, "x": 1.1, "y": 1.1, "curve": ease2(0.4, (1.1, 1.1), 0.6, (1, 1))},
                                                               {"time": 0.6, "x": 1, "y": 1}]}}}

# ======================================================== 7. BRANCH / VINE (4-bone FK chain, weighted mesh + vine leaves)
BL_ = 118; NB = 4
bone("j_branch")
bone("j_branch_0", "j_branch", rotation=90)
for k in range(1, NB): bone(f"j_branch_{k}", f"j_branch_{k - 1}", x=BL_ / NB)
VL = [(1, 6, 55), (2, 12, -60), (3, 18, 40)]          # (bone, x along, angle)
for n, (k, x, a) in enumerate(VL): bone(f"j_vine_{n}", f"j_branch_{k}", x=x, rotation=a)
slot("j_branch", "j_branch_0", "branch")
for n in range(len(VL)): slot(f"j_vine_{n}", f"j_vine_{n}", "vine_leaf_small")
bw = BL_ * IMG("branch_full_mesh")[0] / IMG("branch_full_mesh")[1]
skin("branch", {"j_branch": {"branch": chain_mesh("branch_full_mesh", BL_, bw, [f"j_branch_{k}" for k in range(NB)], C=2, N=8)},
                **{f"j_vine_{n}": {"vine_leaf_small": leaf("vine_leaf_small", 26)} for n in range(len(VL))}})
anims["branch_wave"] = {"bones": {**{f"j_branch_{k}": {"rotate": sin_keys(1.5, 4, phase=-k * 0.08, base=0)} for k in range(NB)},
                                  **{f"j_vine_{n}": {"rotate": sin_keys(4, 4, phase=n * 0.3, base=a, n=24) if False else
                                     lin1([(4 * q / 24, 4 * math.sin(2 * math.pi * (3 * q / 24 + n * 0.3))) for q in range(25)])}
                                     for n, (k, x, a) in enumerate(VL)}}}

# ======================================================== GREENHOUSE (glass house PNG + glint sweep clipped to the glass)
GW = 304; GH_ = GW * IMG("greenhouse")[1] / IMG("greenhouse")[0]
bone("j_gh")
bone("j_gh_glint", "j_gh", rotation=-8)
slot("j_gh_body", "j_gh", "greenhouse")
slot("j_gh_clip", "j_gh", "clip")
slot("j_gh_glint", "j_gh_glint", "glint_streak", "additive", "ffffffb3")
skin("greenhouse", {"j_gh_body": {"greenhouse": region("greenhouse", w=GW)},
                    "j_gh_clip": {"clip": clip("j_gh_glint", GW * 0.9, GH_ * 0.88)},
                    "j_gh_glint": {"glint_streak": region("glint_streak", h=GH_ * 1.5)}})
anims["greenhouse_glint"] = {"bones": {"j_gh_glint": {"translate": [
    {"x": -220, "y": 0, "curve": ease2(0, (-220, 0), 1.6, (220, 0), 0.25)},
    {"time": 1.6, "x": 220, "y": 0, "curve": "stepped"}, {"time": 6.0, "x": -220, "y": 0}]}}}
