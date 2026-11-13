// Hoodie prototypes for San Sudo, second round (the first looked like a nun's veil). A hoodie's hood:
// - a slightly peaked top with the centre seam, short: it ends on the neck and shoulders, gathered at
//   the collar, it does not fall on the chest;
// - its opening rim overhangs the forehead (a shadow under it) and is wider and puffier by the cheeks;
//   the rim is a doubled band of fabric;
// - collars: open with a zip (a T-shirt crew neck, concave, under the neck) or closed (the two edges of
//   the opening meet at the throat in a round collar); the drawstrings come out of two eyelets on the rim.
// Hood down: the bunched hood lies BEHIND the neck and on the shoulders; the neck goes into the crew neck.
// The hair: a fringe coming out from under the rim, one mass with its strands going the same way.
// (included by speciali96.px.js, after the specials: G96, ALONE, attrSprite and "terminale" come from there)
{ // own scope
const { S, F, cx, EYE_Y, BROW_Y, FAR } = G96
const ell = (x, y, x0, y0, rx, ry) => ((x - x0) / rx) ** 2 + ((y - y0) / ry) ** 2 <= 1
const q = (x, y, rx, ry) => Math.hypot((x - cx) / rx, (y - 47) / ry)      // the opening, centred lower than the face
const OPEN = [20, 23], RIM = [23, 26]                                     // inner and outer edge of the rim
const SHELL = [cx, 5, cx + 8, 7, cx + 18, 13, cx + 25, 23, cx + 28, 36, cx + 29, 50, cx + 26, 61, cx + 21, 69,
  cx - 21, 69, cx - 26, 61, cx - 29, 50, cx - 28, 36, cx - 25, 23, cx - 18, 13, cx - 8, 7]

function felpa(nome, modo, col = "#4a4e58", conOcchi = true) {
  const sk = rampa("#f6d0b0", { shift: 10, sat: 0.75 }), hr = rampa("#684228", { shift: 8, sat: 0.8 }), v = rampa(col, { shift: 12 })
  const d = { capelli: "corti", eta: "giovane", guance: true, _sk: sk, viso: 0, naso_v: 0, bocca: 0, attacc: 0 }
  const al = ALONE.santo
  sprite(`_${nome}_aureola`, { w: F, h: F, outline: "K" }, circ(cx, 34, 35, al[0]), circ(cx, 34, 33, al[1]), circ(cx, 34, 29, al[2]),
    recolor({ [al[2]]: al[3] }, (x, y) => x + y > cx + 34 + 22))
  const corpo = [ellipse(cx, F + 20, 46, 34, v[2]), ...simm([cx - 13, 66, cx - 30, 74, cx - 46, 81, cx - 46, 94, cx, 94, cx, 66], v[2]),
    recolor({ [v[2]]: v[1] }, (x, y) => y > 72 && x > cx + 14), ...[cx - 28, cx + 28].map((x) => vline(x, 82, 12, v[1]))]
  const lacci = (y0) => [px(cx - 6, y0, v[0]), px(cx + 6, y0, v[0]), vline(cx - 6, y0 + 1, 13, "#e4dcec"), vline(cx + 6, y0 + 1, 13, "#cfc6d8"),
    px(cx - 6, y0 + 14, "#a89eb4"), px(cx + 6, y0 + 14, "#a89eb4")]
  // the fringe: one mass under the rim (inside the opening, above the brows), strands slanting the same way,
  // a longer lock towards the left eye
  // the hair fills the top of the opening down to above the brows (no skin between hair and hood), darker
  // by the rim that shades it; its lower edge is irregular: locks of different lengths, two slants, one
  // longer towards the left eye (never below y 32: the brows start at 33)
  const sotto = (x, y) => q(x, y, ...OPEN) <= 1
  const ciocche = [[-17, 3, -1], [-12, 5, -2], [-7, 2, -1], [-2, 4, 1], [3, 2, 1], [8, 3, 1], [13, 2, 1]]
  const frangia = [clip((x, y) => sotto(x, y) && y <= 29, rect(cx - 22, 18, 44, 12, hr[2])),
    recolor({ [hr[2]]: hr[1] }, (x, y) => sotto(x, y) && q(x, y, ...OPEN) > 0.86 && y <= 29),
    ...ciocche.map(([dx, n, sl]) => clip(sotto, poly([cx + dx - 2, 29, cx + dx + 2, 29, cx + dx + sl * 2, 29 + n], hr[2]))),
    ...[[-15, -3], [-10, -3], [-5, -2], [0, 2], [5, 2], [10, 3]].map(([dx, sl]) => clip((x, y) => sotto(x, y) && y <= 30, line(cx + dx, 22, cx + dx + sl, 29, hr[1]))),
    ...[[-13, -2], [1, 1], [9, 2]].map(([dx, sl]) => clip((x, y) => sotto(x, y) && y <= 28, line(cx + dx + 1, 23, cx + dx + 1 + sl, 26, hr[3])))]
  const items = []
  if (modo !== "giu") {
    items.push(...corpo,
      poly(SHELL, v[2]),                                                                  // the hood, short, a slight point on top
      ellipse(cx, 47, OPEN[0], OPEN[1], v[0]),                                            // its dark inside
      // the doubled rim: in shadow over the hair (the light fold read as skin there), lit only lower, by the left cheek
      recolor({ [v[2]]: v[1] }, (x, y) => { const k = q(x, y, ...OPEN); return k > 1 && k <= 1.06 && y < 34 }),
      recolor({ [v[2]]: v[3] }, (x, y) => { const k = q(x, y, ...OPEN); return k > 1 && k <= 1.06 && x < cx + 8 && y >= 34 }),
      recolor({ [v[2]]: v[1] }, (x, y) => { const k = q(x, y, ...OPEN); return k > 1.14 && k <= 1.2 }),               // its outer edge
      recolor({ [v[2]]: v[1] }, (x, y) => x > cx + 16 && q(x, y, ...RIM) > 1),            // far side in shadow
      vline(cx, 6, 16, v[1]), px(cx - 1, 7, v[3]),                                        // the centre seam
      rect(cx - 11, 56, 22, 14, sk[1]), rect(cx - 11, 56, 22, 4, sk[0]))                 // the neck, in the hood's shadow
    if (modo === "aperta") {
      // open with a zip: the T-shirt under the neck (crew neck: concave), the two fronts with their zip tapes
      items.push(rect(cx - 9, 68, 18, 26, "#1e2028"), clip((x, y) => y >= 68, ellipse(cx, 67, 7, 4, sk[1])),
        poly([cx - 21, 68, cx - 9, 68, cx - 9, 94, cx - 34, 94], v[2]), poly([cx + 21, 68, cx + 9, 68, cx + 9, 94, cx + 34, 94], v[1]),
        vline(cx - 9, 68, 26, v[0]), vline(cx + 9, 68, 26, v[0]), vline(cx - 10, 68, 26, v[3]), ...lacci(72))
    } else {
      // closed: the edges of the opening meet at the throat in a round collar
      items.push(clip((x, y) => y >= 68 && q(x, y, ...RIM) > 1, ellipse(cx, 76, 26, 10, v[2])),
        recolor({ [v[2]]: v[3] }, (x, y) => { const k = q(x, y, ...OPEN); return k > 1 && k <= 1.06 && y >= 66 }), ...lacci(72))
    }
  } else {
    // hood down: bunched behind the neck and on the shoulders; the neck whole, into the crew neck
    items.push(...capelliDietro(d, hr), ...corpo,
      ellipse(cx, 67, 27, 9, v[2]), recolor({ [v[2]]: v[1] }, (x, y) => ell(x, y, cx, 67, 27, 9) && (y > 70 || x > cx + 14)),
      ...[cx - 20, cx - 12, cx + 12, cx + 20].map((x) => line(x, 61, x + Math.sign(x - cx), 72, v[1])), hline(cx - 22, 63, 8, v[3]),
      rect(cx - 12, 56, 24, 15, sk[2]), rect(cx - 12, 56, 24, 5, sk[1]),                // the neck, in front of the hood
      clip((x, y) => y >= 70, ellipse(cx, 69, 13, 4, v[1])), clip((x, y) => y >= 71, ellipse(cx, 69, 12, 3, sk[2])),   // the crew neck's rib
      ...lacci(72))
  }
  sprite(`_${nome}_fig`, { w: F, h: F, outline: "K" },
    ...items, ...(modo === "giu" ? orecchie(d, sk) : []), ...faccia(d, sk),
    ...(modo === "giu" ? capelliDavanti(d, hr) : [...frangia, recolor({ [sk[2]]: sk[1] }, (x, y) => q(x, y, ...OPEN) <= 1 && y >= 31 && y <= 32 && inFaccia(x, y)),
      // the hood over the top of the head again, AFTER the face: the face's top (y 22) is higher than the
      // opening's (y 24) and painted over the rim (the "skin-coloured edge" between hair and hood)
      clip((x, y) => q(x, y, ...OPEN) > 1 && y < 47, poly(SHELL, v[2])),
      recolor({ [v[2]]: v[1] }, (x, y) => { const k = q(x, y, ...OPEN); return k > 1 && k <= 1.06 && y < 34 }),
      recolor({ [v[2]]: v[3] }, (x, y) => { const k = q(x, y, ...OPEN); return k > 1 && k <= 1.06 && x < cx + 8 && y >= 34 && y < 47 }),
      recolor({ [v[2]]: v[1] }, (x, y) => { const k = q(x, y, ...OPEN); return k > 1.14 && k <= 1.2 && y < 47 }),
      recolor({ [v[2]]: v[1] }, (x, y) => x > cx + 16 && q(x, y, ...RIM) > 1 && y < 47), vline(cx, 6, 16, v[1]), px(cx - 1, 7, v[3])]),
    ...(conOcchi ? [(c) => occhi(c, cx, fr(), { y: EYE_Y, browY: BROW_Y, iride: "#5a6a3e", pelle: (x) => (x > cx + FAR ? sk[1] : sk[2]), ciglio: hr[0], ombra: sk[1] })] : []))
  const att = attrSprite("terminale", {})
  sprite(nome, { w: S, h: S }, rect(0, 0, S, S, "#2a3a30"), rect(0, 72, S, S - 72, mixc("#2a3a30", "#000000", 0.15)),
    stamp(`_${nome}_aureola`, 0, 0), layer("ombra", { shade: true }, stamp(`_${nome}_fig`, 2, 2), stamp(att, 2, 2)), stamp(`_${nome}_fig`, 0, 0), stamp(att, 0, 0))
}
felpa("spec_s5_san_sudo", "aperta")
felpa("s5", "aperta", undefined, false)               // for the app: without eyes (Occhi.kt draws them)   // the closed and hood-down variants were discarded: see felpe96b_v3.px.js
}
