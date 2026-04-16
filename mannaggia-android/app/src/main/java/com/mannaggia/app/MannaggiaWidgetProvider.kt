package com.mannaggia.app

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * Home screen widget. Tap the widget → fetch a saint → widget text updates
 * in place. No notification, no app launch.
 */
class MannaggiaWidgetProvider : AppWidgetProvider() {

    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray
    ) {
        for (id in appWidgetIds) {
            render(context, appWidgetManager, id, text = null)
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action != ACTION_INVOKE) return

        val mgr = AppWidgetManager.getInstance(context)
        val component = ComponentName(context, MannaggiaWidgetProvider::class.java)
        val ids = mgr.getAppWidgetIds(component)
        if (ids.isEmpty()) return

        // Show loading state in every instance of the widget.
        for (id in ids) render(context, mgr, id, text = "…")

        // Run the fetch asynchronously; goAsync keeps the BroadcastReceiver alive.
        val pendingResult = goAsync()
        CoroutineScope(SupervisorJob() + Dispatchers.IO).launch {
            val phrase = runCatching { Mannaggia.phraseOf(Mannaggia.fetchRandomSaint()) }
                .getOrElse { "Errore" }
            try {
                for (id in ids) render(context, mgr, id, text = phrase)
            } finally {
                pendingResult.finish()
            }
        }
    }

    private fun render(
        context: Context,
        mgr: AppWidgetManager,
        widgetId: Int,
        text: String?
    ) {
        val views = RemoteViews(context.packageName, R.layout.widget_mannaggia)
        if (text != null) views.setTextViewText(R.id.widget_text, text)

        val intent = Intent(context, MannaggiaWidgetProvider::class.java).apply {
            action = ACTION_INVOKE
        }
        val pending = PendingIntent.getBroadcast(
            context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_root, pending)

        mgr.updateAppWidget(widgetId, views)
    }

    companion object {
        private const val ACTION_INVOKE = "com.mannaggia.app.ACTION_INVOKE_WIDGET"
    }
}
