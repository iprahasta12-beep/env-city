# Remove everything not used: skins not placed, then slots/bones/anims/images nobody references.
# usage: prune.py <theme_dir>            (uses placements.json)
#        prune.py <dir> <json> <imgdir>  (keep all skins, just drop unreferenced images) — for win_fx
import json, os, sys

def attachments_images(skins):
    imgs = set()
    for sk in skins:
        for slot, atts in sk.get("attachments", {}).items():
            for name, a in atts.items():
                if a.get("type") in ("clipping", "boundingbox", "point", "path"): continue
                imgs.add(a.get("path", name))
    return imgs

def prune_theme(d):
    J = json.load(open(os.path.join(d, "env.json")))
    pl = json.load(open(os.path.join(d, "placements.json")))
    used_sk = {i["skin"] for k in ("landscape", "portrait") for i in pl[k]["items"]}
    used_an = {i["anim"] for k in ("landscape", "portrait") for i in pl[k]["items"]}
    J["skins"] = [s for s in J["skins"] if s["name"] == "default" or s["name"] in used_sk]
    bone_names = [b["name"] for b in J["bones"]]
    slot_used = {sl for s in J["skins"] for sl in s.get("attachments", {})}
    keep_b = set()
    for s in J["slots"]:
        if s["name"] in slot_used: keep_b.add(s["bone"])
    for s in J["skins"]:                      # weighted meshes reference bones by index
        for atts in s.get("attachments", {}).values():
            for a in atts.values():
                v = a.get("vertices")
                if a.get("type") == "mesh" and v and len(v) > len(a["uvs"]):
                    i = 0
                    while i < len(v):
                        n = int(v[i]); i += 1
                        for _ in range(n): keep_b.add(bone_names[int(v[i])]); i += 4
    parent = {b["name"]: b.get("parent") for b in J["bones"]}
    for b in list(keep_b):
        while b: keep_b.add(b); b = parent[b]
    keep_b.add("root")
    # descendants of kept bones that anims move (e.g. glint streak bone under clip) are kept via slots already
    old_idx = {n: i for i, n in enumerate(bone_names)}
    J["bones"] = [b for b in J["bones"] if b["name"] in keep_b]
    new_idx = {b["name"]: i for i, b in enumerate(J["bones"])}
    remap = {old_idx[n]: new_idx[n] for n in new_idx}
    for s in J["skins"]:
        for atts in s.get("attachments", {}).values():
            for a in atts.values():
                v = a.get("vertices")
                if a.get("type") == "mesh" and v and len(v) > len(a["uvs"]):
                    i = 0
                    while i < len(v):
                        n = int(v[i]); i += 1
                        for _ in range(n): v[i] = remap[int(v[i])]; i += 4
    J["slots"] = [s for s in J["slots"] if s["name"] in slot_used and s["bone"] in keep_b]
    slots = {s["name"] for s in J["slots"]}
    skins = {s["name"] for s in J["skins"]}
    anims = {}
    for an, a in J["animations"].items():
        na = {}
        if "bones" in a: na["bones"] = {k: v for k, v in a["bones"].items() if k in keep_b}
        if "slots" in a: na["slots"] = {k: v for k, v in a["slots"].items() if k in slots}
        if "attachments" in a:
            na["attachments"] = {sk: {sl: v for sl, v in d_.items() if sl in slots} for sk, d_ in a["attachments"].items() if sk in skins}
        for key in ("drawOrder", "events"):
            if key in a: na[key] = a[key]
        na = {k: v for k, v in na.items() if v}
        if na: anims[an] = na
    J["animations"] = anims
    json.dump(J, open(os.path.join(d, "env.json"), "w"), indent=1)
    return attachments_images(J["skins"]), os.path.join(d, "images"), len(J["skins"]) - 1, len(anims)

def drop_images(imgdir, keep):
    gone = []
    for f in os.listdir(imgdir):
        if f.endswith(".png") and f[:-4] not in keep:
            os.remove(os.path.join(imgdir, f)); gone.append(f[:-4])
    return gone

if len(sys.argv) == 2:
    keep, imgdir, ns, na = prune_theme(sys.argv[1])
    print(os.path.basename(sys.argv[1].rstrip("/")), "skins", ns, "anims", na, "removed images:", sorted(drop_images(imgdir, keep)))
else:
    J = json.load(open(sys.argv[2]))
    print("removed images:", sorted(drop_images(sys.argv[3], attachments_images(J["skins"]))))
