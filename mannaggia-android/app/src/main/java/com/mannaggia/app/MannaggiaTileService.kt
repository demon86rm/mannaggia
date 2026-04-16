package com.mannaggia.app

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * Quick Settings tile. One tap → fetch a saint → post a notification
 * with the phrase. Tapping the notification opens the app.
 */
class MannaggiaTileService : TileService() {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    override fun onClick() {
        super.onClick()
        setTileState(Tile.STATE_ACTIVE)

        scope.launch {
            val phrase = runCatching { Mannaggia.phraseOf(Mannaggia.fetchRandomSaint()) }
                .getOrElse { "Errore: ${it.message}" }
            showNotification(phrase)
            setTileState(Tile.STATE_INACTIVE)
        }
    }

    override fun onStartListening() {
        super.onStartListening()
        setTileState(Tile.STATE_INACTIVE)
    }

    private fun setTileState(state: Int) {
        qsTile?.apply {
            this.state = state
            updateTile()
        }
    }

    private fun showNotification(phrase: String) {
        // Need runtime POST_NOTIFICATIONS on API 33+. Silently skip if missing.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val granted = ContextCompat.checkSelfPermission(
                this, Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) return
        }

        val nm = getSystemService(NotificationManager::class.java) ?: return

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID, "Mannaggia", NotificationManager.IMPORTANCE_DEFAULT
            )
            nm.createNotificationChannel(channel)
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        }
        val pending = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Mannaggia!")
            .setContentText(phrase)
            .setStyle(NotificationCompat.BigTextStyle().bigText(phrase))
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pending)
            .setAutoCancel(true)
            .build()

        nm.notify(NOTIF_ID, notification)
    }

    companion object {
        private const val CHANNEL_ID = "mannaggia"
        private const val NOTIF_ID = 1
    }
}
