// Every nose x mouth combination, plain and with "naso largo" + "labbra piene", on light and dark skin
include("libreria96.px.js")
include("parti96.px.js")
for (const [pk, pelle] of [["chiara", "#eaba92"], ["scura", "#5a3a28"]])
  for (const [fk, f] of [["normale", {}], ["largo", { naso: "largo", labbra: "piene" }]])
    for (let n = 0; n < 3; n++) for (let b = 0; b < 3; b++)
      ritratto96(`comb_${pk}_${fk}_${n}${b}`, { capelli: "corti", chioma: "#3a2a22", abito: "tunica", veste: "#3a5a9a", sfondo: "#5e78a8",
        pelle, iride: "#5a4636", naso_v: n, bocca: b, ...f })
