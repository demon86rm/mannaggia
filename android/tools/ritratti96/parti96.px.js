// More parts for libreria96.px.js: the attributes, robes, headgear and extras of the FAMOSI saints
// (ripieghi.tsv). Attributes are drawn on the right (x >= 64 above y 47, the eye area); a second one
// is mirrored on the left by ritratto96. Fixed colours: an attribute looks the same for every saint.
// The glasses (occhiali) are left out: they sit on the eyes, so they belong with the animated eyes.
{ // own scope
const { cx, F } = G96
const ORO = rampa("#e2b646"), ARG = rampa("#b6bcc4", { shift: 12 }), LEG = rampa("#8a5a34"), BIANCO = rampa("#f0ece4", { shift: 14, sat: 0.4 })
const VERDE = rampa("#5aa046"), ROSSO = rampa("#c8303a"), PIETRA = rampa("#8a8a8e", { shift: 8 }), AVORIO = rampa("#e8dcc0", { shift: 10, sat: 0.5 })
const NERO = "#1e1a20"
// a big key: a thick bow with its hole at the top, a 4 px shaft, a bit with two wards at the bottom; t = tones
const chiave = (x0, y0, x1, y1, t) => { const s = x1 > x0 ? 1 : -1
  return [line(x0, y0, x1, y1, t[2], 3), line(x0 - s, y0 + 1, x1 - s, y1 + 1, t[3]),
    circ(x0, y0, 5, t[2]), circ(x0, y0, 2, "_"), ring(x0, y0, 5, t[1]), ring(x0, y0, 3, t[1]), px(x0 - 2, y0 - 4, t[3]),
    rect(x1 + (s > 0 ? 0 : -6), y1 - 7, 7, 3, t[2]), rect(x1 + (s > 0 ? 0 : -6), y1 - 2, 7, 3, t[2]), hline(x1 + (s > 0 ? 0 : -6), y1 - 7, 7, t[3])] }
// an animal's eye
const occhietto = (x, y) => [px(x, y, NERO), px(x - 1, y - 1, "#ffffff")]

Object.assign(ATTRIBUTI96, {
  chiavi: () => [...chiave(86, 46, 73, 92, ARG), ...chiave(73, 40, 86, 92, ORO)],           // St Peter: silver and gold, crossed
  ruota: () => {                                                                            // St Catherine: the spiked wheel
    const w = LEG
    return [ring(80, 80, 12, w[2]), ring(80, 80, 11, w[1]), ring(80, 80, 3, w[2]),
      ...[0, 1, 2, 3, 4, 5].map((k) => { const a = k * Math.PI / 3; return line(80, 80, Math.round(80 + 10 * Math.cos(a)), Math.round(80 + 10 * Math.sin(a)), w[2]) }),
      ...[0, 1, 2, 3, 4, 5, 6, 7].map((k) => { const a = k * Math.PI / 4 + 0.4; return px(Math.round(80 + 14 * Math.cos(a)), Math.round(80 + 14 * Math.sin(a)), ARG[2]) })]
  },
  // the dragon of the approved San Giorgio prototype: at the bottom right, head turned up, jaws open
  drago: () => {
    // saturated greens a step darker than a plain ramp, so its lit top stands out from steel and silver;
    // ochre horns (the pale green of the first version merged with San Giorgio's armour)
    const g = ["#163c16", "#24601e", "#33802a", "#58b034"], r = rampa("#b8302c"), HORN = "#c89a3a"
    return [ellipse(88, 92, 10, 7, g[2]), ellipse(81, 85, 9, 6, g[2]), poly([64, 81, 73, 78, 76, 89, 65, 89], g[2]),
      poly([63, 83, 75, 82, 75, 86, 63, 87], r[1]), hline(65, 85, 8, r[2]),
      ...[[65, 82], [68, 82], [71, 82], [66, 87], [70, 87]].map(([x, y]) => px(x, y, "#ffffff")),
      poly([86, 79, 92, 71, 90, 80], HORN), poly([80, 79, 83, 73, 84, 80], HORN), rect(78, 80, 3, 2, "#f2d23c"), px(79, 80, NERO), px(79, 81, NERO),
      recolor({ [g[2]]: g[3] }, (x, y) => y < 82 && x < 82), recolor({ [g[2]]: g[1] }, (x, y) => y > 89 || x > 90),
      ...[84, 88, 92].map((x) => px(x, 92, g[1])), ...[86, 90].map((x) => px(x, 93, g[3]))]
  },
  // a lance held upright: a sturdy shaft, a leaf-shaped steel head at the top; a crusader carries the
  // white pennant with the red cross just under the head (San Giorgio)
  lancia: (d) => [rect(80, 16, 4, 78, LEG[2]), vline(80, 16, 78, LEG[3]), vline(83, 16, 78, LEG[1]),
    poly([82, 1, 86, 8, 84, 16, 80, 16, 78, 8], ARG[2]), line(82, 2, 80, 14, ARG[3]), rect(79, 15, 6, 3, ARG[1]),
    ...(d.abito === "crociato" ? [poly([84, 18, 94, 21, 94, 30, 84, 33], BIANCO[2]), rect(87, 20, 2, 11, ROSSO[2]), rect(84, 24, 9, 2, ROSSO[2]),
      recolor({ [BIANCO[2]]: BIANCO[1] }, (x, y) => y > 29)] : [])],
  agnello: () => {                                                                          // a white lamb at the bottom right
    const w = rampa("#f0ece4", { shift: 10, sat: 0.3 })
    return [...[74, 79, 85, 90].map((x) => rect(x, 88, 2, 6, NERO)), ellipse(82, 84, 11, 7, w[2]),
      ...[[76, 80], [82, 79], [88, 81], [79, 86], [86, 87]].map(([x, y]) => circ(x, y, 2, w[3])), ellipse(70, 79, 5, 4, w[1]),
      ellipse(67, 76, 2, 1, w[0]), ...occhietto(69, 78), recolor({ [w[2]]: w[1] }, (x, y) => y > 86)]
  },
  leone: () => {                                                                            // a lion's head at the bottom right
    const m = rampa("#c87a30"), f = rampa("#e2b060")
    return [circ(80, 82, 12, m[2]), ...[0, 1, 2, 3, 4, 5, 6, 7].map((k) => { const a = k * Math.PI / 4; return circ(Math.round(80 + 11 * Math.cos(a)), Math.round(82 + 11 * Math.sin(a)), 3, m[1]) }),
      ellipse(80, 84, 7, 8, f[2]), ...occhietto(77, 81), ...occhietto(84, 81), poly([78, 86, 82, 86, 80, 88], NERO), hline(78, 91, 5, f[0])]
  },
  colomba: () => {                                                                          // the dove, by the right shoulder
    const w = rampa("#f4f2ee", { shift: 10, sat: 0.2 })
    return [ellipse(78, 50, 9, 5, w[2]), poly([74, 48, 86, 36, 84, 48], w[3]), ellipse(68, 47, 4, 3, w[2]), poly([64, 47, 61, 48, 64, 49], "#e09030"),
      ...occhietto(67, 46), poly([86, 50, 93, 46, 93, 54], w[1]), recolor({ [w[2]]: w[1] }, (x, y) => y > 52)]
  },
  teschio: () => [ellipse(80, 82, 8, 7, AVORIO[2]), rect(76, 86, 9, 5, AVORIO[2]), ellipse(77, 82, 2, 2, NERO), ellipse(84, 82, 2, 2, NERO),
    px(80, 86, NERO), ...[77, 79, 81, 83].map((x) => vline(x, 89, 2, AVORIO[0])), recolor({ [AVORIO[2]]: AVORIO[1] }, (x, y) => x > 85)],
  bambino: (d) => {                                                                         // the Child, held on the right
    const s = rampa(d.pelle_bambino || "#f0c8a0", { shift: 10, sat: 0.75 })
    return [circ(80, 60, 9, ORO[1]), circ(80, 60, 8, ORO[3]), ellipse(80, 80, 11, 13, BIANCO[2]), circ(80, 60, 6, s[2]),
      clip((x, y) => y <= 57, circ(80, 60, 6, "#c89048")), ...occhietto(78, 61), ...occhietto(83, 61), hline(79, 64, 3, s[0]),
      recolor({ [BIANCO[2]]: BIANCO[1] }, (x, y) => x > 86 || y > 88), ellipse(72, 76, 3, 2, s[2])]
  },
  cane: () => {                                                                             // a dog sitting at the bottom right
    const b = rampa("#a87444")
    return [ellipse(84, 86, 9, 8, b[2]), ellipse(74, 76, 6, 5, b[2]), ellipse(68, 79, 3, 2, b[3]), px(66, 78, NERO), ...occhietto(73, 75),
      poly([76, 71, 80, 70, 79, 78], b[0]), rect(80, 90, 3, 4, b[1]), rect(86, 90, 3, 4, b[1]), recolor({ [b[2]]: b[1] }, (x, y) => x > 88)]
  },
  penna: () => [line(70, 90, 88, 44, AVORIO[2], 4), line(71, 88, 88, 46, AVORIO[3]), line(70, 90, 88, 44, AVORIO[0]),
    line(68, 94, 70, 90, NERO, 2), ...[0, 1, 2, 3, 4, 5].map((k) => px(86 - k * 3, 50 + k * 7, AVORIO[1]))],
  ihs: () => [circ(80, 74, 13, ORO[1]), circ(80, 74, 11, ORO[2]), circ(80, 74, 9, ORO[3]),
    ...[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((k) => { const a = k * Math.PI / 6; return line(Math.round(80 + 13 * Math.cos(a)), Math.round(74 + 13 * Math.sin(a)), Math.round(80 + 16 * Math.cos(a)), Math.round(74 + 16 * Math.sin(a)), ORO[2]) }),
    vline(74, 71, 6, "#8a2a1a"), vline(78, 71, 6, "#8a2a1a"), vline(81, 71, 6, "#8a2a1a"), hline(78, 74, 4, "#8a2a1a"),
    hline(84, 71, 3, "#8a2a1a"), px(84, 72, "#8a2a1a"), hline(84, 73, 3, "#8a2a1a"), px(86, 75, "#8a2a1a"), hline(84, 76, 3, "#8a2a1a")],
  vaso: () => [ellipse(80, 82, 9, 10, AVORIO[2]), rect(76, 70, 9, 4, AVORIO[2]), ellipse(80, 69, 6, 2, ORO[2]), circ(80, 66, 2, ORO[2]),
    hline(72, 80, 17, ORO[2]), recolor({ [AVORIO[2]]: AVORIO[1] }, (x, y) => x > 84)],
  citta: () => {                                                                            // a small walled city, held at the bottom right
    const m = rampa("#d8c098"), t = rampa("#b8483a")
    return [rect(64, 80, 30, 14, m[2]), rect(66, 68, 7, 12, m[2]), rect(78, 64, 8, 16, m[2]), rect(88, 72, 6, 8, m[2]),
      poly([65, 68, 69, 62, 74, 68], t[2]), poly([77, 64, 82, 56, 87, 64], t[2]), poly([87, 72, 91, 67, 94, 72], t[2]),
      ...[[68, 72], [81, 68], [81, 74], [90, 75]].map(([x, y]) => rect(x, y, 2, 3, NERO)), ...[66, 70, 74, 78, 82, 86, 90].map((x) => rect(x, 78, 2, 2, m[2])),
      rect(77, 86, 5, 8, NERO), recolor({ [m[2]]: m[1] }, (x, y) => x > 86)]
  },
  cuore: () => [circ(76, 76, 5, ROSSO[2]), circ(84, 76, 5, ROSSO[2]), poly([71, 78, 89, 78, 80, 89], ROSSO[2]), px(75, 74, ROSSO[3]), px(74, 75, ROSSO[3]),
    poly([78, 70, 80, 62, 83, 70], "#f0a030"), poly([79, 70, 80, 66, 81, 70], "#ffe080"), recolor({ [ROSSO[2]]: ROSSO[1] }, (x, y) => x > 84 && y > 76)],
  tenaglia: () => [line(70, 92, 86, 58, ARG[2], 2), line(84, 92, 70, 58, ARG[2], 2), ring(77, 75, 2, ARG[0]),
    line(86, 58, 82, 54, ARG[1], 2), line(70, 58, 74, 54, ARG[1], 2)],
  coltello: () => [poly([80, 40, 84, 44, 84, 76, 78, 76], ARG[2]), vline(84, 44, 32, ARG[1]), vline(79, 46, 28, ARG[3]), rect(77, 76, 9, 3, ORO[2]), rect(79, 79, 5, 14, "#5a3a24")],
  // St Blaise's two candles, crossed in the middle and tied with a red ribbon; a flame on each
  candele: () => [line(70, 93, 88, 56, AVORIO[2], 5), line(70, 93, 88, 56, AVORIO[3]), line(90, 93, 72, 56, AVORIO[1], 5), line(90, 93, 72, 56, AVORIO[2]),
    ...[[88, 56], [72, 56]].flatMap(([x, y]) => [vline(x, y - 3, 3, NERO), ellipse(x, y - 7, 3, 4, "#f0a030"), ellipse(x, y - 6, 1, 2, "#ffe880")]),
    rect(76, 72, 9, 5, ROSSO[2]), hline(76, 72, 9, ROSSO[3]), poly([78, 77, 75, 84, 79, 82], ROSSO[1]), poly([83, 77, 86, 84, 82, 82], ROSSO[1])],
  arpa: () => [line(70, 92, 70, 52, ORO[1], 3), line(70, 52, 90, 64, ORO[2], 3), line(90, 64, 88, 92, ORO[1], 2), hline(70, 92, 19, ORO[1]),
    ...[74, 78, 82, 86].map((x) => vline(x, 56 + Math.round((x - 70) * 0.6), 36 - Math.round((x - 70) * 0.6), "#f0e8d0"))],
  caritas: () => [circ(80, 74, 12, ORO[2]), circ(80, 74, 10, ORO[3]), ...[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((k) => { const a = k * Math.PI / 6
      return line(Math.round(80 + 12 * Math.cos(a)), Math.round(74 + 12 * Math.sin(a)), Math.round(80 + 16 * Math.cos(a)), Math.round(74 + 16 * Math.sin(a)), ORO[2]) }),
    ...[71, 75, 78].map((y) => hline(73, y, 14, "#8a2a1a"))],
  conchiglia: () => {                                                                       // the pilgrim's scallop shell
    const c = rampa("#f0dcb8", { shift: 10, sat: 0.6 })
    return [clip((x, y) => y <= 80, ellipse(80, 82, 12, 12, c[2])), poly([76, 80, 84, 80, 82, 86, 78, 86], c[2]),
      ...[-8, -4, 0, 4, 8].map((dx) => line(80, 84, 80 + dx, 71, c[0])), recolor({ [c[2]]: c[1] }, (x, y) => x > 86)]
  },
  aquila: () => {                                                                           // St John's eagle at the bottom right
    const b = rampa("#7a5230")
    return [ellipse(82, 84, 8, 10, b[2]), poly([74, 80, 64, 70, 66, 86], b[1]), poly([90, 80, 94, 68, 94, 88], b[1]), circ(80, 72, 5, "#f0ece4"),
      poly([75, 72, 71, 74, 75, 75], "#e0a020"), ...occhietto(79, 71), ...[78, 84].map((x) => rect(x, 93, 3, 1, "#e0a020"))]
  },
  graticola: () => [rect(70, 62, 19, 2, "#7e7c86"), rect(70, 92, 19, 2, "#7e7c86"), rect(70, 62, 2, 32, "#7e7c86"), rect(87, 62, 2, 32, "#7e7c86"), ...[75, 79, 83].map((x) => vline(x, 64, 30, "#a8a6b0")),
    hline(72, 74, 15, "#7e7c86"), hline(72, 85, 15, "#7e7c86"), rect(78, 55, 3, 7, "#7e7c86"),
    ...[[73, 91], [77, 90], [81, 92], [85, 90]].map(([x, y]) => px(x, y, "#ffb040"))],
  bue: () => {                                                                              // St Luke's ox, its head at the bottom right
    const b = rampa("#a0603a")
    return [ellipse(80, 82, 10, 11, b[2]), ellipse(80, 90, 7, 4, b[3]), px(77, 90, NERO), px(83, 90, NERO), ...occhietto(76, 80), ...occhietto(85, 80),
      poly([70, 74, 64, 66, 72, 72], AVORIO[2]), poly([90, 74, 96, 66, 88, 72], AVORIO[2]), recolor({ [b[2]]: b[1] }, (x, y) => x > 86)]
  },
  ascia: () => [line(82, 30, 80, 94, LEG[2], 3), poly([82, 32, 94, 28, 94, 46, 82, 42], ARG[2]), vline(93, 29, 17, ARG[3])],
  palle: () => [...[[74, 72], [86, 72], [80, 83]].flatMap(([x, y]) => [circ(x, y, 5, ORO[2]), px(x - 2, y - 2, ORO[3]), px(x - 1, y - 3, "#ffffff")])],
  trifoglio: () => [line(80, 92, 79, 72, VERDE[1], 2), ...[[75, 66], [84, 66], [80, 60]].map(([x, y]) => circ(x, y, 4, VERDE[2])), circ(80, 65, 2, VERDE[3])],
  frecce: () => [...[[70, 70, 90, 90], [66, 84, 90, 76], [72, 94, 88, 66]].flatMap(([a, b, c2, e]) => [line(a, b, c2, e, LEG[2], 1),
    poly([c2 - 2, e - 2, c2 + 2, e + 2, c2 + 3, e - 3], ARG[2]), line(a, b, a - 3, b - 1, BIANCO[2]), line(a, b, a - 1, b + 3, BIANCO[2])])],
  sega: () => [rect(74, 40, 8, 40, ARG[2]), ...[42, 46, 50, 54, 58, 62, 66, 70, 74, 78].map((y) => px(73, y, ARG[0])), rect(74, 80, 8, 12, "#5a3a24"), ring(78, 86, 2, NERO)],
  frusta: () => [rect(78, 70, 4, 22, "#5a3a24"), ...[-6, 0, 6].map((dx) => line(80, 70, 80 + dx, 46, "#8a6a4a")), ...[-6, 0, 6].flatMap((dx) => [px(80 + dx, 47, "#5a3a24"), px(80 + Math.round(dx * 0.5), 58, "#5a3a24")])],
  maialino: () => {                                                                         // St Anthony the Abbot's piglet
    const p = rampa("#f0a8a8", { shift: 10, sat: 0.7 })
    return [ellipse(82, 86, 11, 7, p[2]), ellipse(70, 84, 5, 5, p[2]), ellipse(66, 86, 2, 2, p[1]), px(65, 86, NERO), ...occhietto(70, 82),
      poly([71, 79, 74, 76, 74, 81], p[1]), ...[76, 86].map((x) => rect(x, 91, 3, 3, p[1])), recolor({ [p[2]]: p[1] }, (x, y) => y > 89)]
  },
  torre: () => {                                                                            // St Barbara's tower, three windows
    const m = rampa("#c8b090")
    return [rect(72, 56, 16, 38, m[2]), ...[72, 76, 80, 84].map((x) => rect(x, 52, 3, 4, m[2])), ...[[78, 62], [75, 74], [82, 74]].map(([x, y]) => rect(x, y, 2, 4, NERO)),
      recolor({ [m[2]]: m[1] }, (x, y) => x > 84)]
  },
  organo: () => [...[0, 1, 2, 3, 4, 5].map((k) => rect(68 + k * 4, 60 + Math.abs(k - 2.5) * 4, 3, 30 - Math.abs(k - 2.5) * 4, k % 2 ? ARG[2] : ARG[3])),
    rect(66, 88, 26, 6, LEG[2])],
  ostensorio: () => [circ(80, 64, 12, ORO[2]), ...[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((k) => { const a = k * Math.PI / 6
      return line(Math.round(80 + 11 * Math.cos(a)), Math.round(64 + 11 * Math.sin(a)), Math.round(80 + 16 * Math.cos(a)), Math.round(64 + 16 * Math.sin(a)), ORO[3]) }),
    circ(80, 64, 5, "#fffbe8"), rect(79, 76, 3, 12, ORO[2]), ellipse(80, 90, 7, 3, ORO[1])],
  occhi: () => [ellipse(80, 84, 12, 5, ARG[3]), ellipse(80, 84, 10, 3, ARG[2]), ...[75, 85].flatMap((x) => [ellipse(x, 82, 3, 2, "#ffffff"), px(x, 82, "#4c6a8a")])],
  pietre: () => [...[[72, 86, 6], [84, 88, 5], [78, 78, 5]].flatMap(([x, y, r]) => [ellipse(x, y, r, r - 1, PIETRA[2]), px(x - 2, y - 2, PIETRA[3]), px(x + 2, y + 1, PIETRA[1])])],
  pesce: () => {                                                                            // St Zeno's fish
    const f = rampa("#8aa0b0", { shift: 10 })
    return [ellipse(78, 80, 11, 5, f[2]), poly([88, 80, 94, 74, 94, 86], f[1]), ...occhietto(71, 79), line(70, 82, 68, 82, NERO),
      ...[74, 78, 82].map((x) => px(x, 78, f[3])), recolor({ [f[2]]: f[1] }, (x, y) => y > 81)]
  },
})

Object.assign(ABITI, {
  felpa(d, rb) {        // a hoodie, one garment with its hood (COPRICAPI.cappuccio): no shirt, no lapels; the
                        // hood's two sides cross under the chin in a soft V, the neck in shadow inside it,
                        // the drawstrings hang from the V
    const { cx } = G96, sk = d._sk
    return [...spalle(rb[2]), poly([cx - 7, 60, cx + 7, 60, cx, 70], sk[1]),
      poly([cx - 14, 60, cx - 7, 60, cx + 1, 72, cx - 3, 76], rb[2]), poly([cx + 14, 60, cx + 7, 60, cx - 1, 72, cx + 3, 76], rb[1]),
      line(cx - 7, 60, cx, 71, rb[3]), line(cx + 7, 60, cx + 1, 70, rb[0]),
      vline(cx - 3, 74, 10, "#e8e8ec"), vline(cx + 3, 74, 10, "#d0d0d8"), px(cx - 3, 84, "#a0a0a8"), px(cx + 3, 84, "#a0a0a8"),
      recolor({ [rb[2]]: rb[1] }, (x, y) => y > 74 && x > cx + 12)]
  },
  crociato(d, rb) {     // armour with the white surcoat and the red cross (San Giorgio)
    const { cx } = G96, w = BIANCO
    return [...ABITI.armatura(d, rb), ellipse(cx, F + 22, 30, 32, w[2]), rect(cx - 3, 76, 6, F - 76, ROSSO[2]), rect(cx - 12, 82, 24, 6, ROSSO[2]),
      recolor({ [w[2]]: w[1], [ROSSO[2]]: ROSSO[1] }, (x, y) => y > 72 && x > cx + 9)]
  },
  pelliccia(d, rb) {    // St John the Baptist: camel-hair tunic over one shoulder, the other bare
    const { cx } = G96, p = rampa("#9a7046"), sk = d._sk
    return [...spalle(sk[2]), recolor({ [sk[2]]: sk[1] }, (x, y) => y > 74 && x > cx + 12),
      poly([cx - 46, 80, cx - 14, 69, cx + 10, 74, cx + 46, 94, cx - 46, 94], p[2]),
      (c) => { for (let k = 0; k < 40; k++) { const x = cx - 40 + ((k * 23) % 80), y = 80 + ((k * 7) % 14); c.recolor({ [p[2]]: p[1] }, (xx, yy) => xx === x && yy === y) } },
      line(cx - 14, 69, cx + 10, 74, p[3])]
  },
  righe(d, rb) {        // St Maximilian Kolbe: the striped prison uniform
    const { cx } = G96
    return [...spalle("#d8dce4"), (c) => c.recolor({ "#d8dce4": "#4a5a7a" }, (x, y) => Math.floor((x - cx + 64) / 4) % 2 === 0),
      ellipse(cx, 70, 12, 4, "#4a5a7a"), ellipse(cx, 69, 11, 3, d._sk[2]), recolor({ "#d8dce4": "#b0b4c0", "#4a5a7a": "#3a4862" }, (x, y) => y > 72 && x > cx + 12)]
  },
  nudo(d, rb) {         // St Sebastian: bare chest
    const { cx } = G96, sk = d._sk
    return [...spalle(sk[2]), line(cx - 10, 80, cx - 2, 84, sk[1]), line(cx + 10, 80, cx + 2, 84, sk[1]), vline(cx, 84, 10, sk[1]),
      recolor({ [sk[2]]: sk[1] }, (x, y) => y > 72 && x > cx + 14)]
  },
  camice(d, rb) {       // a doctor's white coat, open over a blue dress, the stethoscope
    const { cx } = G96, w = BIANCO
    return [...spalle(w[2]), poly([cx - 9, 68, cx + 9, 68, cx + 4, 94, cx - 4, 94], "#6e8cc0"), line(cx - 9, 68, cx - 4, 94, w[0]), line(cx + 9, 68, cx + 4, 94, w[0]),
      line(cx - 12, 70, cx - 14, 86, "#3a3a44"), ring(cx - 14, 88, 2, ARG[1]), recolor({ [w[2]]: w[1] }, (x, y) => y > 72 && x > cx + 12)]
  },
  sari(d, rb) {         // St Teresa of Calcutta: the white sari with blue borders over the shoulders
    const { cx } = G96, w = BIANCO, b = "#3a68b8"
    return [...spalle(w[2]), line(cx - 46, 86, cx - 14, 70, b, 2), line(cx - 46, 90, cx - 14, 74, b), line(cx + 46, 86, cx + 14, 70, b, 2),
      line(cx + 46, 90, cx + 14, 74, b), ellipse(cx, 70, 12, 4, w[1]), ellipse(cx, 69, 11, 3, d._sk[2]), recolor({ [w[2]]: w[1] }, (x, y) => y > 72 && x > cx + 12)]
  },
})

Object.assign(COPRICAPI, {
  pellegrino(d) {       // a wide pilgrim's hat with the shell
    const b = rampa("#7a5232")
    return { dietro: [], davanti: [ellipse(cx, 22, 28, 5, b[2]), clip((x, y) => y <= 22, ellipse(cx, 22, 16, 10, b[2])), hline(cx - 26, 21, 52, b[3]),
      clip((x, y) => y <= 18, ellipse(cx + 6, 17, 4, 4, "#f0dcb8")), recolor({ [b[2]]: b[1] }, (x, y) => x > cx + 8)] }
  },
  corona_rose(d) {      // a wreath of roses on the head
    return { dietro: [], davanti: [ellipse(cx, 22, 19, 4, VERDE[1]), ...[-15, -9, -3, 3, 9, 15].flatMap((dx) => [circ(cx + dx, 21, 3, ROSSO[2]), px(cx + dx - 1, 20, ROSSO[3])])] }
  },
  elmo(d) {             // a Roman helmet with a red crest (Sant'Efisio)
    return { dietro: [], davanti: [clip((x, y) => y <= 28, ellipse(cx, 28, 20, 18, ARG[2])), rect(cx - 20, 24, 40, 4, ARG[1]), hline(cx - 20, 24, 40, ARG[3]),
      ellipse(cx, 8, 6, 8, ROSSO[2]), rect(cx - 2, 2, 5, 14, ROSSO[1]), recolor({ [ARG[2]]: ARG[1] }, (x, y) => x > cx + 8 && y <= 28)] }
  },
  sari(d) {             // the sari over the head, white with blue borders
    const w = BIANCO, b = "#3a68b8"
    return { dietro: [poly([cx - 26, 40, cx - 30, 70, cx - 44, 86, cx - 46, 94, cx + 46, 94, cx + 44, 86, cx + 30, 70, cx + 26, 40], w[2]),
      ellipse(cx, 38, 26, 27, w[2]), ellipse(cx, 41, 21, 24, w[1])],
      davanti: [clip((x, y) => y <= 25, ellipse(cx, 38, 26, 27, w[2])), (c) => { const q = (x, y) => Math.hypot((x - cx) / 26, (y - 38) / 27)
        c.recolor({ [w[2]]: b }, (x, y) => { const v = q(x, y); return v > 0.86 && v < 0.94 && !inFaccia(x, y) }) },
        recolor({ [w[2]]: w[1] }, (x, y) => x > cx + 14 && !inFaccia(x, y))] }
  },
})

// Extras: details on the bust (busto, over the robe) or on the head (testa, after the headgear)
var EXTRA96 = {
  croce_rossa: () => ({ busto: [rect(cx - 22, 78, 4, 12, ROSSO[2]), rect(cx - 26, 82, 12, 4, ROSSO[2])] }),        // St Camillus
  stella: () => ({ testa: [px(cx, 27, "#f2d23c"), hline(cx - 2, 28, 5, "#f2d23c"), px(cx, 29, "#f2d23c"), px(cx - 1, 30, "#f2d23c"), px(cx + 1, 30, "#f2d23c")] }),   // St Dominic
  stigmate: () => ({}),                                                     // the hands are not in the portrait
  medaglione: (d) => ({ busto: [circ(cx, 82, 6, ORO[2]), circ(cx, 82, 4, d._sk ? d._sk[2] : "#eab992"), line(cx - 6, 72, cx - 3, 77, ORO[1]), line(cx + 6, 72, cx + 3, 77, ORO[1])] }),   // St Jude
  // the Pentecost flame over the head: a drop of fire, its tip bent, a yellow heart
  fiamma: () => ({ testa: [ellipse(cx, 9, 5, 5, "#e8682a"), poly([cx - 5, 8, cx + 1, -2, cx + 2, 2, cx + 5, 8], "#e8682a"),
    ellipse(cx, 10, 3, 3, "#f8b030"), poly([cx - 2, 9, cx + 1, 2, cx + 2, 9], "#f8b030"), ellipse(cx, 11, 1, 1, "#fff0a0")] }),
  mantello: () => ({ busto: [poly([cx - 46, 80, cx - 14, 69, cx - 4, 94, cx - 46, 94], ROSSO[2]), line(cx - 14, 69, cx - 4, 94, ROSSO[3]),
    poly([cx - 4, 94, cx - 8, 86, cx - 2, 88], ROSSO[1])] }),               // St Martin's cloak, cut in half
  sole_petto: () => ({ busto: [circ(cx, 82, 7, ORO[2]), circ(cx, 82, 4, ORO[3]),
    ...[0, 1, 2, 3, 4, 5, 6, 7].map((k) => { const a = k * Math.PI / 4; return line(Math.round(cx + 8 * Math.cos(a)), Math.round(82 + 8 * Math.sin(a)), Math.round(cx + 11 * Math.cos(a)), Math.round(82 + 11 * Math.sin(a)), ORO[2]) })] }),   // St Thomas Aquinas
  spine: () => ({ testa: [ellipse(cx, 22, 19, 3, "#6a4a2a"), ...[-16, -10, -4, 2, 8, 14].map((dx) => line(cx + dx, 20, cx + dx + 2, 18, "#4a3220"))] }),   // crown of thorns
  stelle: () => ({ testa: [...[[-20, 6], [-10, 1], [0, -1], [10, 1], [20, 6]].flatMap(([dx, y]) => [px(cx + dx, y, "#fff4b0"), hline(cx + dx - 1, y + 1, 3, "#fff4b0"), px(cx + dx, y + 2, "#fff4b0")])] }),   // Our Lady's stars
  manto_azzurro: () => { const b = rampa("#3a60b0"); return { busto: [...simm([cx - 14, 68, cx - 46, 80, cx - 46, 94, cx - 18, 94, cx - 12, 76], b[2]),
    recolor({ [b[2]]: b[1] }, (x, y) => x > cx + 12)] } },                  // Our Lady's blue mantle
  ferita_fronte: () => ({ testa: [hline(cx - 1, 29, 3, "#8a2a2a"), px(cx, 28, "#b8403a"), px(cx, 30, "#5a1a1a")] }),   // St Rita's wound
}
}
