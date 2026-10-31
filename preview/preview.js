// Offline preview: multiple env themes (env.json + placements.json each) + shared CRASH/SMASH WIN overlay (win_fx.json).
// Data comes from data.js (window.ENV_DATA) or "Load folder". No fetch → works on file://
(async () => {
  const $ = (id) => document.getElementById(id);
  const toast = (t) => { const e = $("toast"); e.textContent = t; e.style.display = "block"; clearTimeout(toast.h); toast.h = setTimeout(() => (e.style.display = "none"), 2400); };
  const store = { get: (k) => { try { return localStorage.getItem(k); } catch { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch {} } };

  const app = new PIXI.Application();
  await app.init({ resizeTo: $("stage"), background: "#14161b", antialias: true, autoDensity: true, resolution: Math.min(2, window.devicePixelRatio || 1) });
  $("stage").appendChild(app.canvas);

  const world = new PIXI.Container();          // game frame (layout px)
  app.stage.addChild(world);
  const frame = new PIXI.Graphics();
  const bgSprite = new PIXI.Sprite();
  const animLayer = new PIXI.Container();
  const sel = new PIXI.Graphics();
  const fxLayer = new PIXI.Container();         // win overlay lives inside the frame
  const frameMask = new PIXI.Graphics(), animMask = new PIXI.Graphics();
  world.addChild(frame, bgSprite, animLayer, sel, fxLayer, frameMask, animMask);
  animLayer.mask = animMask;   // clip env objects to the game frame
  fxLayer.mask = frameMask;

  let DATA = window.ENV_DATA || null;
  let theme = null, layout = "landscape";
  let speed = 1, playing = true, editing = false, debug = false;
  let views = [];
  let selected = null;
  const skelCache = {};   // theme -> SkeletonData
  const texCache = {};    // key -> Texture

  const imgTex = (key, src) => new Promise((res, rej) => {
    if (texCache[key]) return res(texCache[key]);
    const img = new Image();
    img.onload = () => res((texCache[key] = PIXI.Texture.from(img)));
    img.onerror = () => rej(new Error("image decode failed: " + key));
    img.src = src;
  });
  const T = () => DATA.themes[theme];
  const L = () => T().placements[layout];

  async function loadSkeleton(name, d, fxMode) {
    const atlas = new spine.TextureAtlas(d.atlas);
    for (const page of atlas.pages) {
      const src = d.images[page.name];
      if (!src) throw new Error(`Atlas page "${page.name}" missing (${name})`);
      page.setTexture(spine.SpineTexture.from((await imgTex(name + "/" + page.name, src)).source));
    }
    const json = typeof d.skeleton === "string" ? JSON.parse(d.skeleton) : d.skeleton;
    return new spine.SkeletonJson(new spine.AtlasAttachmentLoader(atlas)).readSkeletonData(json);
  }

  // ---------- theme / layout UI ----------
  function renderThemeButtons() {
    const ids = Object.keys(DATA.themes);
    $("themes").innerHTML = ids.map((k) => `<button data-theme="${k}">${DATA.themes[k].label || k}</button>`).join("");
    $("themes").querySelectorAll("button").forEach((b) => (b.onclick = () => setTheme(b.dataset.theme)));
  }
  function syncButtons() {
    $("themes").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.theme === theme));
    $("layouts").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.layout === layout));
  }
  $("layouts").querySelectorAll("button").forEach((b) => (b.onclick = () => setLayout(b.dataset.layout)));

  async function setTheme(t) {
    if (!DATA.themes[t]) return;
    killFx(true);
    theme = t; store.set("env-theme", t); syncButtons();
    if (!skelCache[t]) skelCache[t] = await loadSkeleton(t, T());
    const sd = skelCache[t];
    $("iSkin").innerHTML = sd.skins.map((s) => s.name).filter((n) => n !== "default").map((s) => `<option>${s}</option>`).join("");
    $("iAnim").innerHTML = sd.animations.map((a) => `<option>${a.name}</option>`).join("");
    await buildScene();
  }
  async function setLayout(l) {
    if (!T().placements[l]) return;
    killFx(true);
    layout = l; store.set("env-layout", l); syncButtons();
    await buildScene();
  }

  // ---------- scene ----------
  function applyView(v, it) {
    v.position.set(it.x, it.y);
    const s = it.scale ?? 1;
    v.scale.set(it.flipX ? -s : s, s * (it.scaleY ?? 1));
    v.angle = it.rotation ?? 0;
    v.state.timeScale = (it.timeScale ?? 1) * (playing ? speed : 0);
  }
  function makeView(it, i) {
    const sd = skelCache[theme];
    const v = new spine.Spine({ skeletonData: sd, autoUpdate: true });
    try { v.skeleton.setSkinByName(it.skin); } catch { console.warn(`${it.name}: skin "${it.skin}" missing`); }
    v.skeleton.setSlotsToSetupPose();
    if (sd.findAnimation(it.anim)) {
      const e = v.state.setAnimation(0, it.anim, true);
      e.trackTime = it.random === false ? 0 : ((i * 0.6180339) % 1) * e.animationEnd; // desync instances
    } else console.warn(`${it.name}: anim "${it.anim}" missing`);
    v.eventMode = "static";
    v.on("pointerdown", (e) => {
      if (!editing) return;
      select(views.find((x) => x.view === v));
      startDrag(e);
      e.stopPropagation();
    });
    applyView(v, it);
    return v;
  }
  async function buildScene() {
    select(null);
    animLayer.removeChildren().forEach((c) => c.destroy());
    views = [];
    const lay = L();
    bgSprite.texture = await imgTex(theme + "/" + lay.background, T().images[lay.background]);
    bgSprite.width = lay.width; bgSprite.height = lay.height;
    frame.clear().rect(-6, -6, lay.width + 12, lay.height + 12).fill({ color: 0x000000, alpha: 0.35 });
    frameMask.clear().rect(0, 0, lay.width, lay.height).fill(0xffffff);
    animMask.clear().rect(0, 0, lay.width, lay.height).fill(0xffffff);
    lay.items.forEach((it, i) => {
      const view = makeView(it, i);
      animLayer.addChild(view);
      views.push({ item: it, view });
    });
    setDebug(debug);
    setEdit(editing);
    fit();
    $("info").textContent = `${T().label || theme} · ${lay.width}×${lay.height} · ${lay.items.length} objects`;
  }
  function fit() {
    if (!DATA || !theme) return;
    const lay = L();
    const pad = 16;
    const s = Math.min((app.screen.width - pad * 2) / lay.width, (app.screen.height - pad * 2) / lay.height);
    world.scale.set(s);
    world.x = (app.screen.width - lay.width * s) / 2;
    world.y = (app.screen.height - lay.height * s) / 2;
    layoutFx();
  }
  app.renderer.on("resize", fit);

  // ---------- CRASH WIN / SMASH WIN overlay (win_fx.json, shared by all themes) ----------
  const dim = new PIXI.Graphics();
  dim.alpha = 0;
  fxLayer.addChild(dim);
  let fxData = null, fx = null; // fx = { view, tick, goOut, phase }
  const amtMode = () => $("fxAmt").querySelector(".on").dataset.a;
  $("fxAmt").querySelectorAll("button").forEach((b) => (b.onclick = () => { $("fxAmt").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b)); }));

  const FXB = () => [...document.querySelectorAll("button.fx[data-lv]")];
  // per level: hold seconds before auto out, random amount range
  const LV = { win: [2.4, 50, 900], crash_win: [3.0, 1000, 5000], smash_win: [3.6, 5000, 25000], wreckage_win: [4.2, 25000, 100000], total_win: [5.0, 100000, 500000] };
  async function buildFx() {
    fxData = null;
    FXB().forEach((b) => (b.disabled = true));
    if (!DATA.fx) { $("fxState").textContent = "win_fx missing"; return; }
    fxData = await loadSkeleton("win_fx", DATA.fx);
    FXB().forEach((b) => (b.disabled = !fxData.findAnimation(b.dataset.lv + "_in")));
  }
  function layoutFx() {
    if (!theme) return;
    const lay = L();
    dim.clear().rect(0, 0, lay.width, lay.height).fill({ color: 0x000000 });
    if (fx) {
      fx.view.position.set(lay.width / 2, lay.height / 2);
      fx.view.scale.set(Math.min(lay.width, lay.height * 1.25) / 1080 * 0.95);
    }
  }
  function setFxUi() {
    const busy = !!fx;
    $("fxOut").disabled = !busy || fx.phase === "out";
    FXB().forEach((b) => b.classList.toggle("on", busy && fx.kind === b.dataset.lv));
  }
  function killFx(instant) {
    if (!fx) return;
    app.ticker.remove(fx.tick);
    fx.view.destroy(); fx = null; dim.alpha = 0;
    fxLayer.eventMode = "none";
    $("fxState").textContent = "Idle";
    setFxUi();
  }
  function playFx(kind) {
    if (!fxData) return;
    if (fx) killFx(true);
    const pre = kind, [hold, lo, hi] = LV[kind] || [3, 1000, 9000];
    const m = amtMode();
    const target = m === "random" ? lo + Math.round(Math.random() * (hi - lo)) : +m;
    const view = new spine.Spine({ skeletonData: fxData, autoUpdate: true });
    view.state.data.defaultMix = 0.15;
    view.state.timeScale = playing ? speed : 0;
    if ($("fxDebug").checked) view.debug = new spine.SpineDebugRenderer();
    const amount = new PIXI.Text({ text: "0", style: {
      fontFamily: "Arial Black, Impact, system-ui, sans-serif", fontWeight: "900", fontSize: 96,
      fill: "#fff3d6", stroke: { color: "#d9400f", width: 12, join: "round" },
      dropShadow: { color: "#000000", alpha: 0.5, distance: 6, blur: 4, angle: Math.PI / 2 } } });
    amount.anchor.set(0.5);
    amount.scale.y = -1; // spine bone space is y-up
    view.addSlotObject("amount", amount);
    fxLayer.addChild(view);
    dim.alpha = 0;
    view.state.setAnimation(0, pre + "_in", false);
    view.state.addAnimation(0, pre + "_loop", true, 0);
    let t = 0, outAt = 0;
    const countDur = hold + 0.6;
    fx = { view, kind, phase: "in" };
    layoutFx();
    fx.goOut = () => {
      if (!fx || fx.phase === "out") return;
      fx.phase = "out"; outAt = t; view.state.setAnimation(0, pre + "_out", false); setFxUi();
    };
    fx.tick = (tk) => {
      const dt = (tk.deltaMS / 1000) * (playing ? speed : 0);
      t += dt;
      const dimTo = $("fxDim").checked ? 0.55 : 0;
      dim.alpha = fx.phase === "out" ? Math.max(0, dim.alpha - dt * 2) : Math.min(dimTo, dim.alpha + dt * 2);
      const k = Math.min(1, Math.max(0, (t - 0.35) / countDur));
      amount.text = Math.round(target * (1 - Math.pow(1 - k, 3))).toLocaleString();
      amount.alpha = Math.min(1, Math.max(0, (t - 0.3) / 0.2)) * (fx.phase === "out" ? Math.max(0, 1 - (t - outAt) / 0.3) : 1);
      if (fx.phase === "in" && t > 1.4) { fx.phase = "loop"; setFxUi(); }
      $("fxState").innerHTML = `<b>${pre}_${fx.phase}</b> · ${t.toFixed(1)}s`;
      if (fx.phase !== "out" && $("fxAuto").checked && t > hold + 1) fx.goOut();
      if (fx.phase === "out" && t - outAt > 0.55) killFx();
    };
    fxLayer.eventMode = "static";
    fxLayer.hitArea = new PIXI.Rectangle(0, 0, L().width, L().height);
    fxLayer.removeAllListeners("pointerdown");
    fxLayer.on("pointerdown", (e) => { e.stopPropagation(); fx && fx.goOut(); });
    app.ticker.add(fx.tick);
    setFxUi();
  }
  FXB().forEach((b) => (b.onclick = () => playFx(b.dataset.lv)));
  $("fxOut").onclick = () => fx && fx.goOut();
  $("fxDebug").onchange = () => { if (fx) fx.view.debug = $("fxDebug").checked ? new spine.SpineDebugRenderer() : undefined; };

  // ---------- selection / editing ----------
  function drawSel() {
    sel.clear();
    if (!selected || !editing) return;
    const s = 1 / world.scale.x;
    const wb = selected.view.getBounds();
    const p0 = world.toLocal({ x: wb.x, y: wb.y }), p1 = world.toLocal({ x: wb.x + wb.width, y: wb.y + wb.height });
    sel.rect(p0.x, p0.y, p1.x - p0.x, p1.y - p0.y).stroke({ color: 0x4ea1ff, width: 2 * s });
    sel.circle(selected.item.x, selected.item.y, 5 * s).fill(0x4ea1ff);
  }
  app.ticker.add(drawSel);

  function select(entry) {
    selected = entry || null;
    $("insp").style.display = selected && editing ? "block" : "none";
    if (!selected) return;
    const it = selected.item;
    $("iName").textContent = it.name;
    $("iSkin").value = it.skin; $("iAnim").value = it.anim;
    $("iX").value = it.x; $("iY").value = it.y; $("iScale").value = it.scale ?? 1; $("iScaleY").value = it.scaleY ?? 1;
    $("iRot").value = it.rotation ?? 0; $("iTS").value = it.timeScale ?? 1; $("iFlip").checked = !!it.flipX;
  }
  const num = (v, d) => (isFinite(parseFloat(v)) ? parseFloat(v) : d);
  const onField = () => {
    if (!selected) return;
    const it = selected.item;
    it.x = Math.round(num($("iX").value, it.x)); it.y = Math.round(num($("iY").value, it.y));
    it.scale = num($("iScale").value, 1); it.rotation = num($("iRot").value, 0);
    const sy = num($("iScaleY").value, 1); if (sy !== 1) it.scaleY = sy; else delete it.scaleY;
    it.timeScale = num($("iTS").value, 1);
    if ($("iFlip").checked) it.flipX = true; else delete it.flipX;
    applyView(selected.view, it);
  };
  ["iX", "iY", "iScale", "iScaleY", "iRot", "iTS", "iFlip"].forEach((id) => $(id).addEventListener("input", onField));
  const rebuildSelected = () => {
    if (!selected) return;
    const it = selected.item;
    it.skin = $("iSkin").value; it.anim = $("iAnim").value;
    const nv = makeView(it, views.indexOf(selected));
    animLayer.addChildAt(nv, animLayer.getChildIndex(selected.view));
    selected.view.destroy();
    selected.view = nv;
    setDebug(debug);
  };
  $("iSkin").onchange = rebuildSelected;
  $("iAnim").onchange = rebuildSelected;
  $("iDup").onclick = () => {
    if (!selected) return;
    const it = { ...selected.item, name: selected.item.name + " copy", x: selected.item.x + 20, y: selected.item.y + 20 };
    const items = L().items; items.splice(items.indexOf(selected.item) + 1, 0, it);
    const v = makeView(it, items.length);
    animLayer.addChildAt(v, animLayer.getChildIndex(selected.view) + 1);
    const entry = { item: it, view: v }; views.push(entry); select(entry); setDebug(debug);
  };
  const del = () => {
    if (!selected) return;
    const items = L().items; items.splice(items.indexOf(selected.item), 1);
    selected.view.destroy(); views = views.filter((x) => x !== selected); select(null);
  };
  $("iDel").onclick = del;

  let drag = null;
  function startDrag(e) {
    const p = world.toLocal(e.global);
    drag = { dx: selected.item.x - p.x, dy: selected.item.y - p.y };
  }
  app.stage.eventMode = "static";
  app.stage.hitArea = app.screen;
  app.stage.on("pointermove", (e) => {
    if (!drag || !selected) return;
    const p = world.toLocal(e.global);
    selected.item.x = Math.round(p.x + drag.dx); selected.item.y = Math.round(p.y + drag.dy);
    applyView(selected.view, selected.item);
    $("iX").value = selected.item.x; $("iY").value = selected.item.y;
  });
  const endDrag = () => (drag = null);
  app.stage.on("pointerup", endDrag).on("pointerupoutside", endDrag);
  app.stage.on("pointerdown", () => { if (editing) select(null); });
  app.canvas.addEventListener("wheel", (e) => {
    if (!editing || !selected) return;
    e.preventDefault();
    const it = selected.item;
    if (e.shiftKey) it.rotation = Math.round(((it.rotation ?? 0) + (e.deltaY > 0 ? 5 : -5)) % 360);
    else it.scale = Math.max(0.05, Math.round((it.scale ?? 1) * (e.deltaY > 0 ? 0.95 : 1.05) * 100) / 100);
    applyView(selected.view, it); select(selected);
  }, { passive: false });

  function setEdit(v) {
    editing = v;
    $("edit").classList.toggle("on", v);
    $("edit").textContent = v ? "Editing" : "Edit";
    views.forEach(({ view }) => (view.cursor = v ? "move" : "default"));
    select(v ? selected : null);
  }
  $("edit").onclick = () => setEdit(!editing);
  function setDebug(v) {
    debug = v;
    $("bones").classList.toggle("on", v);
    for (const { view } of views) {
      if (v && !view.debug) view.debug = new spine.SpineDebugRenderer();
      if (!v && view.debug) view.debug = undefined;
    }
  }
  $("bones").onclick = () => setDebug(!debug);

  // ---------- playback ----------
  const refreshSpeed = () => { views.forEach(({ item, view }) => applyView(view, item)); if (fx) fx.view.state.timeScale = playing ? speed : 0; };
  const setSpeed = (s) => { speed = s; $("speed").value = s; $("speedV").textContent = s.toFixed(s < 1 && s % 0.5 ? 2 : 1) + "x"; refreshSpeed(); };
  $("play").onclick = () => { playing = !playing; $("play").textContent = playing ? "❚❚ Pause" : "▶ Play"; $("play").classList.toggle("on", !playing); refreshSpeed(); };
  $("speed").oninput = (e) => setSpeed(parseFloat(e.target.value));
  $("speedChips").querySelectorAll("button").forEach((b) => (b.onclick = () => setSpeed(parseFloat(b.dataset.s))));

  window.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    const k = e.key.toLowerCase();
    if (k === "e") setEdit(!editing);
    if (k === "d") setDebug(!debug);
    if (k === " ") { e.preventDefault(); $("play").click(); }
    const lvKey = { w: "win", c: "crash_win", s: "smash_win", r: "wreckage_win", x: "total_win" }[k];
    if (lvKey) playFx(lvKey);
    if (k === "1") setLayout("landscape");
    if (k === "2") setLayout("portrait");
    if (k === "t") { const ids = Object.keys(DATA.themes); setTheme(ids[(ids.indexOf(theme) + 1) % ids.length]); }
    if ((k === "delete" || k === "backspace") && editing) del();
  });

  // ---------- save / load ----------
  const download = (name, text, type) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type }));
    a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  };
  $("savePl").onclick = () => { download("placements.json", JSON.stringify(T().placements, null, 1), "application/json"); toast(`placements.json downloaded → replace themes/${theme}/placements.json`); };
  $("bake").onclick = () => { download("data.js", "// AUTO-GENERATED preview data\nwindow.ENV_DATA = " + JSON.stringify(DATA) + ";\n", "text/javascript"); toast("data.js downloaded → replace preview/data.js"); };

  const readUrl = (f) => new Promise((r) => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(f); });
  const atlasPages = (txt) => txt.split(/\r?\n/).map((l) => l.trim()).filter((l) => /\.(png|jpe?g|webp)$/i.test(l));
  // Accepts: env-animation root (themes/<id>/..., win_fx/...) or a single theme folder (env.json + env.atlas + placements.json).
  $("dir").onchange = async (e) => {
    const files = [...e.target.files];
    const rel = (f) => f.webkitRelativePath.split("/").slice(1).join("/");
    try {
      const dirs = {};
      for (const f of files) { const p = rel(f); const d = p.includes("/") ? p.slice(0, p.lastIndexOf("/")) : ""; (dirs[d] ||= {})[f.name] = f; }
      const themeDirs = Object.keys(dirs).filter((d) => dirs[d]["env.json"] && dirs[d]["env.atlas"] && dirs[d]["placements.json"]);
      if (!themeDirs.length) throw new Error("No folder with env.json + env.atlas + placements.json");
      const next = { themes: { ...DATA.themes }, fx: DATA.fx };
      for (const d of themeDirs) {
        const F = dirs[d];
        const id = d ? d.split("/").pop() : (theme || "theme");
        const t = { label: DATA.themes[id]?.label || id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()), skeleton: await F["env.json"].text(), atlas: await F["env.atlas"].text(), placements: JSON.parse(await F["placements.json"].text()), images: {} };
        const bgs = ["landscape", "portrait"].map((k) => t.placements[k]?.background).filter(Boolean);
        for (const n of [...atlasPages(t.atlas), ...bgs]) { if (!F[n]) throw new Error(`Missing ${d}/${n}`); t.images[n] = await readUrl(F[n]); }
        next.themes[id] = t;
        delete skelCache[id];
        Object.keys(texCache).filter((k) => k.startsWith(id + "/")).forEach((k) => delete texCache[k]);
      }
      const fxDir = Object.keys(dirs).find((d) => dirs[d]["win_fx.json"] && dirs[d]["win_fx.atlas"]);
      if (fxDir !== undefined) {
        const F = dirs[fxDir];
        next.fx = { skeleton: await F["win_fx.json"].text(), atlas: await F["win_fx.atlas"].text(), images: {} };
        for (const n of atlasPages(next.fx.atlas)) { if (!F[n]) throw new Error(`Missing ${fxDir}/${n}`); next.fx.images[n] = await readUrl(F[n]); }
        Object.keys(texCache).filter((k) => k.startsWith("win_fx/")).forEach((k) => delete texCache[k]);
      }
      DATA = next;
      renderThemeButtons();
      await buildFx();
      const loaded = themeDirs.map((d) => (d ? d.split("/").pop() : theme));
      await setTheme(loaded.includes(theme) ? theme : loaded[0]);
      toast(`Loaded: ${loaded.join(", ")}${fxDir !== undefined ? " + win_fx" : ""}`);
    } catch (err) { console.error(err); toast(err.message); }
    e.target.value = "";
  };

  // ---------- boot ----------
  if (!DATA) { $("info").textContent = "data.js missing — use Load folder"; return; }
  renderThemeButtons();
  const ids = Object.keys(DATA.themes);
  const savedT = store.get("env-theme"), savedL = store.get("env-layout");
  theme = ids.includes(savedT) ? savedT : ids[0];
  if (savedL === "portrait" || savedL === "landscape") layout = savedL;
  await buildFx();
  await setTheme(theme);
})();
