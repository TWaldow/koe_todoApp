package com.twaldow.koe.util

/**
 * Reine Helligkeitsberechnung ohne Android-Abhängigkeit, damit sie sich als JVM-Unit-Test
 * ohne Robolectric/Instrumentation testen lässt. Relative Luminanz (ITU-R BT.601),
 * Schwelle 0.6 statt 0.5, weil Weiß auf mittelhellen Farben (z. B. Gelb) sonst schwer
 * lesbar bleibt.
 */
fun needsDarkText(hexColor: String): Boolean {
    val hex = hexColor.removePrefix("#")
    require(hex.length == 6) { "Erwarte #RRGGBB, bekommen: $hexColor" }
    val r = hex.substring(0, 2).toInt(16)
    val g = hex.substring(2, 4).toInt(16)
    val b = hex.substring(4, 6).toInt(16)
    val luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return luminance > 0.6
}
