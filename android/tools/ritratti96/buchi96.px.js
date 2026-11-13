include("libreria96.px.js")
include("parti96.px.js")
include("tratti96.data.js")
// check for holes: magenta background, no halo shadow matters
for (const d of TRATTI) ritratto96(`p_${d.id}`, { ...d, sfondo: "#ff00ff" }, { con_occhi: false })
