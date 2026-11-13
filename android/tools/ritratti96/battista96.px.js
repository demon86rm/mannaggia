// San Giovanni Battista's secret back, 96 px (approved proposal A): the head upright on the plate. Pale, X eyes, tongue, no blood.
// Other proposals (B on its side, C tilted, A2 dishevelled): battista96_prove.px.js
// The beard follows the jaw (no clip with a straight edge) and spreads on the plate (no stalk under the chin).
// (included by speciali96.px.js, which already has libreria96, parti96 and tratti96.data.js: do not include them again, it resets ATTRIBUTI96)
{
const { S, F, cx } = G96
const NERO = "#1e1a20", ORO = rampa("#e2b646")
const b = TRATTI.find((t) => t.n === "San Giovanni Battista")
const sk = rampa(mixc(b.pelle, "#ece8e2", 0.35), { shift: 10, sat: 0.6 }), hr = rampa(b.chioma, { shift: 8, sat: 0.8 })
const d = { ...b, _sk: sk, copricapo: null, eta: "adulto", capelli: "lunghi", barba: null }
const al = ALONE.santo
const ell = (x, y, x0, y0, rx, ry) => ((x - x0) / rx) ** 2 + ((y - y0) / ry) ** 2 <= 1

// hair behind the face: a mass on top, long locks on both sides, ragged lower edge (never a straight wall)
const LOCKS = [[-22, 36, -25, 52, -24, 63, -21, 59, -19, 69, -16, 57, -17, 42]]
const capelliBat = [ellipse(cx, 35, 23, 20, hr[2]), ...LOCKS.flatMap((p) => simm(p, hr[2])),
  recolor({ [hr[2]]: hr[1] }, (x, y) => x > cx + 13)]

// beard: a band round the jaw that leaves the cheeks and the mouth free; the sideburns start at the ears,
// the cheek line is curved, below the chin it falls in a rounded mass with two uneven tips
const finestra = (x, y) => ell(x, y, cx, 41, 15.5, 12.5) || (Math.abs(x - cx) <= 5 && y >= 53 && y <= 57)
const sagoma = (x, y) => (ell(x, y, cx, 51, 19.5, 18) || ell(x, y, cx, 59, 14, 13)) && y >= 44 &&
  y <= 67 + [5, 3, 6, 2, 4, 1, 3, 5, 2][Math.abs(Math.round((x - cx) / 3)) % 9]
const barbaBat = [clip((x, y) => sagoma(x, y) && !finestra(x, y), rect(cx - 21, 44, 43, 32, hr[2])),
  hline(cx - 8, 52, 17, hr[2]), hline(cx - 7, 53, 15, hr[1]),                              // the moustache
  ...[[-9, 62, -10, 70], [-4, 61, -5, 72], [2, 61, 2, 73], [7, 62, 9, 70], [-13, 57, -15, 65], [12, 57, 14, 64]]
    .map(([x0, y0, x1, y1]) => line(cx + x0, y0, cx + x1, y1, hr[1])),
  recolor({ [hr[2]]: hr[1] }, (x, y) => x > cx + 9 && y > 44)]

const croce = (x0, y0) => (c) => { for (let k = -2; k <= 2; k++) { c.px(x0 + k, y0 + k, NERO); c.px(x0 + k, y0 - k, NERO) } }
sprite("_bt_raw0", { w: F, h: F },
  ...capelliBat, ...orecchie(d, sk), ...faccia(d, sk), ...capelliDavanti(d, hr), ...barbaBat,
  rect(cx - 3, 54, 7, 2, "#a8485a"), rect(cx - 2, 56, 5, 3, "#e2788a"), px(cx, 58, "#e2788a"), vline(cx, 56, 3, "#b84a5a"))   // mouth open, tongue out
sprite("_bt_raw", { w: F, h: F }, stamp("_bt_raw0", 0, 0), croce(cx - 11, 41), croce(cx + 10, 41))

const piatto = (cy) => [ellipse(cx, cy, 42, 11, ORO[1]), ellipse(cx, cy - 1, 40, 9, ORO[3]), ellipse(cx, cy, 32, 6, ORO[2]),
  recolor({ [ORO[2]]: ORO[1] }, (x, y) => x > cx + 14)]
sprite("_bt_piatto", { w: F, h: F, outline: "K" }, ...piatto(80))
const alone = (nome, cy) => sprite(nome, { w: F, h: F, outline: "K" }, circ(cx, cy, 35, al[0]), circ(cx, cy, 33, al[1]), circ(cx, cy, 29, al[2]),
  recolor({ [al[2]]: al[3] }, (x, y) => x + y > cx + cy + 22))
const sfondo = () => [rect(0, 0, S, S, b.sfondo), rect(0, 72, S, S - 72, mixc(b.sfondo, "#000000", 0.15))]
// a soft shadow of the head on the plate
const ombraPiatto = (x0, y0, rx, ry) => ellipse(x0, y0, rx, ry, mixc(ORO[1], "#000000", 0.25))

// A: upright, the beard lies on the plate
sprite("_bt_a", { w: F, h: F, outline: "K" }, stamp("_bt_raw", 0, 0))
sprite("decollato96", { w: S, h: S }, ...sfondo(), stamp("_bt_aureola_a", 0, 0),
  stamp("_bt_piatto", 0, 0), layer("ombra", { shade: true }, stamp("_bt_a", 2, 10)), ombraPiatto(cx + 1, 80, 22, 4), stamp("_bt_a", 0, 8))
alone("_bt_aureola_a", 42)
}
