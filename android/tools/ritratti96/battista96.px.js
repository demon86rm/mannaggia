// San Giovanni Battista's secret back, 96 px, in the rich style (approved 2026-11-18): the head of his front
// portrait (libreria96: hair, beard, face) upright on a gold plate. Pale, X eyes, tongue out, no blood.
// Legendary like the front: diapered ground and punched halo. The beard lies in the plate's well, with uneven tips.
// (included by speciali96.px.js, which already has libreria96, parti96 and tratti96.data.js: do not include them again, it resets ATTRIBUTI96)
{
const { S, F, cx } = G96
const b = TRATTI.find((t) => t.n === "San Giovanni Battista")
const PY = 81
const DY = 8                                    // the head sits lower, on the plate
// pale, cold skin: the colour of today's back
const d0 = { ...b, pelle: mixc(b.pelle, "#dcdedc", 0.5), copricapo: null }
const sk6 = rampa6(d0.pelle, PELLE6), sk = sk6.slice(1, 5), hr = rampa(d0.chioma, { shift: 8, sat: 0.8 })
const d = { ...d0 }
_MAT = []
d._sk = sk; d._sk6 = sk6; d._rb = rampa(d.veste, { shift: 12 })
const viso = faccia6(d)
const tg = !d.donna && d.taglio ? tagli6(d, viso) : null
_MAT = null

// X eyes: two strokes, dark core and a paler shadow under each arm (the sockets sunk and bluish)
const OCC = mixc(sk6[1], "#4a5a7a", 0.35), X = "#2a1a1c"
const xEye = (x0, y0) => (c) => {
  for (let k = -2; k <= 2; k++) for (const s of [1, -1]) { c.px(x0 + k, y0 + s * k + 1, OCC) }
  for (let k = -2; k <= 2; k++) { c.px(x0 + k, y0 + k, X); c.px(x0 + k, y0 - k, X) } }
// mouth open with the tongue out, shaded: lit top-left, groove in the middle, darker right and below
const LING = ["#7a2a36", "#a8404e", "#c85a68", "#e2788a", "#f2a0ae", "#fbd0d6"]
const bocca = (c) => {
  for (let x = cx - 3; x <= cx + 3; x++) { c.px(x, 54, "#3a1418"); c.px(x, 55, x > cx + 1 ? "#3a1418" : "#5a1e26") }
  const L = [[-2, 2], [-2, 2], [-2, 2], [-1, 1]]
  L.forEach(([a, z], i) => { for (let dx = a; dx <= z; dx++) {
    let t = 3 - (dx > 0 ? 1 : 0) - (i === 3 ? 1 : 0)
    if (i === 0 && dx < 0) t = 4
    if (dx === 0 && i < 3) t = 2
    if (dx === a && i === 0) t = 5
    c.px(cx + dx, 56 + i, LING[t]) } }) }

sprite("_bt6_testa", { w: F, h: F, outline: "K" }, tara96,
  ...(tg ? tg.dietro : capelliDietro(d, MARCA_C)),
  ...orecchie(tg && tg.coperte ? { ...d, capelli: "lunghi" } : d, sk), viso.viso,
  ...(tg ? tg.davanti : capelliDavanti(d, MARCA_C)), capelli6(d, viso, tg && tg.stile),
  ...barba(d, MARCA_B), barba6(d, viso), viso.ombra,
  xEye(cx - 11, 41), xEye(cx + 10, 41), bocca,
  // the beard lies in the well: nothing below its near edge (head coordinates, DY higher than the plate's)
  (c) => { for (let y = 0; y < F; y++) for (let x = 0; x < F; x++)
    if (y + DY > PY - 2 && (q96(x, y + DY, cx, PY - 1, 31.5, 6.5) > 1 || y + DY > PY + 1 + [2, 0, 3, 1, 2, 0][Math.floor((x + 1) / 3) % 6]))
      c.px(x, y, "_") })

// the plate, gold in six tones: a rim lit on top and dark below, the well sunk (its far edge lit,
// its near edge in shadow), a reflection of the sky on the left
sprite("_bt6_piatto", { w: F, h: F, outline: "K" }, (c) => {
  for (let y = PY - 13; y <= PY + 13; y++) for (let x = 0; x < F; x++) {
    const e = q96(x, y, cx, PY, 42.5, 11.5)
    if (e > 1) continue
    const w = q96(x, y, cx, PY - 1, 32.5, 7.5), ombra = x > cx + 16
    let k
    if (w > 1) {                                       // the rim
      k = y < PY - 1 ? 4 : y > PY + 3 ? 2 : 3
      if (e > 0.82) k = y < PY ? 5 : 1
      if (ombra) k--
      if (x < cx - 24 && x > cx - 34 && y < PY - 3 && y > PY - 8) k = 5
    } else {                                           // the well
      k = 2
      if (w > 0.72) k = y < PY - 1 ? 1 : 3
      if (ombra) k--
      if (x < cx - 14 && x > cx - 24 && y > PY - 1 && y < PY + 3) k = 3
    }
    c.px(x, y, ORO6[tra05(k)])
  } })
// the head's shadow on the plate: one dark ellipse in the well
const ombraPiatto = (c) => { for (let y = PY - 4; y <= PY + 5; y++) for (let x = 0; x < F; x++)
  if (q96(x, y, cx + 3, PY + 1, 21, 4.5) <= 1 && q96(x, y, cx, PY - 1, 32.5, 7.5) <= 1) c.px(x, y, mixc(ORO6[1], "#000000", 0.3)) }

const al = aureola6(false, true)
const carta = (nome, legg) => sprite(nome, { w: S, h: S }, ...sfondo6({ ...b, leggendario: legg }),
  stamp(al, 0, DY), stamp("_bt6_piatto", 0, 0), ombraPiatto,
  layer("ombra", { shade: true }, stamp("_bt6_testa", 2, DY + 2)), stamp("_bt6_testa", 0, DY))
carta("decollato96", true)
}
