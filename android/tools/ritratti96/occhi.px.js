// Eyes and brows for the 96 px portraits, drawn per frame and NOT mirrored, so both look the same way
// (iris and pupil centred, the glint top-left in both: the light's side). Eye centres cx-11 and cx+10
// (the mirror of a 94 px figure, axis 46.5); white rows y..y+3 with the lid open.
//
// A frame is { g: [dx, dy], lid, brow: [left, right], worry, small }:
//   g      gaze: dx -1..1, dy -2..1 (the iris is clipped by the lids, so -2 hides it under the top lid)
//   lid    "n" open, "w" wide open (one row more), "h" half-closed, "d" lowered (looking down), "x" closed
//   brow   rows up (negative) or down for the left and right brow; worry: the inner ends raised
//   small  a small pupil (surprise)

var fr = (o = {}) => ({ g: [0, 0], lid: "n", brow: [0, 0], worry: false, small: false, ...o })
var rep = (n, o) => Array.from({ length: n }, () => fr(o))
var blink = (base = {}) => [fr({ ...base, lid: "h" }), fr({ ...base, lid: "x" }), fr({ ...base, lid: "x" }), fr({ ...base, lid: "h" })]

// (var, not const: this file is included by every portrait, so it may be loaded more than once.)
// Six emotions, 48 steps at 12 fps = 4 s each, two loops of the frames.
var EMOZIONI = {
  // the classic: still, a blink, a look left and right
  sinistra_destra: [...rep(16), ...blink(), ...rep(8), ...rep(6, { g: [-1, 0] }), ...rep(2), ...rep(6, { g: [1, 0] }), ...rep(6)],
  // sly: half-closed, a smug sideways glance with one brow up, back
  scaltro: [...rep(12, { lid: "h" }), ...rep(14, { lid: "h", g: [1, 0], brow: [0, -1] }), ...rep(8, { lid: "h" }),
            ...blink({ lid: "h" }), ...rep(10, { lid: "h" })],
  // eyes to heaven, "Oh Gesù": the iris up under the lid, brows raised and worried
  cielo: [...rep(10), ...rep(2, { g: [0, -1], worry: true }), ...rep(18, { g: [0, -2], brow: [-1, -1], worry: true }),
          ...rep(2, { g: [0, -1], worry: true }), ...rep(6), ...blink(), ...rep(6)],
  // disbelief: eyes wide, pupils small, brows high, a quick blink, wide again
  incredulo: [...rep(8), ...rep(16, { lid: "w", small: true, brow: [-2, -2] }), fr({ lid: "x", brow: [-2, -2] }),
              ...rep(9, { lid: "w", small: true, brow: [-2, -2] }), ...rep(10), ...blink()],
  // looking down at a smartphone: lids lowered, iris low; a glance up and back down
  smartphone: [...rep(18, { lid: "d", g: [0, 1] }), ...rep(5, { g: [0, 0] }), ...rep(14, { lid: "d", g: [0, 1] }),
               ...blink({ lid: "d", g: [0, 1] }), ...rep(7, { lid: "d", g: [0, 1] })],
  // fed up, the eye roll: left, up-left, up, up-right, right, then a sigh with half-closed lids
  spazientito: [...rep(10), ...rep(2, { g: [-1, 0] }), ...rep(2, { g: [-1, -1] }), ...rep(3, { g: [0, -2] }),
                ...rep(2, { g: [1, -1] }), ...rep(2, { g: [1, 0] }), ...rep(12, { lid: "h", brow: [1, 1] }), ...rep(11), ...blink()],
}

// The "B" eyes (approved on Santa Giovanna, 2026-11-13), animated: arched tapered brows (three rows for
// an old man, "folte"), the lid's crease, a three-tone iris with the pupil and a glint, the lid's shadow on
// the white's top row, rounded lower corners, a lash at the outer end. Rows from the eye's row y (41 in
// the figure): crease y-3, lid y-1, white y..y+3, lower lid y+4; brows from browY (36).
// Lids: "n" open; "w" wide, one row more; "d" lowered, "h" half-closed (the upper lid comes down over the
// white, the skin above it in the crease tone); "x" closed, an arc of lashes.
// pelle(ex): the crease and lower-lid tone of that eye's side; ciglio: the brows; coda: their outer tail
// (ciglio mixed with the skin); iride: the iris' middle tone (hex), its dark and light tones mixed from it.
// forma "mono": no crease (the white keeps all its rows: the user). occhiali: no outer lash (it would land
// on the frame).
// The brows never go above y 33, the top of the eye zone (incredulo raises them two rows).
var _mixO = (a, b, t) => {
  if (!/^#[0-9a-f]{6}$/i.test(a)) return a
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)), x = p(a), y = p(b)
  return "#" + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, "0")).join("")
}
var LID_B = "#2a1a18", OMBRA_B = "#d9cfd2"
function occhi(c, cx, f, { y = 41, browY = 36, iride = "#5a4636", pelle = () => "3", ciglio = "6", coda = null, folte = false, forma = "", occhiali = false } = {}) {
  const [dx, dy] = f.g, mono = forma === "mono"
  const IR = [_mixO(iride, "#000000", 0.45), iride, _mixO(iride, "#ffffff", 0.3)]
  const tail = coda || ciglio
  // the brows' rows for i = 0 (inner) .. 6 (outer), relative to browY
  const BR = folte ? [[-1, 0, 1], [-1, 0, 1], [-2, -1, 0], [-2, -1, 0], [-2, -1, 0], [-1, 0], [0, 1]]
    : [[0, 1], [0, 1], [-1, 0], [-1, 0], [-1, 0], [0], [1]]
  for (const [ex, lato] of [[cx - 11, 0], [cx + 10, 1]]) {
    const out = lato ? 1 : -1, sk = pelle(ex)
    const lidRow = { w: y - 2, n: y - 1, d: y, h: y + 1, x: y + 1 }[f.lid]
    // the crease, and the lowered lid's skin over the white
    if (!mono) c.hline(ex - 3, y - 3, 7, sk)
    for (let yy = y - 1; yy < lidRow; yy++) c.hline(ex - 3, yy, 7, sk)
    // the brows: offset, the inner half raised when worried, never above the eye zone
    const off = Math.max(f.brow[lato], 33 - (browY + (folte ? -2 : -1) - (f.worry ? 1 : 0)))
    BR.forEach((rows, i) => rows.forEach((r, k) => {
      const yy = browY + off + r - (f.worry && i <= 2 ? 1 : 0)
      c.px(ex + out * (i - 1), yy, i >= 5 || (folte && k === rows.length - 1) ? tail : ciglio)
    }))
    if (f.lid === "x") {                                             // closed: an arc of lashes, the lash at the end
      c.hline(ex - 2, y + 2, 5, LID_B); c.px(ex - 3, y + 1, LID_B); c.px(ex + 3, y + 1, LID_B)
      c.px(ex + out * 4, y, LID_B)
      c.hline(ex - 2, y + 4, 5, sk)
      continue
    }
    const top = lidRow + 1
    for (let yy = top; yy <= y + 3; yy++) for (let x = ex - 3; x <= ex + 3; x++) {
      if (yy === y + 3 && Math.abs(x - ex) === 3) continue              // rounded lower corners
      const ix = x - (ex + dx), iy = yy - (y + dy)
      let col = yy === top ? OMBRA_B : "W"
      if (Math.abs(ix) <= 1 && iy >= 0 && iy <= 3) {
        col = iy <= 1 ? IR[0] : iy === 2 ? IR[1] : IR[2]
        if (ix === 0 && (f.small ? iy === 1 : iy === 1 || iy === 2)) col = "E"   // the pupil
        if (ix === -1 && yy === Math.max(top, y + dy)) col = "X"                 // the glint, top-left
      }
      c.px(x, yy, col)
    }
    c.hline(ex - 4, lidRow, 9, LID_B); c.px(ex + out * 4, lidRow + 1, LID_B)     // the lid, its outer corner
    if (!occhiali) c.px(ex + out * 5, lidRow - 1, LID_B)                       // the lash
    c.hline(ex - 2, y + 4, 5, sk)                                              // the lower lid
  }
}

// Glasses over the animated eyes (San Deploy, Kolbe, Escrivá): drawn after occhi() at every frame, so
// the eyes move and blink behind the lenses. A thin frame round each eye, the bridge, the temples to
// the ears; the lenses clear, a glint on the upper-left of each. Same places as occhi(): eyes at cx-11, cx+10.
function occhiali(c, cx, { y = 41, montatura = "#7c6c78", riflesso = "#ffffff", su = 0 } = {}) {
  for (const ex of [cx - 11, cx + 10]) {      // su: raises the top bar of the frame by that many rows
    c.hline(ex - 5, y - 2 - su, 11, montatura); c.hline(ex - 5, y + 5, 11, montatura)
    c.vline(ex - 5, y - 1 - su, 6 + su, montatura); c.vline(ex + 5, y - 1 - su, 6 + su, montatura)
    c.px(ex - 4, y - 1, riflesso)
  }
  c.hline(cx - 5, y, 9, montatura)                          // bridge over the nose
  c.hline(cx - 19, y - 1, 3, montatura); c.hline(cx + 16, y - 1, 3, montatura)   // temples, to the ears
}
