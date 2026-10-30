package com.mannaggia.app

import android.app.Activity
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.os.Build
import androidx.core.content.FileProvider
import java.io.File

/** Share a card or a picture as an image with a line of text (album, main screen, quadro). */
object Condividi {

    fun card(activity: Activity, saint: String, image: Bitmap, text: String) =
        image(activity, Avatars.fileId(saint), "image/png", text) { image.compress(Bitmap.CompressFormat.PNG, 100, it) }

    /** Write the file [name] with [write] and open the share sheet; a target actually chosen counts for Evangelista. */
    fun image(activity: Activity, name: String, mime: String, text: String?, write: (java.io.OutputStream) -> Unit) {
        val ext = if (mime == "image/gif") "gif" else "png"
        val file = File(File(activity.cacheDir, "condivisi").apply { mkdirs() }, "$name.$ext")
        file.outputStream().use(write)
        val send = Intent(Intent.ACTION_SEND)
            .setType(mime)
            .putExtra(Intent.EXTRA_STREAM, FileProvider.getUriForFile(activity, "${activity.packageName}.condivisi", file))
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        if (text != null) send.putExtra(Intent.EXTRA_TEXT, text)
        // The system fills in the chosen component, so the PendingIntent must be mutable (explicit, our own receiver).
        val flags = PendingIntent.FLAG_UPDATE_CURRENT or
            (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) PendingIntent.FLAG_MUTABLE else 0)
        val chosen = PendingIntent.getBroadcast(activity, 0, Intent(activity, Scelta::class.java), flags)
        activity.startActivity(Intent.createChooser(send, activity.getString(R.string.share_chooser), chosen.intentSender))
    }

    /** Called by the share sheet when the user picks an app. */
    class Scelta : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) = Trofei.condivisione(context)
    }
}
