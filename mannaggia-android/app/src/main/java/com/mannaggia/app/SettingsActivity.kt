package com.mannaggia.app

import android.content.SharedPreferences
import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.preference.Preference
import androidx.preference.PreferenceFragmentCompat
import androidx.preference.PreferenceViewHolder
import com.mannaggia.app.databinding.ActivitySettingsBinding

/**
 * Options screen: shake-to-Mannaggia, text-to-speech and phrase style
 * (font, color, neon glow) with a live preview on top.
 */
class SettingsActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySettingsBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.toolbar.setNavigationOnClickListener { finish() }

        // Edge-to-edge: toolbar below the status bar, list above the navigation bar.
        ViewCompat.setOnApplyWindowInsetsListener(binding.root) { view, insets ->
            val bars = insets.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout()
            )
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }

        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.settingsContainer, SettingsFragment())
                .commit()
        }
    }

    class SettingsFragment : PreferenceFragmentCompat(),
        SharedPreferences.OnSharedPreferenceChangeListener {

        override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
            setPreferencesFromResource(R.xml.preferences, rootKey)
        }

        override fun onResume() {
            super.onResume()
            preferenceManager.sharedPreferences?.registerOnSharedPreferenceChangeListener(this)
        }

        override fun onPause() {
            preferenceManager.sharedPreferences?.unregisterOnSharedPreferenceChangeListener(this)
            super.onPause()
        }

        override fun onSharedPreferenceChanged(prefs: SharedPreferences?, key: String?) {
            if (key == Prefs.KEY_THEME) {
                Prefs.applyNightMode(requireContext())
                return
            }
            if (key == Prefs.KEY_FONT || key == Prefs.KEY_COLOR || key == Prefs.KEY_GLOW) {
                findPreference<StylePreviewPreference>("preview")?.refresh()
            }
        }
    }
}

/** Shows a sample phrase with the current font, color and glow. */
class StylePreviewPreference(
    context: android.content.Context,
    attrs: android.util.AttributeSet?
) : Preference(context, attrs) {

    init {
        layoutResource = R.layout.preference_style_preview
        isSelectable = false
    }

    private var themeColor: Int? = null

    override fun onBindViewHolder(holder: PreferenceViewHolder) {
        super.onBindViewHolder(holder)
        val text = holder.findViewById(R.id.txtPreview) as TextView
        val color = themeColor ?: text.currentTextColor.also { themeColor = it }
        Prefs.applyPhraseStyle(text, color)
    }

    fun refresh() = notifyChanged()
}
