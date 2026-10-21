package com.twaldow.koe.util

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ColorContrastTest {

    @Test
    fun `dark text on bright yellow`() {
        assertTrue(needsDarkText("#FDD835"))
    }

    @Test
    fun `light text on dark blue`() {
        assertFalse(needsDarkText("#4169E1"))
    }

    @Test
    fun `white needs dark text, black does not`() {
        assertTrue(needsDarkText("#FFFFFF"))
        assertFalse(needsDarkText("#000000"))
    }

    @Test
    fun `works without a leading hash`() {
        assertTrue(needsDarkText("FDD835"))
    }
}
