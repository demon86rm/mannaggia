package com.mannaggia.app

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.text.method.LinkMovementMethod
import android.text.util.Linkify
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import com.google.android.material.tabs.TabLayout
import com.mannaggia.app.databinding.ActivityInfoBinding

/**
 * Info: three tabs. "Novità" is the changelog (assets/novita.txt), "Prossimamente" the roadmap
 * (upcoming_features, with a link to propose ideas), "Crediti" the about text.
 * Opened by the "Info" button and by "Tutte le novità" in the post-update popup (EXTRA_TAB).
 */
class InfoActivity : AppCompatActivity() {

    private lateinit var binding: ActivityInfoBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityInfoBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.toolbar.title = getString(R.string.about_title, BuildConfig.VERSION_NAME)
        binding.toolbar.setNavigationOnClickListener { finish() }
        ViewCompat.setOnApplyWindowInsetsListener(binding.root) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout())
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }
        binding.btnPropose.setOnClickListener { openUrl(ISSUES_URL) }
        binding.tabs.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab) = show(tab.position)
            override fun onTabUnselected(tab: TabLayout.Tab) = Unit
            override fun onTabReselected(tab: TabLayout.Tab) = Unit
        })
        val tab = savedInstanceState?.getInt(KEY_TAB) ?: intent.getIntExtra(EXTRA_TAB, TAB_NEWS)
        binding.tabs.getTabAt(tab)?.select()
        show(tab)
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putInt(KEY_TAB, binding.tabs.selectedTabPosition)
    }

    private fun show(tab: Int) {
        binding.txtInfo.text = when (tab) {
            TAB_UPCOMING -> resources.getStringArray(R.array.upcoming_features).joinToString("\n\n")
            TAB_CREDITS -> getString(R.string.about_text)
            else -> Novita.testo(this)
        }
        if (tab == TAB_CREDITS) {
            Linkify.addLinks(binding.txtInfo, Linkify.WEB_URLS)
            binding.txtInfo.movementMethod = LinkMovementMethod.getInstance()
        } else {
            binding.txtInfo.movementMethod = null
        }
        binding.btnPropose.visibility = if (tab == TAB_UPCOMING) View.VISIBLE else View.GONE
        binding.scroll.scrollTo(0, 0)
    }

    /** Links open in the browser, so the app itself still needs no network access. */
    private fun openUrl(url: String) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        } catch (e: ActivityNotFoundException) {
            Toast.makeText(this, R.string.no_browser, Toast.LENGTH_SHORT).show()
        }
    }

    companion object {
        const val EXTRA_TAB = "tab"
        const val TAB_NEWS = 0
        const val TAB_UPCOMING = 1
        const val TAB_CREDITS = 2
        private const val KEY_TAB = "tab"
        private const val ISSUES_URL = "https://github.com/demon86rm/mannaggia/issues"
    }
}
