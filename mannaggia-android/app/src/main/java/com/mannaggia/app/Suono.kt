package com.mannaggia.app

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.MediaPlayer
import androidx.annotation.RawRes
import kotlinx.coroutines.CompletableDeferred

/**
 * A short sound played once: the angelic choir of legendary saints
 * (R.raw.coro, tools/suoni/coro.py) or the trophy jingle (R.raw.trofeo,
 * tools/suoni/jingle.py). It plays at the media volume whatever the ringer mode
 * (the user keeps the phone on silent). [done] completes when it has finished
 * (or could not be played, or was stopped).
 */
class Suono(private val context: Context, @RawRes private val res: Int) {

    private var player: MediaPlayer? = null
    val done = CompletableDeferred<Unit>()

    fun start() {
        val audio = context.getSystemService(AudioManager::class.java)
        val attrs = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_GAME)
            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
            .build()
        val session = audio?.generateAudioSessionId() ?: AudioManager.AUDIO_SESSION_ID_GENERATE
        val mp = MediaPlayer.create(context, res, attrs, session)
        if (mp == null) {
            done.complete(Unit)
            return
        }
        mp.setOnCompletionListener { stop() }
        player = mp
        mp.start()
    }

    /** Stop at once (e.g. the app goes to the background). */
    fun stop() {
        player?.let { runCatching { it.stop() }; it.release() }
        player = null
        done.complete(Unit)
    }
}
