// Prototypes at 96 px: the 7 special cards (S1-S7, SPECIALI of avatar.py), San Giovanni Battista's secret
// back ("decollato") and the glasses over the animated eyes (San Deploy, Kolbe, Escrivá).
include("libreria96.px.js")
include("parti96.px.js")
include("tratti96.data.js")
{ // own scope
const { S, F, cx } = G96
const NERO = "#1e1a20", ORO = rampa("#e2b646"), ARG = rampa("#b6bcc4", { shift: 12 }), LEG = rampa("#7a4e2e"), ROSSO = rampa("#c8303a")

Object.assign(ATTRIBUTI96, {
  striscione: () => [rect(68, 30, 3, 64, LEG[2]), rect(90, 30, 3, 64, LEG[2]), rect(68, 34, 25, 17, "#f4f0e8"),
    recolor({ "#f4f0e8": "#d8d2c8" }, (x, y) => y > 48), text(70, 36, "SANTO\nSUBITO", ROSSO[2])],         // "SANTO SUBITO"
  ferro_cavallo: () => [ring(80, 78, 10, ARG[1]), ring(80, 78, 9, ARG[2]), ring(80, 78, 8, ARG[2]), ring(80, 78, 7, ARG[1]),
    rect(70, 64, 21, 14, "_"), rect(70, 66, 3, 12, ARG[2]), rect(88, 66, 3, 12, ARG[2]),
    ...[[72, 72], [89, 72], [74, 84], [86, 84]].map(([x, y]) => px(x, y, NERO))],                            // open upwards: luck
  quadrifoglio: () => { const g = rampa("#4a9a3a"); return [line(80, 92, 79, 74, g[1], 2),
    ...[[76, 66], [84, 66], [76, 74], [84, 74]].map(([x, y]) => circ(x, y, 4, g[2])), ...[[75, 65], [83, 65]].map(([x, y]) => px(x, y, g[3])), px(80, 70, g[0])] },
  calendario_mano: () => [rect(68, 56, 22, 30, "#f4f0e8"), rect(68, 56, 22, 7, ROSSO[2]), px(72, 55, NERO), px(85, 55, NERO),
    text(74, 66, "17", ROSSO[2], { scale: 2 }), ...[78, 81, 84].flatMap((y) => [70, 74, 78, 82, 86].map((x) => px(x, y, "#9a9aa4"))),
    poly([84, 86, 90, 80, 90, 86], "#d8d2c8")],                                                               // a wall calendar, Friday 17
  server_fuoco: () => { const f = ["#f8e070", "#f8a030", "#e05a20"]
    return [rect(66, 58, 26, 36, "#3a3e48"), ...[64, 72, 80, 88].map((y) => hline(67, y, 24, "#20232a")),
      ...[60, 68, 76, 84].flatMap((y) => [px(69, y + 1, "#5ae05a"), px(71, y + 1, "#e05a5a"), hline(76, y + 1, 12, "#2a2e36")]),
      ...[[68, 44], [75, 38], [82, 42], [88, 46]].map(([x, y]) => poly([x - 3, 58, x, y, x + 4, 58], f[2])),
      ...[[70, 48], [77, 44], [84, 48]].map(([x, y]) => poly([x - 2, 58, x, y, x + 3, 58], f[1])), ...[73, 80, 86].map((x) => poly([x - 1, 58, x, 52, x + 2, 58], f[0]))] },
  terminale: () => [rect(64, 64, 28, 19, "#282a32"), rect(66, 66, 24, 15, "#101614"), hline(68, 69, 3, "#5ae05a"), px(72, 69, "#5ae05a"),
    hline(68, 73, 10, "#3aa04a"), hline(68, 76, 6, "#3aa04a"), rect(70, 76, 2, 1, "#5ae05a"), rect(60, 83, 36, 5, "#7a7e88"), hline(60, 83, 36, "#a8acb4")],   // the laptop, "$ _"
  fulmine: () => [poly([84, 26, 74, 52, 80, 52, 72, 80, 90, 46, 83, 46, 90, 26], "#f8d830"), line(84, 27, 76, 50, "#fff4a0")],
  sfere: () => [...[[74, 84], [86, 84]].flatMap(([x, y]) => [circ(x, y, 6, "#8a8aa0"), circ(x - 2, y - 2, 2, "#c8c8dc"), px(x - 3, y - 3, "#ffffff")])],
  clessidra: () => [rect(68, 60, 22, 4, LEG[1]), rect(68, 89, 22, 4, LEG[1]), hline(68, 60, 22, LEG[3]), hline(68, 92, 22, LEG[0]),
    vline(69, 64, 25, LEG[1]), vline(88, 64, 25, LEG[0]), poly([71, 64, 87, 64, 81, 76, 77, 76], "#dfeef6"), poly([77, 77, 81, 77, 87, 89, 71, 89], "#dfeef6"),
    poly([73, 68, 85, 68, 80, 75, 78, 75], ORO[2]), vline(79, 76, 10, ORO[3]), poly([72, 89, 79, 84, 86, 89], ORO[2]), px(79, 84, ORO[3]),
    vline(72, 65, 3, "#ffffff"), vline(73, 79, 3, "#ffffff"), recolor({ "#dfeef6": "#a9c4d4" }, (x, y) => x > 82)],   // Santa Pazienza's hourglass
})
EXTRA96.cuffie = () => ({ testa: [clip((x, y) => y <= 30, ring(cx, 32, 22, "#2a2c34"), ring(cx, 32, 21, "#3a3e48")),
  rect(cx - 25, 37, 6, 11, "#2a2c34"), rect(cx + 20, 37, 6, 11, "#2a2c34"), vline(cx - 24, 38, 9, "#5a5e68"), vline(cx + 21, 38, 9, "#4a4e58")] })   // headphones

// the 7 specials: traits and colours of SPECIALI in avatar.py
const SPEC = {
  s1_santo_subito: { eta: "anziano", capelli: "corti", chioma: "#e8e4dc", copricapo: "zucchetto_bianco", abito: "papa", veste: "#f0eee8",
    attributi: ["striscione"], pelle: "#f6d0b0", sfondo: "#b2944a", iride: "#4c6a8a", viso: 1, naso_v: 1, bocca: 2 },
  s2_san_culo: { eta: "giovane", capelli: "ricci", chioma: "#d6ac5c", abito: "tunica", tunica_v: 1, taglio: 2, veste: "#3c5aaa",
    attributi: ["ferro_cavallo", "quadrifoglio"], pelle: "#eaba92", sfondo: "#548c82", iride: "#4c6a8a", guance: true, bocca: 2, naso_v: 2 },
  s3_san_calendario: { capelli: "corti", chioma: "#684228", barba: "corta", taglio: 1, abito: "tunica", veste: "#96323c",
    attributi: ["calendario_mano"], pelle: "#d49c70", sfondo: "#78609a", iride: "#5a4636", viso: 2 },
  s4_san_deploy: { capelli: "corti", chioma: "#684228", barba: "corta", taglio: 3, abito: "moderno", veste: "#323c50", extra: ["cuffie"], occhiali: true,
    attributi: ["server_fuoco"], pelle: "#eaba92", sfondo: "#465a78", iride: "#5a4636", naso_v: 1 },
  s5_san_sudo: { eta: "giovane", capelli: "corti", chioma: "#684228", copricapo: "cappuccio", abito: "felpa", veste: "#555a66",
    attributi: ["terminale"], pelle: "#f6d0b0", sfondo: "#2a3a30", iride: "#5a6a3e", guance: true },
  s6_santa_pazienza: { donna: true, eta: "anziano", copricapo: "velo", velo: "#6e78a0", abito: "suora", veste: "#6e78a0",
    attributi: ["clessidra"], pelle: "#e2b08c", sfondo: "#5e78a8", iride: "#6a5a4a", bocca: 2 },
  s7_santa_cunegonda: { donna: true, copricapo: "velo", velo: "#3c3c46", abito: "suora", veste: "#3c3c46",
    attributi: ["fulmine", "sfere"], pelle: "#eaba92", sfondo: "#5a4a6a", iride: "#4c6a8a", guance: true, viso: 1 },
}
for (const [k, d] of Object.entries(SPEC)) { if (k === "s5_san_sudo") continue; ritratto96(`spec_${k}`, { ...d }); ritratto96(`specanim_${k}`, { ...d }, { seq: EMOZIONI.sinistra_destra }) }

// for the app: S1..S7 without eyes (S5 comes from felpe96b.px.js, S6 from pazienza96px.px.js: pazienza96_base)
Object.keys(SPEC).forEach((k, i) => { if (k !== "s5_san_sudo" && k !== "s6_santa_pazienza") ritratto96(`s${i + 1}`, { ...SPEC[k] }, { con_occhi: false }) })

// glasses over the animated eyes: San Deploy, and the two FAMOSI saints with glasses
const T = (n) => TRATTI.find((t) => t.n === n)
const OCCHIALI = { deploy: { ...SPEC.s4_san_deploy }, kolbe: { ...T("San Massimiliano Maria Kolbe"), occhiali: true },
  escriva: { ...T("San Josemaría Escrivá de Balaguer"), occhiali: true } }
for (const [k, d] of Object.entries(OCCHIALI)) for (const [emo, seq] of Object.entries(EMOZIONI)) ritratto96(`occh_${k}_${emo}`, { ...d }, { seq })
}
include("battista96.px.js")
include("felpe96b.px.js")      // San Sudo: the approved hoodie, replaces spec_s5_san_sudo
