package com.mannaggia.app

import android.app.Activity
import android.content.Intent
import android.graphics.Bitmap
import androidx.core.content.FileProvider
import java.io.File

/** Share a card as an image with a line of text (album detail and main screen). */
object Condividi {

    fun card(activity: Activity, saint: String, image: Bitmap, text: String) {
        val file = File(File(activity.cacheDir, "condivisi").apply { mkdirs() }, "${Avatars.fileId(saint)}.png")
        file.outputStream().use { image.compress(Bitmap.CompressFormat.PNG, 100, it) }
        val send = Intent(Intent.ACTION_SEND)
            .setType("image/png")
            .putExtra(Intent.EXTRA_STREAM, FileProvider.getUriForFile(activity, "${activity.packageName}.condivisi", file))
            .putExtra(Intent.EXTRA_TEXT, text)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        activity.startActivity(Intent.createChooser(send, activity.getString(R.string.share_chooser)))
    }
}
