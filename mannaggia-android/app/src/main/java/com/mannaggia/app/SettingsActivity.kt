package com.mannaggia.app

import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.SharedPreferences
import android.net.Uri
import android.os.Bundle
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.preference.Preference
import androidx.preference.PreferenceFragmentCompat
import androidx.preference.PreferenceViewHolder
import com.mannaggia.app.databinding.ActivitySettingsBinding

/**
 * Options screen: shake-to-Mannaggia, text-to-speech, phrase style
 * (font, color, neon glow) with a live preview on top, and project links
 * (roadmap, issues, contributing).
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
            onClick("upcoming") { showUpcoming() }
            onClick("issues") { openUrl(ISSUES_URL) }
            onClick("contribute") { openUrl(REPO_URL) }
        }

        private fun onClick(key: String, action: () -> Unit) {
            findPreference<Preference>(key)?.setOnPreferenceClickListener { action(); true }
        }

        /** Roadmap from res/values/strings.xml, with a shortcut to propose ideas. */
        private fun showUpcoming() {
            val items = resources.getStringArray(R.array.upcoming_features)
            AlertDialog.Builder(requireContext())
                .setTitle(R.string.upcoming_title)
                .setMessage(items.joinToString("\n\n"))
                .setNeutralButton(R.string.upcoming_propose) { _, _ -> openUrl(ISSUES_URL) }
                .setPositiveButton(R.string.about_close, null)
                .show()
        }

        /** Links open in the browser, so the app itself still needs no network access. */
        private fun openUrl(url: String) {
            try {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
            } catch (e: ActivityNotFoundException) {
                Toast.makeText(requireContext(), R.string.no_browser, Toast.LENGTH_SHORT).show()
            }
        }

        override fun onResume() {
            super.onResume()
            preferenceManager.sharedPreferences?.registerOnSharedPreferenceChangeListener(this)
        }

        override fun onPause() {
            preferenceManager.sharedPreferences?.unregisterOnSharedPreferenceChangeListener(this)
            super.onPause()
        }

        companion object {
            private const val REPO_URL = "https://github.com/demon86rm/mannaggia"
            private const val ISSUES_URL = "$REPO_URL/issues/new/choose"
        }

        override fun onSharedPreferenceChanged(prefs: SharedPreferences?, key: String?) {
            if (key == Prefs.KEY_THEME) {
                Prefs.applyNightMode(requireContext())
                return
            }
            if (key == Prefs.KEY_FONT) Trofei.cambioCarattere(requireContext())
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
