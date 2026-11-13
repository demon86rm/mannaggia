// Parts library of the 96 px portrait generator. Every portrait is built from a description
// (skin, hair, beard, features, robe, headgear, attribute, colours) on ONE fixed geometry, the one
// of the approved prototypes: face rx 18 ry 21 at y 43, neck 24 px, halo r 35 at y 34, shoulders
// full width. The eyes and brows stay out of the portrait (the app draws them, occhi.px.js) at
// FIXED places: eyes at y 41, brows at y 36, far-side shadow from x > cx + 12. Nothing else may be
// drawn in that area (verifica_occhi() checks it).
// Everything is `var`/function: this file is included by several files.
include("occhi.px.js")
pal({ K: "#22181f", W: "#fff6ea", X: "#ffffff", E: "#2a2228" })
shades("1234", "#888890")   // a ramp: the shade layer needs one (on hex colours it darkens)

var G96 = { S: 96, F: 94, cx: 47, EYE_Y: 41, BROW_Y: 36, FAR: 12 }

// --- colour: hue-shifted ramps as pxl's shades() (MIT), one per material and per saint
function _hsl(r, g, b) {
  r /= 255; g /= 255; b /= 255
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn
  if (!d) return [0, 0, l]
  const s = d / (1 - Math.abs(2 * l - 1))
  const h = mx === r ? ((g - b) / d + 6) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4
  return [h * 60, s, l]
}
function _rgb(h, s, l) {
  const c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = l - c / 2
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x]
  return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)]
}
function _toward(a, b, by) { const d = ((b - a + 540) % 360) - 180; return (a + Math.sign(d) * Math.min(Math.abs(d), by) + 360) % 360 }
function hex2rgb(h) { return [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)) }
function rgb2hex(c) { return "#" + c.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("") }
function mixc(a, b, t) { const x = hex2rgb(a), y = hex2rgb(b); return rgb2hex(x.map((v, i) => v + (y[i] - v) * t)) }
// 4 tones dark -> light: [0] deep shadow, [1] shadow, [2] base, [3] light
function ramp(base, { shift = 24, spread = 0.56, sat = 1 } = {}) {
  const [h, s0, l0] = _hsl(...hex2rgb(base))
  return [0, 1, 2, 3].map((i) => {
    const t = i / 3 - 0.5
    const l = Math.max(0.04, Math.min(0.96, l0 + t * spread))
    const hh = t < 0 ? _toward(h, 250, shift * -t * 2) : _toward(h, 55, shift * t * 2)
    const s = Math.max(0, Math.min(1, s0 * sat * (t < 0 ? 1 + 0.15 * -t * 2 : 1 - 0.3 * t * 2)))
    return rgb2hex(_rgb(hh, s, l))
  })
}
// the base colour must be the [2] tone: shift the ramp so that it is
function rampa(base, o = {}) {
  const r = ramp(base, o), d = hex2rgb(base), b = hex2rgb(r[2])
  return r.map((c) => rgb2hex(hex2rgb(c).map((v, i) => v + d[i] - b[i])))
}

// the curls round the head and on the fringe (San Giorgio's)
var RICCI = [[-20, 34], [-21, 26], [-17, 18], [-11, 13], [-4, 11], [4, 11], [11, 13], [17, 18], [21, 26], [20, 34]]
// the hood lowered behind the neck: a roll of the habit's own colour, its lower rim and fold in shadow
var cappuccioGiu = (col, ombra) => [ellipse(G96.cx, 72, 22, 7, col),
  recolor({ [col]: ombra }, (x, y) => { const q = Math.hypot((x - G96.cx) / 22, (y - 72) / 7); return y >= 72 && q > 0.82 && q <= 1 }),
  hline(G96.cx - 13, 75, 27, ombra)]
var ell96 = (x, y, x0, y0, rx, ry) => ((x - x0) / rx) ** 2 + ((y - y0) / ry) ** 2 <= 1
var inFaccia = (x, y) => ell96(x, y, G96.cx, 43, 18, 21)
// mirror a polygon around the axis
var spec = (pts) => pts.map((v, i) => (i % 2 ? v : 2 * G96.cx - v))
var simm = (pts, col) => [poly(pts, col), poly(spec(pts), col)]

// --- head, behind the figure: hair that falls behind, neck
function capelliDietro(d, hr) {
  const { cx } = G96, h = d.capelli
  if (h === "lunghi_lisci" || h === "trecce") return [ellipse(cx, 36, 23, 20, hr[2]), rect(cx - 23, 36, 46, 34, hr[2])]
  if (h === "lunghi") return [ellipse(cx, 36, 23, 20, hr[2]), rect(cx - 23, 36, 46, 26, hr[2])]
  if (h === "afro") return [[ellipse(cx, 30, 23, 18, hr[2]), rect(cx - 21, 30, 42, 12, hr[2])],
    [ellipse(cx, 32, 20, 15, hr[2]), rect(cx - 20, 32, 40, 10, hr[2])],
    [ellipse(cx, 29, 24, 21, hr[2]), rect(cx - 20, 36, 40, 7, hr[2])]][d.afro_v || 0]   // tall: an oval mass
  if (h === "corti" || h === "lisci") return [ellipse(cx, 31, 21, 17, hr[2]), rect(cx - 21, 31, 42, 11, hr[2])]
  if (h === "ricci") return [ellipse(cx, 30, 22, 19, hr[2]), rect(cx - 22, 30, 44, 15, hr[2]),
    ...RICCI.map(([dx, y]) => circ(cx + dx, y, 5, hr[2]))]
  // tonsure (as San Lorenzo): the hair mass behind the head, short at the temples; the crown is shaved in front
  if (h === "tonsura") return [ellipse(cx, 33, 22, 18, hr[2]), rect(cx - 22, 33, 44, 10, hr[2])]
  // bald: the hair left on the sides, and a skull as tall and wide as the others' hair (top at y 14),
  // so the head is not squashed and the forehead curves gently; far side in shadow
  if (h === "calvo") { const sk = d._sk
    // the fringe of hair follows the skull: a band round the back of the head, thin towards the temples
    return [clip((x, y) => y <= 37, ellipse(cx, 32, 19, 18, sk[2])),
      recolor({ [sk[2]]: sk[1] }, (x, y) => y <= 37 && x > cx + G96.FAR),
      clip((x, y) => !ell96(x, y, cx, 27, 17, 17), ellipse(cx, 37, 21, 15, hr[2])),
      recolor({ [hr[2]]: hr[1] }, (x, y) => x > cx + G96.FAR)] }
  return []
}
function collo(sk) {
  const { cx } = G96
  return [rect(cx - 12, 58, 24, 14, sk[2]), rect(cx - 12, 58, 24, 6, sk[1])]     // the chin's shadow on the neck
}
function spalle(col) {
  const { cx, F } = G96
  // the shoulders close at the middle (cx, 68): without that point a triangle under the neck stays empty
  return [ellipse(cx, F + 20, 46, 34, col), ...simm([cx - 13, 68, cx - 30, 76, cx - 46, 82, cx - 46, 94, cx, 94, cx, 68], col)]
}

// --- robes: each returns the items of the bust from the shoulders down
var ABITI = {
  tunica(d, rb) {
    const { cx } = G96
    // round neckline: the neck goes on into it in its own colour, the tunic's hem a thin line below
    return [...spalle(rb[2]), ellipse(cx, 70, 12, 4, rb[1]), ellipse(cx, 69, 11, 3, d._sk[2]),
      ...[cx - 26, cx - 9, cx + 9, cx + 26].map((x) => vline(x, 80, 16, rb[1])),
      recolor({ [rb[2]]: rb[1] }, (x, y) => y > 72 && x > cx + 12)]
  },
  // the mantle over one shoulder (apostles, laymen): a second colour, diagonal
  mantello(d, rb, col) {
    const { cx } = G96, m = rampa(d.secondo || col)
    return [...ABITI.tunica(d, rb), poly([cx - 46, 81, cx - 14, 69, cx + 2, 94, cx - 46, 94], m[2]),
      line(cx - 14, 69, cx + 2, 94, m[3]), line(cx - 30, 76, cx - 20, 94, m[1])]
  },
  suora(d, rb) {
    const { cx } = G96, w = rampa("#ece8e0", { shift: 14, sat: 0.5 })
    return [...spalle(rb[2]), ellipse(cx, 66, 12, 8, w[2]), ellipse(cx, 60, 17, 9, w[2]),
      recolor({ [w[2]]: w[1] }, (x, y) => y < 63 || x > cx + 8),
      recolor({ [rb[2]]: rb[1] }, (x, y) => y > 72 && x > cx + 12)]
  },
  domenicano(d, rb) {   // white habit, black cappa open on the front, white scapular
    const { cx } = G96, b = rampa("#2c2830")
    // the black hood lowered on the shoulders, with its fold (as the saio), the white habit under the chin
    return [...spalle(rb[2]), ...simm([cx - 14, 69, cx - 46, 82, cx - 46, 94, cx - 13, 94, cx - 11, 78], b[2]),
      ...cappuccioGiu(b[2], b[0]),
      vline(cx - 1, 78, 16, rb[1])]
  },
  saio(d, rb) {         // habit with the hood lowered behind the neck, a white cord
    const { cx } = G96
    return [...spalle(rb[2]), ...cappuccioGiu(rb[2], rb[1]),
      vline(cx - 8, 80, 14, "#ece0c4"), px(cx - 8, 86, "#c8b890"), px(cx - 8, 91, "#c8b890"),
      ...[cx - 26, cx + 26].map((x) => vline(x, 82, 12, rb[1])),
      recolor({ [rb[2]]: rb[1] }, (x, y) => y > 74 && x > cx + 12)]
  },
  talare(d, rb) {       // cassock: Roman collar, a row of buttons, a short shoulder cape
    const { cx } = G96
    return [...spalle(rb[2]), ellipse(cx, 77, 32, 9, rb[3]), ellipse(cx, 78, 31, 8, rb[2]),
      rect(cx - 3, 68, 6, 3, "#f4f0e8"), ...[80, 84, 88, 92].map((y) => px(cx, y, rb[3])),
      recolor({ [rb[2]]: rb[1] }, (x, y) => y > 74 && x > cx + 12)]
  },
  vescovo(d, rb) {      // chasuble with the gold Y-shaped orphrey, white amice at the neck
    const { cx } = G96, g = rampa("#e2b646")
    return [...spalle(rb[2]), ellipse(cx, 71, 17, 5, "#f0ece4"), recolor({ "#f0ece4": "#d8d2c8" }, (x, y) => y > 72 || x > cx + 8),
      line(cx - 20, 74, cx - 2, 86, g[2], 3), line(cx + 20, 74, cx + 2, 86, g[2], 3), rect(cx - 2, 85, 5, 9, g[2]),
      line(cx - 20, 73, cx - 2, 85, g[3]), recolor({ [rb[2]]: rb[1], [g[2]]: g[1] }, (x, y) => y > 74 && x > cx + 12)]
  },
  benedettino(d, rb) {  // black cowl: the hood lowered behind the neck, the scapular down the front
    const { cx } = G96
    return [...spalle(rb[2]), rect(cx - 10, 77, 20, 17, rb[1]), ...cappuccioGiu(rb[2], rb[0]),
      ...[cx - 26, cx + 26].map((x) => vline(x, 82, 12, rb[1])), recolor({ [rb[2]]: rb[1] }, (x, y) => y > 74 && x > cx + 12)]
  },
  cistercense(d, rb) {  // white cowl, black scapular and hood
    const { cx } = G96, b = rampa("#2c2830")
    return [...spalle(rb[2]), rect(cx - 10, 77, 20, 17, b[2]), ...cappuccioGiu(b[2], b[0]),
      ...[cx - 26, cx + 26].map((x) => vline(x, 82, 12, rb[1])), recolor({ [rb[2]]: rb[1] }, (x, y) => y > 74 && x > cx + 12)]
  },
  regale(d, rb) {       // a gold-trimmed tunic, the mantle on the shoulders, the ermine collar
    const { cx } = G96, g = rampa("#e2b646"), m = rampa(d.secondo || "#b8302c"), w = rampa("#f0ece4", { shift: 14, sat: 0.4 })
    return [...spalle(rb[2]), ...simm([cx - 14, 68, cx - 32, 75, cx - 46, 81, cx - 46, 94, cx - 22, 94, cx - 16, 78], m[2]),
      ellipse(cx, 70, 20, 6, w[2]), ...[-14, -6, 4, 12].map((dx) => rect(cx + dx, 69, 1, 2, "#1e1a20")),
      recolor({ [w[2]]: w[1] }, (x, y) => ell96(x, y, cx, 70, 20, 6) && (y > 71 || x > cx + 8)),
      rect(cx - 2, 77, 5, 17, g[2]), vline(cx - 2, 77, 17, g[3]),
      recolor({ [rb[2]]: rb[1], [m[2]]: m[1] }, (x, y) => y > 74 && x > cx + 12)]
  },
  papa(d, rb) {         // white cassock, red mozzetta with buttons, gold stole
    const { cx } = G96, r = rampa("#b8302c"), g = rampa("#e2b646")
    return [...spalle(rb[2]), ellipse(cx, 77, 34, 10, r[2]), rect(cx - 3, 66, 6, 2, "#f4f0e8"),   // the white collar, small
      line(cx - 8, 76, cx - 6, 94, g[2], 3), line(cx + 8, 76, cx + 6, 94, g[2], 3), ...[78, 82].map((y) => px(cx, y, rb[3])),
      recolor({ [rb[2]]: rb[1], [r[2]]: r[1] }, (x, y) => y > 72 && x > cx + 12)]
  },
  cardinale(d, rb) {    // red cassock and mozzetta, a white collar
    const { cx } = G96
    return [...spalle(rb[2]), ellipse(cx, 77, 34, 10, rb[1]), ellipse(cx, 78, 33, 9, rb[2]), rect(cx - 3, 68, 6, 3, "#f4f0e8"),
      ...[80, 84, 88, 92].map((y) => px(cx, y, rb[3])), recolor({ [rb[2]]: rb[1] }, (x, y) => y > 72 && x > cx + 12)]
  },
  armatura(d, rb) {     // steel plate (San Giorgio's, without the surcoat): mail coif, pauldrons with lames
    const { cx } = G96, s = rampa("#9aa2b0", { shift: 12 })
    return [...spalle(s[2]), ellipse(cx - 34, 85, 16, 12, s[2]), ellipse(cx + 34, 85, 16, 12, s[2]), ellipse(cx, 72, 21, 7, s[1]),
      recolor({ [s[1]]: s[0] }, (x, y) => ell96(x, y, cx, 72, 21, 7) && (x + 2 * y) % 3 === 0),
      (c) => { for (const sx of [-1, 1]) for (const y of [81, 86]) { const x0 = cx + sx * 34
        c.recolor({ [s[2]]: s[0] }, (x, yy) => yy === y && Math.abs(x - x0) <= 15); c.recolor({ [s[2]]: s[3] }, (x, yy) => yy === y + 1 && Math.abs(x - x0) <= 14) } },
      line(cx, 78, cx, 94, s[1]), recolor({ [s[2]]: s[1] }, (x, y) => y > 76 && x > cx + 30)]
  },
  moderno(d, rb) {      // jacket with lapels over a white shirt
    const { cx } = G96
    return [...spalle(rb[2]), poly([cx - 8, 68, cx + 8, 68, cx, 84], "#f0ece4"), ...simm([cx - 9, 68, cx - 14, 72, cx - 2, 90, cx, 84], rb[1]),
      recolor({ [rb[2]]: rb[1] }, (x, y) => y > 74 && x > cx + 12)]
  },
  dalmatica(d, rb) {    // deacon's dalmatic: white amice, two gold clavi (San Lorenzo)
    const { cx } = G96, g = rampa("#e2b646")
    return [...spalle(rb[2]), ellipse(cx, 71, 18, 6, "#f0ece4"), recolor({ "#f0ece4": "#d8d2c8" }, (x, y) => x > cx + 6 || y < 69),
      rect(cx - 19, 76, 5, 18, g[2]), rect(cx + 15, 76, 5, 18, g[1]), vline(cx - 19, 76, 18, g[3]),
      recolor({ [rb[2]]: rb[1] }, (x, y) => y > 72 && x > cx + 10)]
  },
  // Korean dress (hanbok): crossed collar with a white band, a ribbon (goreum)
  hanbok(d, rb) {
    const { cx } = G96
    return [...spalle(rb[2]), poly([cx - 12, 68, cx + 10, 88, cx + 6, 90, cx - 15, 70], "#f4f0e8"),
      poly([cx + 12, 68, cx - 2, 80, cx - 4, 77, cx + 9, 67], "#f4f0e8"),
      line(cx + 4, 84, cx - 2, 94, "#b8302c", 2), line(cx + 5, 84, cx + 9, 94, "#b8302c", 2),
      recolor({ [rb[2]]: rb[1] }, (x, y) => y > 74 && x > cx + 14)]
  },
  // a blanket wrapped round the shoulders, with a coloured band
  coperta(d, rb, col) {
    const { cx } = G96, m = rampa(col)
    return [...spalle(rb[2]), ...simm([cx - 16, 70, cx - 46, 82, cx - 46, 94, cx - 6, 94], m[2]),
      clip((x, y) => (y === 84 || y === 85 || y === 90) && x !== cx, ...simm([cx - 16, 70, cx - 46, 82, cx - 46, 94, cx - 6, 94], "#e8c45a")),
      clip((x, y) => y === 87 && x !== cx, ...simm([cx - 16, 70, cx - 46, 82, cx - 46, 94, cx - 6, 94], "#b8302c")),
      recolor({ [m[2]]: m[1], "#e8c45a": "#c8a040" }, (x, y) => x > cx + 12)]
  },
  // Juan Diego's tilma: a cloak knotted on the right shoulder
  tilma(d, rb, col) {
    const { cx } = G96, m = rampa(col)
    return [...spalle(rb[2]), poly([cx - 46, 80, cx - 14, 69, cx + 18, 70, cx + 32, 76, cx + 10, 94, cx - 46, 94], m[2]),
      ellipse(cx + 18, 72, 3, 2, m[0]), ...[cx - 30, cx - 12, cx + 4].map((x) => vline(x, 80, 14, m[1]))]
  },
}

// --- the face: skin, shading, features. Never inside the eye area.
// face variants (d.viso, d.naso_v, d.bocca from the name, see esporta.py), all within the approved
// proportions (face rx 18-19, ry 21-22) and outside the eye area
var VISI = [[18, 21, false], [19, 21, false], [18, 22, true]]          // rx, ry, squarer chin
function faccia(d, sk) {
  const { cx, FAR } = G96, lab = d.labbra === "piene", largo = d.naso === "largo"
  const [rx, ry, mento] = VISI[d.viso || 0]
  const lip = mixc(sk[0], "#9a3a3a", 0.4), lipL = mixc(lip, sk[3], 0.35)
  const it = [ellipse(cx, 43, rx, ry, sk[2]), ...(mento ? [rect(cx - 8, 60, 17, 4, sk[2])] : []),
    recolor({ [sk[2]]: sk[1] }, (x, y) => (ell96(x, y, cx, 43, rx, ry) || (mento && y >= 60 && y <= 63 && Math.abs(x - cx) <= 8)) && x > cx + FAR)]
  // nose: 0 straight, 1 long and pointed, 2 short and rounded; "largo" spreads the nostrils. Nothing of the
  // nose goes below y 52: row 53 stays skin, so the mouth (54, a smile's corners 53) never touches it
  const nv = d.naso_v || 0, w = largo ? 1 : 0
  if (nv === 0) it.push(vline(cx + 1, 44, 7, sk[1]), vline(cx - 1, 44, 3, sk[3]))
  if (nv === 1) it.push(vline(cx + 1, 44, 8, sk[1]), vline(cx - 1, 44, 6, sk[3]), px(cx, 51, sk[3]))      // 1: a long ridge to the tip at y 51
  if (nv === 2) it.push(vline(cx + 1, 46, 3, sk[1]), px(cx - 1, 47, sk[3]), hline(cx - 1, 50, 3, sk[1]), px(cx, 49, sk[3]))   // 2: a short ridge, a round tip
  it.push(hline(cx - 3 - w, 51, 1 + w, sk[1]), hline(cx + 3, 51, 1 + w, sk[1]))   // nostrils symmetric about cx
  if (largo) it.push(px(cx - 3, 52, sk[1]), px(cx + 3, 52, sk[1]))
  // mouth: 0 wide, 1 narrow with the lower lip in shadow, 2 a wider smile with the corners up
  const bv = d.bocca || 0, bw = [9, 5, 7][bv], bx = cx - [4, 2, 3][bv]   // odd widths: centred on the axis pixel cx
  it.push(hline(bx, 54, bw, lip))
  if (lab) it.push(hline(bx + 1, 55, bw - 2, lipL))
  if (bv === 1) it.push(hline(cx - 2, lab ? 56 : 55, 5, sk[1]), hline(cx - 1, lab ? 57 : 56, 3, sk[1]))
  if (bv === 2) it.push(px(bx - 1, 53, lip), px(bx + bw, 53, lip))
  if (d.eta === "anziano") it.push(hline(cx - 6, 29, 12, sk[1]), line(cx - 8, 49, cx - 9, 55, sk[1]), line(cx + 9, 49, cx + 10, 55, sk[1]))
  if (d.guance) it.push(hline(cx - 14, 48, 3, mixc(sk[2], "#e07070", 0.25)), hline(cx + 12, 48, 3, mixc(sk[1], "#e07070", 0.2)))
  return it
}

// ears, beside the face, when no veil, hood or long hair covers them (x <= 31 and >= 63: off the eye area)
function orecchie(d, sk) {
  const { cx } = G96
  if (["velo", "cappuccio", "sari", "elmo"].includes(d.copricapo) || ["lunghi", "lunghi_lisci", "trecce"].includes(d.capelli)) return []
  const rim = mixc(sk[3], "#ffffff", 0.3)
  return [ellipse(cx - 19, 43, 2, 4, sk[2]), vline(cx - 19, 42, 3, sk[0]), vline(cx - 21, 41, 5, rim),
    ellipse(cx + 19, 43, 2, 4, sk[1]), vline(cx + 19, 42, 3, sk[0]), px(cx + 20, 40, mixc(sk[2], "#ffffff", 0.2))]
}

// --- hair over the face (fringe, curls, braids): never below y 31
function capelliDavanti(d, hr) {
  const { cx } = G96, h = d.capelli, top = (y) => y <= 30
  const it = []
  const at = d.attacc || 0                                  // the hairline one row higher or lower
  if (h === "corti") it.push(clip((x, y) => y <= 27 + at, ellipse(cx, 32, 19, 13, hr[2])),
    recolor({ [hr[2]]: hr[3] }, (x, y) => ell96(x, y, cx - 7, 18, 7, 3)))
  if (h === "lisci" || h === "lunghi_lisci" || h === "trecce" || h === "lunghi") {
    // a straight fringe, parted on the left, with strands
    it.push(clip((x, y) => y <= 28 + at, ellipse(cx, 32, 19, 13, hr[2])),
      ...[cx - 12, cx - 6, cx + 2, cx + 8, cx + 14].map((x) => clip((xx, y) => top(y), vline(x, 20, 9, hr[1]))),
      line(cx - 4, 16, cx - 2, 24, hr[0]), recolor({ [hr[2]]: hr[3] }, (x, y) => ell96(x, y, cx - 9, 18, 6, 2)))
  }
  if (h === "afro") {
    // tightly curled: a mass with a curled edge and small coils inside; 0 round, 1 cropped short, 2 tall
    const [ey, ery, erx, top] = [[30, 18, 22, 13], [32, 15, 20, 18], [29, 21, 23, 10]][d.afro_v || 0]
    it.push(clip((x, y) => y <= 27 + at, ellipse(cx, ey, 20, ery - 4, hr[2])),
      ...(d.afro_v === 1 ? [] : [(c) => { for (let a = 0; a < 26; a++) { const t = Math.PI * (0.05 + a / 25 * 0.9)
        c.circ(Math.round(cx - erx * Math.cos(t)), Math.round(ey - ery * Math.sin(t)), 2, hr[2]) } }]),
      // small coils scattered irregularly (a fixed pseudo-random pattern), each a dark dot with a lit one above
      (c) => { for (let k = 0; k < 40; k++) { const x = cx - 18 + ((k * 37) % 37), y = top + ((k * 23 + (k >> 2) * 5) % (27 + at - top))
        if (ell96(x, y, cx, ey, 20, ery - 2)) { c.px(x, y, hr[1]); if (k % 3) c.px(x - 1, y - 1, hr[3]) } } })
  }
  if (h === "ricci") it.push(...[-14, -7, 0, 7, 14].map((dx) => clip((x, y) => y <= 27, circ(cx + dx, 24, 5, hr[2]))),
    (c) => { for (const [dx, y] of [...RICCI, [-14, 24], [-7, 24], [0, 24], [7, 24], [14, 24]]) { const x0 = cx + dx
      c.recolor({ [hr[2]]: hr[3] }, (x, yy) => { const q = Math.hypot(x - x0, yy - y); return q > 2.5 && q < 4 && x < x0 && yy < y && yy <= 27 + (Math.abs(dx) > 16 ? 20 : 0) }) } },
    (c) => { for (const [dx, y] of RICCI) { const x0 = cx + dx
      c.recolor({ [hr[2]]: hr[1] }, (x, yy) => { const q = Math.hypot(x - x0, yy - y); return q > 4 && q < 5.2 }) } })
  if (h === "tonsura") it.push(ellipse(cx, 22, 14, 7, d._sk[2]), recolor({ [d._sk[2]]: d._sk[3] }, (x, y) => ell96(x, y, cx - 4, 20, 6, 3)),
    clip((x, y) => y >= 21 && y <= 28, ellipse(cx, 32, 19, 12, hr[2])),
    ...[-16, -12, -8, -4, 0, 4, 8, 12, 16].map((dx) => clip((x, y) => y >= 23 && y <= 27, vline(cx + dx, 23, 5, hr[1]))))
  if (h === "calvo") it.push(recolor({ [d._sk[2]]: d._sk[3] }, (x, y) => ell96(x, y, cx - 7, 20, 6, 2)))   // the light on the skull
  if (h === "trecce") it.push(...[-21, 21].map((dx) => (c) => {
    for (let y = 46; y <= 84; y += 4) { c.rect(cx + dx - 2, y, 5, 3, hr[2]); c.px(cx + dx - 2, y, hr[1]); c.px(cx + dx + 2, y + 2, hr[1]); c.px(cx + dx, y + 1, hr[3]) }
    c.rect(cx + dx - 1, 86, 3, 3, "#c84a3a") }))
  // far side of the hair one step darker
  it.push(recolor({ [hr[2]]: hr[1], [hr[3]]: hr[2] }, (x, y) => x > cx + 13 && y < 60))
  return it
}

function barba(d, hr) {
  const { cx } = G96
  if (d.barba === "corta") return [clip((x, y) => y >= 48, ellipse(cx, 49, 18, 15, hr[2])), ellipse(cx, 54, 5, 2, d._sk[1]),
    hline(cx - 6, 52, 13, hr[2]), recolor({ [hr[2]]: hr[1] }, (x, y) => x > cx + 9)]
  if (d.barba === "lunga") return [clip((x, y) => y >= 48, ellipse(cx, 52, 18, 16, hr[2])), poly([cx - 14, 60, cx + 14, 60, cx + 6, 80, cx, 83, cx - 6, 80], hr[2]),
    ellipse(cx, 54, 5, 2, d._sk[1]), hline(cx - 6, 52, 13, hr[2]),
    ...[cx - 6, cx, cx + 6].map((x) => line(x, 62, x + (x - cx) / 3, 78, hr[1])), recolor({ [hr[2]]: hr[1] }, (x, y) => x > cx + 9)]
  if (d.barba === "baffi") return [hline(cx - 5, 52, 11, hr[2]), hline(cx - 4, 53, 9, hr[1])]
  return []
}

// --- headgear: drawn last on the head, never below y 31 except at the sides of the face
var COPRICAPI = {
  velo(d) {     // nun's veil with a white band on the forehead
    const { cx } = G96, v = rampa(d.velo || "#2c2830"), w = rampa("#ece8e0", { shift: 14, sat: 0.5 })
    const ombra = d.velo_ombra_scura ? v[0] : v[1]          // one tone darker on request (Santa Cunegonda)
    return { dietro: [poly([cx - 26, 40, cx - 30, 70, cx - 44, 86, cx - 46, 94, cx + 46, 94, cx + 44, 86, cx + 30, 70, cx + 26, 40], v[2]),
      ellipse(cx, 38, 26, 27, v[2]), ellipse(cx, 41, 21, 24, ombra)],
      davanti: [clip((x, y) => y <= 29, ellipse(cx, 41, 21, 24, w[2])), clip((x, y) => y <= 23, ellipse(cx, 41, 21, 24, v[2])),
        recolor({ [v[2]]: v[3] }, (x, y) => { const q = Math.hypot((x - cx) / 26, (y - 38) / 27); return q > 0.9 && q < 1 && x < cx - 6 && y < 40 }),
        recolor({ [v[2]]: v[1] }, (x, y) => x > cx + 14 && !inFaccia(x, y))] }
  },
  cappuccio(d) { // hood up, in the robe's colour; with the modern robe it is a hoodie
    const { cx } = G96, v = d._rb
    if (d.abito === "felpa") {
      // the hoodie's hood: softer than the monk's, its sides falling onto the shoulders in the body's own
      // fabric (ABITI.felpa), the opening edged by a lighter fold, the fringe showing under it
      const bordo = (x, y) => { const q = Math.hypot((x - cx) / 21, (y - 42) / 24); return q > 0.86 && q <= 1.06 }
      return { dietro: [ellipse(cx, 40, 27, 27, v[2]), ...simm([cx - 27, 42, cx - 40, 80, cx - 14, 76, cx - 12, 58], v[2]), ellipse(cx, 42, 21, 24, v[0])],
        davanti: [clip((x, y) => y <= 22, ellipse(cx, 40, 27, 27, v[2])),
          recolor({ [v[2]]: v[3] }, (x, y) => bordo(x, y) && !inFaccia(x, y) && x < cx + 12 && y < 66),
          recolor({ [v[2]]: v[1] }, (x, y) => x > cx + 16 && !inFaccia(x, y) && y < 70)] }
    }
    return { dietro: [ellipse(cx, 38, 26, 28, v[2]), ellipse(cx, 41, 21, 24, v[0])],
      davanti: [clip((x, y) => y <= 26, ellipse(cx, 38, 26, 28, v[2])), recolor({ [v[2]]: v[1] }, (x, y) => x > cx + 14 && !inFaccia(x, y))] }
  },
  mitra(d) {    // bishop's mitre: white, gold band at the bottom and down the middle
    const { cx } = G96, w = rampa("#f0ece4", { shift: 14, sat: 0.5 }), g = rampa("#e2b646")
    return { dietro: [], davanti: [poly([cx - 16, 28, cx - 18, 12, cx, 1, cx + 18, 12, cx + 16, 28], w[2]),
      rect(cx - 17, 23, 34, 5, g[2]), rect(cx - 2, 3, 5, 20, g[2]), hline(cx - 17, 23, 34, g[3]),
      recolor({ [w[2]]: w[1], [g[2]]: g[1] }, (x, y) => x > cx + 8 && y < 28)] }
  },
  corona(d) {   // a gold crown with five points and red stones
    const { cx } = G96, g = rampa("#e2b646")
    return { dietro: [], davanti: [rect(cx - 17, 20, 34, 7, g[2]), hline(cx - 17, 20, 34, g[3]), hline(cx - 17, 26, 34, g[1]),
      ...[-14, -7, 0, 7, 14].map((dx) => poly([cx + dx - 3, 20, cx + dx, 12, cx + dx + 3, 20], g[2])),
      ...[-10, 0, 10].map((dx) => rect(cx + dx - 1, 22, 3, 3, "#c83a4a")), recolor({ [g[2]]: g[1] }, (x, y) => x > cx + 10)] }
  },
  tiara(d) {    // papal tiara: white, three gold crowns, a small cross on top
    const { cx } = G96, w = rampa("#f0ece4", { shift: 14, sat: 0.4 }), g = rampa("#e2b646")
    return { dietro: [], davanti: [clip((x, y) => y <= 27, ellipse(cx, 16, 15, 15, w[2])), ...[25, 18, 11].map((y) => rect(cx - 15 + (25 - y) / 2, y, 30 - (25 - y), 3, g[2])),
      rect(cx - 1, -1, 2, 4, g[2]), rect(cx - 2, 0, 4, 1, g[2]), recolor({ [w[2]]: w[1], [g[2]]: g[1] }, (x, y) => x > cx + 7 && y <= 27)] }
  },
  zucchetto_rosso(d) { const { cx } = G96; return { dietro: [], davanti: [clip((x, y) => y <= 20, ellipse(cx, 22, 14, 7, "#b8302c")), hline(cx - 6, 16, 6, "#e05a50")] } },
  zucchetto_bianco(d) { const { cx } = G96; return { dietro: [], davanti: [clip((x, y) => y <= 20, ellipse(cx, 22, 14, 7, "#f0ece4")), hline(cx - 6, 16, 6, "#ffffff")] } },
  gat(d) {      // Korean horsehair hat: a tall black crown, a wide brim, the chin strap
    const { cx } = G96, b = rampa("#2a2630")
    return { dietro: [], davanti: [rect(cx - 9, 6, 18, 14, b[2]), ellipse(cx, 6, 9, 2, b[1]), ellipse(cx, 21, 28, 4, b[2]),
      ellipse(cx, 20, 26, 2, b[3]), recolor({ [b[2]]: b[1] }, (x, y) => x > cx + 3 && y < 20),
      line(cx - 19, 24, cx - 17, 30, b[1]), line(cx + 19, 24, cx + 17, 30, b[1])] }
  },
}

// --- attributes, bottom right (x 64..92) or along the right edge
var ATTRIBUTI96 = {
  palma(d) {     // martyr's palm: a curved rib from the hand up to the right, leaflets on both sides
    const g = rampa("#5aa046")
    return [(c) => {
      const pts = []
      for (let k = 0; k <= 30; k++) { const t = k / 30; pts.push([Math.round(68 + 18 * t + 4 * Math.sin(t * Math.PI)), Math.round(94 - 62 * t)]) }
      for (let k = 2; k < pts.length - 1; k += 2) {           // leaflets, longer in the middle, drooping outwards
        const [x, y] = pts[k], n = Math.round(3 + 5 * Math.sin((k / pts.length) * Math.PI))
        for (let j = 1; j <= n; j++) { c.px(x - j, y + Math.floor(j / 2), j === n ? g[3] : g[2]); c.px(x + j, y + 1 + Math.floor(j / 2), j === n ? g[2] : g[1]) }
      }
      for (const [x, y] of pts) c.px(x, y, g[0])
    }]
  },
  croce(d) {
    const w = rampa("#8a5a34")
    return [rect(80, 30, 4, 64, w[2]), rect(72, 44, 20, 4, w[2]), vline(80, 30, 64, w[3]), hline(72, 44, 20, w[3])]
  },
  giglio(d) {
    const g = rampa("#4e8a3a"), wh = "#f6f2e6"
    return [line(70, 94, 80, 44, g[1]), line(74, 76, 82, 70, g[2]), line(72, 84, 66, 78, g[2]),
      ...[[80, 44], [76, 52], [84, 54]].flatMap(([x, y]) => [ellipse(x, y, 3, 4, wh), px(x, y, "#e8c45a"), px(x + 1, y + 2, "#d8d0c0")])]
  },
  libro(d) {
    const r = rampa("#8a2a2a")
    return [rect(66, 70, 22, 24, r[2]), rect(66, 70, 3, 24, r[1]), rect(69, 92, 19, 2, "#f0e8d0"), rect(76, 78, 6, 8, "#e2b646"), vline(87, 71, 22, r[0])]
  },
  pastorale(d) { // bishop's crozier: a gold staff with the crook at the top
    const g = rampa("#e2b646")
    // the staff rises to the crook's left end (x 77..79 at y 18): staff and crook are one piece
    return [rect(77, 18, 3, 76, g[2]), vline(77, 18, 76, g[3]), clip((x, y) => y <= 18 || x >= 84, ring(84, 18, 7, g[2]), ring(84, 18, 6, g[2]), ring(84, 18, 5, g[3])),
      rect(75, 30, 7, 4, g[1]), px(76, 31, g[3])]
  },
  bastone(d) {
    const w = rampa("#8a5a34")
    return [rect(80, 14, 3, 80, w[2]), vline(80, 14, 80, w[3]), ellipse(81, 13, 3, 3, w[1])]
  },
  spada(d) {     // sword held upright on the right (Santa Giovanna's)
    const s = rampa("#b6bcc4", { shift: 12 }), g = rampa("#e2b646")
    return [rect(79, 8, 5, 60, s[2]), vline(79, 8, 60, s[3]), vline(83, 8, 60, s[1]), poly([79, 8, 81, 3, 83, 8], s[2]),
      rect(71, 68, 21, 4, g[2]), hline(71, 68, 21, g[3]), rect(80, 72, 3, 12, "#5a3a24"), circ(81, 87, 3, g[2])]
  },
  sassofono(d) { // tenor sax at the side, the bell turned up (San John Coltrane)
    const b = rampa("#e2b040")
    // crook and mouthpiece right of the eye area (x >= 64)
    return [line(66, 42, 71, 47, b[1], 2), rect(64, 40, 3, 3, "#1e1a20"), line(72, 46, 74, 82, b[2], 5), line(74, 86, 84, 84, b[2], 5),
      poly([80, 84, 88, 84, 92, 62, 78, 62], b[2]), hline(78, 62, 15, b[1]), hline(80, 64, 11, "#5a4018"),
      ...[54, 62, 70, 78].map((y) => rect(71, y, 2, 2, b[0])), line(74, 48, 76, 80, b[3])]
  },
  scopa(d) {     // San Martino de Porres
    const w = rampa("#8a5a34"), s = rampa("#c8a050")
    return [line(70, 30, 82, 80, w[2], 2), poly([76, 78, 88, 74, 94, 94, 78, 94], s[2]), ...[80, 84, 88].map((x) => line(x, 80, x + 2, 94, s[1]))]
  },
  rosa(d) { return ATTRIBUTI96.rose(d) },
  rose(d) {      // Juan Diego: roses in the tilma
    return [ellipse(78, 84, 13, 9, "#d8c8a0"), ...[[72, 80], [80, 78], [86, 84], [76, 87], [83, 89]].flatMap(([x, y]) => [ellipse(x, y, 3, 3, "#c83a4a"), px(x - 1, y - 1, "#f07080"), px(x + 1, y + 1, "#8a1a2a")]),
      ...[[70, 85], [89, 80]].map(([x, y]) => ellipse(x, y, 2, 1, "#4e8a3a"))]
  },
}

var ALONE = {
  santo: ["#c2861c", "#e2b646", "#fce896", "#f2d27a"],   // ring, edge, fill, fill in shadow
  beato: ["#a89a6a", "#c4b88c", "#f6f2e0", "#ece6c8"],
}

// The portrait of description [d] as sprite [nome] (and its parts _nome_*). con_occhi: eyes open,
// looking ahead (for previews: in the app the eyes are an overlay).
// Each attribute is its own sprite with its own dark outline, made once and shared: so it is outlined
// everywhere, also over robes and armour (only the figure's silhouette had an outline before, so a
// dragon's horns were outlined against the sky and merged with San Giorgio's armour)
var _ATTR = new Set()
function attrSprite(a, d) {
  const k = a + (a === "lancia" && d.abito === "crociato" ? "_crociato" : "")
  if (!_ATTR.has(k)) { _ATTR.add(k); sprite(`_at_${k}`, { w: G96.F, h: G96.F, outline: "K" }, ...ATTRIBUTI96[a](d)) }
  return `_at_${k}`
}
// seq: an emotion of EMOZIONI (occhi.px.js) for an animated preview; without it the eyes are still
function ritratto96(nome, d, { con_occhi = true, seq = null } = {}) {
  const { S, F, cx, EYE_Y, BROW_Y, FAR } = G96
  const sk = rampa(d.pelle, { shift: 10, sat: 0.75 }), hr = rampa(d.chioma || "#5a4030", { shift: 8, sat: 0.8 }), rb = rampa(d.veste, { shift: 12 })   // hair colour: under a veil it is only the brows
  d._sk = sk; d._rb = rb
  // under a mitre, tiara, crown or skullcap a bald head shows only its bare edge, wider than the
  // headgear: there the hair at the temples (cut short) gives the head its shape
  if (["mitra", "tiara", "corona", "zucchetto_rosso", "zucchetto_bianco"].includes(d.copricapo) && ["calvo", "tonsura"].includes(d.capelli))
    d = { ...d, capelli: "corti" }
  const cop = d.copricapo && COPRICAPI[d.copricapo] ? COPRICAPI[d.copricapo](d) : { dietro: [], davanti: [] }
  const coperto = d.copricapo === "velo" || d.copricapo === "cappuccio"
  const frangia = !coperto || (d.copricapo === "cappuccio" && d.abito === "felpa")     // the hoodie shows the fringe
  const al = ALONE[d.beato ? "beato" : "santo"]
  sprite(`_${nome}_aureola`, { w: F, h: F, outline: "K" },
    circ(cx, 34, 35, al[0]), circ(cx, 34, 33, al[1]), circ(cx, 34, 29, al[2]),
    recolor({ [al[2]]: al[3] }, (x, y) => x + y > cx + 34 + 22))
  const occ = con_occhi ? [(c) => { occhi(c, cx, seq ? seq[c.frame] : fr(), { y: EYE_Y, browY: BROW_Y, iride: d.iride || "#5a4636",
    pelle: (x) => (x > cx + FAR ? sk[1] : sk[2]), ciglio: d.sopracciglia || hr[0], ombra: sk[1], forma: d.occhi || "" })
    if (d.occhiali) occhiali(c, cx, { y: EYE_Y, ...(typeof d.occhiali === "object" ? d.occhiali : {}) }) }] : []
  const extra = (d.extra || []).map((e) => (typeof EXTRA96 !== "undefined" && EXTRA96[e] ? EXTRA96[e](d) : {}))
  // a second attribute goes on the left, mirrored: its own sprite, the same for every saint
  const [a1, a2] = d.attributi || (d.attributo ? [d.attributo] : [])
  const s1 = a1 && ATTRIBUTI96[a1] ? attrSprite(a1, d) : null, s2 = a2 && ATTRIBUTI96[a2] ? attrSprite(a2, d) : null
  ;(seq ? (n, o, ...it) => anim(n, { ...o, frames: seq.length, fps: 12 }, ...it) : sprite)(`_${nome}_fig`, { w: F, h: F, outline: "K" },
    ...cop.dietro, ...(coperto ? [] : capelliDietro(d, hr)), ...collo(sk),
    ...(ABITI[d.abito] || ABITI.tunica)(d, rb, d.secondo || "#3a5a9a"), ...extra.flatMap((e) => e.busto || []),
    ...orecchie(d, sk), ...faccia(d, sk), ...(frangia ? capelliDavanti(d, hr) : []), ...barba(d, d.colore_barba ? rampa(d.colore_barba, { shift: 8, sat: 0.8 }) : hr), ...cop.davanti, ...extra.flatMap((e) => e.testa || []),
    ...occ)
  // the attributes go over the outlined figure, each with its own 1 px outline: one line per edge (drawn
  // inside the figure they got the figure's outline on top of their own, 2 px on the silhouette)
  const attr = (dx) => [...(s1 ? [stamp(s1, dx, dx)] : []), ...(s2 ? [stamp(s2, dx, dx, { flip: "x" })] : [])]
  sprite(nome, { w: S, h: S }, rect(0, 0, S, S, d.sfondo), rect(0, 72, S, S - 72, mixc(d.sfondo, "#000000", 0.15)),
    stamp(`_${nome}_aureola`, 0, 0), layer("ombra", { shade: true }, stamp(`_${nome}_fig`, 2, 2), ...attr(2)), stamp(`_${nome}_fig`, 0, 0), ...attr(0))
}
