package com.mannaggia.app

import android.content.Context
import android.content.SharedPreferences
import android.graphics.Color
import android.graphics.Typeface
import android.widget.TextView
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.content.ContextCompat
import androidx.core.content.res.ResourcesCompat
import androidx.preference.PreferenceManager
import java.util.Calendar
import java.util.Locale

/**
 * User options (edited in SettingsActivity) and the phrase styling they drive.
 * Keys and defaults must match res/xml/preferences.xml.
 */
object Prefs {

    const val KEY_SHAKE = "shake"
    const val KEY_TTS = "tts"
    const val KEY_TTS_ENGINE = "tts_engine"
    const val KEY_FONT = "font"
    /** font_values prefix of the fonts bundled in res/font (e.g. "font:medievalsharp"). */
    private const val BUNDLED_FONT = "font:"
    const val FONT_MEDIEVAL = "font:medievalsharp"
    const val KEY_COLOR = "color"
    const val KEY_EFFECT = "effect"
    /** Old on/off neon switch, migrated to KEY_EFFECT = "neon". */
    private const val KEY_GLOW_OLD = "glow"
    const val EFFECT_NEON = "neon"
    const val EFFECT_AUREOLA = "aureola"
    const val EFFECT_TREMOLIO = "tremolio"
    const val EFFECT_FIAMMA = "fiamma"
    const val EFFECT_TERMINALE = "terminale"
    const val KEY_THEME = "theme"
    const val KEY_CARD_ANIM = "card_anim"
    const val KEY_SPLASH_CHOIR = "splash_choir"
    const val KEY_COLORFUL = "colorful"
    /** Album order (ALBUM_SORT_*) and which cards it shows (ALBUM_FILTER_*). */
    private const val KEY_ALBUM_SORT = "album_sort"
    private const val KEY_ALBUM_FILTER = "album_filter"
    const val ALBUM_SORT_NUMBER = "number"
    const val ALBUM_SORT_NAME = "name"
    const val ALBUM_SORT_DISCOVERY = "discovery"
    private const val KEY_ALBUM_DESCENDING = "album_descending"
    const val ALBUM_FILTER_ALL = "all"
    const val ALBUM_FILTER_SAINTS = "santi"
    const val ALBUM_FILTER_BLESSED = "beati"
    /** versionCode whose "what's new" popup was handled (shown, or skipped on a fresh install). */
    private const val KEY_SEEN_VERSION = "seen_version"
    /** Frame of the legendary cards: an asset prefix ("cornice" = gold, or a reward frame). */
    const val KEY_FRAME = "frame"
    /** Invocation formula id (Formule), or Formule.A_CASO. */
    const val KEY_FORMULA = "formula"
    /** Date (yyyy-MM-dd) of the last saint-of-the-day invocation: one a day. */
    private const val KEY_SAINT_OF_DAY_USED = "saint_of_day_used"

    /** Value of KEY_COLOR meaning "keep the theme's text color". */
    private const val COLOR_THEME = "theme"

    /** KEY_COLOR values → colors with a light and a dark (neon) shade. */
    private val PHRASE_COLORS = mapOf(
        "red" to R.color.phrase_red,
        "gold" to R.color.phrase_gold,
        "orange" to R.color.phrase_orange,
        "green" to R.color.phrase_green,
        "cyan" to R.color.phrase_cyan,
        "magenta" to R.color.phrase_magenta,
        "oro" to R.color.phrase_oro,
        "acquasanta" to R.color.phrase_acquasanta,
        "inferno" to R.color.phrase_inferno,
        "porpora" to R.color.phrase_porpora,
        "incenso" to R.color.phrase_incenso,
        "pergamena" to R.color.phrase_pergamena,
    )

    /** Glow radius, in dp, for the neon effect. */
    private const val GLOW_RADIUS_DP = 10f

    private fun prefs(context: Context): SharedPreferences =
        PreferenceManager.getDefaultSharedPreferences(context)

    fun shakeEnabled(context: Context) = prefs(context).getBoolean(KEY_SHAKE, true)

    fun ttsEnabled(context: Context) = prefs(context).getBoolean(KEY_TTS, false)

    /** The TTS engine package chosen in Options, or null for the phone's default one. */
    fun ttsEngine(context: Context): String? = prefs(context).getString(KEY_TTS_ENGINE, "").takeUnless { it.isNullOrEmpty() }

    /** Animate each new album card; legendary saints are animated anyway. */
    fun cardAnimEnabled(context: Context) = prefs(context).getBoolean(KEY_CARD_ANIM, true)

    /** Animated frames for every card (Avatars.frameName), not only the legendary ones. */
    fun colorfulEnabled(context: Context) = prefs(context).getBoolean(KEY_COLORFUL, false)

    /** The angelic choir on the splash screen (at the media volume). */
    fun splashChoirEnabled(context: Context) = prefs(context).getBoolean(KEY_SPLASH_CHOIR, true)

    /** True when the phrase font is "Medievale" (trophy "Amanuense"). */
    fun isMedieval(context: Context) = prefs(context).getString(KEY_FONT, "sans-serif") == FONT_MEDIEVAL

    /**
     * The phrase typeface for a font_values entry: a system family in bold, or a font
     * bundled in res/font for the "font:" values (gothic fonts, one weight only).
     */
    private fun phraseTypeface(context: Context, value: String): Typeface {
        if (value.startsWith(BUNDLED_FONT)) {
            val id = context.resources.getIdentifier(value.removePrefix(BUNDLED_FONT), "font", context.packageName)
            if (id != 0) ResourcesCompat.getFont(context, id)?.let { return it }
        }
        return Typeface.create(value, Typeface.BOLD)
    }

    /** True when the phrase font is "Monospace (terminale)" (trophy "sudo !!"). */
    fun isMonospace(context: Context) = prefs(context).getString(KEY_FONT, "sans-serif") == "monospace"

    fun albumSort(context: Context) = prefs(context).getString(KEY_ALBUM_SORT, ALBUM_SORT_NUMBER) ?: ALBUM_SORT_NUMBER
    fun setAlbumSort(context: Context, value: String) = prefs(context).edit().putString(KEY_ALBUM_SORT, value).apply()

    fun albumDescending(context: Context) = prefs(context).getBoolean(KEY_ALBUM_DESCENDING, false)
    fun setAlbumDescending(context: Context, value: Boolean) = prefs(context).edit().putBoolean(KEY_ALBUM_DESCENDING, value).apply()

    fun albumFilter(context: Context) = prefs(context).getString(KEY_ALBUM_FILTER, ALBUM_FILTER_ALL) ?: ALBUM_FILTER_ALL
    fun setAlbumFilter(context: Context, value: String) = prefs(context).edit().putString(KEY_ALBUM_FILTER, value).apply()

    fun seenVersion(context: Context) = prefs(context).getInt(KEY_SEEN_VERSION, -1)
    fun setSeenVersion(context: Context, version: Int) = prefs(context).edit().putInt(KEY_SEEN_VERSION, version).apply()

    fun frame(context: Context) = prefs(context).getString(KEY_FRAME, Avatars.GOLD_FRAME) ?: Avatars.GOLD_FRAME

    fun formula(context: Context) = prefs(context).getString(KEY_FORMULA, Formule.PREDEFINITA) ?: Formule.PREDEFINITA

    fun saintOfDayUsedToday(context: Context) = prefs(context).getString(KEY_SAINT_OF_DAY_USED, null) == today()

    fun markSaintOfDayUsed(context: Context) =
        prefs(context).edit().putString(KEY_SAINT_OF_DAY_USED, today()).apply()

    private fun today(): String = Calendar.getInstance().let {
        String.format(Locale.ROOT, "%04d-%02d-%02d",
            it.get(Calendar.YEAR), it.get(Calendar.MONTH) + 1, it.get(Calendar.DAY_OF_MONTH))
    }

    /** Apply the light/dark choice app-wide; AppCompat recreates open activities. */
    fun applyNightMode(context: Context) {
        val mode = when (prefs(context).getString(KEY_THEME, "system")) {
            "light" -> AppCompatDelegate.MODE_NIGHT_NO
            "dark" -> AppCompatDelegate.MODE_NIGHT_YES
            else -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
        }
        AppCompatDelegate.setDefaultNightMode(mode)
    }

    /**
     * Apply font, color and glow to [view]. [themeColor] is the view's original
     * text color, used when the user keeps the theme color.
     */
    fun applyPhraseStyle(view: TextView, themeColor: Int) {
        val p = prefs(view.context)

        view.typeface = phraseTypeface(view.context, p.getString(KEY_FONT, "sans-serif") ?: "sans-serif")
        PhraseEffects.refit(view)

        val colorRes = PHRASE_COLORS[p.getString(KEY_COLOR, COLOR_THEME)]
        val color = if (colorRes == null) themeColor else ContextCompat.getColor(view.context, colorRes)
        view.setTextColor(color)

        // Neon is a still glow; the other effects animate (PhraseEffects).
        val effect = effect(view.context)
        PhraseEffects.stop(view)
        if (effect == EFFECT_NEON) {
            val radius = GLOW_RADIUS_DP * view.resources.displayMetrics.density
            view.setShadowLayer(radius, 0f, 0f, color)
        } else {
            view.setShadowLayer(0f, 0f, 0f, Color.TRANSPARENT)
            PhraseEffects.start(view, effect, color)
        }
    }

    /** The phrase effect; migrates the old neon switch the first time. */
    fun effect(context: Context): String {
        val p = prefs(context)
        if (!p.contains(KEY_EFFECT) && p.contains(KEY_GLOW_OLD)) {
            p.edit().putString(KEY_EFFECT, if (p.getBoolean(KEY_GLOW_OLD, false)) EFFECT_NEON else "none")
                .remove(KEY_GLOW_OLD).apply()
        }
        return p.getString(KEY_EFFECT, "none") ?: "none"
    }
}
