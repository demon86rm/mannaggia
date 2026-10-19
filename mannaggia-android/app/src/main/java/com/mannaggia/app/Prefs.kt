package com.mannaggia.app

import android.content.Context
import android.content.SharedPreferences
import android.graphics.Color
import android.graphics.Typeface
import android.widget.TextView
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.content.ContextCompat
import androidx.preference.PreferenceManager

/**
 * User options (edited in SettingsActivity) and the phrase styling they drive.
 * Keys and defaults must match res/xml/preferences.xml.
 */
object Prefs {

    const val KEY_SHAKE = "shake"
    const val KEY_TTS = "tts"
    const val KEY_FONT = "font"
    const val KEY_COLOR = "color"
    const val KEY_GLOW = "glow"
    const val KEY_THEME = "theme"

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
    )

    /** Glow radius, in dp, for the neon effect. */
    private const val GLOW_RADIUS_DP = 10f

    private fun prefs(context: Context): SharedPreferences =
        PreferenceManager.getDefaultSharedPreferences(context)

    fun shakeEnabled(context: Context) = prefs(context).getBoolean(KEY_SHAKE, true)

    fun ttsEnabled(context: Context) = prefs(context).getBoolean(KEY_TTS, false)

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

        val family = p.getString(KEY_FONT, "sans-serif") ?: "sans-serif"
        view.typeface = Typeface.create(family, Typeface.BOLD)

        val colorRes = PHRASE_COLORS[p.getString(KEY_COLOR, COLOR_THEME)]
        val color = if (colorRes == null) themeColor else ContextCompat.getColor(view.context, colorRes)
        view.setTextColor(color)

        if (p.getBoolean(KEY_GLOW, false)) {
            val radius = GLOW_RADIUS_DP * view.resources.displayMetrics.density
            view.setShadowLayer(radius, 0f, 0f, color)
        } else {
            view.setShadowLayer(0f, 0f, 0f, Color.TRANSPARENT)
        }
    }
}
