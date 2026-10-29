package com.mannaggia.app

import android.content.Context
import android.content.SharedPreferences
import java.util.Calendar
import java.util.Locale

/**
 * Hidden trophies ("Trofei"): local statistics, the rules that unlock trophies
 * and the cosmetic rewards they give (colors, fonts, effects, special cards).
 *
 * Everything stays on the phone (SharedPreferences "stats"). Unlocks from any
 * source (main screen, widget, tile, options, album) go into a queue that the
 * main screen announces with [TrophyPop] when it is visible.
 */
object Trofei {

    /** Where an invocation came from. */
    enum class Fonte { PULSANTE, SCUOTIMENTO, CALENDARIO, WIDGET, RIQUADRO }

    /**
     * CORNICE: an animated frame for the legendary cards; FORMULA: an invocation formula (Formule);
     * OPZIONE: a switch in Options (its key).
     */
    enum class Tipo { COLORE, CARATTERE, EFFETTO, FIGURINA, CORNICE, FORMULA, OPZIONE }

    /** A cosmetic reward: [valore] is the preference value (or the special card's name). */
    data class Ricompensa(val tipo: Tipo, val valore: String, val nome: String) {
        val descrizione: String
            get() = when (tipo) {
                Tipo.COLORE -> "Nuovo colore: $nome"
                Tipo.CARATTERE -> "Nuovo carattere: $nome"
                Tipo.EFFETTO -> "Nuovo effetto: $nome"
                Tipo.FIGURINA -> "Figurina speciale: $nome"
                Tipo.CORNICE -> "Nuova cornice: $nome"
                Tipo.FORMULA -> "Nuova formula: $nome"
                Tipo.OPZIONE -> "Nuova opzione: $nome"
            }
    }

    /** [extra]: further rewards of the same trophy (shown and unlocked with the main one). */
    data class Trofeo(
        val id: String, val nome: String, val condizione: String, val ricompensa: Ricompensa,
        val extra: List<Ricompensa> = emptyList(),
    ) {
        val ricompense get() = listOf(ricompensa) + extra
        val descrizione get() = ricompense.joinToString("\n") { it.descrizione }
    }

    private fun colore(v: String, n: String) = Ricompensa(Tipo.COLORE, v, n)
    private fun carattere(v: String, n: String) = Ricompensa(Tipo.CARATTERE, v, n)
    private fun effetto(v: String, n: String) = Ricompensa(Tipo.EFFETTO, v, n)
    private fun figurina(n: String) = Ricompensa(Tipo.FIGURINA, n, n)
    private fun cornice(v: String, n: String) = Ricompensa(Tipo.CORNICE, v, n)
    private fun formula(id: String) = Ricompensa(Tipo.FORMULA, id, Formule.esempio(Formule.TUTTE.first { it.id == id }))

    val TUTTI = listOf(
        Trofeo("primo", "Primo peccato", "La prima imprecazione", colore("oro", "Oro zecchino")),
        Trofeo("messa", "Messa saltata", "Scuotere il telefono la domenica mattina, tra le 9 e le 12",
            colore("acquasanta", "Acquasanta")),
        Trofeo("diavolo", "L'ora del diavolo", "Imprecare tra le 3 e le 4 di notte",
            colore("inferno", "Fuoco infernale")),
        Trofeo("helvetica", "Il diavolo veste Helvetica", "Cambiare carattere 666 volte",
            carattere("sans-serif-black", "Black")),
        Trofeo("esorcismo", "Esorcismo", "Scuotere il telefono 5 volte in 15 secondi",
            effetto("tremolio", "Tremolio")),
        Trofeo("trinita", "Santissima Trinità", "Imprecare dal pulsante, dal widget e dal riquadro",
            effetto("aureola", "Aureola")),
        Trofeo("pellegrino", "Pellegrino", "Imprecare per 7 giorni di fila",
            carattere("sans-serif-smallcaps", "Maiuscoletto")),
        Trofeo("devoto", "Devoto", "100 imprecazioni", colore("porpora", "Porpora cardinalizia")),
        Trofeo("sacrestano", "Sacrestano", "Album al 10%", carattere("sans-serif-light", "Leggero")),
        Trofeo("parroco", "Parroco", "Album al 25%", Ricompensa(Tipo.OPZIONE, Prefs.KEY_COLORFUL, "Colorful"),
            listOf(cornice("canonica", "Canonica"))),
        Trofeo("vescovo", "Vescovo", "Album al 50%", effetto("fiamma", "Fiamma")),
        Trofeo("papa", "Papa", "Album completo", figurina("Santo Subito")),
        Trofeo("leggenda", "Colpo di fortuna", "Trovare il primo santo leggendario", figurina("San Culo")),
        Trofeo("onomastico", "Onomastico", "Pescare per caso il santo del giorno", figurina("San Calendario")),
        Trofeo("venerdi", "Deploy del venerdì", "Imprecare il venerdì tra le 17 e le 19", figurina("San Deploy")),
        Trofeo("root", "Root", "1000 imprecazioni", figurina("San Sudo")),
        Trofeo("pazienza", "Santa Pazienza", "Aprire l'album 50 volte senza figurine nuove",
            figurina("Santa Pazienza")),
        Trofeo("sudo", "sudo !!", "Imprecare 10 volte di fila con il carattere Monospace",
            effetto(Prefs.EFFECT_TERMINALE, "Terminale")),
        Trofeo("amanuense", "Amanuense", "Imprecare 50 volte con il carattere Medievale",
            carattere("font:mainzer_fraktur", "Fraktur")),
        Trofeo("gutenberg", "Gutenberg", "Trovare un santo di Magonza",
            carattere("font:cat_altgotisch", "Gotico antico")),
        Trofeo("mille", "Mille e non più mille", "Trovare 1000 santi",
            carattere("font:unifraktur_maguntia", "Unifraktur")),
        // Last FIGURINA reward, so Santa Cunegonda is card S7 (same order as SPECIALI in avatar.py).
        Trofeo("vua", "In onore dei Veteran Unix Admins", "50 imprecazioni",
            figurina("Santa Cunegonda Bipalluta")),
        // Gifts (made + saints received).
        Trofeo("evangelista", "Evangelista", "Condividere 10 volte un santo o un quadro", colore("pergamena", "Pergamena")),
        Trofeo("dono1", "Primo dono", "Fare o ricevere il primo dono", colore("incenso", "Incenso")),
        Trofeo("dono10", "Buon samaritano", "10 doni fatti o ricevuti", cornice("alloro", "Alloro")),
        Trofeo("dono50", "Elemosiniere", "50 doni fatti o ricevuti", cornice("vetrata", "Vetrata")),
        Trofeo("dono100", "Comunione dei santi", "100 doni fatti o ricevuti", cornice("gemme", "Gemme")),
        Trofeo("ognissanti", "La Passione di Mannaggia!", "Trovare tutti i santi e tutte le figurine speciali",
            cornice("ognissanti", "Ognissanti")),
        // Invocation formulas (the author's), at invocation milestones.
        Trofeo("guai", "Saaanto, Santo combinaguai!", "125 imprecazioni", formula("guai")),
        Trofeo("fatti", "San Tommaso Ficcanaso", "250 imprecazioni", formula("fatti")),
        Trofeo("pelle", "La Sacra Epidermide", "275 imprecazioni", formula("pelle")),
        Trofeo("pentecoste", "Pentecoste Strikes back!", "300 imprecazioni", formula("pentecoste")),
        Trofeo("sandali", "I sandali de chi?!?", "350 imprecazioni", formula("sandali")),
        Trofeo("bestiario", "Bestiarium", "400 imprecazioni", formula("bestiario")),
        Trofeo("iconoclastia", "Iconoclasta", "500 imprecazioni", formula("iconoclastia")),
        Trofeo("penitenziagite", "Il Nome della Rosa", "777 imprecazioni", formula("penitenziagite")),
    )

    /** Formula trophy id -> invocations needed. */
    private val FORMULE_A = mapOf("guai" to 125, "fatti" to 250, "pelle" to 275, "pentecoste" to 300, "sandali" to 350,
        "bestiario" to 400, "iconoclastia" to 500, "penitenziagite" to 777)

    private val BY_ID = TUTTI.associateBy { it.id }

    /** The special (off-catalogue) cards, in card order: S1 = first (same order as speciali.txt). */
    val SPECIALI: List<String> = TUTTI.filter { it.ricompensa.tipo == Tipo.FIGURINA }.map { it.ricompensa.valore }

    fun isSpecial(saint: String) = saint in SPECIALI

    /** "S3" number of a special card (1-based), or null. */
    fun specialNumber(saint: String): Int? = SPECIALI.indexOf(saint).takeIf { it >= 0 }?.plus(1)

    private const val ESORCISMO_SHAKES = 5      // 7 was hard: shakes come at most 1 s apart and peaks can be missed
    private const val ESORCISMO_WINDOW_MS = 15_000L
    private const val PELLEGRINO_DAYS = 7
    private const val PAZIENZA_OPENS = 50
    private const val HELVETICA_CHANGES = 666
    private const val EVANGELISTA_SHARES = 10
    private const val KEY_RETRO = "retro_decollato"
    private const val KEY_RETRO_NOTICE = "retro_avviso"
    private const val SUDO_IN_A_ROW = 10
    private const val AMANUENSE_INVOCATIONS = 50
    private const val VUA_INVOCATIONS = 50
    private const val MILLE_SAINTS = 1000

    /** The saints of Mainz, Gutenberg's city: San Lullo di Magonza, Sant'Albano da Magonza... */
    private val MAGONZA = Regex("""\b(di|da) Magonza$""")

    private fun prefs(context: Context): SharedPreferences =
        context.applicationContext.getSharedPreferences("stats", Context.MODE_PRIVATE)

    // --- Events ---------------------------------------------------------------

    /** An invocation of [saint]; [isNew] if it just entered the album. */
    suspend fun invocazione(context: Context, fonte: Fonte, saint: String, isNew: Boolean) {
        val legendary = isNew && Avatars.isLegendary(context, saint)
        val dayMatch = fonte != Fonte.CALENDARIO && saint == Mannaggia.saintOfDay(context)
        val entries = Album.entries(context)
        val albumSize = entries.count { !isSpecial(it.saint) }
        val hasBattista = entries.any { it.saint == Retro.FRONTE }
        val total = Mannaggia.saintCount(context)
        synchronized(this) {
            val p = prefs(context)
            val e = p.edit()
            val cal = Calendar.getInstance()
            val count = p.getInt("total", 0) + 1
            e.putInt("total", count)
            e.putInt("src_${fonte.name}", p.getInt("src_${fonte.name}", 0) + 1)

            val today = day(cal)
            val last = p.getString("lastDay", null)
            val streak = when (last) {
                today -> p.getInt("streak", 1)
                day(Calendar.getInstance().apply { add(Calendar.DAY_OF_YEAR, -1) }) -> p.getInt("streak", 0) + 1
                else -> 1
            }
            e.putString("lastDay", today).putInt("streak", streak)
            val mono = Prefs.isMonospace(context)
            val monoRun = if (mono) p.getInt("monoRun", 0) + 1 else 0
            e.putInt("monoRun", monoRun)
            val medieval = p.getInt("medieval", 0) + if (Prefs.isMedieval(context)) 1 else 0
            e.putInt("medieval", medieval)
            val monthDay = String.format(Locale.ROOT, "%02d-%02d", cal.get(Calendar.MONTH) + 1, cal.get(Calendar.DAY_OF_MONTH))
            if (hasBattista && Retro.isRetroDay(monthDay) && !p.contains(KEY_RETRO)) {
                e.putLong(KEY_RETRO, System.currentTimeMillis()).putBoolean(KEY_RETRO_NOTICE, true)
            }
            e.apply()

            val hour = cal.get(Calendar.HOUR_OF_DAY)
            val weekday = cal.get(Calendar.DAY_OF_WEEK)
            val src = { f: Fonte -> f == fonte || p.getInt("src_${f.name}", 0) > 0 }
            val ok = mutableListOf<String>()
            if (count >= 1) ok += "primo"
            if (hour == 3) ok += "diavolo"
            if (src(Fonte.PULSANTE) && src(Fonte.WIDGET) && src(Fonte.RIQUADRO)) ok += "trinita"
            if (streak >= PELLEGRINO_DAYS) ok += "pellegrino"
            if (count >= VUA_INVOCATIONS) ok += "vua"   // mannaggia.sh summoned her every 50 saints
            if (count >= 100) ok += "devoto"
            if (count >= 1000) ok += "root"
            FORMULE_A.forEach { (id, n) -> if (count >= n) ok += id }
            collezione(ok, albumSize, total, legendary, saint, allSpecials(context))
            if (dayMatch) ok += "onomastico"
            if (weekday == Calendar.FRIDAY && hour in 17..18) ok += "venerdi"
            if (monoRun >= SUDO_IN_A_ROW) ok += "sudo"
            if (medieval >= AMANUENSE_INVOCATIONS) ok += "amanuense"
            unlock(context, ok)
        }
    }

    /** Trophies for what the album holds: found by invocation or received as a gift. */
    private fun collezione(
        ok: MutableList<String>, albumSize: Int, total: Int, legendary: Boolean, saint: String, allSpecials: Boolean,
    ) {
        if (total > 0 && albumSize * 10 >= total) ok += "sacrestano"
        if (total > 0 && albumSize * 4 >= total) ok += "parroco"
        if (total > 0 && albumSize * 2 >= total) ok += "vescovo"
        if (albumSize >= MILLE_SAINTS) ok += "mille"
        if (total > 0 && albumSize >= total) ok += "papa"
        // shortcut: specials won elsewhere (shake, options) are seen at the next invocation or album opening, fine for a final goal.
        if (total > 0 && albumSize >= total && allSpecials) ok += "ognissanti"
        if (legendary) ok += "leggenda"
        if (MAGONZA.containsMatchIn(saint)) ok += "gutenberg"
    }

    /** A gift of [saint] was received ([isNew] if it entered the album): not an invocation. */
    suspend fun dono(context: Context, saint: String, isNew: Boolean) {
        Dono.ricevuto(context, saint, isNew)
        val legendary = isNew && Avatars.isLegendary(context, saint)
        val albumSize = Album.entries(context).count { !isSpecial(it.saint) }
        val total = Mannaggia.saintCount(context)
        val gifts = Dono.count(context)
        synchronized(this) {
            val ok = mutableListOf<String>()
            collezione(ok, albumSize, total, legendary, saint, allSpecials(context))
            doni(ok, gifts)
            unlock(context, ok)
        }
    }

    /** A gift of [saint] was sent ("Regala" in the album). */
    suspend fun donoInviato(context: Context, saint: String) {
        Dono.inviato(context, saint)
        val gifts = Dono.count(context)
        synchronized(this) {
            val ok = mutableListOf<String>()
            doni(ok, gifts)
            unlock(context, ok)
        }
    }

    private fun doni(ok: MutableList<String>, gifts: Int) {
        for (n in listOf(1, 10, 50, 100)) if (gifts >= n) ok += "dono$n"
    }

    /**
     * A shake, counted even when it doesn't start an invocation (e.g. during the
     * spoken phrase): "Esorcismo" needs 7 of them in 15 seconds.
     */
    fun scossa(context: Context) = synchronized(this) {
        val p = prefs(context)
        val now = System.currentTimeMillis()
        val shakes = (p.getString("shakes", "")!!.split(',').mapNotNull { it.toLongOrNull() } + now)
            .takeLast(ESORCISMO_SHAKES)
        p.edit().putString("shakes", shakes.joinToString(",")).apply()
        val cal = Calendar.getInstance()
        val ok = mutableListOf<String>()
        if (cal.get(Calendar.DAY_OF_WEEK) == Calendar.SUNDAY && cal.get(Calendar.HOUR_OF_DAY) in 9..11) ok += "messa"
        if (shakes.size >= ESORCISMO_SHAKES && now - shakes.first() <= ESORCISMO_WINDOW_MS) ok += "esorcismo"
        unlock(context, ok)
    }

    /** The back of San Giovanni Battista is unlocked (see Retro). */
    fun retroSbloccato(context: Context) = prefs(context).contains(KEY_RETRO)

    /** True once, right after the back was unlocked: time for the hint. */
    fun takeRetroNotice(context: Context): Boolean = synchronized(this) {
        val p = prefs(context)
        p.getBoolean(KEY_RETRO_NOTICE, false).also { if (it) p.edit().remove(KEY_RETRO_NOTICE).apply() }
    }

    /** A card or picture was shared to an app actually chosen in the share sheet (see Condividi). */
    fun condivisione(context: Context) = synchronized(this) {
        val p = prefs(context)
        val n = p.getInt("shares", 0) + 1
        p.edit().putInt("shares", n).apply()
        if (n >= EVANGELISTA_SHARES) unlock(context, listOf("evangelista"))
    }

    /** The phrase font was changed in Options. */
    fun cambioCarattere(context: Context) = synchronized(this) {
        val p = prefs(context)
        val n = p.getInt("fonts", 0) + 1
        p.edit().putInt("fonts", n).apply()
        if (n >= HELVETICA_CHANGES) unlock(context, listOf("helvetica"))
    }

    /** The album was opened: 50 openings in a row without new cards in between; also "ognissanti". */
    suspend fun aperturaAlbum(context: Context) {
        val size = Album.entries(context).size
        val albumSize = Album.entries(context).count { !isSpecial(it.saint) }
        val total = Mannaggia.saintCount(context)
        synchronized(this) {
            if (total > 0 && albumSize >= total && allSpecials(context)) unlock(context, listOf("ognissanti"))
            val p = prefs(context)
            val empty = if (size == p.getInt("albumSizeAtOpen", -1)) p.getInt("emptyOpens", 0) + 1 else 0
            p.edit().putInt("albumSizeAtOpen", size).putInt("emptyOpens", empty).apply()
            if (empty >= PAZIENZA_OPENS) unlock(context, listOf("pazienza"))
        }
    }

    // --- State ----------------------------------------------------------------

    fun isUnlocked(context: Context, id: String) = prefs(context).contains("unlocked_$id")

    fun unlockedAt(context: Context, id: String): Long? =
        prefs(context).getLong("unlocked_$id", 0L).takeIf { it > 0 }

    fun unlockedCount(context: Context) = TUTTI.count { isUnlocked(context, it.id) }

    /** All the special cards (S1–S7) won. */
    private fun allSpecials(context: Context) =
        TUTTI.filter { it.ricompensa.tipo == Tipo.FIGURINA }.all { isUnlocked(context, it.id) }

    /** True if the reward [valore] of type [tipo] belongs to an unlocked trophy (or to no trophy). */
    fun rewardAvailable(context: Context, tipo: Tipo, valore: String): Boolean {
        val owner = TUTTI.firstOrNull { t -> t.ricompense.any { it.tipo == tipo && it.valore == valore } }
        return owner == null || isUnlocked(context, owner.id)
    }

    /** Names of the special cards already unlocked. */
    fun unlockedSpecials(context: Context): List<String> =
        TUTTI.filter { it.ricompensa.tipo == Tipo.FIGURINA && isUnlocked(context, it.id) }.map { it.ricompensa.valore }

    /** Unlocks waiting to be announced, oldest first; clears the queue. */
    fun takePending(context: Context): List<Trofeo> = synchronized(this) {
        val p = prefs(context)
        val ids = p.getString("pending", "")!!.split(',').filter { it.isNotEmpty() }
        p.edit().remove("pending").apply()
        ids.mapNotNull { BY_ID[it] }
    }

    /** Debug builds: unlock everything, one trophy at a time. */
    fun debugUnlockNext(context: Context): Boolean = synchronized(this) {
        val next = TUTTI.firstOrNull { !isUnlocked(context, it.id) } ?: return false
        unlock(context, listOf(next.id))
        true
    }

    private fun unlock(context: Context, ids: List<String>) {
        val p = prefs(context)
        val fresh = ids.filter { !p.contains("unlocked_$it") }
        if (fresh.isEmpty()) return
        val e = p.edit()
        val now = System.currentTimeMillis()
        fresh.forEach { e.putLong("unlocked_$it", now) }
        val pending = p.getString("pending", "")!!.split(',').filter { it.isNotEmpty() } + fresh
        e.putString("pending", pending.joinToString(",")).apply()
    }

    private fun day(c: Calendar) = String.format(Locale.ROOT, "%04d-%02d-%02d",
        c.get(Calendar.YEAR), c.get(Calendar.MONTH) + 1, c.get(Calendar.DAY_OF_MONTH))
}
