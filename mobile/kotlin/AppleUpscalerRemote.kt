package com.appleupscaler.studio.remote

import java.net.Socket
import java.io.OutputStream
import java.io.InputStream
import org.json.JSONObject

/**
 * Android Companion Controller & Remote Batch Queue Manager (Kotlin)
 * Manages remote preview scrubbing, render triggers, and real-time GPU telemetry.
 */
class AppleUpscalerRemote(private val host: String, private val port: Int = 8080) {
    private var socket: Socket? = null

    fun connect() {
        socket = Socket(host, port)
    }

    fun sendScrubTimestamp(timestampSec: Double) {
        val payload = JSONObject().apply {
            put("action", "seek")
            put("timestamp", timestampSec)
        }
        sendJson(payload)
    }

    fun triggerRemasterExport(outputFormat: String = "mp4") {
        val payload = JSONObject().apply {
            put("action", "export")
            put("format", outputFormat)
        }
        sendJson(payload)
    }

    private fun sendJson(json: JSONObject) {
        socket?.getOutputStream()?.let { out ->
            out.write((json.toString() + "\n").toByteArray(Charsets.UTF_8))
            out.flush()
        }
    }

    fun disconnect() {
        socket?.close()
        socket = null
    }
}
