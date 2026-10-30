package com.mannaggia.app

import android.app.Application

/** Applies the user's light/dark theme choice before any activity starts. */
class MannaggiaApp : Application() {
    override fun onCreate() {
        super.onCreate()
        Prefs.applyNightMode(this)
    }
}
