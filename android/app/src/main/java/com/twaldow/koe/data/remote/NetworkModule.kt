package com.twaldow.koe.data.remote

import com.twaldow.koe.BuildConfig
import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.Retrofit

/** Haengt den Bearer-Token aus BuildConfig an jeden Request (siehe spec-v1.md, Abschnitt 3). */
private class AuthInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer ${BuildConfig.API_TOKEN}")
            .build()
        return chain.proceed(request)
    }
}

/**
 * Einfaches, objektbasiertes DI: kein Hilt/Koin fuer dieses kleine Projekt, ein globales
 * Singleton reicht. `encodeDefaults` bleibt false (Standard), damit FolderUpdateRequest
 * echte Teil-Updates schicken kann (nicht gesetzte Felder werden weggelassen); siehe
 * TodoUpdateRequest fuer den Fall, der trotzdem explizites `null` braucht.
 */
object NetworkModule {

    private val json = Json {
        ignoreUnknownKeys = true
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(AuthInterceptor())
        .addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC })
        .build()

    val api: KoeApi = Retrofit.Builder()
        .baseUrl(BuildConfig.BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()
        .create(KoeApi::class.java)
}
