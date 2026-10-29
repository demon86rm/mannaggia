package com.mannaggia.app

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Invocation formulas: variants of "Mannaggia San X!", chosen in Options (or one at random
 * among those available) and unlocked by trophies. Written by the author; `{santo}` is the
 * full name with its title, `{maschile|femminile}` picks by the saint's gender.
 * The special cards (S1–S7) keep their own invocation (see Mannaggia.phraseOf).
 */
object Formule {

    data class Formula(val id: String, val testo: String)

    const val PREDEFINITA = "mannaggia"
    const val A_CASO = "caso"

    val TUTTE = listOf(
        Formula(PREDEFINITA, "Mannaggia {santo}!"),
        Formula("guai", "{Stramaledetto|Stramaledetta} {santo}, solo guai!"),
        Formula("fatti", "Ma non potevi farti i cazzi tuoi, {santo}?"),
        Formula("pelle", "Accidenti alla Pelle di {santo}!"),
        Formula("pentecoste", "Mannaggia la Pentecoste e te, {santo}!"),
        Formula("sandali", "Mannaggia i sandali di {santo}!"),
        Formula("bestiario", "{Maledetto quel tardigrado|Maledetta quella scolopendra} di {santo}!"),
        Formula("iconoclastia", "Eclissati {santo}, e che l'iconoclastia ti si porti via!"),
        Formula("penitenziagite", "Penitenziagite {santo}!"),
    )

    private val SCELTA = Regex("""\{([^{}|]*)\|([^{}|]*)\}""")

    /** [testo] with the saint's name and the gendered words in place. */
    fun componi(testo: String, saint: String, female: Boolean): String =
        SCELTA.replace(testo.replace("{santo}", saint)) { m -> m.groupValues[if (female) 2 else 1] }

    /** Shown in Options: the formula with a sample saint. */
    fun esempio(f: Formula) = componi(f.testo, "San X", female = false)

    /** The default formula always; the others once their trophy is won (all of them in debug builds). */
    fun disponibile(context: Context, id: String): Boolean =
        id == PREDEFINITA || BuildConfig.DEBUG || Trofei.TUTTI.any {
            it.ricompensa.tipo == Trofei.Tipo.FORMULA && it.ricompensa.valore == id && Trofei.isUnlocked(context, it.id)
        }

    /** The phrase for [saint] with the formula chosen in Options (or a random available one). */
    suspend fun frase(context: Context, saint: String): String {
        val scelta = Prefs.formula(context)
        val formula = if (scelta == A_CASO) TUTTE.filter { disponibile(context, it.id) }.random()
        else TUTTE.firstOrNull { it.id == scelta && disponibile(context, it.id) } ?: TUTTE.first()
        return componi(formula.testo, saint, female(context, saint))
    }

    @Volatile
    private var sante: Set<String>? = null

    /** Santa/Beata by title; "Sant'" hides the gender, so those come from avatar/sante.txt (Wikidata). */
    suspend fun female(context: Context, saint: String): Boolean {
        if (saint.startsWith("Santa ") || saint.startsWith("Beata ")) return true
        if (!saint.startsWith("Sant'")) return false
        val set = sante ?: withContext(Dispatchers.IO) {
            runCatching {
                context.applicationContext.assets.open("avatar/sante.txt").bufferedReader(Charsets.UTF_8)
                    .useLines { lines -> lines.map { it.trim() }.filter { it.isNotEmpty() && !it.startsWith("#") }.toSet() }
            }.getOrDefault(emptySet())
        }.also { sante = it }
        return saint in set
    }
}
