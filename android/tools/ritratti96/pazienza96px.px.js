// Santa Pazienza (special card S6) at 96 px: an old woman with a grey-blue veil over a white wimple,
// a tunic of the same colour and an hourglass. Proportions as the approved portraits: face rx 18 ry 21
// centred at y 43, neck (under the wimple) 24 px wide, halo r 35 at y 34, shoulders full width.
use("pico8")
include("occhi.px.js")
{ // own scope
shades("1234", "#e2b08c", { shift: 10, sat: 0.7 })   // skin, older: a little less pink
shades("abcd", "#6e78a0", { shift: 12, sat: 0.8 })   // veil and tunic: c base, b shadow, d lit
shades("mnop", "#ece8e0", { shift: 14, sat: 0.5 })   // wimple, white linen: o base
shades("efgh", "#e2b646")                            // gold (halo, sand)
shades("ijkl", "#7a4e2e")                            // hourglass wood
pal({ K: "#22181f", W: "#fff6ea", X: "#ffffff", E: "#2a2228", I: "#6a5a4a", M: "#b8706a", G: "#c9c9cc",
      B: "#5e78a8", N: "#4f668e", H: "#fce896", V: "#dfeef6", U: "#a9c4d4" })

const S = 96, F = S - 2, cx = 47
const ell = (x, y, x0, y0, rx, ry) => ((x - x0) / rx) ** 2 + ((y - y0) / ry) ** 2 <= 1
const face = (x, y) => ell(x, y, cx, 43, 18, 21)

sprite("_p_busto", { w: F, h: F, mx: true },
  ellipse(cx, F + 22, 46, 34, "c"),                                             // tunic: shoulders full width
  poly([cx - 26, 40, cx - 30, 70, cx - 44, 86, cx - 46, 94, cx, 94, cx, 40], "c"),   // the veil falling on the shoulders
  ellipse(cx, 38, 26, 27, "c"),                                                 // veil over the head
  ellipse(cx, 41, 21, 24, "a"),                                                 // the veil's inner shadow round the face (one tone darker than the first prototype)
  ellipse(cx, 66, 12, 8, "o"), ellipse(cx, 60, 17, 9, "o"),                    // wimple, rounded: under the chin, over the neck
  ellipse(cx, 43, 18, 21, "3"),                                                 // face, 36 px like the approved ones
  line(cx - 7, 49, cx - 8, 55, "2"),                                            // fold beside the mouth
  hline(cx - 3, 54, 6, "M"), px(cx - 4, 53, "M"))                               // a small patient smile

sprite("_p_aureola", { w: F, h: F, outline: "K" },
  circ(cx, 34, 35, "f"), circ(cx, 34, 33, "g"), circ(cx, 34, 29, "H"),
  recolor({ H: "h" }, (x, y) => x + y > cx + 34 + 22))

var PAZIENZA_CORPO
const CORPO = PAZIENZA_CORPO = [
  stamp("_p_busto", 0, 0),
  // face: far side, nose, forehead line, cheeks
  recolor({ 3: "2" }, (x, y) => face(x, y) && x > cx + 11),
  vline(cx + 1, 44, 6, "2"), px(cx - 1, 50, "2"), px(cx + 3, 50, "2"), vline(cx - 1, 44, 3, "4"),
  hline(cx - 6, 30, 12, "2"),
  hline(cx - 14, 48, 3, "M"), hline(cx + 12, 48, 3, "M"),                     // faint blush
  // veil: far side darker, folds falling from the head, a lit edge on the left
  recolor({ c: "b", b: "a" }, (x, y) => x > cx + 14 && !face(x, y)),
  (c) => { for (const x of [cx - 36, cx - 28, cx + 28, cx + 36]) c.recolor({ c: "b", b: "a" }, (xx, y) => xx === x && y > 66) },
  recolor({ c: "d" }, (x, y) => { const d = Math.hypot((x - cx) / 26, (y - 38) / 27); return d > 0.9 && d < 1 && x < cx - 6 && y < 40 }),
  // wimple: a soft shadow under the chin and on the far side
  recolor({ o: "#bdbccb" }, (x, y) => y < 63 || x > cx + 8),   // level 2 of the tests (was "n", too close to the skin)

  // --- hourglass, bottom right: wooden caps and posts, glass bulbs, sand falling
  rect(68, 60, 22, 4, "j"), rect(68, 89, 22, 4, "j"), hline(68, 60, 22, "k"), hline(68, 92, 22, "i"),
  vline(69, 64, 25, "j"), vline(88, 64, 25, "i"),                                     // posts
  poly([71, 64, 87, 64, 81, 76, 77, 76], "V"), poly([77, 77, 81, 77, 87, 89, 71, 89], "V"),   // glass bulbs
  poly([73, 68, 85, 68, 80, 75, 78, 75], "g"),                                         // sand left above
  vline(79, 76, 10, "h"),                                                              // the falling stream
  poly([72, 89, 79, 84, 86, 89], "g"), px(79, 84, "h"),                                // the pile below
  vline(72, 65, 3, "X"), vline(73, 79, 3, "X"),                                        // glints on the glass
  recolor({ V: "U" }, (x, y) => x > 82),                                               // the far side of the glass
  ]

// One animated portrait per emotion (occhi.px.js); the card uses spazientito. Eyes at the fixed place of
// the 96 px generator (y 41, brows 36: one row lower than the first prototype), for the app overlay.
for (const [emo, seq] of Object.entries(EMOZIONI)) {
  anim(`_p_fig_${emo}`, { w: F, h: F, outline: "K", frames: seq.length, fps: 12 },
    ...CORPO, (c) => occhi(c, cx, seq[c.frame], { y: 41, browY: 36, pelle: (x) => (x > cx + 11 ? "2" : "3"), ciglio: "G" }))
  sprite(`pazienza_${emo}`, { w: S, h: S },
    rect(0, 0, S, S, "B"), rect(0, 72, S, S, "N"),
    stamp("_p_aureola", 0, 0),
    layer("ombra", { shade: true }, stamp(`_p_fig_${emo}`, 2, 2)),
    stamp(`_p_fig_${emo}`, 0, 0))
}
sprite("pazienza_96", { w: S, h: S }, stamp("pazienza_spazientito", 0, 0))

// Silver frame of the special cards: still (no animation), three tones, plates with a blue stone.
sprite("cornice_argento_96", { w: S, h: S }, (c) => {
  for (let i = 0; i < 4; i++) for (let k = i; k < S - i; k++) {
    const col = i === 0 ? "#5c626e" : i === 3 ? "#4a505a" : "#c4cad4"
    c.px(k, i, i === 1 ? "#eef2f8" : col); c.px(i, k, i === 1 ? "#eef2f8" : col)
    c.px(k, S - 1 - i, i === 1 ? "#9aa2b0" : col); c.px(S - 1 - i, k, i === 1 ? "#9aa2b0" : col)
  }
  for (const [x0, y0] of [[0, 0], [S - 11, 0], [S - 11, S - 11], [0, S - 11]]) {
    for (let y = 0; y < 11; y++) for (let x = 0; x < 11; x++)
      c.px(x0 + x, y0 + y, x === 0 || y === 0 ? "#eef2f8" : x === 10 || y === 10 ? "#5c626e" : "#b4bac6")
    c.rect(x0 + 3, y0 + 3, 5, 5, "#3a8ad0"); c.rect(x0 + 3, y0 + 3, 2, 2, "#a8d8ff"); c.rect(x0 + 6, y0 + 6, 2, 2, "#1e4e88")
  }
})
sprite("pazienza_con_argento", { w: S, h: S }, stamp("pazienza_96", 0, 0), stamp("cornice_argento_96", 0, 0))
}
// for the app: the portrait without eyes (the overlay draws them), and a still one with the eyes open
{
  sprite("_pz_fig_base", { w: 94, h: 94, outline: "K" }, ...PAZIENZA_CORPO)
  sprite("pazienza96_base", { w: 96, h: 96 }, rect(0, 0, 96, 96, "B"), rect(0, 72, 96, 24, "N"), stamp("_p_aureola", 0, 0),
    layer("ombra", { shade: true }, stamp("_pz_fig_base", 2, 2)), stamp("_pz_fig_base", 0, 0))
}
