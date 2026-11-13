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

function occhi(c, cx, f, { y = 39, browY = 33, iride = "I", pelle = () => "3", ciglio = "6", ombra = "2", forma = "" } = {}) {
  // forma "mono": an eye without the lid crease, one row less of white and the outer corner a little higher
  const [dx, dy] = f.g
  for (const [ex, lato] of [[cx - 11, 0], [cx + 10, 1]]) {
    // brow: two rows, the outer end longer; "worry" lifts the inner half one row
    const by = browY + f.brow[lato], out = lato ? 1 : -1
    for (let i = 0; i <= 6; i++) {
      const x = ex + out * (i - 1), inner = i <= 2
      const yy = by + (f.worry && inner ? -1 : 0)
      c.px(x, yy + 1, ciglio); if (i <= 5) c.px(x, yy, ciglio)
    }
    if (f.lid === "x") {                                   // closed: the lashes' curve
      c.hline(ex - 3, y + 2, 7, "E"); c.px(ex - 4, y + 1, "E"); c.px(ex + 4, y + 1, "E")
      continue
    }
    let top = { w: y - 1, n: y, d: y + 1, h: y + 2 }[f.lid]     // first visible row of the white
    if (forma === "mono") top = Math.min(top + 1, y + 2)
    for (let yy = top; yy <= y + 3; yy++) for (let x = ex - 3; x <= ex + 3; x++) {
      const ix = x - (ex - 1 + dx), iy = yy - (y + dy)
      const inIris = ix >= 0 && ix < 3 && iy >= 0 && iy < 4
      let col = inIris ? iride : "W"
      if (inIris && ix === 1 && (f.small ? iy === 1 : iy === 1 || iy === 2)) col = "E"     // pupil
      if (inIris && ix === 0 && yy === Math.max(top, y + dy)) col = "W"                   // glint, top-left
      c.px(x, yy, col)
    }
    c.hline(ex - 4, top - 1, 9, "E")                       // upper lid
    if (forma === "mono") c.px(ex + out * 5, top - 2, "E")     // its outer end, lifted
    c.hline(ex - 2, y + 4, 5, ombra)                       // lower lash
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
