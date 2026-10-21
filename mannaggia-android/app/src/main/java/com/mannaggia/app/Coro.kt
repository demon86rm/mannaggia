package com.mannaggia.app

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.MediaPlayer
import kotlinx.coroutines.CompletableDeferred

/**
 * The short angelic choir played when a legendary saint is found for the first
 * time (res/raw/coro.ogg, about 3 s, synthesized by tools/suoni/coro.py). It
 * plays once and ends by itself, at the media volume whatever the ringer mode
 * (the user keeps the phone on silent). [done] completes when it has finished
 * (or could not be played, or was stopped).
 */
class Coro(private val context: Context) {

    private var player: MediaPlayer? = null
    val done = CompletableDeferred<Unit>()

    fun start() {
        val audio = context.getSystemService(AudioManager::class.java)
        val attrs = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_GAME)
            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
            .build()
        val session = audio?.generateAudioSessionId() ?: AudioManager.AUDIO_SESSION_ID_GENERATE
        val mp = MediaPlayer.create(context, R.raw.coro, attrs, session)
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
