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
    )

    /** Glow radius, in dp, for the neon effect. */
    private const val GLOW_RADIUS_DP = 10f

    private fun prefs(context: Context): SharedPreferences =
        PreferenceManager.getDefaultSharedPreferences(context)

    fun shakeEnabled(context: Context) = prefs(context).getBoolean(KEY_SHAKE, true)

    fun ttsEnabled(context: Context) = prefs(context).getBoolean(KEY_TTS, false)

    /** Animate each new album card; legendary saints are animated anyway. */
    fun cardAnimEnabled(context: Context) = prefs(context).getBoolean(KEY_CARD_ANIM, true)

    /** The angelic choir on the splash screen (only when the phone is not on silent). */
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
