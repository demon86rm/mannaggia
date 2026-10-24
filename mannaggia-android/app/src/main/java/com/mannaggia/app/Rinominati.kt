package com.mannaggia.app

/**
 * Saints renamed in santi.txt after release, old name → new name. The album and the
 * favourites are keyed by name, so their files may still hold an old name: they map it
 * on load, and the card keeps its discovery date.
 *
 * 2.0.1: Wikidata gives some Italian labels in English or French ("Saint Amun"), and
 * the app said "San Saint Amun". tools/genera_santi.py now drops that title
 * (`--correggi` prints these pairs).
 */
object Rinominati {

    private val RINOMINATI = mapOf(
        "Beato Saint Richard Martin" to "Beato Richard Martin",
        "San Saint Amun" to "Sant'Amun",
        "San Saint Antide" to "Sant'Antide",
        "San Saint Baglan" to "San Baglan",
        "San Saint Bashnouna" to "San Bashnouna",
        "San Saint Bernulf" to "San Bernulf",
        "San Saint Calupan" to "San Calupan",
        "San Saint Conven" to "San Conven",
        "San Saint Croidan" to "San Croidan",
        "San Saint Derien" to "San Derien",
        "San Saint Doetval" to "San Doetval",
        "San Saint Doha" to "San Doha",
        "San Saint Eigrad" to "Sant'Eigrad",
        "San Saint Elouan" to "Sant'Elouan",
        "San Saint Fachanan" to "San Fachanan",
        "San Saint Frambold" to "San Frambold",
        "San Saint Gilduin" to "San Gilduin",
        "San Saint Herbert" to "San Herbert",
        "San Saint Houardon" to "San Houardon",
        "San Saint Ilar" to "Sant'Ilar",
        "San Saint Isan" to "Sant'Isan",
        "San Saint Loubouer" to "San Loubouer",
        "San Saint Maden" to "San Maden",
        "San Saint Momble" to "San Momble",
        "San Saint Munn" to "San Munn",
        "San Saint Nonna" to "San Nonna",
        "San Saint Ratian" to "San Ratian",
        "San Saint Roland" to "San Roland",
        "San Saint Rubin" to "San Rubin",
        "San Saint Rufinien" to "San Rufinien",
        "San Saint Setni" to "San Setni",
        "San Saint Stamp" to "Santo Stamp",
        "San Saint Tadec" to "San Tadec",
        "San Saint Tariec" to "San Tariec",
        "San Saint Thivisiau" to "San Thivisiau",
        "San Saint Trillo" to "San Trillo",
        "San Saint Turiau" to "San Turiau",
        "San Saint Urfol" to "Sant'Urfol",
        "San Saint Vulfric" to "San Vulfric",
        "Santa Saint Derchairthinn" to "Santa Derchairthinn",
        "Santa Saint Eigen" to "Sant'Eigen",
        "Santa Saint Llechid" to "Santa Llechid",
        "Santa Saint Rais" to "Santa Rais",
        "Santa Saint Rhian" to "Santa Rhian",
        "Santa Sainte Grimonie" to "Santa Grimonie",
        "Santa Sainte Ode" to "Sant'Ode",
        "Santa Sainte Soline" to "Santa Soline",
        "Santa Sainte Ulphe" to "Sant'Ulphe",
    )

    /** The current name of [saint] (itself if it was never renamed). */
    fun attuale(saint: String): String = RINOMINATI[saint] ?: saint
}
