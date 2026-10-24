plugins {
    id("com.android.application")
}

// Upload key for Play Store builds. Keep the keystore and passwords out of the
// repo: set these in ~/.gradle/gradle.properties (see README, "Release build").
val releaseStoreFile = providers.gradleProperty("MANNAGGIA_STORE_FILE").orNull

android {
    namespace = "com.mannaggia.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "io.github.demon86rm.mannaggia"
        minSdk = 24
        targetSdk = 36
        versionCode = 5
        versionName = "2.0.1"
    }

    signingConfigs {
        if (releaseStoreFile != null) {
            create("release") {
                storeFile = file(releaseStoreFile)
                storePassword = providers.gradleProperty("MANNAGGIA_STORE_PASSWORD").get()
                keyAlias = providers.gradleProperty("MANNAGGIA_KEY_ALIAS").get()
                keyPassword = providers.gradleProperty("MANNAGGIA_KEY_PASSWORD").get()
            }
        }
    }

    buildTypes {
        // Installs next to the Play version ("Mannaggia debug"), so testing doesn't touch its album.
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.findByName("release")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        viewBinding = true
        buildConfig = true
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.preference:preference-ktx:1.2.1")
    implementation("androidx.recyclerview:recyclerview:1.3.2")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
}
