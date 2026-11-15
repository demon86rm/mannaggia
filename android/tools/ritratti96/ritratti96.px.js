// The 96 px portraits of the saints in tratti96.data.js (esporta.py), one sprite per saint named
// p_<file id> (the sha1 of the name, as avatar.py). Without eyes: the app draws them (occhi.px.js).
// CON_OCCHI = true draws them open, for the previews.
include("libreria96.px.js")
include("parti96.px.js")
include("tratti96.data.js")
var CON_OCCHI = typeof CON_OCCHI === "undefined" ? false : CON_OCCHI
for (const d of TRATTI) ritratto96(`p_${d.id}`, d, { con_occhi: CON_OCCHI })
