# city placements (greenhouse bg). Landscape measured on 1672x941 src (x1.1483), portrait on 1086x1448 src (x0.99448, +240 y).
# Fan centers/diameters = dark holes detected in the final 1920/1080 bgs.
import json, sys, random
out = sys.argv[1]
KL = 1920 / 1672
KP = 1080 / 1086
def L(x, y): return round(x * KL), round(y * KL)
def P(x, y): return round(x * KP), round(y * KP + 240)
def it(name, skin, anim, xy, scale=1.0, **kw):
    d = {"name": name, "skin": skin, "anim": anim, "x": xy[0], "y": xy[1], "scale": round(scale, 3)}
    d.update(kw); return d
def fan(name, c, dia, **kw):  # blade fills the hole (blade png 160px)
    return it(name, "fan", "fan_spin", c, dia * 0.97 / 80, **kw)  # blade shows 80px at scale 1

# ---------------- greenhouse (TR roof): normalized (u,v) layout, draw order back -> front
GH = [
    *[("Shrub", s, "shrub_breathe", u, v, 1.0) for (u, v), s in zip(
        [(0.05, 0.15), (0.18, 0.9), (0.32, 0.5), (0.45, 0.1), (0.55, 0.9), (0.68, 0.45), (0.82, 0.1), (0.95, 0.88),
         (0.25, 0.22), (0.76, 0.78), (0.4, 0.72), (0.92, 0.42)], ["shrub_dark", "shrub_mid", "shrub_light"] * 4)],
    *[("Branch", "branch", "branch_wave", u, v, 1.0, r) for u, v, r in [(0.12, 0.55, 30), (0.5, 0.4, -60), (0.78, 0.22, 120), (0.99, 0.62, -15)]],
    *[("Fern", "fern", "fern_flutter", u, v, 0.9) for u, v in [(0.0, 0.02), (0.3, 0.0), (0.62, 0.02), (1.0, 0.05), (0.0, 0.5),
                                                              (1.0, 0.97), (0.35, 1.0), (0.7, 1.0), (0.02, 1.0)]],
    *[("Broad leaf", "broad_leaf", "broad_sway", u, v, 1.0, r) for u, v, r in [(0.22, 0.62, 0), (0.42, 0.36, 70), (0.6, 0.66, 150), (0.82, 0.55, 220), (0.15, 0.28, 300)]],
    *[("Monstera", "monstera", "monstera_sway", u, v, 1.0, r) for u, v, r in [(0.05, 0.78, 20), (0.07, 0.3, 140), (0.3, 0.84, 260), (0.53, 0.16, 80), (0.9, 0.24, 200)]],
    *[("Red flower", "red_flower", "flower_bob", u, v, 1.0) for u, v in [(0.94, 0.64), (0.86, 0.92), (0.72, 0.3), (0.27, 0.48)]],
    *[("Palm", "palm", "palm_sway", u, v, s, r) for u, v, s, r in [(0.2, 0.45, 0.95, 10), (0.12, 0.86, 0.8, 50), (0.92, 0.8, 0.85, 95),
                                                                     (0.66, 0.74, 0.9, 140), (0.76, 0.18, 0.95, 200), (0.48, 0.32, 1.25, 0)]],
]
def greenhouse(x0, y0, x1, y1, smul, seed):
    rnd = random.Random(seed); out_ = []; cnt = {}
    for row in GH:
        name, skin, anim, u, v, s = row[:6]; r = row[6] if len(row) > 6 else rnd.randint(0, 359)
        cnt[name] = cnt.get(name, 0) + 1
        out_.append(it(f"GH {name} {cnt[name]}", skin, anim, (round(x0 + u * (x1 - x0)), round(y0 + v * (y1 - y0))),
                       s * smul * rnd.uniform(0.9, 1.1), rotation=r))
    return out_

land = [
    it("Glint TL solar", "glint_square", "glint_sweep_small", L(412, 213), 1.3),
    it("Glint BL canopy", "glint_canopy", "glint_sweep", L(281, 666), 1.03, scaleY=1.1),
    it("Glint BL corner", "glint_small", "glint_sweep_small", L(545, 866), 1.15),
    fan("Fan TL 1", (153, 196), 103.5), fan("Fan TL 2", (322, 196), 102),
    fan("Fan BL", (625, 815), 71.5), fan("Fan BR", (1806, 889), 90, timeScale=0.7),
    it("Bus blue", "bus_blue", "bus_static", L(180, 783), 1.0),
    it("Bus red", "bus_red", "bus_static", L(385, 783), 1.0),
    it("Canopy lamps", "lamp_row8", "lamp_chase", L(87, 712), 1.05, random=False),
    it("Helipad ring", "helipad_ring", "ring_chase", L(1307, 756), 1.09, scaleY=0.945, random=False),
    *[it(f"Helipad corner {i+1}", "light_red", "light_blink", L(x, y), 1.0, random=False)
      for i, (x, y) in enumerate([(1140, 630), (1478, 630), (1140, 882), (1478, 882)])],
    it("Helicopter", "helicopter", "heli_cycle", L(1307, 756), 0.95, random=False),
    it("LED TL a", "light_green", "light_flicker", L(565, 222), 0.6), it("LED TL b", "light_blue", "light_pulse", L(565, 240), 0.6),
    it("LED TR a", "light_green", "light_flicker", L(1100, 222), 0.6), it("LED TR b", "light_blue", "light_pulse", L(1100, 240), 0.6),
    it("LED BL a", "light_green", "light_flicker", L(486, 598), 0.6), it("LED BL b", "light_blue", "light_pulse", L(486, 612), 0.6),
    it("GH shrub 1", "shrub_light", "shrub_breathe", (1367, 116), 1.85),
    it("GH shrub 2", "shrub_mid", "shrub_breathe", (1367, 240), 1.85),
    it("Greenhouse", "greenhouse", "greenhouse_glint", (1718, 184), 1.0),
    it("Tree TL", "bush", "bush_sway", L(575, 35), 0.58), it("Tree TR", "bush", "bush_sway", L(1097, 35), 0.58),
    it("Tree BL top", "bush", "bush_sway", L(38, 648), 0.6), it("Tree BL low", "bush", "bush_sway", L(42, 868), 0.62),
    it("Tree BR top", "bush", "bush_sway", L(1097, 655), 0.58), it("Tree BR low", "bush", "bush_sway", L(1097, 868), 0.58),
    it("Bush TR", "bush", "bush_sway", L(1225, 297), 0.38), it("Bush BR", "bush", "bush_sway", L(1530, 602), 0.38),
    it("Windsock BR", "flag", "flag_wave", L(1517, 662), 1.0),
    it("Pigeon 1", "pigeon", "pigeon_peck", L(598, 300), 0.85, rotation=60),
    it("Pigeon 2", "pigeon", "pigeon_peck", L(1075, 610), 0.85, rotation=-120),
    it("Pigeon 3", "pigeon", "pigeon_peck", L(1650, 305), 0.85, rotation=200),
]
# portrait: new bg (1086x1448 -> 1080 wide, +240 bands). Coordinates measured directly in final 1080x1920 px.
def F(x, y): return (x, y)
port = [
    *[it(f"Tree band {i+1}", "tree", "tree_sway", F(x, y), sc) for i, (x, y, sc) in enumerate(
        [(95, 105, 0.72), (275, 165, 0.58), (835, 95, 0.7), (1012, 175, 0.6), (90, 1815, 0.72), (272, 1760, 0.58), (838, 1825, 0.7), (1012, 1755, 0.6)])],
    *[it(f"Flowers band {i+1}", sk, "bush_sway", F(x, y), sc, rotation=r) for i, (sk, x, y, sc, r) in enumerate(
        [("flowers", 190, 40, 0.75, 20), ("bush", 20, 215, 0.7, 80), ("flowers", 940, 215, 0.7, 140), ("bush", 735, 30, 0.7, 200),
         ("bush", 190, 1890, 0.75, 30), ("flowers", 20, 1700, 0.7, 110), ("flowers", 935, 1700, 0.7, 250), ("bush", 735, 1895, 0.7, 310)])],
    it("Glint TL solar", "glint_square", "glint_sweep_small", F(235, 608), 0.98, scaleY=1.2),
    it("Glint BL canopy", "glint_canopy_short", "glint_sweep", F(170, 1241), 1.03, scaleY=1.45),
    it("Glint BL corner", "glint_square", "glint_sweep_small", F(310, 1531), 0.95),
    fan("Fan TL 1", (100, 488), 77), fan("Fan TL 2", (204, 488), 77),
    fan("Fan BL", (308, 1295), 48), fan("Fan BR", (1009, 1370), 64, timeScale=0.7),
    it("Bus blue", "bus_blue", "bus_static", F(112, 1411), 0.9, rotation=90),
    it("Bus red", "bus_red", "bus_static", F(220, 1411), 0.9, rotation=90),
    it("Canopy lamps", "lamp_row6", "lamp_chase", F(67, 1300), 0.66, random=False),
    it("Helipad ring", "helipad_ring", "ring_chase", F(869, 1373), 0.64, scaleY=1.35, random=False),
    *[it(f"Helipad corner {i+1}", "light_red", "light_blink", F(x, y), 0.75, random=False)
      for i, (x, y) in enumerate([(777, 1187), (960, 1187), (777, 1553), (960, 1553)])],
    it("Helicopter", "helicopter", "heli_cycle", F(869, 1372), 0.5, random=False),
    it("LED TL a", "light_green", "light_flicker", F(334, 612), 0.5), it("LED TL b", "light_blue", "light_pulse", F(334, 640), 0.5),
    it("LED TR a", "light_green", "light_flicker", F(742, 615), 0.5), it("LED TR b", "light_blue", "light_pulse", F(742, 640), 0.5),
    it("LED BL", "light_green", "light_flicker", F(278, 1160), 0.5),
    it("GH shrub 1", "shrub_light", "shrub_breathe", F(825, 375), 1.6),
    it("GH shrub 2", "shrub_mid", "shrub_breathe", F(978, 375), 1.6),
    it("Greenhouse", "greenhouse", "greenhouse_glint", F(901, 556), 0.88),
    it("Tree TL", "bush", "bush_sway", F(318, 290), 0.52),
    it("Tree BL top", "bush", "bush_sway", F(35, 1185), 0.52), it("Tree BL low", "bush", "bush_sway", F(35, 1540), 0.52),
    it("Tree BR top", "bush", "bush_sway", F(750, 1215), 0.52), it("Tree BR low", "bush", "bush_sway", F(750, 1540), 0.52),
    it("Bush BR", "bush", "bush_sway", F(990, 1155), 0.34),
    it("Windsock BR", "flag", "flag_wave", F(985, 1230), 0.75),
    it("Pigeon 1", "pigeon", "pigeon_peck", F(200, 230), 0.7, rotation=40),
    it("Pigeon 2", "pigeon", "pigeon_peck", F(900, 1640), 0.7, rotation=-150),
    it("Pigeon 3", "pigeon", "pigeon_peck", F(150, 1665), 0.7, rotation=110),
    it("Pigeon 4", "pigeon", "pigeon_peck", F(960, 260), 0.7, rotation=200),
]
doc = {"_readme": "Coordinates = background pixels (top-left origin). List order = draw order. Fields: name, skin, anim, x, y, scale, scaleY (optional, multiplies scale on Y), rotation(deg, clockwise), flipX, timeScale, random (false = start at t=0, keeps synced rigs in phase).",
       "skeleton": "env.json", "atlas": "env.atlas",
       "landscape": {"background": "bg_landscape.png", "width": 1920, "height": 1080, "items": land},
       "portrait": {"background": "bg_portrait.png", "width": 1080, "height": 1920, "items": port}}
json.dump(doc, open(out, "w"), indent=1)
print(len(land), len(port))
