package com.mannaggia.app

import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.SharedPreferences
import android.net.Uri
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.preference.ListPreference
import androidx.preference.Preference
import androidx.preference.PreferenceFragmentCompat
import androidx.preference.PreferenceViewHolder
import com.mannaggia.app.databinding.ActivitySettingsBinding

/**
 * Options screen: shake-to-Mannaggia, text-to-speech, phrase style
 * (font, color, effect; trophy rewards only once unlocked) with a live preview on top, and project links
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
            Prefs.effect(requireContext())  // migrate the old neon switch before showing the list
            // Trophy rewards appear in the lists only once unlocked.
            onlyUnlocked(Prefs.KEY_COLOR, Trofei.Tipo.COLORE)
            onlyUnlocked(Prefs.KEY_FONT, Trofei.Tipo.CARATTERE)
            onlyUnlocked(Prefs.KEY_EFFECT, Trofei.Tipo.EFFETTO)
            onlyUnlocked(Prefs.KEY_FRAME, Trofei.Tipo.CORNICE)
            findPreference<ListPreference>(Prefs.KEY_FRAME)?.let { it.isVisible = it.entries.size > 1 }  // only gold so far
            findPreference<Preference>(Prefs.KEY_COLORFUL)?.isVisible =
                BuildConfig.DEBUG || Trofei.rewardAvailable(requireContext(), Trofei.Tipo.OPZIONE, Prefs.KEY_COLORFUL)
            formulas()
            ttsEngines()
            onClick("issues") { openUrl(ISSUES_URL) }
            onClick("contribute") { openUrl(REPO_URL) }
        }

        private fun onlyUnlocked(key: String, tipo: Trofei.Tipo) {
            val list = findPreference<ListPreference>(key) ?: return
            val keep = list.entryValues.indices.filter {
                Trofei.rewardAvailable(requireContext(), tipo, list.entryValues[it].toString())
            }
            list.entries = keep.map { list.entries[it] }.toTypedArray()
            list.entryValues = keep.map { list.entryValues[it] }.toTypedArray()
        }

        /** The phone's default voice, then every TTS app installed; disabled while Pronuncia is off. */
        private fun ttsEngines() {
            val list = findPreference<ListPreference>(Prefs.KEY_TTS_ENGINE) ?: return
            val probe = TextToSpeech(requireContext().applicationContext, null)
            val engines = probe.engines
            probe.shutdown()
            list.entries = (listOf(getString(R.string.pref_tts_engine_default)) + engines.map { it.label }).toTypedArray()
            list.entryValues = (listOf("") + engines.map { it.name }).toTypedArray()
            if (list.value !in list.entryValues.map { it.toString() }) list.value = ""   // an engine since uninstalled
        }

        /** The formulas available (with a sample saint), plus "at random" when there is a choice. */
        private fun formulas() {
            val list = findPreference<ListPreference>(Prefs.KEY_FORMULA) ?: return
            val ok = Formule.TUTTE.filter { Formule.disponibile(requireContext(), it.id) }
            val names = ok.map { Formule.esempio(it) } + if (ok.size > 1) listOf(getString(R.string.pref_formula_random)) else emptyList()
            val values = ok.map { it.id } + if (ok.size > 1) listOf(Formule.A_CASO) else emptyList()
            list.entries = names.toTypedArray()
            list.entryValues = values.toTypedArray()
            if (list.value !in values) list.value = Formule.PREDEFINITA
            list.isVisible = ok.size > 1                // nothing to choose until a formula is won
        }

        private fun onClick(key: String, action: () -> Unit) {
            findPreference<Preference>(key)?.setOnPreferenceClickListener { action(); true }
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
            if (key == Prefs.KEY_FONT || key == Prefs.KEY_COLOR || key == Prefs.KEY_EFFECT) {
                findPreference<StylePreviewPreference>("preview")?.refresh()
            }
        }
    }
}

/** Shows a sample phrase with the current font, color and effect. */
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
