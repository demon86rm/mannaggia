// The parchment of the card (home and album detail), 112 x 170 px, always light: the app scales it up
// without smoothing and lays its texts and the 96 px portrait on it (Pergamena.kt). From the proof
// carta96.px.js (2026-11-13): label band on top, the portrait at (8, 28) inside a double ink rule, number
// and name below.
//   node ../pxl/bin/pxl.js build pergamena96.px.js --no-preview --out ~/mannaggia-cache/pergamena96
//   cp ~/mannaggia-cache/pergamena96/sprites/pergamena.png ../../app/src/main/res/drawable-nodpi/pergamena.png
shades("mnpq", "#e8d4a8", { shift: 14, sat: 0.9 })   // parchment: m dark .. q light
pal({ u: "#3b2b26", v: "#9a2b25", z: "#5a3a26" })
{
const CW = 112, CH = 170, PX = 8, PY = 28          // card size, portrait position
// smooth tone variation (a few broad waves, no grain) and the aged, darker margin
const tone = (x, y) => 0.5 * Math.sin(x * 0.09 + y * 0.05) + 0.3 * Math.sin(-x * 0.05 + y * 0.11 + 1.7) + 0.2 * Math.sin(x * 0.17 - y * 0.08 + 0.4)
const edge = (x, y) => Math.min(x, y, CW - 1 - x, CH - 1 - y)
// deckled edge: the outer pixel ring bites in here and there (a fixed pattern, not random grain)
const torn = (x, y) => edge(x, y) < 1 + Math.round(1.2 + Math.sin(x * 0.7) * Math.sin(y * 0.53) * 1.4 + Math.sin((x + y) * 0.31))
sprite("pergamena", { w: CW, h: CH }, (c) => {
  for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
    if (torn(x, y) && edge(x, y) < 2) continue                            // torn margin: transparent
    const e = edge(x, y)
    const v = 0.62 + 0.1 * tone(x, y) - (e < 9 ? (9 - e) / 9 * 0.45 : 0)  // darker toward the edges
    const k = v + (((x * 3 + y * 5) % 4) / 4 - 0.375) * 0.03             // a thin dithered seam between bands
    c.px(x, y, k > 0.66 ? "q" : k > 0.5 ? "p" : k > 0.3 ? "n" : "m")
  }
},
  // two old ring stains, one ramp step darker, broken like real ones
  clip((x, y) => (x * 13 + y * 7) % 11 > 2, ring(88, 146, 9, "n"), ring(21, 156, 6, "n")),
  // double ink rule around the portrait, small red flourishes at the corners
  box(PX - 2, PY - 2, 96 + 4, 96 + 4, "u"), box(PX - 4, PY - 4, 96 + 8, 96 + 8, "z"),
  (c) => { for (const [x, y] of [[PX - 4, PY - 4], [PX + 99, PY - 4], [PX - 4, PY + 99], [PX + 99, PY + 99]]) {
    c.rect(x - 1, y - 1, 3, 3, "v"); c.px(x, y, "q") } })
}
