"""
neopixels.py — NeoPixel RGB LED Strip
========================================
Board: Dev Board + Ruler Baseboard

Controls the NeoPixel RGB LED chain on board.NEOPIXEL:
  pixel 0     — on the dev board
  pixels 1-4  — on the Ruler baseboard (chained after the dev-board pixel)
With the baseboard attached the chain has 5 LEDs; the dev board on its own
has 1 (use NeoPixels(num_pixels=1)).

Use this module for:
  - Status indicators (colours per state)
  - Animations and light effects (rainbow, chase, pulse)
  - Visual feedback for sensor readings (colour-mapped values)
"""

import board
import neopixel
import time

try:
    from rainbowio import colorwheel
except ImportError:
    def colorwheel(pos: int) -> tuple:
        """Fallback colorwheel if rainbowio is not available."""
        pos = pos & 0xFF
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        if pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)

OFF = 0x000000

class Colors:
    
    WHITE      = 0xFFFFFF
    RED        = 0xFF0000
    GREEN      = 0x00FF00
    BLUE       = 0x0000FF
    ORANGE     = 0xFF8000
    YELLOW     = 0xFFFF00
    CYAN       = 0x00FFFF
    PURPLE     = 0xB400FF


class NeoPixels:
    """Drive the NeoPixel chain: pixel 0 on the dev board, pixels 1-4 on the baseboard.

    Parameters
    ----------
    pin         : NeoPixel data pin  (default board.NEOPIXEL)
    num_pixels  : number of LEDs     (default 5 = dev board + baseboard;
                                      use 1 for the dev board on its own)
    brightness  : global brightness  (default 0.1, range 0.0–1.0)

    Example - Basic usage: fill, set individual pixels, and rainbow cycle
    -------
import pykit_explorer
from neopixels import NeoPixels, Colors, OFF
px = NeoPixels()
while True:
    px.fill(Colors.RED)          # all red
    time.sleep(1)
    px.set(2, Colors.GREEN)      # pixel 2 green only
    time.sleep(1)
    px.set(3, OFF)               # pixel 3 off
    time.sleep(1)
    px.rainbow_cycle()    # blocking rainbow animation
    
    """

    def __init__(self, pin=board.NEOPIXEL, num_pixels: int = 5,
                 brightness: float = 0.1):
        self._pixels = neopixel.NeoPixel(pin, num_pixels,
                                          brightness=brightness,
                                          auto_write=False)
        self._n = num_pixels

    # -- Basic controls ------------------------------------------------------

    def fill(self, color: tuple):
        """Set all pixels to *color* and update the strip."""
        self._pixels.fill(color)
        self._pixels.show()

    def off(self):
        """Turn all pixels off."""
        self.fill(OFF)

    def set(self, index: int, color: tuple, show: bool = True):
        """Set a single pixel.

        Parameters
        ----------
        index : pixel index (0-based)
        color : (R, G, B) tuple
        show  : push update to strip immediately (default True)
        """
        self._pixels[index] = color
        if show:
            self._pixels.show()

    def set_all(self, colors: list):
        """Set each pixel from a list of (R,G,B) tuples, then update."""
        for i, c in enumerate(colors[:self._n]):
            self._pixels[i] = c
        self._pixels.show()

    @property
    def brightness(self) -> float:
        return self._pixels.brightness

    @brightness.setter
    def brightness(self, value: float):
        self._pixels.brightness = max(0.0, min(1.0, value))
        self._pixels.show()

    # -- Animations ----------------------------------------------------------

    def color_chase(self, color: tuple, wait: float = 0.1):
        """Light pixels one by one in *color* (blocking)."""
        for i in range(self._n):
            self._pixels[i] = color
            time.sleep(wait)
            self._pixels.show()
        time.sleep(0.5)

    def rainbow_cycle(self, wait: float = 0.0, cycles: int = 1):
        """Cycle through the colour wheel across all pixels (blocking)."""
        for _ in range(cycles):
            for j in range(255):
                for i in range(self._n):
                    rc_index = (i * 256 // self._n) + j
                    self._pixels[i] = colorwheel(rc_index & 255)
                self._pixels.show()
                time.sleep(wait)

    def pulse(self, color: tuple, steps: int = 20, delay: float = 0.05):
        """Fade *color* in and out once (blocking).

        Parameters
        ----------
        color : target (R, G, B)
        steps : number of brightness increments
        delay : seconds between steps
        """
        old_brightness = self._pixels.brightness
        self._pixels.fill(color)
        for i in range(steps + 1):
            self._pixels.brightness = (i / steps) * old_brightness
            self._pixels.show()
            time.sleep(delay)
        for i in range(steps, -1, -1):
            self._pixels.brightness = (i / steps) * old_brightness
            self._pixels.show()
            time.sleep(delay)
        self._pixels.brightness = old_brightness

    def map_value(self, value: float, min_val: float = 0.0,
                  max_val: float = 100.0):
        """Show a colour-mapped bar based on *value* within [min_val, max_val].

        Pixels light up from green (low) to red (high) as a bar graph.
        """
        fraction = max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
        lit = round(fraction * self._n)
        hue = int((1.0 - fraction) * 85)   # 85 = green, 0 = red in colorwheel
        color = colorwheel(hue)
        for i in range(self._n):
            self._pixels[i] = color if i < lit else OFF
        self._pixels.show()

    def deinit(self):
        """Turn all pixels off and release the data pin."""
        self.off()
        self._pixels.deinit()
