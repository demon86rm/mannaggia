package com.mannaggia.app

import android.content.Context

/**
 * What the voice should read for a phrase, when the device text-to-speech would get it
 * wrong. The phrase on screen stays as it is; only the spoken text changes:
 * - regnal numbers become Italian ordinals agreeing with the saint ("San Carlo I" →
 *   "San Carlo primo", "Santa Beatrice II" → "Santa Beatrice seconda"): a lone "I" is
 *   otherwise read as the letter;
 * - the Spanish "y" between two names ("Calvo y Calvo") is read "i", not "uai";
 * - single words the voice mispronounces get a phonetic spelling ([PAROLE]);
 * - stress marks for the default voice only ([ACCENTI]).
 */
object Pronuncia {

    /** Written word (any case) → how to spell it so the Italian voice says it right. */
    private val PAROLE = mapOf(
        "systemd" to "sistem di",
        "TLS" to "ti elle èsse",                    // open "e", as the letter is said
        "change request" to "ceinge riquest",       // soft g: the final e makes it like "change"
        "777" to "sette sette sette",                // the permissions, digit by digit
    )

    /** Stress marks tuned on the phone's default voice: left out with another engine chosen in Options. */
    private val ACCENTI = mapOf(
        "Eclissati" to "Eclìssati",                  // the stress on the first "i", not on the "a"
        // Women called Elia, stressed on the "E": the prophet and the men keep "Elìa", so full names only.
        "Elia Pulcheria" to "Èlia Pulcheria",
        "Elia Eudocia" to "Èlia Eudocia",
        "Elia Flaccilla" to "Èlia Flaccilla",
        "Elia di Ohren" to "Èlia di Ohren",
        "Elia di San Clemente" to "Èlia di San Clemente",
        "Mesia Elia" to "Mesia Èlia",
    )

    private fun words(map: Map<String, String>) =
        Regex("""\b(${map.keys.joinToString("|") { Regex.escape(it) }})\b""", RegexOption.IGNORE_CASE)

    private val WORDS = words(PAROLE)
    private val STRESSED = words(ACCENTI)

    /** A Roman numeral standing alone after a name (followed by a space, punctuation or the end). */
    private val ROMAN = Regex("""(?<=\s)(?=[IVXLCDM])(M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))(?=[\s!,.;:]|$)""")

    /** The Spanish conjunction: a lowercase "y" alone between two words. */
    private val SPANISH_AND = Regex("""(?<=\p{L}) y (?=\p{L})""")

    private val FEMALE_TITLE = Regex("""\b(Santa|Beata)\s""")

    private val ORDINALI = listOf(
        "primo", "secondo", "terzo", "quarto", "quinto", "sesto", "settimo", "ottavo", "nono", "decimo",
        "undicesimo", "dodicesimo", "tredicesimo", "quattordicesimo", "quindicesimo", "sedicesimo",
        "diciassettesimo", "diciottesimo", "diciannovesimo", "ventesimo", "ventunesimo", "ventiduesimo",
        "ventitreesimo", "ventiquattresimo", "venticinquesimo", "ventiseiesimo", "ventisettesimo",
        "ventottesimo", "ventinovesimo", "trentesimo",
    )

    /**
     * The text to give to the voice for [phrase]. The stress marks ([ACCENTI]) are tuned on the
     * phone's default voice and left out with another engine chosen in Options; the rest always applies.
     */
    fun perVoce(context: Context, phrase: String): String {
        val female = FEMALE_TITLE.containsMatchIn(phrase)
        val numbers = ROMAN.replace(phrase) { m ->
            val n = romanValue(m.value)
            val word = ORDINALI.getOrNull(n - 1) ?: return@replace m.value
            if (female) word.dropLast(1) + "a" else word
        }
        val spanish = SPANISH_AND.replace(numbers, " i ")
        val fixed = WORDS.replace(spanish) { m -> PAROLE.entries.first { it.key.equals(m.value, ignoreCase = true) }.value }
        if (Prefs.ttsEngine(context) != null) return fixed
        return STRESSED.replace(fixed) { m -> ACCENTI.entries.first { it.key.equals(m.value, ignoreCase = true) }.value }
    }

    private fun romanValue(s: String): Int {
        val v = mapOf('I' to 1, 'V' to 5, 'X' to 10, 'L' to 50, 'C' to 100, 'D' to 500, 'M' to 1000)
        var total = 0
        for (i in s.indices) {
            val cur = v.getValue(s[i])
            val next = if (i + 1 < s.length) v.getValue(s[i + 1]) else 0
            total += if (cur < next) -cur else cur
        }
        return total
    }
}
