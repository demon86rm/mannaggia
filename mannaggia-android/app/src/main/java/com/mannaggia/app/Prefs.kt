package com.mannaggia.app

import android.content.Context
import android.content.SharedPreferences
import android.graphics.Color
import android.graphics.Typeface
import android.widget.TextView
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

    /** Value of KEY_COLOR meaning "keep the theme's text color". */
    private const val COLOR_THEME = "theme"

    /** Glow radius, in dp, for the neon effect. */
    private const val GLOW_RADIUS_DP = 10f

    private fun prefs(context: Context): SharedPreferences =
        PreferenceManager.getDefaultSharedPreferences(context)

    fun shakeEnabled(context: Context) = prefs(context).getBoolean(KEY_SHAKE, true)

    fun ttsEnabled(context: Context) = prefs(context).getBoolean(KEY_TTS, false)

    /**
     * Apply font, color and glow to [view]. [themeColor] is the view's original
     * text color, used when the user keeps the theme color.
     */
    fun applyPhraseStyle(view: TextView, themeColor: Int) {
        val p = prefs(view.context)

        val family = p.getString(KEY_FONT, "sans-serif") ?: "sans-serif"
        view.typeface = Typeface.create(family, Typeface.BOLD)

        val colorValue = p.getString(KEY_COLOR, COLOR_THEME) ?: COLOR_THEME
        val color = if (colorValue == COLOR_THEME) themeColor else Color.parseColor(colorValue)
        view.setTextColor(color)

        if (p.getBoolean(KEY_GLOW, false)) {
            val radius = GLOW_RADIUS_DP * view.resources.displayMetrics.density
            view.setShadowLayer(radius, 0f, 0f, color)
        } else {
            view.setShadowLayer(0f, 0f, 0f, Color.TRANSPARENT)
        }
    }
}
