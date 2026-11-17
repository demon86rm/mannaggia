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

var _MAT = null
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
  // while ritratto96 lists a figure's robes and headgear, every ramp is four marker colours (red 0xf2,
  // green the material's number, blue 0x10 + tone): stoffe6() repaints them in six tones at the end
  if (_MAT) { let i = _MAT.indexOf(base); if (i < 0) i = _MAT.push(base) - 1
    return [0, 1, 2, 3].map((k) => "#f2" + i.toString(16).padStart(2, "0") + "1" + k) }
  const r = ramp(base, o), d = hex2rgb(base), b = hex2rgb(r[2])
  return r.map((c) => rgb2hex(hex2rgb(c).map((v, i) => v + d[i] - b[i])))
}

// --- the "rich" style: six tones per material, dark -> light, [3] the base colour. A ramp for any base
// colour is made from a hand-picked one of the same material: its hue shifts and saturation as they are,
// the shadows as fractions of the base's lightness (a dark skin never goes black), the lights as steps
var PELLE6 = ["#8a4a44", "#b8705a", "#d4946f", "#eaba92", "#f6d2ae", "#fde8cc"]
var ORO6 = ["#7a4a14", "#a86c1c", "#d09a2c", "#eac050", "#fbe08a", "#fff6cc"]
var ORO6_BEATO = ["#6e6646", "#a89a6a", "#c4b88c", "#e2dab8", "#f6f2e0", "#fffef6"]     // a blessed's pale halo
var CAPELLI6 = ["#2a1616", "#45261c", "#684228", "#8a5c36", "#b08650", "#d8b878"]     // hair: the base is tone 2
var BIANCHI6 = ["#6a6e86", "#9498ac", "#b8bac8", "#d6d6de", "#eeeeee", "#ffffff"]     // white hair and beards
function rampa6(base, rif, i0 = 3) {
  const [h0, s0, l0] = _hsl(...hex2rgb(rif[i0])), [h, s, l] = _hsl(...hex2rgb(base))
  return rif.map((c, i) => {
    if (i === i0) return base
    const [hi, si, li] = _hsl(...hex2rgb(c))
    const ll = li < l0 ? l * li / l0 : Math.min(0.96, l + li - l0)
    return rgb2hex(_rgb((h + hi - h0 + 360) % 360, Math.max(0, Math.min(1, s0 ? s * si / s0 : si)), ll))
  })
}
// hair and beard: white and very fair ones take the white ramp (the brown one would shade them too dark)
var chioma6 = (col) => rampa6(col, _hsl(...hex2rgb(col))[2] > 0.7 ? BIANCHI6 : CAPELLI6, 2)
var hash96 = (n) => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v) }
var tra05 = (t) => Math.max(0, Math.min(5, t))

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
  // (the tunic is drawn by hand further down: ABITI.tunica)
  // (the nun's habit is drawn by hand further down: ABITI.suora)
  // (the friar's habit is drawn by hand further down: ABITI.saio)
  // (the cassock is drawn by hand further down: ABITI.talare)
  // (the Benedictine is drawn by hand further down: ABITI.benedettino)
  // (the royal robe is drawn by hand further down: ABITI.regale)
  // (the pope's robe is drawn by hand further down: ABITI.papa)
  // (the soldier's dress is drawn by hand further down: ABITI.armatura)
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
// rx, ry, squarer chin, tapered chin. 0 and 3 are the women's (3 narrows to the chin from y 54), 2 and 4 the
// men's (4: broad, the square chin); 1 is no longer assigned (esporta.py)
var VISI = [[18, 21, false], [19, 21, false], [18, 22, true], [18, 21, false, true], [19, 22, true]]
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

// --- the face and the neck in the rich style (ritratto96; faccia() and collo() above stay for the specials)
// The eye area keeps two tones only, base and far side: the app draws the eyes there (verifica_occhi.py)
var inZonaOcchi = (x, y) => y >= 33 && y <= 45 && ((x >= G96.cx - 16 && x <= G96.cx - 7) || (x >= G96.cx + 6 && x <= G96.cx + 15))
var q96 = (x, y, x0, y0, rx, ry) => ((x - x0) / rx) ** 2 + ((y - y0) / ry) ** 2
// Returns { viso, ombra }: the face, and the shadow that hair and headgear cast on it, to draw after them
function faccia6(d) {
  const { cx, F, FAR } = G96, SK = d._sk6, [rx, ry, mento, punta] = VISI[d.viso || 0]
  // the same outline as pxl's ellipse(cx, 43, rx, ry), which faccia() draws: half a pixel wider. A tapered
  // chin narrows it smoothly from y 46, down to 0.82 of its width at the chin (a straight cut left a step:
  // the user); a square chin is cut flat at y 62, two rows clear of a collar's top (the user, 2026-11-17)
  const inV = (x, y) => {
    if (mento) return y <= 62 && (q96(x, y, cx, 43, rx + 0.5, ry + 0.5) <= 1 || (y >= 59 && Math.abs(x - cx) <= 8))
    if (!punta || y < 46) return q96(x, y, cx, 43, rx + 0.5, ry + 0.5) <= 1
    const e = 1 - ((y - 43) / (ry + 0.5)) ** 2
    return e >= 0 && Math.abs(x - cx) <= (rx + 0.5) * Math.sqrt(e) * (1 - 0.18 * ((y - 46) / (ry - 3)) ** 1.5)
  }
  const vecchio = d.eta === "anziano", calvo = d.capelli === "calvo", largo = d.naso === "largo", piene = d.labbra === "piene"
  const nv = d.naso_v || 0, bv = d.bocca || 0, w = [4, 2, 3][bv], barbuto = d.barba === "corta" || d.barba === "lunga"
  const L = [mixc(SK[0], "#7a2a30", 0.5), mixc(SK[2], "#c84a4a", d.donna ? 0.45 : 0.25), mixc(SK[4], "#e87878", d.donna ? 0.4 : 0.2)]   // the mouth's line, the lip, its light
  const tono = (x, y) => {
    const dx = x - cx, a = Math.abs(dx)
    if (inZonaOcchi(x, y)) return SK[dx > FAR ? 2 : 3]
    let t = 3
    if (x > cx + FAR - Math.max(0, y - 47) * 0.45) t = 2            // the far side
    // its core shadow, at the edge (not on a bald head's brow: there the skull goes on above the face)
    if (q96(x, y, cx - 3, 43, rx, ry) > 1 && x > cx && !(calvo && y < 38)) t = 1
    if (q96(x, y, cx, 41.5, rx, ry) > 1 && y > 55 && x > cx + 2) t -= 1   // under the jaw
    if (q96(x, y, cx - 7, 30.4, 7, 2.2) <= 1) t = 4                 // forehead
    if (!vecchio && q96(x, y, cx - 12, 49, 3.5, 1.4) <= 1) t = 4    // cheekbone (the old have bags and hollows there: three stripes with it)
    if (vecchio) {
      if (calvo && q96(x, y, cx - 6, 26, 6, 1.6) <= 1) t = 5        // the bald skull's shine
      if (q96(x, y, cx - 5, 28.5, 10, 4) <= 1) t = Math.max(t, 4)
      if ((y === 29 && dx >= -10 && dx <= 8) || (y === 32 && dx >= -8 && dx <= 9)) t = dx > 2 ? 2 : 3   // forehead lines
      if (dx === 0 && y >= 36 && y <= 38) t = 2                     // the frown
      if ((a === 18 || a === 17) && (y === 40 || y === 43)) t = dx < 0 ? 2 : 1   // crow's feet
      if (y === 47 && ((dx >= -14 && dx <= -9) || (dx >= 7 && dx <= 12))) t = dx < 0 ? 2 : 1   // bags under the eyes
      if (!d.guance && q96(x, y, cx - 12, 50.5, 4, 1.5) <= 1) t = 2   // hollow cheeks (a blush takes their place)
      if (!d.guance && q96(x, y, cx + 12, 50.5, 4, 1.5) <= 1) t = 1
    }
    let col = SK[Math.max(0, t)]
    if (d.guance) {
      if (q96(x, y, cx - 12, 51.4, 4, 1.3) <= 1) col = mixc(SK[3], "#e06a6a", 0.32)
      if (q96(x, y, cx + 12, 51.4, 3.5, 1.3) <= 1) col = mixc(SK[2], "#e06a6a", 0.28)
    }
    // nose: 0 straight, 1 long and pointed, 2 short and rounded; a lit ridge, the shadow side, the tip.
    // Nothing of it below y 52: row 53 stays skin
    const [l0, l1, s0, s1] = [[45, 49, 44, 50], [44, 50, 43, 50], [46, 49, 44, 50]][nv]
    if (x === cx - 1 && y >= l0 && y <= l1) col = SK[y === l1 ? 5 : 4]
    if (x === cx + 1 && y >= s0 && y <= s1) col = SK[2]
    if (nv === 2 && x === cx + 2 && y >= 48 && y <= 50) col = SK[2]
    if (nv === 1 && x === cx && y === 51) col = SK[4]
    else if (y === 51 && a <= 2) col = SK[2]
    if (y === 51 && a >= 3 && a <= (largo ? 4 : 3)) col = SK[1]     // nostrils, symmetric about cx
    if (largo && y === 52 && a === 3) col = SK[1]
    // mouth: 0 wide, 1 narrow, 2 a smile with the corners up; the line at y 54, the lower lip, its shadow
    if (barbuto) return col                                         // barba6() draws the mouth under the moustache
    const sy = piene ? 57 : 56
    if (y === 54 && a <= w) col = L[0]
    if (y === 55 && a <= w - 1) col = dx === -1 ? L[2] : L[1]
    if (piene && y === 56 && a <= w - 2) col = L[1]
    if (y === sy && a <= Math.max(1, w - 2)) col = SK[2]
    if (bv === 2 && y === 53 && a === w + 1) col = SK[1]
    return col
  }
  const noti = new Map()                                            // the skin tones as the canvas packs them
  const viso = (c) => { for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) if (inV(x, y)) {
    const col = tono(x, y), k = SK.indexOf(col)
    c.px(x, y, col)
    if (k >= 0) noti.set(c.get(x, y), k)
  } }
  // what covers the skin (a fringe, a mitre, a veil) darkens the row or two under it, and the skin beside
  // a lock on the lit side; never in the eye area
  const ombra = (c) => {
    const coperto = (x, y) => inV(x, y) && !noti.has(c.get(x, y))
    const scuri = []
    for (let y = 22; y <= 46; y++) for (let x = 0; x < F; x++) {
      if (!inV(x, y) || inZonaOcchi(x, y)) continue
      const k = noti.get(c.get(x, y))
      if (k === undefined || k < 2) continue
      if ((y <= 32 && (coperto(x, y - 1) || (x > cx - 4 && coperto(x, y - 2)))) || (x < cx - 16 && coperto(x - 1, y))) scuri.push([x, y, k >= 3 ? 2 : 1])
    }
    for (const [x, y, k] of scuri) c.px(x, y, SK[k])
  }
  return { viso, ombra, tono, dentro: inV, labbra: L }
}
// the neck: the chin's shadow follows the jaw, the far side darker
function colloT(d, x, y) {
  const { cx } = G96, [rx, ry] = VISI[d.viso || 0]
  const g = y - (43 + ry * Math.sqrt(Math.max(0, 1 - ((x - cx) / rx) ** 2)))
  let t = g < 3 ? 1 : g < 5 ? 2 : 3
  if (x > cx + 6) t = Math.min(t, 2)
  if (x >= cx + 10) t = 1
  return d._sk6[t]
}
function collo6(d) {
  const { cx } = G96
  return [(c) => { for (let y = 58; y <= 71; y++) for (let x = cx - 12; x < cx + 12; x++) c.px(x, y, colloT(d, x, y)) }]
}

// --- hair and beard in the rich style. Their shapes are the ones above (capelliDietro, capelliDavanti,
// barba), drawn in marker colours; then one pass repaints every marked pixel with a tone of the six
var MARCA_C = ["#f000f1", "#f000f2", "#f000f3", "#f000f4"], MARCA_B = ["#f100e1", "#f100e2", "#f100e3", "#f100e4"]
var _PK = new Map()                                                 // the markers as the canvas packs them
// first item of the figure: (0, 0) is still empty there
var tara96 = (c) => { for (const h of [...MARCA_C, ...MARCA_B]) if (!_PK.has(h)) { c.px(0, 0, h); _PK.set(h, c.get(0, 0)) } c.px(0, 0, "_") }
function marcati(c, marca) {
  const { F } = G96, pk = marca.map((h) => _PK.get(h)), m = new Int8Array(F * F).fill(-1)
  for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) m[y * F + x] = pk.indexOf(c.get(x, y))
  return { m, e: (x, y) => x >= 0 && x < F && y >= 0 && y < F && m[y * F + x] >= 0 }
}
// Straight hair: strands fanning from the crown, a dark gap between two of them, a broken band of sheen
// under the top, the left rim lit, the tips and the far side in shadow, a ragged fringe.
// Curls and coils keep their own lights and shadows, with the head's volume over them
function capelli6(d, viso, st) {
  st = st || {}                                                     // a men's cut (tagli6): how its strands run
  const { cx, F } = G96, H = chioma6(d.chioma || "#5a4030"), ricci = (d.capelli === "ricci" || d.capelli === "afro") && !st.onde
  const pg = d.donna && d.capelli === "lunghi" ? d.piega : 0
  const c0 = st.c0 === undefined ? cx - 5 : st.c0, amp = pg === 2 ? 1.5 : st.onda || 0
  // swept back: the strands rise from the hairline, closer together towards the top
  const ciocca = (x, y) => st.indietro ? ((x - cx) / 2.6) * (1 + (28 - Math.min(y, 28)) / 45)
    : (x + (amp && (!pg || y > 34) ? amp * Math.sin(y / 3.2) : 0) - c0) / (1 + (Math.min(y, 30) - 4) / 12)
  // curls: staggered cells of side s, each a ball lit from the top left, a dark gap round it
  const riccio = (x, y, s) => {
    const sy = s * 0.85, j = Math.floor(y / sy), xo = x + (j % 2 ? s / 2 : 0), i = Math.floor(xo / s), k = i * 31 + j * 17
    const ex = xo - (i + 0.5) * s - (hash96(k) - 0.5) * s * 0.3, ey = y - (j + 0.5) * sy - (hash96(k + 5) - 0.5) * s * 0.3
    const r = Math.hypot(ex, ey) / (s / 2), l = -(ex + ey) / s
    if (r > 1.05 || (s >= 6 && r < 0.28)) return 1
    return l > 0.3 ? 4 : l > -0.05 ? 3 : l > -0.4 ? 2 : 1
  }
  return (c) => {
    const { m, e } = marcati(c, MARCA_C)
    let top = F
    for (let y = pg === 3 ? 15 : 0; y < F && top === F; y++) for (let x = cx - 10; x <= cx; x++) if (e(x, y)) { top = y; break }
    for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) {
      if (!e(x, y)) continue
      const u = ciocca(x, y), si = Math.floor(u), l = -(((x - cx) / 24) * 0.62 + ((y - 31) / 21) * 0.5)
      let t
      if (st.ricci) {
        t = riccio(x, y, st.ricci)
        if (l > 0.45) t += 1; else if (l < -0.35) t -= 1
        if (x > cx + 13) t = Math.min(t, 3)
        if (st.sotto && y <= 25 && Math.abs(x - cx) <= 15) t = 2      // the strip under a mitre's rim: in its shadow, no curls (a dotted line)
        if (y >= 36 && (!e(x, y + 1) || !e(x + 1, y))) t = Math.min(t, 1)
      } else if (ricci) {
        t = [0, 1, 2, 4][m[y * F + x]]
        if (l > 0.45) t += 1; else if (l < -0.4 && t >= 2) t -= 1
      } else {
        // the fringe's lower edge, one strand in two a row shorter
        if (y >= 24 && y <= 30 && Math.abs(x - cx) <= 16 && !e(x, y + 1) && viso.dentro(x, y + 1) && hash96(si + 70) > 0.5) { c.px(x, y, viso.tono(x, y)); continue }
        t = l > 0.42 ? 3 : l > -0.25 ? 2 : 1
        if (x > cx + 13) t = Math.max(t - 1, 1)
        if (hash96(si) > 0.8) t += 1; else if (hash96(si) < 0.14 && !st.corto) t -= 1
        if (si !== Math.floor(ciocca(x - 1, y)) && hash96(si + 3) > 0.4) t -= 1
        const yb = top + 5 + 0.011 * (x - cx + 4) ** 2 + (hash96(si + 50) < 0.5 ? 0 : 1)
        if (st.onde) t += Math.sin(y / 2.1 + si * 1.9) > 0.55 ? 1 : Math.sin(y / 2.1 + si * 1.9) < -0.7 ? -1 : 0
        if (st.corto && hash96(x * 7 + y * 13) > 0.86) t += 1                  // cropped: a stipple, no sheen
        if (!st.corto && !st.tonsura && !st.onde && x > cx - 21 && x < cx + 9 && y >= yb && y <= yb + 2 && hash96(si + 9) > 0.25) t = y < yb + 1 && u - si > 0.3 && hash96(si + 9) > 0.6 ? 5 : 4
        if (x < cx - 4 && y < 30 && (!e(x - 1, y) || !e(x - 2, y)) && !viso.dentro(x - 1, y)) t = Math.max(t, 3)
        if (y >= 40 && (!e(x, y + 1) || !e(x, y + 2))) t -= 1
        if (st.riga !== undefined && y > top + 1 && y <= 24) { if (x === st.riga) t = 1; else if (x === st.riga + 1) t = Math.max(t, 4) }   // the parting
        if (st.tonsura && y < 30 && !e(x, y - 1) && Math.abs(x - cx) < 17 && hash96(si + 21) > 0.35) t = x > cx + 8 ? 3 : 4            // the ring's upper rim
        if (pg === 3 && y <= 16 && q96(x, y, cx + 1, 9, 8.5, 7.5) <= 1) {       // the bun: a ball, wound round
          const lb = -(((x - cx - 1) / 8.5) * 0.6 + ((y - 9) / 7.5) * 0.7)
          t = lb > 0.5 ? 4 : lb > 0 ? 3 : lb > -0.5 ? 2 : 1
          if ((x + 2 * y) % 5 === 0) t -= 1
          if (y >= 15) t = 1
        }
        if (pg === 4 && y >= 48 && x < cx - 12) {                              // the braid: crossed locks
          const v = (((y + Math.abs(x - Math.round(cx - 19 + (y - 46) * 0.07)) * 2) % 6) + 6) % 6
          t = v === 0 ? 0 : v === 1 ? 4 : v === 2 ? 3 : 2
        }
      }
      c.px(x, y, H[tra05(t)])
    }
  }
}
// Women's long hair, d.piega (from the name, esporta.py): 0 or none the shoulder-length cut with a fringe
// of capelliDietro/capelliDavanti; 1 long and straight over the shoulders, a centre parting; 2 the same
// in waves; 3 gathered in a bun, the ears bare; 4 a braid over the shoulder; 5 a modern bob, a deep side
// parting, no fringe, the ends curling in. Each is three masks in the marker colour: behind the figure, over the
// shoulders, over the face (there only above the eye area, or at its sides from |dx| 17)
function pieghe6(d, viso) {
  const { cx, F } = G96, p = d.piega
  const segna = (f) => (c) => { for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) if (f(x, y, Math.abs(x - cx))) c.px(x, y, MARCA_C[2]) }
  const testa = (x, y) => q96(x, y, cx, 36, 23.5, 20.5) <= 1
  const onda = (y) => (p === 2 ? 1.5 * Math.sin(y / 3.2) : 0)
  const tende = (x, y, a) => viso.dentro(x, y) && (y <= 22 + a * 0.55 || (a >= 17 && y <= 58))     // parted in the middle, falling beside the face
  const raccolti = (x, y, a) => viso.dentro(x, y) && y <= 24 + Math.max(0, a - 10) * 0.7           // pulled back from the forehead
  if (p === 1 || p === 2) { const fine = p === 1 ? 90 : 82
    return { dietro: segna((x, y, a) => testa(x, y) || (y >= 36 && y <= 72 && a <= 23.5 + onda(y))),
      spalle: segna((x, y, a) => y >= 60 && y <= fine && a >= 14.5 - onda(y + 5) * 0.5 && a <= 23.5 + onda(y) - Math.max(0, y - fine + 7) * 0.9),
      davanti: segna(tende) } }
  if (p === 3) return { orecchie: true, dietro: segna((x, y, a) => (q96(x, y, cx, 32, 21.5, 18.5) <= 1 && y <= 41) || q96(x, y, cx + 1, 9, 8.5, 7.5) <= 1),
    davanti: segna(raccolti) }
  if (p === 4) return { orecchie: true, dietro: segna((x, y, a) => q96(x, y, cx, 32, 21.5, 18.5) <= 1 && y <= 47),
    spalle: segna((x, y) => y >= 46 && y <= 88 && Math.abs(x - (cx - 19 + (y - 46) * 0.07)) <= 3.4 - Math.max(0, y - 82) * 0.5),
    davanti: segna(raccolti) }
  // 5, the modern bob (redrawn 2026-11-17, unlike the men's page-boy): no fringe, a deep side parting
  // that leaves the forehead open, fuller towards the bottom, the ends curling in under the jaw
  if (p === 5) return { dietro: segna((x, y, a) => q96(x, y, cx, 34, 23.5, 20) <= 1 || (y >= 34 && y <= 59 && a <= 24.5 - Math.max(0, y - 54) * 1.6)),
    davanti: segna((x, y, a) => viso.dentro(x, y) && (y <= 20 + Math.abs(x - (cx - 6)) * 0.45 || (a >= 17 - Math.max(0, y - 51) * 0.8 && y >= 22 && y <= 58))) }
  return null
}

// The skullcap sits on the head as it is drawn: a symmetric dome, the lowest one that covers the head's
// top (bare skull or hair) in every column, a pixel above it, so it always covers the summit (the old
// fixed cap sat under a bald head's top). Its rim is an arc, lower at the sides. Six tones, a light piping
// on the rim, which sets it off from red or white hair, and the rim's shadow on the hair or the skull
function zucchetto6(d, col) {
  const { cx } = G96, W = 15, [rx, ry] = VISI[d.viso || 0], R = rampaMat(col)
  return (c) => {
    const cima = (x) => { for (let y = 0; y < 40; y++) if (c.get(x, y) !== 0) return y; return 40 }
    const tops = {}, K = 0.027, fatti = []                          // K: the skull's own curve
    let t0 = 40
    for (let x = cx - W; x <= cx + W; x++) { tops[x] = cima(x); t0 = Math.min(t0, tops[x] - (x - cx) ** 2 * K) }
    t0 = Math.round(t0)
    for (let x = cx - W; x <= cx + W; x++) {
      const a = Math.abs(x - cx), su = Math.round(t0 - 1 + a * a * K)
      // down to the rim's arc, thinner at the ends, and always as far as the head
      const giu = Math.max(Math.min(Math.round(t0 + 5 + a * a * 0.02), su + (W - a) * 2 + 2), tops[x] - 1)
      // what is under the rim, in its shadow (the face's skin gets it from faccia6's ombra)
      if (c.get(x, giu + 1) !== 0 && q96(x, giu + 1, cx, 43, rx + 0.5, ry + 0.5) > 1) { const v = c.get(x, giu + 1)
        fatti.push([x, giu + 1, rgb2hex([24, 16, 8].map((k) => ((v >>> k) & 255) * 0.68))]) }
      for (let y = su; y <= giu; y++) {
        let t = 3
        if (x < cx - 3 && y <= su + 2) t = 4
        if (q96(x, y, cx - 6, t0 + 1.5, 3.5, 1.2) <= 1) t = 5
        if (x > cx + 6) t = 2
        if (x >= cx + 12) t = 1
        if (y === giu - 1 && x > cx - 8) t = Math.min(t, 2)
        if (y === giu) t = 5
        fatti.push([x, y, R[t]])
      }
    }
    for (const [x, y, k] of fatti) c.px(x, y, k)
  }
}

// Men's hair, d.taglio (from the name, esporta.py), by family d.capelli; 0 or none: the old shapes
// (capelliDietro, capelliDavanti). corti: 1 a side parting with a quiff, 2 swept back off a high forehead
// with a peak, 3 cropped with a short ragged fringe, 4 tousled, 5 a page-boy to the jaw. ricci: 1 short
// and tight, 2 fuller locks over the ears, 3 wavy. tonsura: 1 a narrow ring, 2 a wide one. calvo: 1 bald,
// 2 hair at the sides, 3 receding at the temples with a forelock.
// Returns { dietro, davanti } (lists; masks in the marker colour, the bare skull in six skin tones),
// stile (how capelli6 runs the strands), coperte (the hair hides the ears)
function tagli6(d, viso) {
  const { cx, F, FAR } = G96, t = d.taglio, h = d.capelli, SK = d._sk6, at = d.attacc || 0
  const ogni = (f, col) => (c) => { for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) if (f(x, y, Math.abs(x - cx))) c.px(x, y, col ? col(x, y) : MARCA_C[2]) }
  const segna = (f) => ogni(f)
  // the skull: the far side darker, its core shadow at the edge, the light on the top left (the shine no
  // lower than y 19: faccia6's ombra takes a tone the face has not for something covering the skin)
  const cranio = (f) => ogni(f, (x, y) => SK[y <= 19 && q96(x, y, cx - 8, 18.5, 3, 1) <= 1 ? 5 : q96(x, y, cx - 7, 21, 7, 3.2) <= 1 ? 4
    : x > cx && q96(x, y, cx - 3, 32, 19, 18) > 1 ? 1 : x > cx + FAR ? 2 : 3])
  const teschio = (x, y) => q96(x, y, cx, 32, 19.5, 18.5) <= 1 && y <= 37
  const calotta = (x, y, rx, ry, cy, x0 = cx) => y <= cy && q96(x, y, x0, cy, rx, ry) <= 1
  const lati = (y, a, rx, y0, y1) => y >= y0 && y <= y1 && a <= rx - Math.max(0, y - y1 + 4) * 0.9   // down the sides, tapering
  const smerlo = (x, y, rx, ry, cy, n, amp) => y <= cy && q96(x, y, cx, cy, rx, ry) <= (1 + amp * Math.abs(Math.sin(Math.atan2(y - cy, x - cx) * n))) ** 2
  const V = viso.dentro
  if (h === "corti") {
    if (t === 1) return { stile: { c0: cx - 9, riga: cx - 9 },
      dietro: [segna((x, y, a) => calotta(x, y, 21.5, 17.5, 31, cx + 1) || q96(x, y, cx + 5, 21, 13, 9) <= 1 || lati(y, a, 21.5, 31, 41))],
      davanti: [segna((x, y) => V(x, y) && y <= (x <= cx - 9 ? 24 + (cx - 9 - x) * 0.45 : Math.min(29, 23 + (x - cx + 9) * 0.24)))] }
    if (t === 2) return { stile: { indietro: true },
      dietro: [segna((x, y, a) => calotta(x, y, 21, 18.5, 30) || lati(y, a, 21, 30, 40))],
      davanti: [segna((x, y, a) => V(x, y) && y <= 25 - a * 0.8)] }
    if (t === 3) return { stile: { corto: true },
      dietro: [segna((x, y, a) => calotta(x, y, 20.5, 16.5, 32) || lati(y, a, 20.5, 32, 39))],
      davanti: [segna((x, y, a) => V(x, y) && y <= 26 + at + (hash96(Math.floor(x / 2) + 40) > 0.5 ? 1 : 0) + Math.max(0, a - 12) * 0.3)] }
    if (t === 4) return { stile: { onda: 1.2 },
      dietro: [segna((x, y, a) => calotta(x, y, 21, 17.4, 31) || lati(y, a, 21.5 + Math.sin(y / 1.7), 31, 43)
        || [[22, 2.4], [47, 3], [70, 2.4], [93, 3], [112, 2.4], [136, 3], [158, 2.4]].some(([g, r]) => q96(x, y, cx + 20 * Math.cos(g * Math.PI / 180), 31 - 16.4 * Math.sin(g * Math.PI / 180), r, r) <= 1))],
      davanti: [segna((x, y, a) => V(x, y) && y <= 25.5 + at + 2.2 * Math.sin(x / 2.6 + 1) + Math.max(0, a - 13) * 0.5)] }
    if (t === 5) return { stile: {}, coperte: true,
      dietro: [segna((x, y, a) => calotta(x, y, 23, 19.5, 33) || (y >= 33 && y <= 52 && a <= 23 - Math.max(0, y - 48) * 1.2))],
      davanti: [segna((x, y, a) => V(x, y) && (y <= 27 + at || (a >= 17 && y <= 50)))] }
  }
  if (h === "ricci") {
    if (t === 1) return { stile: { ricci: 4 },
      dietro: [segna((x, y, a) => smerlo(x, y, 21, 17, 31, 9, 0.07) || lati(y, a, 21.5, 31, 41))],
      davanti: [segna((x, y) => V(x, y) && y <= 25 + at + 2 * Math.abs(Math.sin(x * Math.PI / 5)))] }
    if (t === 2) return { stile: { ricci: 6 }, coperte: true,
      dietro: [segna((x, y, a) => smerlo(x, y, 22.5, 19, 30, 6, 0.1) || (y >= 30 && y <= 46 && a <= 22.5 + 1.5 * Math.abs(Math.sin(y * Math.PI / 6)) - Math.max(0, y - 43) * 1.5))],
      davanti: [segna((x, y, a) => V(x, y) && (y <= 26 + at + 2.5 * Math.abs(Math.sin(x * Math.PI / 7 + 0.5)) || (a >= 17 && y <= 44)))] }
    if (t === 3) return { stile: { onda: 1.6, onde: true }, coperte: true,
      dietro: [segna((x, y, a) => calotta(x, y, 22.5, 18.4, 31) || (y >= 31 && y <= 48 && a <= 22 + 1.3 * Math.sin(y / 2.4) - Math.max(0, y - 45) * 1.3))],
      davanti: [segna((x, y, a) => V(x, y) && (y <= 25.5 + at + 2 * Math.sin((x - cx) / 4.5) + Math.max(0, a - 13) * 0.4 || (a >= 17 && y <= 46)))] }
  }
  if (h === "tonsura" && (t === 1 || t === 2)) {
    // the shaved crown is a dome of bare skin over the hair, a band of hair under it across the forehead
    const [rx, ry, cy, b0, rm] = t === 1 ? [16, 8.5, 23, 24, 22] : [12.5, 6.2, 21.5, 21, 23]
    return { stile: { tonsura: b0 },
      dietro: [segna((x, y, a) => calotta(x, y, rm, 17.6, 33) || lati(y, a, rm, 33, 42))],
      davanti: [cranio((x, y, a) => y < b0 - a * a * 0.014 && q96(x, y, cx, cy, rx, ry) <= 1),
        segna((x, y) => V(x, y) && y >= b0 && y <= 27 + at + (hash96(Math.floor(x / 2) + 60) > 0.5 ? 1 : 0))] }
  }
  if (h === "calvo") {
    const ailati = (x, y) => q96(x, y, cx, 37, 22.5, 15.5) <= 1 && q96(x, y, cx, 27, 17, 17) > 1
    if (t === 1) return { stile: {}, dietro: [cranio(teschio)], davanti: [] }
    if (t === 2) return { stile: {}, dietro: [cranio(teschio), segna(ailati)], davanti: [] }
    // the hairline as an M: a forelock in the middle, the temples bare, the sides full
    const hl = (a) => (a <= 4 ? 23 : a <= 10 ? 23 - (a - 4) * 0.6 : a <= 14 ? 19.4 : 19.4 + (a - 14) * 3)
    if (t === 3) return { stile: {}, dietro: [cranio(teschio), segna(ailati)],
      // (under a skullcap, which ends at y 20, the forelock does not come out)
      davanti: [segna((x, y, a) => q96(x, y, cx, 32, 20.3, 18.9) <= 1 && y <= Math.min((d.copricapo || "").startsWith("zucchetto") ? 20 : 30, hl(a)))] }
  }
  return null
}

// Beard: strands falling from the jaw (wavy when long), the lower edge and the far side in shadow.
// Its upper edge is a curve: barba()'s shape (cut straight at y 48) loses the cheeks, the nose and the
// mouth's surroundings (libera), and rises at the sides to y 46, just under the eye area.
// The moustache sits above the mouth, never over it: rows 52-53 under the nose, a notch in the middle,
// the ends drooping into the beard; then a row of skin in its shadow, the mouth's line at y 55 (one row
// lower than on a shaven face), the lower lip, the beard's shadow under it
function barba6(d, viso) {
  const { cx, F, FAR } = G96, B = chioma6(d.colore_barba || d.chioma || "#5a4030"), lunga = d.barba === "lunga", SK = d._sk6, L = viso.labbra
  const libera = (x, y) => q96(x, y, cx, lunga ? 44 : 45, lunga ? 13.5 : 14, lunga ? 8.5 : 10.5) <= 1
  const baffi = (a, y) => (y === 52 && a <= 7) || (y === 53 && a >= 1 && a <= 9) || (y === 54 && a >= 6 && a <= (lunga ? 10 : 9)) || (lunga && y === 55 && a >= 8 && a <= 10)
  return (c) => {
    if (!["corta", "lunga", "baffi"].includes(d.barba)) return
    const { e } = marcati(c, MARCA_B)
    for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) {
      const dx = x - cx, a = Math.abs(dx)
      if (d.barba === "baffi") { if (e(x, y)) c.px(x, y, B[y === 52 ? (dx < 0 ? 3 : 2) : 1]); continue }
      const vecchia = e(x, y) || (a <= 5 && y >= 52 && y <= 56)     // barba()'s shape, with the opening it leaves in skin
      const qui = (vecchia || (viso.dentro(x, y) && (y === 46 || y === 47))) && !libera(x, y)
      let t
      if (y >= 54 && y <= 56 && a <= 58 - y) { c.px(x, y, y === 54 ? SK[2] : y === 55 ? L[0] : dx === -1 ? L[2] : L[1]); continue }   // skin, the mouth, the lip
      if (baffi(a, y)) t = (y === 52 ? 4 : y === 53 ? 3 : 2) - (dx > 0 ? 1 : 0)
      else if (qui) {
        const st = (xx) => Math.floor(lunga ? (xx - cx + 1.6 * Math.sin(y / 3.5 + xx / 9)) / 3 : (xx - cx) / (1 + (y - 46) / 40) / 3), si = st(x)
        t = dx < -8 ? 3 : dx > 9 ? 1 : 2
        if (hash96(si + 5) > 0.8 && dx > -8) t += 1
        if (si !== st(x - 1) && (lunga || hash96(si + 8) > 0.35)) t -= 1
        if (y > 56 && (!e(x, y + 1) || !e(x, y + 2))) t -= 1
        if ((baffi(a, y - 1) && a > 5) || (y === 57 && a <= 3)) t = 1       // the moustache's shadow, under the lip
      } else if (vecchia) { c.px(x, y, y >= 52 && a <= 7 ? SK[dx > FAR ? 2 : 3] : viso.tono(x, y)); continue }   // skin again
      else continue
      c.px(x, y, B[tra05(t)])
    }
  }
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
  // (the veil is drawn by hand further down: COPRICAPI.velo)
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
  // (the mitre is drawn by hand further down: COPRICAPI.mitra)
  // (the crown is drawn by hand further down: COPRICAPI.corona)
  // (the tiara is drawn by hand further down: COPRICAPI.tiara)
  zucchetto_rosso(d) { return { dietro: [], davanti: [zucchetto6(d, "#b8302c")] } },
  zucchetto_bianco(d) { return { dietro: [], davanti: [zucchetto6(d, "#f0ece4")] } },
  gat(d) {      // Korean horsehair hat: a tall black crown, a wide brim, the chin strap
    const { cx } = G96, b = rampa("#2a2630")
    return { dietro: [], davanti: [rect(cx - 9, 6, 18, 14, b[2]), ellipse(cx, 6, 9, 2, b[1]), ellipse(cx, 21, 28, 4, b[2]),
      ellipse(cx, 20, 26, 2, b[3]), recolor({ [b[2]]: b[1] }, (x, y) => x > cx + 3 && y < 20),
      line(cx - 19, 24, cx - 17, 30, b[1]), line(cx + 19, 24, cx + 17, 30, b[1])] }
  },
}

// --- attributes, bottom right (x 64..92) or along the right edge
var ATTRIBUTI96 = {
  // (ATTRIBUTI96.palma is drawn by hand further down)

  // (ATTRIBUTI96.croce is drawn by hand further down)
  // (ATTRIBUTI96.giglio is drawn by hand further down)
  // (ATTRIBUTI96.libro is drawn by hand further down)

  // (the crozier is drawn by hand further down: ATTRIBUTI96.pastorale)
  // (ATTRIBUTI96.bastone is drawn by hand further down)
  // (ATTRIBUTI96.spada is drawn by hand further down)

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

// --- robes and headgear in the rich style. Their shapes are the ones of ABITI, COPRICAPI and EXTRA96,
// drawn in marker colours (see rampa); this pass, the last of the figure, gives each marked pixel one of
// the six tones of its material. The old tone stays as a hint (far side, fold lines, lights); on it:
// edges facing up lit and edges facing down shaded, slanting folds on the large cloths of the bust, the
// head's volume and a lit rim on headgear, falling folds on veils and hoods. A mitre gets its jewelled
// band, the stones on the titulus and an embroidered cross on each side; a nun's guimpe its fanning folds
var STOFFA6 = ["#4a1420", "#701c28", "#96283a", "#b83a48", "#d65c5c", "#ee8c7c"]
var BIANCO6 = ["#8a809a", "#a69cac", "#c8c0c8", "#f0ece4", "#faf7f1", "#ffffff"]
var NERO6 = ["#100c12", "#18141a", "#221e24", "#2c2830", "#484050", "#6a6072"]
var gemma96 = (rossa, ix, iy) => (rossa ? ["#f08a8a", "#b02a34", "#701c28"] : ["#8ab0f0", "#2e56b0", "#1c2e6a"])[ix === 0 && iy === 0 ? 0 : iy === 2 ? 2 : 1]
function stoffe6(d, mat) {
  const { cx, F } = G96
  return (c) => {
    const hsl = mat.map((b) => _hsl(...hex2rgb(b)))
    const oro = hsl.map(([h, s, l]) => h >= 30 && h <= 60 && s > 0.5 && l > 0.4 && l < 0.75)
    const R = mat.map((b, i) => rampa6(b, oro[i] ? ORO6 : hsl[i][2] > 0.8 ? BIANCO6 : hsl[i][2] < 0.22 ? NERO6 : STOFFA6))
    const id = new Int16Array(F * F).fill(-1), tono = new Int8Array(F * F), n = mat.map(() => 0)
    for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) {
      const v = c.get(x, y), i = (v >>> 16) & 255, k = (v >>> 8) & 255
      if (v >>> 24 === 0xf2 && k >= 0x10 && k <= 0x13 && i < mat.length) { id[y * F + x] = i; tono[y * F + x] = k - 0x10; n[i]++ }
    }
    const S = (x, y) => (x >= 0 && x < F && y >= 0 && y < F ? id[y * F + x] : -1)
    const telo = d.copricapo === "velo" || d.copricapo === "cappuccio"
    for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) {
      const i = id[y * F + x]
      if (i < 0) continue
      const k = tono[y * F + x], dx = x - cx, a = Math.abs(dx), su = S(x, y - 1) !== i, giu = S(x, y + 1) !== i, grande = n[i] > 500
      let t = k + 1
      if (y >= 62) {                                          // the bust
        if (grande) {
          // folds slanting outwards from the neck, wide apart; none down the middle, where the two sides
          // would meet in a zigzag
          const m = (((Math.round(a - (y - 70) * 0.5) % 17) + 17) % 17)
          if (k === 2 && a >= 12 && y >= 74) { if (m === 0) t -= 1; else if (m === 1 && dx < 0) t += 1 }
          if (y >= 90) t -= 1
          if (dx > 30) t -= 1
          if (c.get(x, y - 1) === 0) t = k + (dx < 0 ? 3 : 2)        // the shoulders' edge against the sky
          else if (dx < 0 && c.get(x, y - 2) === 0) t = k + 2
        } else { if (su && k >= 2) t += 1; if (giu) t -= 1 }
      } else {                                                       // headgear
        const l = -(((x - cx) / 26) * 0.6 + ((y - 30) / 27) * 0.55)
        if (k === 2 && l > 0.45) t += 1
        if (oro[i] || !grande) { if (su && k >= 2) t += 1; if (giu) t -= 1 }
        if (telo && grande && k === 2) {
          const st = (xx) => Math.floor((xx - cx) / (1 + (Math.max(y, 10) - 4) / 14) / 4)
          if (st(x) !== st(x - 1)) t -= 1; else if (st(x) !== st(x + 1) && x < cx) t += 1
        }
        if (k >= 2 && x < cx - 4 && (c.get(x - 1, y) === 0 || c.get(x - 2, y) === 0)) t = Math.max(t, 4)    // the rim, lit
      }
      c.px(x, y, R[i][tra05(t)])
    }
  }
}

// --- robes redrawn by hand in the rich style, one at a time: a mask (the bust's own outline, spalle(), in
// a marker colour) and a tone function, as in the hand-made proofs (see the skill ritratti-mannaggia)
var LINO6 = ["#7c7088", "#a69cac", "#c8c0c8", "#e2dcdc", "#f4f0ea", "#fffdf6"]
var MARCA_V = "#f300f0", PK_V = 0xf300f0ff
var rampaMat = (b) => { const [h, s, l] = _hsl(...hex2rgb(b)); return rampa6(b, h >= 30 && h <= 60 && s > 0.5 && l > 0.4 && l < 0.75 ? ORO6 : l > 0.8 ? BIANCO6 : l < 0.22 ? NERO6 : STOFFA6) }
var mod96 = (v, n) => ((v % n) + n) % n
// cloth on the bust: the edge against the sky lit, folds slanting outwards (none down the middle), the
// far side and the bottom darker. sopra: the pixel above is empty
function panno96(x, y, base, sopra) {
  const dx = x - G96.cx, a = Math.abs(dx), m = mod96(Math.round(a - (y - 70) * 0.5), 17)
  let t = base
  if (a >= 12 && y >= 74) { if (m === 0) t -= 1; else if (m === 1 && dx < 0) t += 1 }
  if (dx > 14) t -= 1
  if (y >= 90) t -= 1
  if (sopra) t = base + (dx < 0 ? 2 : 1)
  return t
}
// The bishop, d.vescovo_v from the name (esporta.py): 0 a cope open over the alb, with jewelled orphreys
// and a morse; 1 a chasuble with a jewelled Y orphrey; 2 a chasuble with a gold column and the pallium,
// a white band with black crosses. The cloth (d.veste) is sown with crosslets; the amice at the neck
ABITI.vescovo = function (d) {
  const { cx, F } = G96, v = d.vescovo_v || 0, C = rampaMat(d.veste), [h0, , l0] = _hsl(...hex2rgb(d.veste))
  const U = l0 > 0.7 ? STOFFA6 : LINO6, G = ORO6, seme = l0 > 0.7 || (h0 >= 25 && h0 <= 60) ? (l0 > 0.7 ? G[2] : LINO6[4]) : G[3]
  const T = (R, t) => R[tra05(t)], rossa = (n) => (n + (d.id ? parseInt(d.id.slice(0, 2), 16) : 0)) % 2 === 0
  const stoffa = (x, y, sopra) => {
    const dx = x - cx, sx = x + (Math.floor(y / 8) % 2) * 5, mx = mod96(sx, 10), my = mod96(y, 8)
    if (!sopra && ((my === 4 && mx >= 3 && mx <= 5) || (mx === 4 && my >= 3 && my <= 5))) return dx > 14 ? mixc(seme, "#000000", 0.25) : seme
    return T(C, panno96(x, y, 3, sopra))
  }
  const tono = (x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx)
    if (v === 0) {
      const e = 9 + (y - 68) * 5 / 26, q = q96(x, y, cx, 79, 6.5, 4.5)
      if (q <= 1) {                                                  // the morse: a gold clasp, a stone
        if (q96(x, y, cx, 79, 2.6, 2) <= 1) return gemma96(rossa(0), x === cx - 1 && y === 78 ? 0 : 1, y === 78 ? 0 : y >= 80 ? 2 : 1)
        return G[q > 0.62 ? (dx + (y - 79) < 0 ? 5 : 1) : 3]
      }
      if (a < e) {                                                   // the alb, or a red dalmatic under a white cope
        let t = dx > 3 ? 2 : 3
        if (dx === 0) t = 1
        if (dx === -1) t = 4
        if ((y === 84 && a <= 6) || q96(x, y, cx + 1, 71, 15, 5) <= 1) t = 1     // the morse's shadow, the amice's
        return T(U, t)
      }
      if (a < e + 7) {                                               // the orphreys: gold bands with stones
        const k = a - e, r = mod96(y, 8)
        if (k < 1 || k >= 6) return G[1]
        if (k >= 3 && k < 5 && r >= 2 && r <= 4) return gemma96(rossa(Math.floor(y / 8)), (k < 4) === (dx > 0) ? 0 : 1, r - 2)
        return T(G, (k < 2 ? (dx < 0 ? 5 : 4) : 3) - (dx > 0 ? 1 : 0))
      }
      return stoffa(x, y, sopra)
    }
    if (v === 1) {
      const yl = 74 + (22 - a) * 12 / 20, r = Math.round(y - yl)     // the arms' centre line, shoulder to stem
      if (a <= 2 && y >= 85) {                                       // the stem, small red crosses down it
        const my = mod96(y, 8)
        if ((my === 4 && a <= 1) || (dx === 0 && (my === 3 || my === 5))) return "#b02a34"
        return G[dx === -2 ? 5 : dx === 2 ? 1 : dx === 1 ? 2 : 3]
      }
      if (a <= 22 && Math.abs(r) <= 2) {
        if (Math.abs(r) <= 1 && (a % 7 === 3 || a % 7 === 4) && a >= 3) return gemma96(rossa(Math.floor(a / 7)), (a % 7 === 3) === (dx > 0) ? 0 : 1, r + 1)
        return G[r === -2 ? (dx < 0 ? 5 : 4) : r === 2 ? 1 : dx > 0 ? 2 : 3]
      }
      if (a <= 22 && r === 3) return T(C, 1)                         // the orphrey's shadow
      return stoffa(x, y, sopra)
    }
    const qp = q96(x, y, cx, 70, 28, 13.5)                           // the pallium: a band round the shoulders, a pendant
    if ((qp > 0.6 && qp <= 1 && y >= 73) || (a <= 2 && y >= 82 && y <= 92)) {
      const croce = (x0, y0) => (x === x0 && Math.abs(y - y0) <= 1) || (y === y0 && Math.abs(x - x0) <= 1)
      if (croce(cx, 88) || croce(cx - 16, 79) || croce(cx + 16, 79)) return "#2a2228"
      if (a <= 2 && y >= 85) return LINO6[y === 92 ? 2 : dx === -2 ? 5 : dx === 2 ? 2 : 4]
      return LINO6[(qp < 0.7 ? 5 : qp > 0.92 ? 2 : 4) - (dx > 10 ? 1 : 0)]
    }
    if (qp > 1 && qp <= 1.1 && y >= 73) return T(C, 1)               // its shadow
    if (a <= 3 && y >= 76) {                                         // the column, a stone every nine rows
      const my = mod96(y, 9)
      if ((my === 3 && a <= 1) || (a === 0 && (my === 2 || my === 4))) return gemma96(rossa(Math.floor(y / 9)), dx === -1 || my === 2 ? 0 : 1, my === 2 ? 0 : my - 2)
      return G[dx === -3 ? 5 : dx === 3 ? 1 : dx > 0 ? 2 : 3]
    }
    return stoffa(x, y, sopra)
  }
  return [...spalle(MARCA_V), (c) => { for (let y = 60; y < F; y++) for (let x = 0; x < F; x++) {
    const dx = x - cx
    if (y >= 65 && q96(x, y, cx, 69, 15, 5) <= 1) {                  // the amice, over the neck
      c.px(x, y, LINO6[q96(x, y, cx, 68, 15, 5) > 1 ? 2 : y <= 66 && dx < 4 ? 5 : dx > 8 ? 3 : 4])
    } else if (c.get(x, y) === PK_V) c.px(x, y, tono(x, y, c.get(x, y - 1) === 0))
  } }]
}

// The tunic, d.tunica_v from the name (esporta.py): 0 a round neck with a hemmed band and a few pleats
// under it; 1 the same with two clavi, the woven bands from the shoulders down, the neck's band in their
// colour (purple, or gold on a purple or dark tunic); 2 a wide neck, the cloth draped in folds across the
// chest, a gold fibula on each shoulder
var PORPORA6 = ["#22102e", "#341a46", "#4a285e", "#623a78", "#84589a", "#aa86bc"]     // the clavi's purple, a muted one
function tunicaT(d) {
  const { cx, F } = G96, v = d.tunica_v || 0, C = rampaMat(d.veste), SK = d._sk6, G = ORO6, T = (R, t) => R[tra05(t)]
  const [h0, s0, l0] = _hsl(...hex2rgb(d.veste)), oro = l0 < 0.3 || (h0 >= 250 && h0 <= 330 && s0 > 0.15)
  const K = oro ? G : PORPORA6
  const [nx, ny, ncy] = v === 2 ? [17, 5.5, 70] : [12.5, 3.5, 69]   // the neckline (12.5: the neck's outer columns stay skin)
  const tono = (x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx)
    if (q96(x, y, cx, ncy, nx, ny) <= 1) {                          // bare skin: the neck, and the collarbones in a wide neck
      if (x >= cx - 12 && x < cx + 12) return colloT(d, x, y)
      return SK[dx > 0 ? 2 : 3]
    }
    if (v === 2) {
      if (q96(x, y, cx, ncy + 0.8, nx + 1.6, ny + 1.4) <= 1) return T(C, dx < -4 ? 5 : dx > 8 ? 2 : 4)   // the neck's rolled edge
      for (const s of [-1, 1]) {                                    // the fibulae
        const ex = x - (cx + s * 22), ey = y - 76, q = ex * ex + ey * ey
        if (q <= 7) return G[q <= 1 ? 5 : ex + ey < -1 ? 4 : ex + ey > 1 ? 1 : 3]
        if (q <= 13 && ex + ey > 0) return T(C, 1)
      }
      // three folds hanging from the fibulae, each deeper in the middle than the one above; beyond the
      // fibulae the cloth falls from the shoulders as on the other tunics
      let t = a > 22 ? panno96(x, y, 3, false) + (dx > 14 ? 1 : 0) : 3
      if (a <= 21) { const sag = 1 - (a / 22) ** 2
        for (const D of [3.5, 8.5, 14]) { const yf = Math.round(77 + D * sag)
          if (y === yf) t = 2; else if (y === yf + 1 && a <= 16) t = 4 } }
      if (q96(x, y, cx, ncy + 2, nx + 2.4, ny + 2) <= 1) t = 2      // the edge's shadow
      if (dx > 14) t -= 1
      if (y >= 90) t -= 1
      if (sopra) t = dx < 0 ? 5 : 4
      return T(C, t)
    }
    const qb = q96(x, y, cx, ncy + 1, nx + 2.6, ny + 2.4)
    if (qb <= 1) {                                                  // the band round the neck
      const R = v === 1 ? K : C
      if (v === 1 && mod96(x, 4) === 1 && qb > 0.55 && qb < 0.85) return oro ? "#b02a34" : G[dx > 6 ? 2 : 4]   // its studs
      return T(R, qb > 0.86 ? 2 : dx < -3 ? 5 : dx > 7 ? 3 : 4)
    }
    if (q96(x, y, cx, ncy + 2, nx + 3, ny + 2.8) <= 1) return T(C, dx > 6 ? 1 : 2)   // its shadow
    if (v === 1 && a >= 16 && a <= 20) {                            // the clavi
      const k = dx < 0 ? 20 - a : a - 16                            // 0 on the lit edge
      if (mod96(y, 7) === 3 && k === 2) return oro ? "#b02a34" : G[dx > 0 ? 2 : 4]
      return T(K, (k === 0 ? 4 : k === 4 ? 1 : 3) - (dx > 0 ? 1 : 0) - (y >= 90 ? 1 : 0) + (sopra ? 1 : 0))
    }
    let t = panno96(x, y, 3, sopra)
    if (v === 1 && (dx === -15 || dx === 21)) t -= 1                // the clavi's shadow
    // pleats gathered under the band
    const yb = ncy + 1 + (ny + 2.8) * Math.sqrt(Math.max(0, 1 - (dx / (nx + 3)) ** 2))
    for (const [px0, n] of [[-8, 6], [-3, 8], [3, 7], [9, 5]]) {
      if (y > yb && y <= yb + n) { if (dx === px0) t -= 1; else if (dx === px0 - 1 && dx < 0) t += 1 }
    }
    return T(C, t)
  }
  return tono
}
ABITI.tunica = function (d) { const t = tunicaT(d); return busto96((x, y, sopra) => (sopra === null ? null : t(x, y, sopra))) }

// a gold cross on the chest, its top at y0: the colour, "ombra" where its shadow falls, or null
var croce96 = (dx, y, y0) => {
  const a = Math.abs(dx), r = y - y0
  if ((a <= 1 && r >= 0 && r <= 12) || (a <= 4 && r >= 3 && r <= 5)) return ORO6[a <= 1 ? (dx < 0 ? 5 : dx === 0 ? 3 : 1) : r === 3 ? 5 : r === 4 ? 3 : 1]
  return (dx === 2 && r >= 6 && r <= 12) || (r === 6 && a >= 2 && a <= 4) ? "ombra" : null
}
// The cassock, d.talare_v from the name (esporta.py): 0 with the short shoulder cape, buttoned; 1 plain,
// a gold crucifix on a cord round the neck; 2 under a white surplice with a square neck, and a stole
// (d.stola its colour; without it red for a martyr, purple for the others); 3 no cassock but a priest's
// chasuble in d.stola's colour, for those of before the Roman collar: plain cloth, one narrow column edged
// in gold, no stones (the bishop's has them), the amice at the neck. The standing collar with its white
// tab on the first three
ABITI.talare = function (d) {
  const { cx, F } = G96, v = d.talare_v || 0, C = rampaMat(d.veste), G = ORO6, T = (R, t) => R[tra05(t)]
  const st = d.stola || (d.martire ? "#a8283a" : "#6a3a7c"), hs = _hsl(...hex2rgb(st))[0]
  const S = hs >= 260 && hs <= 320 ? rampa6(st, PORPORA6) : rampaMat(st), croce = S[0] === ORO6[0] ? "#b02a34" : null   // on a gold stole the cross is red
  const veste = (x, y, sopra, bottoni) => {                        // the cassock's own cloth, buttoned down the middle
    const dx = x - cx
    if (dx === 0 && y >= 71) return T(C, bottoni && mod96(y, 4) === 2 ? 5 : 1)
    return T(C, dx === -1 && y >= 71 ? 4 : panno96(x, y, 3, sopra))
  }
  const tono = (x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx)
    if (v === 0) {
      const qc = q96(x, y, cx, 73, 36, 13.5)                        // the cape: its hem lit, a shadow under it
      if (qc > 0.9 && qc <= 1 && y > 78) return T(C, dx < 0 ? 5 : 4)
      if (qc > 1 && qc <= 1.14 && y > 78) return T(C, 1)
      return veste(x, y, sopra, true)
    }
    if (v === 1) {
      const k = croce96(dx, y, 79)
      if (k) return k === "ombra" ? C[0] : k
      if (y >= 70 && y <= 79 && Math.abs(a - (10 - (y - 70) * 0.95)) < 0.6) return G[dx < 0 ? 3 : 2]   // the cord
      return veste(x, y, sopra, y < 78)
    }
    if (v === 3) {
      if (a === 3 && y >= 74) return G[dx < 0 ? 4 : 2]              // the column's gold edges
      if (a <= 2 && y >= 74) return T(S, dx < 0 ? 5 : dx === 0 ? 4 : 3)
      if ((dx === 4 && y >= 74) || q96(x, y, cx + 1, 71, 15, 5) <= 1) return T(S, 1)   // the column's shadow, the amice's
      return T(S, panno96(x, y, 3, sopra))
    }
    if (a <= 8 && y <= 75) return veste(x, y, false, true)          // the cassock in the surplice's square neck
    if (a <= 10 && y <= 77) return LINO6[y === 77 || a === 10 ? (dx < 0 ? 4 : 3) : 5]   // its hem
    if (a >= 10 && a <= 15) {                                       // the stole, a cross on each side
      const k = dx < 0 ? 15 - a : a - 10
      if ((k === 2 && y >= 81 && y <= 87) || (y === 83 && k >= 1 && k <= 3)) return croce || G[dx < 0 ? 4 : 3]
      return T(S, (k === 0 ? 5 : k === 5 ? 1 : 3) - (dx > 0 ? 1 : 0) + (sopra ? 1 : 0))
    }
    if ((y === 78 && a <= 9) || dx === -9 || dx === 16) return LINO6[2]                  // the shadows of hem and stole
    let t = panno96(x, y, 4, sopra)
    if (a < 9 && y >= 79 && y <= 83 + mod96(dx, 8) / 2 && mod96(dx, 4) === 0) t -= 1   // the gathers under the yoke, short
    return T(LINO6, t)
  }
  return [...spalle(MARCA_V), (c) => { for (let y = 60; y < F; y++) for (let x = 0; x < F; x++) {
    const dx = x - cx
    if (v === 3 && y >= 65 && q96(x, y, cx, 69, 15, 5) <= 1) {      // the amice, as the bishop's
      c.px(x, y, LINO6[q96(x, y, cx, 68, 15, 5) > 1 ? 2 : y <= 66 && dx < 4 ? 5 : dx > 8 ? 3 : 4])
    } else if (v !== 3 && y >= 66 && q96(x, y, cx, 69, 13, 4) <= 1) { // the standing collar, over the neck; its tab (from y 66: at 65 the ellipse left one lone pixel)
      c.px(x, y, Math.abs(dx) <= 3 && y >= 66 && y <= 69 ? LINO6[y === 69 ? 3 : 5] : C[q96(x, y, cx, 68, 13, 4) > 1 ? 1 : y <= 66 && dx < 4 ? 5 : dx > 8 ? 2 : 4])
    } else if (c.get(x, y) === PK_V) c.px(x, y, tono(x, y, c.get(x, y - 1) === 0))
  } }]
}

// --- the nun, as the hand-made Santa Chiara: a veil over a white wimple, a guimpe on the chest, the habit.
// Dark veils and habits take the veil's own ramp, a violet black
var VELO6 = ["#141018", "#221c28", "#322a38", "#463c4c", "#5e5466", "#7e7488"]
var veloR = (col) => (_hsl(...hex2rgb(col))[2] < 0.22 ? rampa6(col, VELO6) : rampaMat(col))
// The veil: folds fanning from the top, the light beside each, the left rim lit, the depth beside the
// wimple. A nun's (d.abito suora) opens on the white wimple, with its band on the forehead; any other
// woman's on its own shadow
COPRICAPI.velo = function (d) {
  const { cx, F } = G96, R = veloR(d.velo || "#2c2830"), T = (Q, t) => Q[tra05(t)], monaca = d.abito === "suora"
  const [rx, ry] = VISI[d.viso || 0], vis = (x, y) => q96(x, y, cx, 43, rx + 0.5, ry + 0.5) <= 1
  const velo = (x, y) => q96(x, y, cx, 38, 26, 26.6) <= 1 || (y >= 40 && Math.abs(x - cx) <= 26 + (y - 40) * 3 / 40)
  const apre = (x, y) => q96(x, y, cx, 41, 20.6, 23.6) <= 1         // not whole radii: no lone pixel at the ends
  const vt = (x, y) => {
    const st = (xx) => Math.floor((xx - cx) / (1 + (Math.max(y, 10) - 4) / 14) / 4), si = st(x)
    const l = -(((x - cx) / 26) * 0.6 + ((y - 38) / 27) * 0.55)
    let t = l > 0.45 ? 3 : l > -0.2 ? 2 : 1
    if (si !== st(x - 1)) t -= 1
    if (si !== st(x + 1) && x < cx) t += 1
    if (x > cx + 14) t = Math.min(t, 1)
    const q = q96(x, y, cx, 38, 26, 27)
    if (q > 0.86 && x < cx - 4 && y < 40) t = q > 0.93 ? 5 : 4
    if (y >= 40 && x < cx && Math.abs(x - cx) >= 25 + (y - 40) * 3 / 40) t = 4
    if (q96(x, y, cx, 41, 22.6, 25.6) <= 1 && y > 23) t = 0
    return T(R, t)
  }
  const wt = (x, y) => {                                            // the wimple, the face's shadow on it
    const dx = x - cx
    if (y <= 29) return LINO6[tra05((dx > 13 ? 3 : y <= 25 && dx < -4 ? 5 : 4) - (y === 29 ? 1 : 0))]
    let t = dx > 15 ? 2 : dx > 8 ? 3 : 4
    if (vis(x - 2, y - 3) && !vis(x, y)) t = Math.min(t, y > 60 ? 1 : 2)
    return LINO6[t]
  }
  const ogni = (f) => (c) => { for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) { const k = f(x, y); if (k) c.px(x, y, k) } }
  return { dietro: [ogni((x, y) => (apre(x, y) && y >= 24 ? (monaca ? wt(x, y) : T(R, x > cx + 6 ? 0 : 1)) : velo(x, y) ? vt(x, y) : null))],
    davanti: [ogni((x, y) => (apre(x, y) && y <= (monaca ? 29 : 25) ? (y <= 23 || !monaca ? vt(x, y) : wt(x, y)) : null))] }
}
// The habit, d.suora_v from the name (esporta.py): 0 a wide guimpe, its folds fanning from the chin; 1 the
// same with a wooden crucifix on it; 2 a shorter guimpe and the scapular down the front
ABITI.suora = function (d) {
  const { cx, F } = G96, v = d.suora_v || 0, C = veloR(d.veste), T = (Q, t) => Q[tra05(t)]
  const [rx, ry] = VISI[d.viso || 0], vis = (x, y) => q96(x, y, cx, 43, rx + 0.5, ry + 0.5) <= 1
  const [gx, gy, gc] = v === 2 ? [18.6, 11.6, 66] : [20.6, 15.6, 68], LEGNO = ["#3a2416", "#5e3c22", "#8a5c34"]
  const tono = (x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx), q = q96(x, y, cx, gc, gx, gy)
    if (y >= 58 && q <= 1) {                                        // the guimpe
      if (v === 1 && ((a <= 1 && y >= 71 && y <= 81) || (a <= 3 && y >= 73 && y <= 75))) return LEGNO[a <= 1 ? 1 - dx : 75 - y]
      let t = dx > 15 ? 2 : dx > 8 ? 3 : 4
      const sg = (xx) => Math.floor(Math.atan2(y - 52, xx - cx) / (Math.PI / 9))
      if (sg(x) !== sg(x - 1)) t -= 1
      if (q > 0.86) t -= 1
      if (dx < -6 && y < 72 && q > 0.7) t = 5
      if (vis(x - 2, y - 3) && !vis(x, y)) t = Math.min(t, y > 60 ? 1 : 2)
      if (v === 1 && ((dx === 2 && y >= 76 && y <= 81) || (y === 76 && a >= 2 && a <= 3))) t = 2    // the crucifix's shadow
      return T(LINO6, t)
    }
    if (sopra === null) return null                                 // not the bust
    if (q96(x, y, cx + 1, gc + 2, gx + 1, gy + 0.5) <= 1) return T(C, 1)    // the guimpe's shadow
    // the scapular: the habit's own cloth, its left edge lit, the right one and what is beside it in shadow
    if (v === 2 && a <= 13) return T(C, a === 13 ? (dx > 0 ? 1 : 2) : a === 12 ? (dx < 0 ? 5 : 1) : dx > 4 ? 2 : 3)
    return T(C, panno96(x, y, 3, sopra))
  }
  return [...spalle(MARCA_V), (c) => { for (let y = 58; y < F; y++) for (let x = 0; x < F; x++) {
    const k = tono(x, y, c.get(x, y) === PK_V ? c.get(x, y - 1) === 0 : null)
    if (k) c.px(x, y, k)
  } }]
}

// --- the monks' habits. The hood lowered on the shoulders is a thick roll round the neck, dipping in
// front where the neck comes out: its upper rim lit, small creases, the lower rim and what is under it in
// shadow. rotolo96(x, y, R) gives its colour, or "ombra" just under it, or null
function rotolo96(x, y, R) {
  const dx = x - G96.cx, q = q96(x, y, G96.cx, 73, 22.6, 7.6)
  if (q96(x, y, G96.cx, 65, 9.6, 5.6) <= 1) return null             // the neck
  if (q > 1) return q <= 1.22 && y > 73 ? "ombra" : null
  let t = y <= 70 ? 4 : y <= 75 ? 3 : 2
  if (q96(x, y, G96.cx, 72, 22.6, 7.6) > 1 && y < 73) t = dx < 4 ? 5 : 4    // the upper rim
  if (q96(x, y, G96.cx, 65, 11.6, 7.2) <= 1) t = 2                  // the fold round the neck
  if (mod96(dx + (y > 73 ? 2 : 0), 7) === 3) t -= 1                 // creases
  if (q > 0.84 && y > 73) t = 1
  if (dx > 12) t -= 1
  return R[tra05(t)]
}
// The Benedictine, d.benedettino_v from the name (esporta.py): 0 the scapular down the front; 1 the same
// with an abbot's gold cross on it; 2 the choir cowl, wide and pleated from the neck, no scapular
ABITI.benedettino = function (d) {
  const { cx, F } = G96, v = d.benedettino_v || 0, C = veloR(d.veste), T = (Q, t) => Q[tra05(t)]
  const tono = (x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx), r = rotolo96(x, y, C)
    if (r && r !== "ombra") return r
    if (sopra === null) return null                                 // not the bust
    if (r) return C[1]
    if (v === 2) {                                                  // pleats fanning from the neck
      const sg = (xx) => Math.floor(Math.atan2(y - 58, xx - cx) / (Math.PI / 16))
      let t = panno96(x, y, 3, sopra)
      if (!sopra && sg(x) !== sg(x - 1)) t = 2; else if (!sopra && sg(x) !== sg(x + 1) && dx < 6) t = 4
      return T(C, t - (y >= 90 ? 1 : 0))
    }
    if (a <= 12) {                                                  // the scapular
      const k = v === 1 ? croce96(dx, y, 81) : null
      if (k) return k === "ombra" ? C[0] : k
      return T(C, a === 12 ? (dx < 0 ? 5 : 1) : dx > 4 ? 2 : 3)
    }
    if (a === 13) return C[dx > 0 ? 1 : 2]
    return T(C, panno96(x, y, 3, sopra))
  }
  return [...spalle(MARCA_V), (c) => { for (let y = 60; y < F; y++) for (let x = 0; x < F; x++) {
    const k = tono(x, y, c.get(x, y) === PK_V ? c.get(x, y - 1) === 0 : null)
    if (k) c.px(x, y, k)
  } }]
}

// The friar's habit, d.saio_v from the name (esporta.py): 0 the white cord with its knots; 1 a wooden tau
// on the chest; 2 patched, a hermit's; 3 a Carmelite's, the white mantle and hood over the brown habit and
// scapular. The hood lowered round the neck on all four (rotolo96)
ABITI.saio = function (d) {
  const { cx, F } = G96, v = d.saio_v || 0, C = rampaMat(d.veste), T = (Q, t) => Q[tra05(t)]
  const CORDA = ["#8a7a5c", "#b8a880", "#ece0c4", "#fff8e4"], TAU = ["#5a3818", "#8a5c2a", "#b88444", "#e6c084"]
  const toppa = (x, y, x0, y0, w, h, chiara) => {                   // a patch: its cloth, stitches round it
    if (x < x0 || x >= x0 + w || y < y0 || y >= y0 + h) return null
    const orlo = x === x0 || x === x0 + w - 1 || y === y0 || y === y0 + h - 1
    return orlo && (x + y) % 2 === 0 ? CORDA[1] : T(C, (chiara ? 4 : 2) - (orlo ? 1 : 0))
  }
  const tono = (x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx), r = rotolo96(x, y, v === 3 ? LINO6 : C)
    if (r && r !== "ombra") return r
    if (sopra === null) return null                                 // not the bust
    if (v === 3) {
      if (a >= 15) return r ? LINO6[2] : T(LINO6, panno96(x, y, 4, sopra))     // the mantle
      if (r) return C[1]
      return T(C, a === 14 ? 1 : a === 12 ? (dx < 0 ? 5 : 1) : a === 13 ? (dx > 0 ? 1 : 2) : dx > 4 ? 2 : 3)   // habit and scapular in its opening
    }
    // the tau's cord, coming out from under the hood
    if (v === 1 && ((dx === 0 && y === 82) || (a === 1 && y === 81) || (a === 2 && y === 80) || (a === 3 && y === 79))) return CORDA[dx > 0 ? 1 : 2]
    if (r) return C[1]
    if (v === 0) {
      const k = dx + 8                                              // the cord, two knots on it
      if (y >= 81 && ((k >= 0 && k <= 1) || (k >= -1 && k <= 2 && (mod96(y, 6) === 1 || mod96(y, 6) === 2)))) return CORDA[k <= 0 ? 3 : mod96(y, 6) === 2 ? 1 : 2]
      if (y >= 81 && k === 2) return C[1]
    }
    if (v === 1) {
      // the Franciscan tau, of olive wood: the arms flare towards their ends, the top edge dips in the
      // middle, the stem widens at the foot; a grain along both, a cord through its top
      const y0 = 83, r = y - y0, punta = a >= 4
      const braccio = a <= 5 && r >= (punta ? 0 : 1) && r <= (punta ? 4 : 3), piede = r >= 9
      const stelo = r >= 4 && r <= 10 && a <= (piede ? 2 : 1)
      const tau = (xx, rr) => { const aa = Math.abs(xx - cx), pp = aa >= 4
        return (aa <= 5 && rr >= (pp ? 0 : 1) && rr <= (pp ? 4 : 3)) || (rr >= 4 && rr <= 10 && aa <= (rr >= 9 ? 2 : 1)) }
      if (braccio || stelo) {
        if (!tau(x, r - 1) || !tau(x - 1, r)) return TAU[3]         // the edges towards the light
        if (!tau(x, r + 1) || !tau(x + 1, r)) return TAU[0]
        return TAU[(braccio && r === 2 && a % 3 !== 1) || (stelo && dx === 0 && r % 3 !== 0) ? 1 : 2]   // the grain
      }
      if (tau(x - 1, r) || tau(x, r - 1)) return C[0]               // its shadow
    }
    if (v === 2) { const k = toppa(x, y, cx - 22, 82, 9, 8, true) || toppa(x, y, cx + 8, 85, 7, 6, false); if (k) return k }
    return T(C, panno96(x, y, 3, sopra))
  }
  return [...spalle(MARCA_V), (c) => { for (let y = 60; y < F; y++) for (let x = 0; x < F; x++) {
    const k = tono(x, y, c.get(x, y) === PK_V ? c.get(x, y - 1) === 0 : null)
    if (k) c.px(x, y, k)
  } }]
}

// --- kings and queens. PERLA: a pearl and its shadow. manto6: a mantle's ramp, the muted purple for a purple one
var PERLA = ["#fffdf6", "#b8a890"]
var manto6 = (col) => { const h = _hsl(...hex2rgb(col))[0]; return h >= 260 && h <= 320 ? rampa6(col, PORPORA6) : rampaMat(col) }
// The crown, d.corona_v with the robe's variant (esporta.py): 0 five points, a pearl on each, stones and
// pearls on the band; 1 the Byzantine stemma, a tall band edged with pearls, a plaque with a cross over the
// brow, strings of pearls hanging beside the face; 2 a circlet with three fleurons
COPRICAPI.corona = function (d) {
  const { cx, F } = G96, v = d.corona_v || 0, G = ORO6
  const gemma = (n, ix, iy) => gemma96(n % 2 === 0, ix === 0 ? 0 : 1, iy)
  // a fleur-de-lis, 7 x 9, standing on the band
  const GIGLIO = ["...#...", "..###..", "..###..", "...#...", "#..#..#", "##.#.##", ".#####.", "..###..", ".#####."]
  const tono = (x, y) => {
    const dx = x - cx, a = Math.abs(dx), lato = dx > 10 ? 1 : 0
    if (v === 1) {
      if (dx === 0 && y >= 8 && y <= 12 || (a <= 1 && y === 10)) return G[4]                       // the cross
      if (y >= 13 && y <= 18 && q96(x, y, cx, 18.5, 4.6, 5.6) <= 1) return a <= 1 && y >= 15 && y <= 17 ? gemma(1, dx + 1, y - 15) : G[dx < -1 ? 5 : dx > 1 ? 2 : 4]   // the plaque
      if (a <= 19 && y >= 19 && y <= 26) {
        if (y === 19 || y === 26) return mod96(dx, 2) === 0 ? PERLA[y === 26 || lato ? 1 : 0] : G[2]
        if (a <= 1 && y >= 21 && y <= 24) return gemma(0, dx + 1, Math.min(2, y - 21))
        for (const g of [7, 13]) if ((a === g || a === g + 1) && y >= 22 && y <= 24) return gemma(g === 7 ? 1 : 0, (a === g) === (dx > 0) ? 0 : 1, y - 22)
        return G[tra05([5, 4, 3, 3, 2, 1][y - 20] - lato)]
      }
      if ((a === 20 || a === 21) && y >= 27 && y <= 48) {                                          // the pendilia
        if (y >= 46) return gemma(0, a === (dx < 0 ? 21 : 20) ? 0 : 1, y - 46)
        return mod96(y, 3) === 2 ? (a === 20 ? G[2] : null) : PERLA[(mod96(y, 3) === 1 || (a === 21) === (dx > 0)) ? 1 : 0]
      }
      return null
    }
    const y0 = v === 2 ? 22 : 20
    if (a <= 17 && y >= y0 && y <= 26) {                                                           // the band
      const r = y - y0
      if (v === 0) {
        for (const g of [-10, 0, 10]) if (Math.abs(dx - g) <= 1 && r >= 2 && r <= 4) return gemma(g / 10 + 1, dx - g + 1, r - 2)
        if (a === 5 && (r === 3 || r === 4)) return PERLA[r - 3]
        return G[tra05([5, 4, 3, 3, 3, 2, 1][r] - lato)]
      }
      for (const g of [-9, 0, 9]) if ((dx === g || dx === g + 1) && (r === 1 || r === 2)) return gemma(g / 9 + 1, dx - g, (r - 1) * 2)
      return G[tra05([5, 4, 3, 2, 1][r] - lato)]
    }
    if (v === 0) for (const p of [-14, -7, 0, 7, 14]) {                                            // the points
      const h = 20 - y, k = dx - p
      if (h >= 1 && h <= 8 && Math.abs(k) <= Math.round(3.4 * (1 - h / 9))) return G[tra05((k < 0 ? 5 : k === 0 ? 4 : 2) - lato)]
      if (k === 0 && (h === 9 || h === 10)) return PERLA[h === 9 ? 1 : 0]
    }
    if (v === 2) for (const p of [-12, 0, 12]) if ((GIGLIO[y - 13] || "")[dx - p + 3] === "#") return G[tra05((dx - p < 0 ? 5 : dx - p === 0 ? 4 : 2) - lato)]
    return null
  }
  return { dietro: [], davanti: [(c) => { for (let y = 0; y < 50; y++) for (let x = 0; x < F; x++) { const k = tono(x, y); if (k) c.px(x, y, k) } }] }
}
// The royal robe, d.regale_v from the name (esporta.py): 0 the mantle open on a tunic with a jewelled gold
// band, a wide ermine collar; 1 Byzantine, the robe in the mantle's colour, a jewelled gold collar edged
// with pearls and the loros, a broad jewelled band down the front; 2 the mantle closed on the chest by a
// round brooch, the tunic's embroidered neck over it. d.secondo: the mantle's colour
ABITI.regale = function (d) {
  const { cx, F } = G96, v = d.regale_v || 0, C = rampaMat(d.veste), M = manto6(d.secondo || "#962832"), G = ORO6, T = (Q, t) => Q[tra05(t)]
  const n0 = d.id ? parseInt(d.id.slice(0, 2), 16) : 0, gemma = (n, ix, iy) => gemma96((n + n0) % 2 === 0, ix === 0 ? 0 : 1, iy)
  const tono = (x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx), q = q96(x, y, cx, 71, 21, 7.5)
    if (v !== 2 && q <= 1 && q96(x, y, cx, 65, 10, 5) > 1) {       // the collar, round the neck
      if (v === 0) {                                               // ermine: white fur, black tails
        if (q < 0.8 && mod96(dx + 3, 7) === 0 && mod96(y + (mod96(Math.floor((dx + 3) / 7), 2)) * 2, 5) <= 1) return "#1e1a20"
        return LINO6[q96(x, y, cx, 70, 21, 7.5) > 1 && y < 71 ? 5 : q > 0.82 ? 2 : dx > 8 ? 3 : 4]
      }
      if (q > 0.84 || q96(x, y, cx, 65, 11.4, 6.2) <= 1) return mod96(dx + y, 2) === 0 ? PERLA[dx > 8 ? 1 : 0] : G[2]
      if (mod96(dx + 1, 6) <= 1 && y >= 72 + (a > 12 ? -3 : a > 7 ? -1 : 1) && y <= 73 + (a > 12 ? -3 : a > 7 ? -1 : 1)) return gemma(Math.floor((dx + 1) / 6), mod96(dx + 1, 6), (y - 72 - (a > 12 ? -3 : a > 7 ? -1 : 1)) * 2)
      return G[tra05((y <= 68 ? 5 : 3) - (dx > 8 ? 1 : 0))]
    }
    if (sopra === null) return null                                // not the bust
    const sotto = v !== 2 && q96(x, y, cx, 72.6, 22, 8.6) <= 1     // in the collar's shadow
    if (v === 1) {
      if (a <= 6) {                                                // the loros
        if (a === 6) return mod96(y, 2) === 0 ? PERLA[dx > 0 ? 1 : 0] : G[2]
        const my = mod96(y, 6), g = a >= 3 && a <= 4 && my <= 1 ? 1 : a <= 1 && my >= 3 && my <= 4 ? 2 : 0
        if (g) return gemma(Math.floor(y / 6) + g, g === 1 ? ((a === 3) === (dx > 0) ? 0 : 1) : dx <= 0 ? 0 : 1, (g === 1 ? my : my - 3) * 2)
        return G[sotto ? 1 : dx < -2 ? 4 : dx > 2 ? 2 : 3]
      }
      return T(M, sotto || a === 7 ? 1 : panno96(x, y, 3, sopra))
    }
    if (v === 2) {
      const qf = (x - cx) ** 2 + (y - 77) ** 2                     // the brooch
      if (qf <= 20) return qf <= 3 ? gemma(0, dx < 0 ? 0 : 1, y - 76) : G[qf > 12 ? (dx + y - 77 < 0 ? 5 : 1) : 3]
      if (qf <= 30 && dx + y - 77 > 0) return M[1]
      const collo = a <= 10 && y <= 74, apre = y > 80 && a < (y - 80) * 0.45
      if (collo || apre) {                                         // the tunic: its neck band, and under the mantle's opening
        if (collo && q96(x, y, cx, 67, 11.6, 6.6) > 0.5) return G[y === 74 ? 1 : dx < -2 ? 4 : dx > 4 ? 2 : 3]
        return T(C, collo ? 2 : dx > 1 ? 3 : 4)
      }
      if ((a <= 11.5 && y <= 75) || (y > 80 && a < (y - 80) * 0.45 + 1.6)) return G[dx < 0 ? 4 : 2]   // the mantle's gold edge
      return T(M, panno96(x, y, 3, sopra))
    }
    const e = 15 + Math.max(0, y - 78) * 0.4                       // the mantle's inner edge
    if (a > e) return a <= e + 1.6 ? G[sotto ? 1 : dx < 0 ? 4 : 2] : T(M, sotto ? 1 : panno96(x, y, 3, sopra))
    if (a <= 2) {                                                  // the tunic's band, a stone every eight rows
      const my = mod96(y, 8)
      if (a <= 1 && my >= 3 && my <= 5) return gemma(Math.floor(y / 8), dx + 1, my - 3)
      return G[sotto ? 1 : dx === -2 ? 5 : dx === 2 ? 1 : 3]
    }
    return T(C, sotto ? 1 : a === 3 && dx > 0 ? 2 : dx > 4 ? 3 : 4)
  }
  return [...spalle(MARCA_V), (c) => { for (let y = 60; y < F; y++) for (let x = 0; x < F; x++) {
    const k = tono(x, y, c.get(x, y) === PK_V ? c.get(x, y - 1) === 0 : null)
    if (k) c.px(x, y, k)
  } }]
}

// --- the popes. The tiara, d.tiara_v (esporta.py): 0 the triregnum, three crowns with their small points
// and stones, an orb and a cross on top; 1 the early one, a white cone with a single crown and a knob
COPRICAPI.tiara = function (d) {
  const { cx, F } = G96, v = d.tiara_v || 0, G = ORO6
  const tono = (x, y) => {
    const dx = x - cx, a = Math.abs(dx), lato = dx > 6 ? 1 : 0
    if (v === 0 && ((dx === 0 && y <= 3) || (a <= 1 && y === 1))) return G[4]                    // the cross
    if (v === 1 && a <= 1 && y >= 0 && y <= 1) return G[dx < 0 ? 5 : 3]                          // the knob
    const dentro = (xx, yy) => yy <= 27 && yy >= 2 && q96(xx, yy, cx, 16, v === 1 ? 14.4 : 15.4, v === 1 ? 14.4 : 13.4) <= 1
    for (const [y0, h] of v === 0 ? [[23, 5], [16, 3], [9, 3]] : [[23, 5]]) {                    // the crowns
      if (y === y0 - 1 && dentro(x, y0) && mod96(dx, 4) === 0) return G[4 - lato]                // their points
      if (y >= y0 && y < y0 + h && dentro(x, y)) {
        const r = y - y0
        if (h === 5 && r >= 1 && r <= 3 && mod96(dx + 1, 6) <= 1) return gemma96(mod96(Math.floor((dx + 1) / 6), 2) === 0, mod96(dx + 1, 6), r - 1)
        if (h === 3 && r === 1 && mod96(dx, 4) === 2) return mod96(Math.floor(dx / 4), 2) ? "#b02a34" : "#2e56b0"
        return G[tra05((r === 0 ? 5 : r === h - 1 ? 1 : 3) - lato)]
      }
    }
    if (!dentro(x, y)) return null
    let t = dx < -7 ? 5 : dx > 9 ? 2 : dx > 3 ? 3 : 4                                             // the white cap, round
    if (!dentro(x - 1, y) || !dentro(x, y - 1)) t = 5
    if ([8, 15, 22].includes(y) && v === 0) t -= 1                                                // the shadow under each crown
    return LINO6[tra05(t)]
  }
  return { dietro: [], davanti: [(c) => { for (let y = 0; y < 28; y++) for (let x = 0; x < F; x++) { const k = tono(x, y); if (k) c.px(x, y, k) } }] }
}
// --- attributes held in the hand. mano96: a closed fist round a shaft at x 80..82, four fingers and the
// thumb, in the saint's skin; manica96: the wide sleeve it comes out of, in the robe's colour. Order in an
// attribute: sleeve, shaft, hand. ATTR_MANO: what the sprite depends on, for attrSprite's key
var LEGNO6 = ["#2e1c12", "#4a2e1a", "#6e4626", "#946236", "#b8844c", "#d8a86c"]
var ATTR_MANO = { pastorale: (d) => d.pelle + d.veste + (d.mitra_v || 0), croce: (d) => d.pelle + d.veste + (d.croce_v || 0),
  bastone: (d) => d.pelle + d.veste + (d.bastone_v || 0),
  giglio: (d) => d.pelle + d.veste + (d.giglio_v || 0), palma: (d) => d.pelle + d.veste + (d.palma_v || 0),
  spada: (d) => d.pelle + d.veste + (d.spada_v || 0),
  libro: (d) => "" + (d.libro_v || 0) + (d.libro_c || 0) }
// a shaft 3 px wide on the axis x 81, from y0 down: tones t of scale Q for its left, middle and right column
function asta96(c, y0, Q, t) { for (let y = y0; y <= 93; y++) for (let i = 0; i < 3; i++) c.px(80 + i, y, Q[t[i]]) }
function mano96(c, R) {
  for (let i = 0; i < 4; i++) { const y = 73 + i * 3
    c.rect(75, y, 10, 3, R[3]); c.hline(75, y, 10, R[4]); c.px(75, y, R[5]); c.px(76, y, R[5]); c.hline(75, y + 2, 10, R[1]); c.px(75, y + 1, R[4]) }
  c.rect(85, 73, 5, 12, R[3]); c.vline(89, 74, 10, R[1]); c.vline(88, 75, 9, R[2]); c.hline(85, 73, 4, R[4]); c.hline(85, 84, 5, R[1])
  for (let i = 0; i < 4; i++) { const y = 73 + i * 3
    c.px(85, y, R[5]); c.px(86, y, R[5]); c.px(85, y + 2, R[0]); c.px(84, y + 2, R[0]) }
  c.px(75, 73, "_"); c.px(75, 84, "_"); c.px(89, 73, "_"); c.px(89, 84, "_")
}
function manica96(c, R) {
  for (let y = 85; y <= 93; y++) for (let x = 74 - (y - 85) / 3; x <= 93; x++) {
    const xi = Math.round(x)
    c.px(xi, y, R[y === 85 ? 1 : y === 86 ? 4 : xi > 88 ? 2 : xi % 5 === 0 ? 2 : 3])
  }
}
// The crozier, by the mitre's variant (d.mitra_v, esporta.py), the two going together: 0 the Gothic one,
// gold, the crook closing in a volute, a knop with a stone; 1 the early one, a plain staff with an
// open hook, all of wood (the user: an ivory hook was not understood); 2 the Eastern bishops' staff, two serpents' heads facing a small cross; 3 the modern
// one, a wider crook with crockets and two knops
ATTRIBUTI96.pastorale = function (d) {
  const v = d.mitra_v || 0, G = ORO6, A = 81                         // the shaft's axis
  const asta = (c, y0, Q, t) => { for (let y = y0; y <= 93; y++) { c.px(A - 1, y, Q[t[0]]); c.px(A, y, Q[t[1]]); c.px(A + 1, y, Q[t[2]]) } }
  const luce = (x, y, x0, y0, r) => { const l = -(((x - x0) / r) * 0.6 + ((y - y0) / r) * 0.7); return 3 + (l > 0.35 ? 1 : 0) + (l > 0.75 ? 1 : 0) - (l < -0.35 ? 1 : 0) - (l < -0.75 ? 1 : 0) }
  const nodo = (c, y, rossa) => { for (let yy = y; yy < y + 4; yy++) for (let x = A - 3; x <= A + 3; x++) {
    if ((yy === y || yy === y + 3) && Math.abs(x - A) === 3) continue
    c.px(x, yy, G[tra05((yy === y ? 5 : yy === y + 3 ? 1 : 3) - (x > A + 1 ? 1 : 0))]) }
    if (rossa !== undefined) { c.px(A, y + 1, gemma96(rossa, 0, 0)); c.px(A, y + 2, gemma96(rossa, 1, 2)) } }
  // a crook: a ring round (x0, y0) from the shaft over the top and down the right, open at the lower left
  const riccio = (c, x0, y0, r, w, Q, fine) => { for (let y = y0 - r - 1; y <= y0 + r + 1; y++) for (let x = x0 - r - 1; x <= x0 + r + 1; x++) {
    const q = Math.hypot(x - x0, y - y0)
    if (q <= r && q > r - w && fine(x, y)) c.px(x, y, Q[tra05(luce(x, y, x0, y0, r) - (q <= r - w + 1 ? 1 : 0) + (q > r - 1 && x + y < x0 + y0 ? 1 : 0))]) } }
  return [(c) => {
    manica96(c, rampaMat(d.veste))
    if (v === 1) {
      const x0 = A + 5, y0 = 20
      asta(c, y0, LEGNO6, [4, 3, 1])
      riccio(c, x0, y0, 6.4, 2.6, LEGNO6, (x, y) => y <= y0 || (x > x0 && y <= y0 + 3))
    } else if (v === 2) {
      asta(c, 20, G, [4, 3, 1]); nodo(c, 22)
      for (const s of [-1, 1]) {                                     // the serpents: a bar curling up to a head
        for (let i = 1; i <= 6; i++) { c.px(A + s * i, 18, G[s < 0 ? 4 : 2]); c.px(A + s * i, 19, G[1]) }
        c.px(A + s * 7, 18, G[3]); c.px(A + s * 7, 17, G[s < 0 ? 4 : 2]); c.px(A + s * 7, 16, G[s < 0 ? 5 : 3])   // the neck
        c.px(A + s * 6, 15, G[4]); c.px(A + s * 5, 15, G[3]); c.px(A + s * 5, 16, "#b02a34")                       // the head, turned in
      }
      c.vline(A, 8, 11, G[4]); c.hline(A - 2, 10, 5, G[4]); c.px(A + 1, 11, G[1])   // the cross between them
    } else {
      const r = v === 3 ? 7 : 6.6, x0 = A + r - 1.4, y0 = v === 3 ? 14 : 17
      asta(c, y0, G, [4, 3, 1])
      riccio(c, x0, y0, r, 2.6, G, (x, y) => !(x < x0 && y > y0))
      for (let y = Math.round(y0); y <= y0 + 4; y++) for (let x = Math.round(x0) - 2; x <= x0 + 2; x++)          // the volute
        if (Math.hypot(x - x0, y - y0 - 2.2) <= 2.3) c.px(x, y, G[luce(x, y, x0, y0 + 2.2, 2.3)])
      if (v === 3) { for (const [x, y] of [[x0 - 5, y0 - 6], [x0, y0 - 8], [x0 + 5, y0 - 6]]) { c.px(Math.round(x), Math.round(y), G[4]); c.px(Math.round(x) + 1, Math.round(y), G[2]) }
        nodo(c, y0 + 10, true); nodo(c, y0 + 18) } else nodo(c, y0 + 11, false)
    }
    mano96(c, d._sk6 || PELLE6)
  }]
}
// The cross in the hand, d.croce_v (esporta.py): 0 a plain wooden one; 1 a gold one with flared ends, a stone
// at the crossing and a knop, for popes, cardinals and sovereigns; 2 a crucifix, the wooden cross with the
// titulus and an ivory figure; 3 the Eastern cross, gold, with three bars, the lowest slanting
ATTRIBUTI96.croce = function (d) {
  const v = d.croce_v || 0, Q = v === 1 || v === 3 ? ORO6 : LEGNO6, A = 81
  const braccio = (c, y, m) => { for (let x = A - m; x <= A + m; x++) { c.px(x, y - 1, Q[x < A ? 5 : 4]); c.px(x, y, Q[3]); c.px(x, y + 1, Q[1]) } }
  return [(c) => {
    manica96(c, rampaMat(d.veste))
    asta96(c, v === 3 ? 26 : 30, Q, [4, 3, 1])
    if (v === 3) {
      braccio(c, 32, 3); braccio(c, 39, 7)
      for (let i = -4; i <= 4; i++) { const y = 49 + Math.round(i / 2); c.px(A + i, y - 1, Q[4]); c.px(A + i, y, Q[3]); c.px(A + i, y + 1, Q[1]) }
    } else {
      braccio(c, 43, 8)
      c.px(A - 1, 42, Q[4]); c.px(A, 42, Q[3])                       // the shaft over the arms
      if (v === 1) {
        for (const [x, y] of [[A - 9, 43], [A + 9, 43], [A, 29]]) for (let i = -2; i <= 2; i++) {                 // the flared ends
          if (y === 43) c.px(x, y + i, Q[i < 0 ? 5 : i > 0 ? 1 : 3]); else c.px(x + i, y, Q[i < 0 ? 5 : 3]) }
        for (let iy = 0; iy < 3; iy++) for (let ix = 0; ix < 3; ix++) c.px(A - 1 + ix, 42 + iy, gemma96(true, ix, iy))
        for (let yy = 54; yy < 57; yy++) for (let x = A - 3; x <= A + 3; x++) c.px(x, yy, Q[yy === 54 ? 5 : yy === 56 ? 1 : x > A + 1 ? 2 : 3])
      }
      if (v === 2) {
        c.hline(A - 2, 33, 5, LINO6[4]); c.hline(A - 2, 34, 5, LINO6[2])                                           // the titulus
        const I = ["#a8927a", "#d8c8ac", "#f4ead6"]                                                               // the ivory figure
        c.px(A, 39, I[2]); c.px(A, 40, I[1])
        for (let i = 1; i <= 6; i++) { c.px(A - i, 42 - (i > 4 ? 1 : 0), I[2]); c.px(A + i, 42 - (i > 4 ? 1 : 0), I[1]) }
        for (let y = 41; y <= 52; y++) c.px(A, y, y >= 47 && y <= 48 ? LINO6[5] : I[y < 47 ? 2 : 1])
        c.px(A - 1, 47, LINO6[4]); c.px(A + 1, 47, LINO6[2]); c.px(A + 1, 52, I[0])
      }
    }
    mano96(c, d._sk6 || PELLE6)
  }]
}
// The staff, d.bastone_v (esporta.py): 0 a hermit's or a pilgrim's, a knobbed stick with two knots; 1 the tau
// staff of the desert monks, a short crosspiece on top
ATTRIBUTI96.bastone = function (d) {
  const v = d.bastone_v || 0, Q = LEGNO6
  return [(c) => {
    manica96(c, rampaMat(d.veste))
    asta96(c, v ? 17 : 14, Q, [4, 3, 1])
    if (v) { for (let x = 75; x <= 87; x++) { c.px(x, 14, Q[x < 81 ? 5 : 4]); c.px(x, 15, Q[3]); c.px(x, 16, Q[1]) } c.px(75, 16, Q[2]); c.px(87, 14, Q[3]) }
    else {
      for (let y = 10; y <= 14; y++) for (let x = 79; x <= 83; x++) if (Math.hypot(x - 81, y - 12) <= 2.6) c.px(x, y, Q[x + y < 92 ? 5 : x + y > 94 ? 1 : 3])
      for (const [y, s] of [[34, -1], [58, 1]]) { c.px(81 + s * 2, y, Q[s < 0 ? 4 : 2]); c.px(81 + s * 2, y + 1, Q[1]); c.px(81, y, Q[1]) }
    }
    mano96(c, d._sk6 || PELLE6)
  }]
}
// The lily, d.giglio_v (esporta.py): 0 a stalk with three open flowers, the top one upright, the others
// turned outwards; 1 one open flower and two buds; 2 a sovereign's gold sceptre ending in a fleur-de-lis.
// Flowers and buds are drawn as rows (p petal, d throat, s stamen, o anther, b bud, g base), the side ones
// turned by a quarter; a petal is lit where it has nothing above or on its left, shaded on the other edges
var GIGLIO6 = ["#56604e", "#88947c", "#b8c0a8", "#dce2cc", "#f0f2e4", "#fffff6"]
var STELO6 = ["#1a3418", "#28502a", "#3a6c32", "#52883e", "#72a850", "#9cc86a"]
var FIORE96 = [".....o.o.....", "pp...s.s...pp", ".pp..sds..pp.", ".ppp.ddd.ppp.", "..pppdddppp..", "..ppppdpppp..",
  "...ppmpmppp..", "...ppmpmppp..", "....ppppp....", ".....ppp.....", "......g......"]
var BOCCIOLO96 = ["..b..", ".bbb.", ".bbb.", "bbbbb", "bbbbb", ".bbb.", ".bbb.", "..b..", "..g.."]
var GIGLIO_ARALDICO = ["......a......", ".....aab.....", ".....abb.....", "....aabbc....", "....aabbc....", ".aa.aabbc.cc.",
  "aab..abc..bcc", "ab...abc...bc", "abb..abc..bbc", ".abbbabcbbbc.", "...bbbbbbb...", "..kkkkkkkkk..", "...ab.b.bc...",
  "..ab..b..bc..", ".ab...b...bc."]
var ruota96 = (R) => R[0].split("").map((_, c) => R.map((_, i) => R[R.length - 1 - i][c]).join(""))   // a quarter clockwise
var specchio96 = (R) => R.map((r) => [...r].reverse().join(""))
function righe96(c, x0, y0, R, col) {
  const at = (x, y) => (R[y] && R[y][x]) || "."
  R.forEach((r, y) => [...r].forEach((k, x) => { if (k !== ".") c.px(x0 + x, y0 + y, col(k, at(x, y - 1), at(x - 1, y), at(x, y + 1), at(x + 1, y))) }))
}
ATTRIBUTI96.giglio = function (d) {
  const v = d.giglio_v || 0, P = GIGLIO6, V = STELO6, G = ORO6
  const fiore = (k, su, sx, giu, dx) => k === "o" ? "#9a4a18" : k === "s" ? "#c8b448" : k === "g" ? V[3] : k === "d" ? P[2] : k === "m" ? P[3]
    : (k === "b" ? (t) => P[Math.max(0, t - 1)] : (t) => P[t])(su === "." || sx === "." ? 5 : giu === "." || dx === "." ? 2 : 4)
  const gambo = (pts) => pts.forEach(([x, y]) => c0.px(x, y, V[3]))
  let c0
  return [(c) => {
    c0 = c
    manica96(c, rampaMat(d.veste))
    if (v === 2) {                                                   // the sceptre
      asta96(c, 29, G, [4, 3, 1])
      for (let y = 40; y < 44; y++) for (let x = 78; x <= 84; x++) if (!((y === 40 || y === 43) && (x === 78 || x === 84))) c.px(x, y, G[y === 40 ? 5 : y === 43 ? 1 : x > 82 ? 2 : 3])
      righe96(c, 75, 14, GIGLIO_ARALDICO, (k) => k === "a" ? G[5] : k === "b" ? G[3] : k === "c" ? G[1] : G[4])
    } else {
      for (let y = 27; y <= 93; y++) { c.px(80, y, V[4]); c.px(81, y, V[2]) }                         // the stalk
      for (const [s, y0, n] of [[1, 54, 7], [-1, 62, 7], [1, 68, 5]]) for (let j = 1; j <= n; j++) {   // the leaves, drooping at the tip
        const x = s < 0 ? 80 - j : 81 + j, y = y0 - Math.round(j * 0.9) + (j === n ? 1 : 0)
        c.px(x, y, V[s < 0 ? 5 : 4]); if (j >= 2 && j <= n - 2) c.px(x, y + 1, V[s < 0 ? 3 : 1])
      }
      righe96(c, 75, 16, FIORE96, fiore)                              // the top flower, base at (81, 26)
      if (v === 0) {
        righe96(c, 83, 34, ruota96(FIORE96), fiore); gambo([[82, 41]])
        righe96(c, 68, 40, specchio96(ruota96(FIORE96)), fiore); gambo([[79, 47]])
      } else {
        righe96(c, 84, 30, BOCCIOLO96, fiore); gambo([[82, 42], [83, 41], [84, 40], [85, 39]])
        righe96(c, 72, 36, BOCCIOLO96, fiore); gambo([[79, 48], [78, 47], [77, 46], [76, 46], [75, 45]])
      }
    }
    mano96(c, d._sk6 || PELLE6)
  }]
}
// The martyr's palm, d.palma_v (esporta.py): a frond from the fist, its rib bending a little to the right,
// opening like a fan towards the tip (the user: a narrow blade looked like a quill), lit on the left;
// 1 the same with the crown of martyrdom, a gold laurel wreath slipped over the frond (the user preferred it
// to a pointed crown)
var PALMA6 = ["#1c3414", "#2c4e1c", "#3e6a26", "#588a32", "#78a844", "#a0c860"]
ATTRIBUTI96.palma = function (d) {
  const v = d.palma_v || 0, V = PALMA6, G = ORO6
  return [(c) => {
    manica96(c, rampaMat(d.veste))
    const corona = (dietro) => {                                     // the wreath round (81, 64): gold laurel leaves on a thin ring
      for (let k = 0; k < 64; k++) {                                 // the ring
        const a = (k / 64) * 2 * Math.PI, x = Math.round(81 + 6.6 * Math.cos(a)), y = Math.round(64 + 2.8 * Math.sin(a))
        if ((Math.sin(a) < 0) === dietro) c.px(x, y, G[1])
      }
      for (let k = 0; k < 14; k++) {                                 // the leaves, pairs leaning outwards and inwards
        const a = (k / 14) * 2 * Math.PI + 0.1, sn = Math.sin(a)
        if ((sn < 0) !== dietro) continue
        const r = k % 2 ? 1.18 : 0.86, x = Math.round(81 + 6.6 * r * Math.cos(a)), y = Math.round(64 + 2.8 * r * sn)
        const l = sn < -0.3 ? 4 : sn > 0.5 ? 2 : 3, lato = Math.cos(a) > 0.5 ? -1 : Math.cos(a) < -0.5 ? 1 : 0
        c.px(x, y, G[tra05(l + 1 + lato)]); c.px(x + 1, y, G[tra05(l + lato)]); c.px(x, y + 1, G[tra05(l - 1 + lato)])
      }
    }
    if (v) corona(true)
    const rib = new Map()                                            // y -> x of the rib
    for (let k = 0; k <= 200; k++) { const t = k / 200, y = 93 - Math.round(74 * t); if (!rib.has(y)) rib.set(y, [80 + Math.round(6 * t ** 1.8), t]) }
    for (const [y, [x, t]] of rib) {                                 // the blade: wider and more splayed towards the tip
      if (t < 0.3) continue
      const u = (t - 0.3) / 0.7, dita = mod96(y, 4) === 0                 // every fourth leaflet sticks out: the fan's fingers
      const W = Math.round(1.5 + 5.5 * u ** 0.7) + (dita && u > 0.4 ? 2 : 0) - (y % 2), pend = 0.5 + 1.1 * u
      for (let j = 1; j <= W; j++) {
        const yy = y - Math.floor(j * pend), riga = mod96(y, 4) === 2
        if (x - j >= 66) c.px(x - j, yy, V[j === W ? 5 : riga ? 3 : 4])
        if (x + j <= 93) c.px(x + j, yy, V[j === W ? 3 : riga ? 1 : 2])
      }
    }
    for (const [y, [x]] of rib) c.px(x, y, V[y > 72 ? 2 : 0])        // the rib
    if (v) corona(false)
    mano96(c, d._sk6 || PELLE6)
  }]
}
// The sword, upright in the fist, d.spada_v (esporta.py), by the armour's age: 0 the medieval one, a long
// blade with a fuller, a straight gold cross-guard, a leather grip and a gold disc pommel; 1 the Roman gladius, short and broad with a
// long point, a bronze guard and a round pommel; 2 a sabre, a curved blade with a flat back and a sharpened
// edge, a gold knuckle-bow round the hand
ATTRIBUTI96.spada = function (d) {
  const v = d.spada_v || 0, A = ACCIAIO6, B = BRONZO6, G = ORO6
  // a blade on the axis 81 from y1 (its point's start) down to y0, w px wide, bending by off(y)
  const lama = (c, y1, y0, w, punta, off, sgusc) => {
    for (let y = y1 - punta; y <= y0; y++) {
      const k = y < y1 ? Math.max(0, Math.round(((y - (y1 - punta)) / punta) * (w - 1) / 2)) : (w - 1) / 2
      const x0 = 81 + off(y)
      for (let dx = -Math.floor(k); dx <= Math.ceil(k); dx++) {
        const t = dx < -Math.floor(w / 2) + 1 ? 5 : dx === Math.ceil(k) ? 1 : dx > 0 ? 2 : sgusc && dx === 0 && y > y1 + 2 && y < y0 - 3 ? 2 : 4
        c.px(x0 + dx, y, A[t])
      }
    }
  }
  return [(c) => {
    manica96(c, rampaMat(d.veste))
    if (v === 1) {                                                   // the gladius
      lama(c, 46, 68, 6, 8, () => 0, false)
      for (let x = 75; x <= 87; x++) { const q = ((x - 81) / 6.4) ** 2; if (q <= 1) { c.px(x, 69, B[x < 79 ? 5 : 4]); c.px(x, 70, B[3]); c.px(x, 71, B[1]) } }
      for (let y = 85; y <= 89; y++) for (let x = 78; x <= 84; x++) if (((x - 81) / 3.4) ** 2 + ((y - 87) / 2.6) ** 2 <= 1) c.px(x, y, B[x + y < 166 ? 5 : x + y > 169 ? 1 : 3])
    } else if (v === 2) {                                            // the sabre
      // drawn row by row, 4 px wide: the flat back on the left (a fuller beside it), the sharpened edge on the
      // right. The whole row shifts by 1 px at each step of the curve (runs getting shorter towards the tip),
      // so both edges stay clean lines; at the tip the edge sweeps up to meet the straight back
      const PUNTA = [1, 2, 2, 3, 3, 4]
      for (let y = 9; y <= 69; y++) {                                // as long as the medieval sword (the user)
        const xb = 79 + Math.round(6 * ((69 - y) / 60) ** 2)          // the back's column
        const w = y - 9 < PUNTA.length ? PUNTA[y - 9] : 4
        for (let i = 0; i < w; i++) c.px(xb + i, y, A[i === 0 ? 3 : i === w - 1 ? 5 : i === 1 && w === 4 && y < 64 ? 2 : 4])
      }
      for (let x = 76; x <= 88; x++) { c.px(x, 70, G[x < 80 ? 5 : 4]); c.px(x, 71, G[2]) }
      c.px(75, 71, G[3]); c.px(75, 72, G[2]); c.px(74, 73, G[1])                         // the back quillon, curling down
      for (const [x, y] of [[89, 71], [90, 72], [91, 73], [91, 84], [90, 85]]) { c.px(x, y, G[3]); c.px(x + 1, y, G[1]) }   // the knuckle-bow
      for (let y = 74; y <= 83; y++) { c.px(92, y, G[3]); c.px(93, y, G[1]) }
      for (let x = 78; x <= 90; x++) { c.px(x, 86, G[x < 82 ? 4 : 3]); c.px(x, 87, G[1]) }
    } else {                                                         // the medieval sword
      lama(c, 14, 68, 5, 5, () => 0, true)
      // gold guard and pommel, a leather grip, as the sword the user knew (the old one's colours)
      for (let x = 70; x <= 92; x++) { c.px(x, 69, G[x < 81 ? 5 : 4]); c.px(x, 70, G[3]); c.px(x, 71, G[1]) }
      for (let x = 80; x <= 82; x++) c.px(x, 72, CUOIO[x === 80 ? 3 : x === 81 ? 2 : 1])
      for (let y = 85; y <= 89; y++) for (let x = 78; x <= 84; x++) if (((x - 81) / 3.2) ** 2 + ((y - 87) / 2.4) ** 2 <= 1) c.px(x, y, G[x + y < 166 ? 5 : x + y > 169 ? 1 : 3])
    }
    mano96(c, d._sk6 || PELLE6)
  }]
}
// The book, floating at the lower right as the old one did (the user: a hand under it looked unnatural),
// d.libro_v (esporta.py): 0 a codex bound in
// leather (d.libro_c: red, brown, green or blue), raised bands on the spine and two clasps; 1 a precious
// gospel book, a gold cover with a cross and stones; 2 open towards the viewer, two written pages
var LIBRO_COL = ["#8a2a2a", "#6e4626", "#2e5a3a", "#2e3e6e"]
ATTRIBUTI96.libro = function (d) {
  const v = d.libro_v || 0, G = ORO6, P = LINO6
  return [(c0) => {
    const [ox, oy] = v === 2 ? [-1, 13] : [-3, 13], c = { px: (x, y, k) => c0.px(x + ox, y + oy, k) }   // drawn higher up, set down here
    if (v === 2) {                                                   // open: two pages, the covers' edges round them
      const C = rampaMat(LIBRO_COL[d.libro_c || 0])
      for (let y = 62; y <= 80; y++) for (let x = 67; x <= 92; x++) {
        const bordo = y === 80 || x === 67 || x === 92, gola = x === 79 || x === 80
        let t = bordo ? null : gola ? 1 : y === 62 ? 5 : (x - 67) % 12 < 2 || (92 - x) < 2 ? 2 : 4
        if (t === null) { c.px(x, y, C[x < 80 ? 3 : 1]); continue }
        if (!gola && y >= 65 && y <= 77 && y % 2 && ((x > 69 && x < 78) || (x > 81 && x < 90)) && (x * 7 + y * 3) % 11 > 1) t = 1   // the lines of writing
        if (x === 81 && y > 62) t = 2
        c.px(x, y, P[t])
      }
      for (let x = 69; x <= 90; x++) { c.px(x, 61, P[x < 79 ? 5 : 4]); if (x !== 79 && x !== 80) c.px(x, 60, x < 72 || x > 87 ? P[3] : P[4]) }   // the pages curving up
    } else {                                                         // closed, standing: cover, spine on the left, pages on top
      const C = v === 1 ? G : rampaMat(LIBRO_COL[d.libro_c || 0])
      for (let y = 54; y <= 80; y++) for (let x = 69; x <= 89; x++) {
        if (y === 54) { if (x > 70) c.px(x, y, P[x < 80 ? 5 : 4]); continue }                       // the top of the pages
        if (x <= 70) { c.px(x, y, C[[58, 66, 74].includes(y) ? 5 : x === 69 ? 2 : 1]); continue }   // the spine with its bands
        let t = 3
        if (x === 71 || y === 55) t = 4
        if (x === 89 || y === 80) t = 1
        if (x > 85 && t === 3) t = 2
        const fx = x === 73 || x === 87, fy = y === 57 || y === 78
        if ((fx && y >= 57 && y <= 78) || (fy && x >= 73 && x <= 87)) t = v === 1 ? 5 : 2                // the tooled frame
        if (v === 1) {
          const cx0 = 80, cy0 = 66, ax = Math.abs(x - cx0), ay = Math.abs(y - cy0)
          if ((ax <= 1 && ay <= 7) || (ay <= 1 && ax <= 5)) t = ax === 1 && ay <= 7 && ay > 1 ? 1 : 5        // the cross
          if (ax === 0 && ay === 0) { c.px(x, y, gemma96(true, 0, 0)); continue }
          if ([[75, 60], [85, 60], [75, 73], [85, 73]].some(([gx, gy]) => x - gx >= 0 && x - gx <= 1 && y - gy >= 0 && y - gy <= 1)) { c.px(x, y, gemma96((x + y) % 2 === 0, x % 2, y % 2 ? 0 : 2)); continue }
        }
        c.px(x, y, C[t])
      }
      if (v === 0) for (const y0 of [60, 73]) for (let x = 86; x <= 90; x++) { c.px(x, y0, G[x < 88 ? 4 : 3]); c.px(x, y0 + 1, G[1]) }   // the clasps
    }
  }]
}
// --- the bishops. The mitre, d.mitra_v (esporta.py): 0 the precious one, pointed, with a jewelled band and
// titulus and the embroidery of d.vescovo_v on each side (0 a cross with flared ends, 1 a lozenge round a
// stone, 2 three studs); 1 the low plain one of the early bishops, white linen with narrow gold bands;
// 2 the Eastern bishops' crown, a gold dome with pearls, an enamel and a cross on top; 3 the tall rounded
// one of the modern age, cloth of gold edged in gold
COPRICAPI.mitra = function (d) {
  const DAMASCO = ["#8a744c", "#b89c64", "#d8c088", "#ecdcae", "#f8eecc", "#fffae6"]              // cloth of gold, pale
  const { cx, F } = G96, v = d.mitra_v || 0, G = ORO6, e = d.vescovo_v || 0
  const pietre = (dx, a, r) => {                                    // the band's stones, rows 1-3 of it
    if (a <= 1) return gemma96(true, dx + 1, r - 1)
    const g = [12, 7].find((g0) => a === g0 || a === g0 + 1)
    return g ? gemma96((g === 7) === (dx < 0), dx < 0 ? g + 1 - a : a - g, r - 1) : null
  }
  const fascia = (dx, r, h) => G[tra05((r === 0 ? 5 : r === h - 1 ? 1 : 3) - (dx > 10 ? 1 : 0))]
  let dentro, tono
  if (v === 2) {
    dentro = (x, y) => y >= 3 && y <= 27 && q96(x, y, cx, 19, 18.4, 16.4) <= 1
    tono = (x, y) => {
      const dx = x - cx, a = Math.abs(dx)
      if ((dx === 0 && y <= 3) || (a <= 1 && y === 1)) return G[4]                               // the cross
      if (!dentro(x, y)) return null
      if (y >= 23) return (y >= 24 && y <= 26 && pietre(dx, a, y - 23)) || fascia(dx, y - 23, 5)
      const m = q96(x, y, cx, 13, 4.4, 5.4)                                                      // the enamel
      if (m <= 1) return m > 0.5 ? G[dx + (y - 13) < 0 ? 5 : 1] : dx < 0 && y < 13 ? "#8ab0f0" : "#2e56b0"
      const costa = Math.round(10.5 * Math.sqrt(Math.max(0, 1 - ((y - 19) / 16.4) ** 2)))        // a rib of pearls
      if (a === costa && y >= 6) return y % 2 ? PERLA[0] : PERLA[1]
      const l = -((dx / 18) * 0.6 + ((y - 15) / 14) * 0.7)
      let t = l > 0.5 ? 5 : l > 0.2 ? 4 : l > -0.25 ? 3 : l > -0.55 ? 2 : 1
      if (y === 22) t -= 1                                                                       // the band's edge
      if (!dentro(x - 1, y) && dx < 0) t = 5
      return G[tra05(t)]
    }
  } else {
    const [yA, ys, W, p] = v === 1 ? [8, 18, 17.5, 1.2] : v === 3 ? [0, 12, 19.5, 2.4] : [1, 13, 18.5, 1.5]
    const larg = (y) => y > 27 || y < yA ? -1 : y >= ys ? 16.5 + (W - 16.5) * (27 - y) / (27 - ys) : W * (1 - ((ys - y) / (ys - yA + 1)) ** p)
    dentro = (x, y) => Math.abs(x - cx) <= larg(y)
    const b0 = v === 1 ? 25 : 23, tw = v === 1 ? 1 : 2, ey = v === 3 ? 13 : 15
    tono = (x, y) => {
      if (!dentro(x, y)) return null
      const dx = x - cx, a = Math.abs(dx)
      if (y >= b0) return (v !== 1 && y >= 24 && y <= 26 && pietre(dx, a, y - 23)) || fascia(dx, y - b0, 28 - b0)
      if (a <= tw && y >= yA + 3) {                                                              // the titulus
        if (v !== 1 && a <= 1 && [9, 10, 16, 17].includes(y)) return gemma96(y > 12, dx + 1, y % 2 ? 0 : 2)
        return G[tra05(3 - dx)]
      }
      if (v === 3 && (!dentro(x - 1, y) || !dentro(x + 1, y) || !dentro(x, y - 1))) return G[dx < 0 ? 4 : 2]                     // the gold edge
      if (v !== 1) {                                                                             // the embroidery
        const bx = Math.abs(a - 10), ay = y - ey, by = Math.abs(ay)
        if (e === 1 && bx === 0 && by === 0) return "#b02a34"
        if (e === 0 ? (bx === 0 && by <= 3) || (by === 0 && bx <= 3) || (bx === 3 && by === 1) || (by === 3 && bx === 1)
          : e === 1 ? bx + by === 3 : bx === 0 && by % 3 === 0 && by <= 3) return G[dx < 0 ? 3 : 2]
      }
      let t = dx < -9 ? 5 : dx > 13 ? 2 : dx > 7 ? 3 : 4                                         // white linen
      if (dx > tw && dx <= tw + 2) t -= 1                                                        // the titulus' shadow
      if (y === b0 - 1) t -= 1
      if (!dentro(x - 1, y) || (!dentro(x, y - 1) && dx < 0)) t = 5
      else if (!dentro(x + 1, y)) t = 2
      return (v === 3 ? DAMASCO : LINO6)[tra05(t)]
    }
  }
  return { dietro: [], davanti: [(c) => { for (let y = 0; y < 28; y++) for (let x = 0; x < F; x++) { const k = tono(x, y); if (k) c.px(x, y, k) } }] }
}
// The pope's robe, d.papa_v (esporta.py): 0 the modern one, the white cassock, the red mozzetta edged with
// white fur and buttoned, a red stole embroidered in gold; 1 a medieval pope's red cope with its jewelled
// morse; 2 an early pope's chasuble with the pallium. The last two are the bishop's (ABITI.vescovo), in
// d.stola's colour where it is given
ABITI.papa = function (d) {
  const { cx, F } = G96, v = d.papa_v || 0, G = ORO6, T = (Q, t) => Q[tra05(t)]
  if (v) return ABITI.vescovo({ ...d, veste: d.stola || (v === 1 ? "#a8283a" : "#e8e0cc"), vescovo_v: v === 1 ? 0 : 2 })
  const C = rampaMat(d.veste), M = rampaMat("#b8302c"), SC = rampaMat("#8a1c28")
  const tono = (x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx), qc = q96(x, y, cx, 73, 36, 13.5)
    if (a >= 5 && a <= 9 && y >= 74) {                              // the stole: gold edges, one gold cross on each side
      if (a === 5 || a === 9) return G[dx < 0 ? 4 : 2]
      if ((a === 7 && y >= 82 && y <= 88) || (y === 84 && a >= 6 && a <= 8)) return G[dx < 0 ? 5 : 4]
      return T(SC, dx < 0 ? 3 : 2)
    }
    if ((a === 10 || a === 4) && y >= 74 && dx !== -4 && dx !== 10) return T(qc <= 1 ? M : C, 1)   // its shadow
    if (qc <= 1 || y <= 78) {                                       // the mozzetta, its fur hem
      if (qc > 0.88 && y > 78) return LINO6[qc > 0.96 ? 2 : dx < 0 ? 5 : 4]
      if (dx === 0) return T(M, mod96(y, 4) === 2 ? 5 : 1)
      return T(M, dx === -1 ? 4 : panno96(x, y, 3, sopra))
    }
    if (qc <= 1.14) return T(C, 2)
    return T(C, panno96(x, y, 4, sopra))
  }
  return [...spalle(MARCA_V), (c) => { for (let y = 60; y < F; y++) for (let x = 0; x < F; x++) {
    const dx = x - cx
    if (y >= 65 && q96(x, y, cx, 69, 13, 4) <= 1) c.px(x, y, LINO6[q96(x, y, cx, 68, 13, 4) > 1 ? 2 : y <= 66 && dx < 4 ? 5 : dx > 8 ? 3 : 4])   // the white collar
    else if (c.get(x, y) === PK_V) c.px(x, y, tono(x, y, c.get(x, y - 1) === 0))
  } }]
}

// --- soldiers. ACCIAIO6: steel. spallaY: the shoulders' upper edge at a pixels from the axis
var ACCIAIO6 = ["#2c3046", "#4a5270", "#6f7a96", "#98a2b6", "#c2cad6", "#eef2f6"], CUOIO = ["#3a2416", "#5e3c22", "#8a5c34", "#b07c48"]
var BRONZO6 = ["#4a2c14", "#7a4a1c", "#a8742a", "#cc9c40", "#e8c468", "#fbe8a8"]
var spallaY = (a) => (a <= 13 ? 68 : a <= 30 ? 68 + (a - 13) * 8 / 17 : 76 + (a - 30) * 6 / 16)
// The soldier's dress by his time, d.armatura_v (esporta.py): 0 plate, as the hand-made Giovanna's: a
// breastplate with a ridge, a gorget, pauldrons of three lames, gilt rivets; 1 a Roman centurion's: the
// bronze muscle cuirass, leather strips at the shoulders, a scarf, the cloak (d.veste its colour);
// 2 mail, the coif lowered round the neck, a leather baldric; 3 a modern uniform (d.veste darkened): a
// standing collar with red tabs, gold epaulettes and buttons, a medal
ABITI.armatura = function (d) {
  const { cx, F } = G96, v = d.armatura_v || 0, S = ACCIAIO6, G = ORO6, T = (Q, t) => Q[tra05(t)]
  const apreY = (x) => (Math.abs(x - cx) < 12.5 ? 67 + 3.2 * Math.sqrt(1 - ((x - cx) / 12.5) ** 2) : 64.5)
  const lucido = (x, y, dx) => {                                   // polished steel: the sky's slanted reflection, the ground's
    const k = x + (y - 76) * 0.5
    let t = k >= cx - 11 && k <= cx - 10 ? 5 : k >= cx - 14 && k <= cx - 7 ? 4 : 3
    if (y >= 89 + (dx / 30) ** 2 * 3) t = 2
    if (y >= 92) t = 1
    return t
  }
  const piastre = (x, y, busto, sopra) => {
    const dx = x - cx, a = Math.abs(dx)
    if (q96(x, y, cx, 70, 17, 6.5) <= 1 && y > apreY(x)) {         // the gorget, rivets along its lower edge
      const dy = y - apreY(x)
      for (const g of [-12, -6, 0, 6, 12]) { const ry = Math.round(70 + 6.5 * Math.sqrt(1 - (g / 17) ** 2)) - 3
        if (y === ry && (dx === g || dx === g + 1)) return G[dx === g ? 4 : 1] }
      let t = dy <= 1 ? (dx < 6 ? 5 : 4) : dy <= 2 ? (dx < 6 ? 4 : 3) : 3
      if (q96(x, y, cx, 69, 17, 6.5) > 1) t = 1
      return T(S, t - (dx > 10 && t > 1 ? 1 : 0))
    }
    for (const s of [-1, 1]) {                                     // the pauldrons
      const x0 = cx + s * 32, nx = (x - x0) / 16.5, ny = (y - 85) / 12.5
      if (nx * nx + ny * ny > 1) continue
      const l = -(nx * 0.6 + ny * 0.75)
      let t = l > 0.74 ? 5 : l > 0.42 ? 4 : l > -0.05 ? 3 : l > -0.5 ? 2 : 1
      if (s > 0 && t < 5) t -= 1
      for (const Y of [81, 87]) { const yk = Math.round(Y + 3.5 * nx * nx), rx = x0 - s * 9
        if (y === yk - 2 && (x === rx || x === rx + 1)) return G[x === rx ? 4 : 1]
        if (y === yk) t = 0; else if (y === yk + 1) t = Math.min(t + 1, 5) }
      if (nx * nx + ny * ny > 0.86 && l < 0) t = Math.min(t, 1)
      return T(S, t)
    }
    if (!busto) return null
    if (a < 12.5 && y <= apreY(x)) return colloT(d, x, y)           // the neck in the gorget's opening
    let t = lucido(x, y, dx)
    if (dx === -2 || dx === -1) t = 4                               // the ridge
    if (dx === 0) t = 1
    if (dx > 0 && dx <= 3) t = 2
    if (sopra) t = dx < 0 ? 5 : 4
    if (dx > 14) t -= 1
    if ((q96(x, y, cx + 1, 72, 18, 7) <= 1 && y > 70) || q96(x, y, cx - 32, 87, 16.5, 12.5) <= 1 || q96(x, y, cx + 32, 87, 16.5, 12.5) <= 1) t = 1   // the shadows of gorget and pauldrons
    return T(S, t)
  }
  // A centurion's: the bronze muscle cuirass, its pectorals modelled, a rim at the neck and a medallion on
  // the breastbone; bronze straps from the shoulders, tied to it with a ring; leather strips with studs
  // hanging from the shoulders; the scarf at the neck; the cloak over one shoulder, pinned with a fibula
  const romano = (x, y, busto, sopra) => {
    const dx = x - cx, a = Math.abs(dx), C = manto6(d.veste), B = BRONZO6
    if (y >= 65 && q96(x, y, cx, 70, 14.6, 5.6) <= 1 && q96(x, y, cx, 65, 9.6, 4.6) > 1)   // the scarf
      return LINO6[q96(x, y, cx, 69, 14.6, 5.6) > 1 ? 2 : y <= 68 && dx < 4 ? 5 : dx > 7 ? 3 : 4]
    if (!busto) return null
    const sotto = q96(x, y, cx + 1, 71.6, 15.6, 6.4) <= 1, orlo = cx - 22 + (y - 70) * 0.42   // the cloak's edge
    const qf = (x - cx + 23) ** 2 + (y - 75) ** 2
    if (qf <= 8) return G[qf <= 1 ? 5 : dx + 23 + y - 75 < 0 ? 4 : dx + 23 + y - 75 > 1 ? 1 : 3]   // the fibula
    if (x <= orlo) {
      const m = mod96(Math.round(orlo - x), 8)
      let t = qf <= 14 ? 1 : m === 4 ? 2 : m === 5 ? 4 : 3
      if (x > orlo - 1.2) t = 2
      if (y >= 90) t -= 1
      return T(C, sopra ? 5 : t)
    }
    if (x <= orlo + 1.6) return B[0]
    const sp = y - spallaY(a)
    if (a >= 25) {                                                  // the shoulder: a bronze cap, the leather strips under it
      if (sp < 3) return T(B, (sopra ? 5 : sp < 2 ? 4 : 1) - (dx > 0 ? 1 : 0))
      const k = mod96(a, 5)
      if (k === 0) return CUOIO[0]
      if (k === 2 && Math.round(sp) === 5) return G[dx < 0 ? 4 : 3]  // a stud
      return CUOIO[tra05((k === 1 ? 3 : k === 4 ? 1 : 2) - (dx > 0 ? 1 : 0))]
    }
    if (sotto) return B[1]
    const qr = q96(x, y, cx, 71.6, 17.4, 8)
    if (qr <= 1) return T(B, (dx < 2 ? 5 : 4) - (qr > 0.9 ? 2 : 0))    // the rim at the neck
    const qm = dx * dx + (y - 84) ** 2
    if (qm <= 7) return G[qm <= 1 ? 1 : dx + y - 84 < -1 ? 5 : dx + y - 84 > 1 ? 2 : 4]            // the medallion
    for (const s of [-1, 1]) {                                      // the straps, a ring where each is tied
      const k = y - (72 + (22 - a) * 0.75)
      if (dx * s > 0 && a >= 15 && a <= 24 && k >= 0 && k < 4) return a <= 16 ? G[k < 2 ? 4 : 2] : T(B, (k < 1 ? 5 : k >= 3 ? 1 : 3) - (s > 0 ? 1 : 0))
    }
    let t = 3
    for (const s of [-1, 1]) {                                      // the pectorals
      const ex = (x - cx - s * 10) / 9.5, ey = (y - 83) / 6.5, qq = ex * ex + ey * ey, l = -(ex * 0.6 + ey * 0.7)
      if (qq <= 1) t = qq > 0.72 && ey > 0.2 ? 1 : l > 0.45 ? 5 : l > 0.1 ? 4 : l > -0.45 ? 3 : 2      // lit above, a dark line under it
      else if (qq <= 1.5 && ey > 0.6 && a <= 17) t = 4                                               // the belly catches the light
    }
    if (y >= 92) t = Math.min(t, 2)
    if (dx === 0) t = 1                                             // the breastbone's groove
    if (dx > 14) t -= 1
    return T(B, t)
  }
  const maglia = (x, y, busto, sopra) => {
    const dx = x - cx, a = Math.abs(dx), q = q96(x, y, cx, 73, 22.6, 7.6)
    // the rings, 4 x 3, each row of them shifted by half a ring: the upper arc lit, the sides, the lower
    // arc in shadow, the hole dark
    const lx = mod96(x + (mod96(Math.floor(y / 3), 2) ? 2 : 0), 4), ly = mod96(y, 3), bordo = lx === 0 || lx === 3
    const anelli = (t) => T(S, t + (ly === 0 ? (bordo ? -1 : 1) : ly === 1 ? (bordo ? 0 : -2) : bordo ? -1 : 0))
    if (q <= 1 && q96(x, y, cx, 65, 9.6, 5.6) > 1) {                // the coif, lowered
      let t = y <= 70 ? 4 : y <= 75 ? 3 : 2
      if (q > 0.84 && y > 73) t = 1
      return q96(x, y, cx, 72, 22.6, 7.6) > 1 && y < 73 ? S[dx < 4 ? 5 : 4] : anelli(t - (dx > 12 ? 1 : 0))
    }
    if (!busto) return null
    if (q <= 1.22 && y > 73) return S[0]
    const k = dx + (y - 74) * 2.3 - 26                              // the baldric, shoulder to hip
    if (Math.abs(k) <= 3.4) return mod96(y, 7) === 3 && Math.abs(k) < 1.2 ? G[3] : CUOIO[k < -2.2 ? 3 : k > 2.2 ? 0 : 2]
    if (k > 3.4 && k <= 5) return S[0]
    let t = dx < -8 && y - spallaY(a) < 9 ? 4 : 3
    if (dx > 14) t -= 1
    if (y >= 90) t -= 1
    return sopra ? S[dx < 0 ? 5 : 4] : anelli(t)
  }
  const uniforme = (x, y, busto, sopra) => {
    const dx = x - cx, a = Math.abs(dx), U = rampaMat(mixc(d.veste, "#2a3038", 0.6))
    if (y >= 65 && a >= 2 && q96(x, y, cx, 69, 13, 4) <= 1)        // the standing collar, its tabs
      return a >= 3 && a <= 8 && q96(x, y, cx, 68, 13, 4) <= 1 ? (dx < 0 ? "#c0303c" : "#96222e") : U[q96(x, y, cx, 68, 13, 4) > 1 ? 1 : y <= 66 && dx < 4 ? 5 : dx > 8 ? 2 : 4]
    if (!busto) return null
    const sp = Math.round(y - spallaY(a))
    if (a >= 20 && sp >= 0 && sp <= 5) return sp <= 3 ? G[tra05([5, 3, 3, 1][sp] - (dx > 0 ? 1 : 0))] : mod96(x, 2) ? G[2] : U[1]   // epaulettes, fringed
    if (a <= 1 && mod96(y, 5) === 2 && y >= 72) return G[dx < 1 ? 4 : 2]                         // buttons
    if (dx === 0) return U[1]
    if (dx >= 9 && dx <= 12 && y >= 78 && y <= 80) return dx === 9 || dx === 12 ? "#c0303c" : "#f0ece4"   // a medal: its ribbon, a cross
    if ((dx >= 10 && dx <= 11 && y >= 81 && y <= 84) || (y === 82 && dx >= 9 && dx <= 12)) return G[dx <= 10 ? 4 : 2]
    return T(U, panno96(x, y, 3, sopra))
  }
  const tono = [piastre, romano, maglia, uniforme][v] || piastre
  return [...spalle(MARCA_V), (c) => { for (let y = 60; y < F; y++) for (let x = 0; x < F; x++) {
    const m = c.get(x, y) === PK_V, k = tono(x, y, m, m && c.get(x, y - 1) === 0)
    if (k) c.px(x, y, k)
  } }]
}

// The white monks and friars: the hood lowered round the neck (rotolo96), the scapular down the front.
// tonaca96 gives the bust under the hood: the scapular (ramp SC) between two edges, the habit (ramp H) at
// its sides, and over the shoulders a cappa (ramp K) where one is worn
function tonaca96(x, y, sopra, r, H, SC, K) {
  const dx = x - G96.cx, a = Math.abs(dx), T = (Q, t) => Q[tra05(t)], chiaro = (Q) => (Q === LINO6 ? 1 : 0)
  if (K && a > 15 + Math.max(0, y - 78) * 0.3) return T(K, r ? 1 : a <= 16.6 + Math.max(0, y - 78) * 0.3 ? (dx < 0 ? 5 : 1) : panno96(x, y, 3, sopra))
  if (a <= 12) return T(SC, r ? 1 + chiaro(SC) : a === 12 ? (dx < 0 ? 5 : 1 + chiaro(SC)) : (dx > 4 ? 2 : 3) + chiaro(SC))
  if (a === 13) return T(H, 1 + chiaro(H))
  return T(H, r ? 1 + chiaro(H) : panno96(x, y, 3 + chiaro(H), sopra))
}
var busto96 = (tono) => [...spalle(MARCA_V), (c) => { for (let y = 60; y < G96.F; y++) for (let x = 0; x < G96.F; x++) {
  const k = tono(x, y, c.get(x, y) === PK_V ? c.get(x, y - 1) === 0 : null)
  if (k) c.px(x, y, k)
} }]
// The Dominican, d.domenicano_v (esporta.py): 0 the black cappa and hood over the white habit and
// scapular, the white hood showing inside the black one; 1 in white alone, without the cappa
ABITI.domenicano = function (d) {
  const v = d.domenicano_v || 0, N = veloR("#2c2830")
  return busto96((x, y, sopra) => {
    const r = rotolo96(x, y, v ? LINO6 : N)
    if (r && r !== "ombra") return !v && q96(x, y, G96.cx, 65, 11.6, 7.2) <= 1 ? LINO6[x > G96.cx + 6 ? 3 : 4] : r
    return sopra === null ? null : tonaca96(x, y, sopra, r, LINO6, LINO6, v ? null : N)
  })
}
// The Cistercian, d.cistercense_v (esporta.py): 0 the black scapular and hood over the white habit; 1 a
// Carthusian, all in white
ABITI.cistercense = function (d) {
  const v = d.cistercense_v || 0, N = veloR("#2c2830")
  return busto96((x, y, sopra) => {
    const r = rotolo96(x, y, v ? LINO6 : N)
    if (r && r !== "ombra") return r
    return sopra === null ? null : tonaca96(x, y, sopra, r, LINO6, v ? LINO6 : N, null)
  })
}
// The cardinal, d.cardinale_v (esporta.py): 0 the red cassock and mozzetta, buttoned, a gold cross on its
// cord; 1 the mozzetta of ermine, white fur with black tails, over the red cassock. The white collar on both
ABITI.cardinale = function (d) {
  const { cx } = G96, v = d.cardinale_v || 0, C = rampaMat(d.veste), G = ORO6, T = (Q, t) => Q[tra05(t)]
  return busto96((x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx), qc = q96(x, y, cx, 73, 36, 13.5)
    if (y >= 66 && q96(x, y, cx, 69, 13, 4) <= 1) return LINO6[q96(x, y, cx, 68, 13, 4) > 1 ? 2 : y <= 66 && dx < 4 ? 5 : dx > 8 ? 3 : 4]   // the collar
    if (sopra === null) return null
    if (v === 1 && (qc <= 1 || y <= 78)) {                           // ermine
      if (mod96(dx + 3, 8) === 0 && mod96(y + mod96(Math.floor((dx + 3) / 8), 2) * 3, 6) <= 1 && qc < 0.9) return "#1e1a20"
      return LINO6[sopra ? 5 : qc > 0.9 && y > 78 ? 2 : dx > 12 ? 3 : 4]
    }
    if (v === 0) {
      const k = croce96(dx, y, 80)
      if (k) return k === "ombra" ? C[0] : k
      if (y >= 70 && y <= 80 && Math.abs(a - (10 - (y - 70) * 0.95)) < 0.6) return G[dx < 0 ? 3 : 2]   // its cord
      if (qc > 0.9 && qc <= 1 && y > 78) return T(C, dx < 0 ? 5 : 4)                                    // the mozzetta's hem
    }
    if (qc > 1 && qc <= 1.14 && y > 78) return T(C, 1)
    if (dx === 0 && y >= 71) return T(C, mod96(y, 4) === 2 ? 5 : 1)
    return T(C, dx === -1 && y >= 71 ? 4 : panno96(x, y, 3, sopra))
  })
}

// The mantle over one shoulder (apostles, laymen), d.secondo its colour, on the tunic (tunicaT): it falls
// from the shoulder across the chest, its edge rolled, folds running with the edge
ABITI.mantello = function (d) {
  const { cx } = G96, t0 = tunicaT(d), M = manto6(d.secondo || "#3a5a9a"), V = rampaMat(d.veste)
  return busto96((x, y, sopra) => {
    if (sopra === null) return null
    const k = cx - 15 + (y - 68) * 0.66 - x                         // how far inside the mantle's edge
    if (k < -1.6) return t0(x, y, sopra)
    if (k < 0) return V[1]                                          // its shadow on the tunic
    const m = mod96(Math.round(k + (y - 68) * 0.2), 9)
    let t = k <= 1.2 ? 2 : k <= 2.6 ? 5 : m === 5 ? 2 : m === 6 ? 4 : 3
    if (y >= 90) t -= 1
    return M[tra05(sopra ? 5 : t)]
  })
}
// Modern dress, d.moderno_v (esporta.py): a jacket with notched lapels over a white shirt, 0 the collar
// open, 1 with a tie
ABITI.moderno = function (d) {
  const { cx } = G96, v = d.moderno_v || 0, J = rampaMat(d.veste), T = (Q, t) => Q[tra05(t)], CRAV = ["#4a1018", "#701c28", "#96283a", "#b83a48"]
  return busto96((x, y, sopra) => {
    if (sopra === null) return null
    const dx = x - cx, a = Math.abs(dx), e = 9 - (y - 68) * 0.5        // the shirt's V, closing at y 86
    if (a < e) {
      if (v === 1 && (a <= (y <= 72 ? 2 : 1) + (y >= 80 ? 1 : 0))) return CRAV[y <= 72 ? (dx < 0 ? 3 : 1) : dx < 0 ? 3 : dx === 0 ? 2 : 1]   // the knot, the tie
      if (v === 0 && a <= 3 - (y - 68) * 0.5) return colloT(d, x, Math.min(y, 71))                // the open collar
      if (y <= 73 && a >= e - 3) return LINO6[dx < 0 ? 5 : 4]                                    // the collar's points
      if (dx === 0) return LINO6[y % 4 === 2 ? 1 : 2]                                            // the placket, its buttons
      return LINO6[y <= 70 ? 2 : dx > 2 ? 3 : 4]
    }
    if (a < e + 1) return J[0]
    const l = 5 - Math.max(0, y - 78) * 0.5                          // the lapels, a notch at y 76
    if (y <= 88 && a < e + 1 + l && !(y >= 75 && y <= 76 && a > e + 3)) return T(J, a >= e + l ? 1 : dx < 0 ? 4 : 3)
    if (dx === 0 && y > 86) return T(J, y === 90 ? 5 : 1)            // where it closes, a button
    return T(J, panno96(x, y, 3, sopra))
  })
}
// The deacon's dalmatic (San Lorenzo, Santo Stefano): the amice at the neck, two gold clavi joined by a
// gold band across the chest, a stone where they cross
ABITI.dalmatica = function (d) {
  const { cx } = G96, C = rampaMat(d.veste), G = ORO6, T = (Q, t) => Q[tra05(t)]
  return busto96((x, y, sopra) => {
    const dx = x - cx, a = Math.abs(dx)
    if (y >= 65 && q96(x, y, cx, 69, 15, 5) <= 1) return LINO6[q96(x, y, cx, 68, 15, 5) > 1 ? 2 : y <= 66 && dx < 4 ? 5 : dx > 8 ? 3 : 4]   // the amice
    if (sopra === null) return null
    if (q96(x, y, cx + 1, 71, 16, 6) <= 1) return C[1]
    const clavo = a >= 15 && a <= 19, fascia = y >= 82 && y <= 86 && a <= 19
    if (clavo && fascia && a >= 16 && a <= 18 && y >= 83 && y <= 85) return gemma96(dx < 0, a === (dx < 0 ? 18 : 16) ? 0 : 1, y - 83)
    if (clavo) return G[tra05((a === (dx < 0 ? 19 : 15) ? 5 : a === (dx < 0 ? 15 : 19) ? 1 : 3) - (dx > 0 ? 1 : 0) + (sopra ? 1 : 0))]
    if (fascia) return G[y === 82 ? 5 : y === 86 ? 1 : dx > 4 ? 2 : 3]
    if ((y === 87 && a <= 19) || dx === -14 || dx === 20) return C[1]
    return T(C, panno96(x, y, 3, sopra))
  })
}

var _ALONI = new Set()
function aureola6(beato, legg) {
  const { F, cx } = G96, G = beato ? ORO6_BEATO : ORO6, nome = `_al6_${beato ? "beato" : "santo"}${legg ? "_legg" : ""}`
  if (_ALONI.has(nome)) return nome
  _ALONI.add(nome)
  sprite(nome, { w: F, h: F, outline: "K" }, (c) => { for (let y = 0; y < F; y++) for (let x = 0; x < F; x++) {
    const r = Math.hypot(x - cx, y - 34), a = Math.atan2(y - 34, x - cx), ombra = x + y > cx + 34 + 22
    let k
    if (r > 35.3) continue
    if (r > 33.3) k = 1
    else if (r > 32.3) k = 3
    else if (r > 29.3) {                                             // the band: plain, or beaded with punch marks
      k = x + y < cx + 34 - 10 ? 3 : 2
      if (legg) { const n = Math.round(a / (Math.PI / 20)), bx = Math.round(cx + 30.8 * Math.cos(n * Math.PI / 20)), by = Math.round(34 + 30.8 * Math.sin(n * Math.PI / 20))
        k = x === bx && y === by ? 5 : x === bx + 1 && y === by + 1 ? 0 : 2 }
    } else if (r > 28.3) k = 1
    else if (legg) { const q = a / (Math.PI / 12), near = Math.abs(q - Math.round(q)) * (Math.PI / 12) * r      // rays in the field
      k = near < 0.5 && r > (Math.round(q) % 2 ? 23 : 20) ? 5 : ombra ? 3 : 4
    } else k = r > 25.6 && r <= 27 && a > -2.9 && a < -1.75 ? 5 : ombra ? 3 : 4     // an arc of light, top-left
    c.px(x, y, G[k])
  } })
  return nome
}
// the ground: flat and darker below the shoulders; the legendaries' is diapered, a lozenge lattice with a gilt dot
function sfondo6(d) {
  const { S } = G96, scuro = mixc(d.sfondo, "#000000", 0.15)
  if (!d.leggendario) return [rect(0, 0, S, S, d.sfondo), rect(0, 72, S, S - 72, scuro)]
  return [(c) => { for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) { const b = y >= 72 ? scuro : d.sfondo
    const l = (x + y) % 12 === 0 || (((x - y) % 12) + 12) % 12 === 0, punto = (x + y) % 12 === 6 && (((x - y) % 12) + 12) % 12 === 6
    c.px(x, y, punto ? mixc(b, ORO6[3], 0.45) : l ? mixc(b, "#000000", 0.13) : b) } }]
}

// The portrait of description [d] as sprite [nome] (and its parts _nome_*). con_occhi: eyes open,
// looking ahead (for previews: in the app the eyes are an overlay).
// Each attribute is its own sprite with its own dark outline, made once and shared: so it is outlined
// everywhere, also over robes and armour (only the figure's silhouette had an outline before, so a
// dragon's horns were outlined against the sky and merged with San Giorgio's armour)
var _ATTR = new Set()
function attrSprite(a, d) {
  // an attribute held in the hand has the saint's skin and sleeve: one sprite for each combination
  const k = a + (a === "lancia" && d.abito === "crociato" ? "_crociato" : "")
    + (ATTR_MANO[a] ? "_" + ATTR_MANO[a](d).replace(/#/g, "") : "")
  if (!_ATTR.has(k)) { _ATTR.add(k); sprite(`_at_${k}`, { w: G96.F, h: G96.F, outline: "K" }, ...ATTRIBUTI96[a](d)) }
  return `_at_${k}`
}
// seq: an emotion of EMOZIONI (occhi.px.js) for an animated preview; without it the eyes are still
function ritratto96(nome, d, { con_occhi = true, seq = null } = {}) {
  const { S, F, cx, EYE_Y, BROW_Y, FAR } = G96
  // skin in six tones; the parts still drawn with four (ears, a bald skull, necklines) take the middle ones
  const sk6 = rampa6(d.pelle, PELLE6), sk = sk6.slice(1, 5), hr = rampa(d.chioma || "#5a4030", { shift: 8, sat: 0.8 })   // hair colour: under a veil it is only the brows
  const mat = []
  _MAT = mat                                                         // from here to the bust: ramps are markers
  const rb = rampa(d.veste, { shift: 12 })
  d._sk = sk; d._sk6 = sk6; d._rb = rb
  // a mitre or a tiara covers the whole top of the head: a bald or tonsured one shows only the hair at
  // the temples, cropped, which gives the head its shape; and no fringe comes out under their rim.
  // Under a crown or a skullcap the bald and the tonsured stay so
  const alto = ["mitra", "tiara"].includes(d.copricapo)
  if (alto && ["calvo", "tonsura"].includes(d.capelli)) d = { ...d, capelli: "corti", taglio: 3 }
  const cop = d.copricapo && COPRICAPI[d.copricapo] ? COPRICAPI[d.copricapo](d) : { dietro: [], davanti: [] }
  const coperto = d.copricapo === "velo" || d.copricapo === "cappuccio"
  const frangia = !coperto || (d.copricapo === "cappuccio" && d.abito === "felpa")     // the hoodie shows the fringe
  const al = aureola6(d.beato, d.leggendario), viso = faccia6(d)
  const pg = d.donna && d.capelli === "lunghi" && !coperto ? pieghe6(d, viso) : null
  const tg = !d.donna && d.taglio && !coperto ? tagli6(d, viso) : null
  // the eyes (occhi() in occhi.px.js, the B eyes, the model for Occhi.kt), still or as an emotion
  const ciglio = d.sopracciglia || mixc(d.chioma || "#5a4030", "#000000", 0.25)
  const occ = con_occhi ? [(c) => { occhi(c, cx, seq ? seq[c.frame] : fr(), { y: EYE_Y, browY: BROW_Y, iride: d.iride || "#5a4636",
    pelle: (x) => (x > cx + FAR ? sk6[1] : sk6[2]), ciglio, coda: mixc(ciglio, sk6[3], 0.3), folte: d.eta === "anziano" && !d.donna, donna: !!d.donna,
    forma: d.occhi || "", occhiali: !!d.occhiali })
    if (d.occhiali) occhiali(c, cx, { y: EYE_Y, ...(typeof d.occhiali === "object" ? d.occhiali : {}) }) }] : []
  const extra = (d.extra || []).map((e) => (typeof EXTRA96 !== "undefined" && EXTRA96[e] ? EXTRA96[e](d) : {}))
  const busto = (ABITI[d.abito] || ABITI.tunica)(d, rb, d.secondo || "#3a5a9a")
  _MAT = null
  // a second attribute goes on the left, mirrored: its own sprite, the same for every saint
  const [a1, a2] = d.attributi || (d.attributo ? [d.attributo] : [])
  const s1 = a1 && ATTRIBUTI96[a1] ? attrSprite(a1, d) : null, s2 = a2 && ATTRIBUTI96[a2] ? attrSprite(a2, d) : null
  ;(seq ? (n, o, ...it) => anim(n, { ...o, frames: seq.length, fps: 12 }, ...it) : sprite)(`_${nome}_fig`, { w: F, h: F, outline: "K" },
    tara96, ...cop.dietro, ...(coperto ? [] : pg ? [pg.dietro] : tg ? tg.dietro : capelliDietro(d, MARCA_C)), ...collo6(d),
    ...busto, ...extra.flatMap((e) => e.busto || []), ...(pg && pg.spalle ? [pg.spalle] : []),
    ...orecchie(pg && pg.orecchie ? { ...d, capelli: "corti" } : tg && tg.coperte ? { ...d, capelli: "lunghi" } : d, sk), viso.viso, ...(frangia ? (pg ? [pg.davanti] : tg ? (alto ? [] : tg.davanti) : capelliDavanti(d, MARCA_C)) : []), capelli6(d, viso, tg && { ...tg.stile, sotto: alto }), ...barba(d, MARCA_B), barba6(d, viso), ...cop.davanti, ...extra.flatMap((e) => e.testa || []),
    stoffe6(d, mat), viso.ombra, ...occ)
  // the attributes go over the outlined figure, each with its own 1 px outline: one line per edge (drawn
  // inside the figure they got the figure's outline on top of their own, 2 px on the silhouette)
  const attr = (dx) => [...(s1 ? [stamp(s1, dx, dx)] : []), ...(s2 ? [stamp(s2, dx, dx, { flip: "x" })] : [])]
  sprite(nome, { w: S, h: S }, ...sfondo6(d),
    stamp(al, 0, 0), layer("ombra", { shade: true }, stamp(`_${nome}_fig`, 2, 2), ...attr(2)), stamp(`_${nome}_fig`, 0, 0), ...attr(0))
}
