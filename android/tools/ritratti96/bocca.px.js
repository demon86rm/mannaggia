// The mouth of the 96 px portraits (approved 2026-11-18), drawn per frame like the eyes: the portraits
// WITHOUT the mouth leave its zone in plain skin, the app draws it (Bocca.kt, which reads BOCCHE from
// bocche.txt, written by occhi96.py from this file: one source).
//
// A form is a list of rows from y 53 of the figure, columns dx -7..7 (15 characters, centred on cx):
//   L the mouth's line, l the lip, h the lip's light, s skin shadow, K the inside of an open mouth, "." skin.
// The bearded forms (B…) start with null: row 53 is the moustache; their zone is the opening barba6()
// leaves under it (rows 54-56), and an open mouth also covers the beard around it.
//
// At rest each saint has the form of their family (esporta.py, bocca_f): women W0-W2, old A0-A1, men M0-M2,
// bearded B0-B2, old bearded B3/B2. The emotions (EMOZIONI in occhi.px.js) give each step a mouth code m:
// "" rest, "s" a sly half smile, "o" agape, "c" ajar, "u" a small "o" (a sigh), "t" twisted, "p" a pout.
var BOCCHE = {
  M0: ["...............", "...LLLLLLLLL...", ".....lhlll.....", "......sss......"],
  M1: ["..........LL...", "...LLLLLLL.....", ".....lhll......", "......ss......."],
  M2: ["...............", ".....LLLLL.....", "....LlhlllL....", ".....lllll.....", "......sss......"],
  A0: ["s.............s", ".s..LLLLLLL..s.", "...L.......L...", "......sss......"],
  A1: ["...............", "...LLLLLLLLL...", ".....lllll.....", "...............", ".....sssss....."],
  W0: [".....ll.ll.....", "....LLLLLLL....", "....lhhllll....", ".....lllll.....", "......sss......"],
  W1: ["...L.......L...", "....LLLLLLL....", ".....lhlll.....", "......sss......"],
  W2: ["......lll......", ".....LLLLL.....", ".....lhhll.....", "......lll......", ".......s......."],
  B0: [null, "...............", "....LLLLLLL....", ".....lhlll....."],
  B1: [null, "...............", "....LLLLLLL....", "....lhhllll....", ".....sssss....."],
  B2: [null, "..........L....", "....LLLLLL.....", ".....lhll......"],
  B3: [null, "...............", "....LLLLLLL....", "......lll......"],
  o: [".....lllll.....", "....lKKKKKl....", "....lKKKKKl....", "....lKKKKKl....", ".....lhlll.....", "......sss......"],
  c: ["...............", "....LLLLLLL....", ".....KKKKK.....", ".....lhlll.....", "......sss......"],
  u: ["...............", "......lll......", ".....lKKKl.....", "......lhl......", ".......s......."],
  t: ["...............", "........LLLLL..", ".....LLL.......", "......ss......."],
  p: ["...............", ".....LLLLL.....", "....L.lll.L....", "......sss......"],
  Bo: [null, ".....lllll.....", "....lKKKKKl....", "....lKKKKKl....", ".....lhlll....."],
  Bc: [null, "...............", "....LLLLLLL....", ".....KKKKK.....", ".....lhlll....."],
  Bu: [null, "......lll......", ".....lKKKl.....", "......lhl......"],
  Bt: [null, "...............", "......LLLLL....", ".....L........."],
  Bp: [null, "...............", ".....LLLLL.....", "......lll......"],
}
// the form of a step: the saint's own at rest, else the emotion's (its bearded version under a beard)
var formaBocca = (riposo, m, barba) => !m ? riposo : m === "s" ? (barba ? "B2" : "M1") : barba ? "B" + m : m
// the colours: the skin's shadow, the mouth's line, the lip and its light (a woman's a livelier red), the inside
var coloriBocca = (SK, donna) => {
  const L = [mixc(SK[0], "#7a2a30", 0.5), mixc(SK[2], "#c84a4a", donna ? 0.5 : 0.25), mixc(SK[4], "#e87878", donna ? 0.45 : 0.2)]
  return { s: SK[2], L: L[0], l: L[1], h: L[2], K: mixc(L[0], "#000000", 0.45) }
}
// draws form [f] on canvas [c] with its axis at [cx], rows from [y0] (53 in the figure)
function bocca(c, cx, f, col, y0 = 53) {
  ;(BOCCHE[f] || []).forEach((row, i) => { if (row) [...row].forEach((ch, j) => { if (col[ch]) c.px(cx + j - 7, y0 + i, col[ch]) }) })
}
