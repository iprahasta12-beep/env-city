# env-animation — Spine 4.2 + Pixi v8 (offline)

Base = env-animation-city-crash-smash-v2. 3 themes (Desert, Urban, City — tab order) + shared win overlay. All Spine **4.2**.

## Folders
| path | what |
|------|------|
| `themes/urban/` | Old "city" (fountain, laundry, awnings…). Unchanged |
| `themes/city/` | Greenhouse bg: heli pad, bus depot, jungle greenhouse roof (TR) |
| `themes/desert/` | Desert (diner, shop, turbine, tumbleweed). Rebuilt from 3.8 demo as Spine 4.2 |
| `themes/<id>/env.json` + `env.atlas` + `env.png` | Skeleton (one skin per object) + packed atlas |
| `themes/<id>/images/` | Source PNGs for Spine editor (`"images": "./images/"`) |
| `themes/<id>/bg_landscape.png` / `bg_portrait.png` | 1920×1080 / 1080×1920 clean plates |
| `themes/<id>/placements.json` | Instances per layout |
| `win_fx/` | Win overlay, 5 levels (shared by all themes). Source art `images_win/` |
| `preview/index.html` | Offline preview. Double-click |
| `tools/` | Python scripts used to build city / desert (optional) |

## Preview
- **Left panel**: Theme (Desert / Urban / City) · Orientation (Landscape 1920×1080 / Portrait 1080×1920) · Pause · Speed (slider + 0.25/0.5/1/2x) · Edit (inspector shows under it) · Debug · Load folder / Save placements.json / Bake data.js.
- **Right panel**: WIN · CRASH WIN · SMASH WIN · WRECKAGE WIN · TOTAL WIN buttons (keys W C S R X) · Skip→out · options (auto out, dim, debug win skeleton) · amount (random / fixed).
- Win overlay now sits inside the game frame (fits 1920×1080 or 1080×1920), not the browser window.
- Keys: `T` theme · `1/2` orientation · `Space` pause · `E` edit · `D` debug · `C` crash · `S` smash.
- Load folder: pick `env-animation` root (loads all themes + win_fx) or one theme folder.
- Save placements.json = current theme → replace `themes/<id>/placements.json`.

## Win overlay — 5 levels (win_fx.json)
Design space 1080 wide, root = screen center. Bone `fx` scale 0.8 = overall size. Slot `amount` (y −215) = game number. Each level: `<lvl>_in` (1.4s) → `<lvl>_loop` (2s) → `<lvl>_out` (0.5s). Setup pose = all parts alpha 0.

| level | anims | text | components | effects |
|---|---|---|---|---|
| 1 | win_* | text_win | — | 8 spark_small |
| 2 | crash_win_* | text_crash + text_win | brake_disc (spin), exhaust_pipe, bumper, bolt ×3 | smoke ×4 light, 8 sparks |
| 3 | smash_win_* | text_smash + text_win | plate_top, tire+rim ×2 (spin), bracket ×2, blade ×2, piston, chain, bolt ×2 | smoke ×6, spark_burst ×4 (01–03 flicker), 10 sparks |
| 4 | wreckage_win_* | wreckage + text_win | car_hood, engine_block, tire+rim, bumper, bracket, debris_round ×2, shard ×3, bolt ×3 | smoke_big ×2 + smoke ×6, bursts ×6, 14 sparks, bigger shake |
| 5 | total_win_* | total + text_win | brake_disc + chains, blades, bumpers, tire+rim ×2, bolts, shards, debris | explosion_main behind text (center), light smoke, 2 big top-middle bursts, small sparks, loop rumble |

Layouts traced from the 5 reference comps (CRASH: exhaust pipes + smoke column; SMASH: plate + tires; WRECKAGE: engine + brackets + big smoke; TOTAL: brake disc + chains + blades + bumpers + tires; WIN: smoke + bursts). Amount slot y −265.
Motion: parts fly in from sides/top with spin + overshoot, small parts pop; main word drops (2.4→0.9→1) + impact shake; WIN punches; loop = float/wobble/spin + text pulse + burst flicker + sparks re-shoot; out = punch, shrink, parts fly outward.
`engineblock.png` (duplicate of engine_block) not used. Rebuild: `tools/build_win.py <win png folder> win_fx` then `tools/pack_atlas.py win_fx/images_win win_fx win_fx`.

## city update (greenhouse)
- New bg (landscape + portrait) from greenhouse zip. Portrait 1086×1448 → 1080 wide, top/bottom 240px filled with sidewalk/road.
- Fans: blade fills the painted hole (scale = hole Ø / 80px blade), like Urban.
- Both buses `bus_static` (no animation).
- Helicopter `heli_cycle` = **56s loop**: idle 0–20 (rotor spins up 18–20) → 20 lift + turn → 23–27 fly off frame → 27–47 gone (20s, hidden) → 47–51 fly back → 51–52.5 turn → 52.5–54.5 land → 54.5–56 rotor stops.
- TR roof: `greenhouse` skin (glass house PNG + `greenhouse_glint` sweep clipped to the glass, 6s) + 2 big `shrub_*` (`shrub_breathe`). Jungle plant skins still in env.json, not placed.
- Portrait: new bg (uploaded image), all placements re-measured. Top/bottom 240px bands filled with Urban `tree` + bush/flowers + pigeons.
- TR building = greenhouse roof filled with jungle plants (plan: jungle_plants_spine.xlsx):

| skin | anim | rig |
|------|------|-----|
| palm | palm_sway (3.5s), palm_gust (1.2s trigger) | 6 leaf bones radiating (long/short alternate), center on top, leaf offset ripple |
| monstera | monstera_sway (2.5s) | 4 leaf bones, back 2 darker tint, stagger 0.2s, leaf scale lift |
| fern | fern_flutter (1.5s) | 7 fronds, each 2-bone chain + weighted mesh (bends). No fern PNG → palm_leaf_short narrowed + green tint |
| broad_leaf | broad_sway (3s) | 4 leaves, bigger on top, rotate ±2° + scaleX 0.98 |
| shrub_dark / mid / light | shrub_breathe (3s) | 1 bone, 3 tint skins |
| red_flower | flower_bob (2s), flower_bloom (0.6s trigger) | leaves bone + flower head child |
| branch | branch_wave (4s) | 4-bone FK chain, weighted mesh, 3 vine leaves flutter |

Track-1 gust mixing is a game-code choice; preview plays one loop anim per instance.
- Billboard / flags / antenna / umbrella skins still in env.json but not placed (new bg has no spot for them).

## city skins → anims
`env.json` = urban skeleton + new parts (city skins still inside: fan, bush, umbrella, flag = windsock, pigeon reused).

| skin | anim | how (Spine keys only) |
|------|------|------|
| light_red / orange / white / green / blue | light_blink, light_pulse, light_flicker | dot + glow (additive), slot alpha keys. Color = slot tint |
| helipad_ring | ring_chase | 12 lights on circle r152, alpha keys offset per slot (1.8s) |
| lamp_row8 / lamp_row6 | lamp_chase, lamp_pulse | canopy lamps, 62px apart, root = leftmost lamp |
| glint_square / wide / canopy / canopy_short / small / tiny | glint_sweep, glint_sweep_small | clipping = glass panel, streak translate + pause |
| billboard / billboard_square | billboard_cycle | 3 screens crossfade, scanline sweep, slow pan, clipped (7.5s) |
| bus_blue / bus_red | bus_idle, bus_drive_out, bus_drive_in, bus_cycle | engine shake; drive = root translate + fade. Front = −x |
| helicopter | heli_idle, heli_spin_fast, heli_takeoff, heli_land, heli_cycle | rotor rotate, blade→blur swap, lift scale + shadow drift. Root = rotor hub |
| antenna | antenna_idle | dishes rotate ±4° offset, red beacon blink |
| flag_long_red / flag_long_blue | flag_long_wave | mesh 8×3 deform wave, root = pole |

Play one-shots: `heli_takeoff` → loop `heli_spin_fast`; later `heli_land` → `heli_idle`. Same for bus (`bus_drive_out` / `bus_drive_in`). `*_cycle` = preview loop.

## desert skins → anims
| skin | anim | how (Spine keys only) |
|------|------|------|
| fan | fan_spin | blade rotate 1.2s, hub static. flipX = reverse spin |
| vent / turbine | vent_spin / turbine_spin | same `spin` bone, 1s / 3s |
| alarm | alarm_blink | lens + red glow (additive) alpha blink 1s |
| awning | awning_flutter | top strip static, flap mesh 8×3 deform (2s). Root = top-center under DINER sign |
| windsock | windsock_wave | mesh deform wave along sock axis (1.6s). Root = pole top |
| tree_a / tree_b / tree_c | tree_gust | gust push + recoil (5s) + leaf flutter bone |
| smoke | smoke_flow | 4 puffs (smoke_1/2/3), keys offset per puff: drift down-wind, grow, fade (3.2s) |
| dust | dust_drift | same puffs, orange tint, 700px drift (6s) |
| tumbleweed | tumbleweed_roll | rolls +x 2100px with hops + shadow (8s), hidden 2s (loop 10s). Root = start point |

Desert notes:
- Heat haze from demo dropped: needs shader, not possible in Spine.
- Demo's per-animation on/off panel + 3.8 drag&drop loader dropped; same viewer as other themes.
- Portrait desert synthesized: whole scene scaled to 1080 wide (crop x 0..1640), desert + vertical road extended above/below, extra trees + 2nd tumbleweed in the bands.

## Cleanup
`tools/prune.py <theme_dir>` removes skins not placed in placements.json, then slots/bones/anims/images nobody uses, then repack atlas.
`tools/prune.py <dir> <win_fx.json> <images_win>` drops unreferenced win PNGs. Already run on all themes + win_fx (city lost billboard/flags/antenna/umbrella/jungle-plant art; win lost car_hood, piston).

## Placements
Fields: `name, skin, anim, x, y, scale, scaleY (opt, extra Y multiplier), rotation (deg cw), flipX, timeScale, random`.
`random: false` = start at t=0 (keep chase rigs / corner lights in sync). `scaleY` used for helipad ring ellipse in portrait.

## Notes
- city bg: painted fan blades removed (dark disc) so Spine blade is the only one. Fan placement x/y/scale fitted to each disc.
- Portrait city source was 1086×1448 → scaled to 1080 wide, top/bottom 240px = mirrored sidewalk/road.
- Not used: `bus_roof_vent.png` (bus body already has vents). No car art → traffic skipped.
- Game code: same as before, load `themes/<id>/env.json` + `env.atlas` + `placements.json`.
