"""
lcd_display.py — ST7789 TFT LCD Display
=========================================
Board: Ruler Baseboard

Initialises the 240×135 pixel ST7789 TFT LCD and exposes helpers for:
  - Drawing filled rectangles and backgrounds
  - Displaying BMP sprite sheets / images
  - Animating positioned displayio Groups (for sprites or text)
  - Backlight control

Hardware pins (defined in the Ruler board variant)
--------------------------------------------------
  board.LCD_SPI()  — SPI bus factory function
  board.LCD_CS     — chip select
  board.D4         — data/command (DC) pin
  board.LCD_BL — backlight LED anode (PA06)

Requires
--------
  adafruit_st7789     (display driver)
  adafruit_imageload  (BMP sprite loading)
  fourwire / displayio

Use this module for:
  - Showing sensor data graphically
  - Sprite-based games
  - Status dashboards
  - IMU-driven animations
"""

import board
import displayio
import digitalio
import adafruit_imageload
import time

try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire

from adafruit_st7789 import ST7789

# Display dimensions
WIDTH  = 240
HEIGHT = 135


class LCDDisplay:
    """Drive the 240×135 ST7789 TFT LCD on the Ruler baseboard.

    Example
    -------
    >>> from lcd_display import LCDDisplay
    >>> lcd = LCDDisplay()
    >>> lcd.backlight_on()
    >>> lcd.fill_screen(0x001F)            # solid blue background
    >>> group = lcd.load_sprite("/Meatball_32x30_16color.bmp", 32, 30)
    >>> lcd.display.root_group = group
    """

    def __init__(self):
        # Backlight controlled via board.LCD_BL (PA06)
        self._backlight = digitalio.DigitalInOut(board.LCD_BL)
        self._backlight.direction = digitalio.Direction.OUTPUT
        self._backlight.value = False

        # Release any previously claimed display resources
        displayio.release_displays()

        spi    = board.LCD_SPI()
        tft_cs = board.LCD_CS
        tft_dc = board.D4

        display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs)
        self._display = ST7789(
            display_bus,
            rotation=90,
            width=WIDTH,
            height=HEIGHT,
            rowstart=40,
            colstart=53,
        )

    # -- Backlight -----------------------------------------------------------

    def backlight_on(self):
        """Turn the LCD backlight on."""
        self._backlight.value = False

    def backlight_off(self):
        """Turn the LCD backlight off."""
        self._backlight.value = True

    @property
    def display(self):
        """The raw ST7789 display object — use for direct displayio access."""
        return self._display

    # -- Background ----------------------------------------------------------

    def fill_screen(self, color_565: int = 0x0000):
        """Fill the entire screen with a 16-bit RGB565 colour.

        Parameters
        ----------
        color_565 : 16-bit colour, e.g. 0xF800 = red, 0x001F = blue

        Returns the root Group that was applied — you can append more elements.
        """
        bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
        palette = displayio.Palette(1)
        palette[0] = color_565
        tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
        group = displayio.Group()
        group.append(tile_grid)
        self._display.root_group = group
        return group

    # -- Sprite loading ------------------------------------------------------

    def load_sprite(self, bmp_path: str, sprite_w: int, sprite_h: int,
                    x: int = 0, y: int = 0) -> displayio.Group:
        """Load a BMP sprite sheet and return a positioned displayio.Group.

        The returned group contains a single TileGrid showing the first tile.
        Assign it to display.root_group or append it to an existing group.

        Parameters
        ----------
        bmp_path  : path to BMP file on the CIRCUITPY filesystem
        sprite_w  : tile width in pixels
        sprite_h  : tile height in pixels
        x, y      : initial pixel position

        Returns
        -------
        displayio.Group  (group.x / group.y can be modified to move the sprite)
        """
        sheet, palette = adafruit_imageload.load(
            bmp_path,
            bitmap=displayio.Bitmap,
            palette=displayio.Palette,
        )
        tile_grid = displayio.TileGrid(
            sheet,
            pixel_shader=palette,
            width=1,
            height=1,
            tile_width=sprite_w,
            tile_height=sprite_h,
        )
        group = displayio.Group(scale=1)
        group.append(tile_grid)
        group.x = x
        group.y = y
        return group

    # -- Sprite animation helpers --------------------------------------------

    def bounce_sprite(self, group: displayio.Group,
                      sprite_w: int, sprite_h: int,
                      dx: int = 2, dy: int = 3,
                      delay: float = 0.05):
        """Move a sprite group with wall-bouncing physics — single frame.

        Maintains velocity state internally on the group object.  Call this
        every loop iteration to animate the sprite.

        Parameters
        ----------
        group            : the displayio.Group to move
        sprite_w, sprite_h : sprite dimensions (for boundary checking)
        dx, dy           : initial pixel velocity (stored on group after first call)
        delay            : optional sleep per call (set 0 for time-managed loops)

        Example
        -------
        >>> group = lcd.load_sprite("/logo.bmp", 32, 30, x=100, y=50)
        >>> lcd.display.root_group = group
        >>> while True:
        ...     lcd.bounce_sprite(group, 32, 30)
        """
        # Store velocity as attributes on the group the first time
        if not hasattr(group, "_vx"):
            group._vx = dx
            group._vy = dy

        group.x += group._vx
        group.y += group._vy

        if group.x >= WIDTH - sprite_w:
            group.x = WIDTH - sprite_w
            group._vx = -abs(group._vx)
        if group.x <= 0:
            group.x = 0
            group._vx = abs(group._vx)
        if group.y >= HEIGHT - sprite_h:
            group.y = HEIGHT - sprite_h
            group._vy = -abs(group._vy)
        if group.y <= 0:
            group.y = 0
            group._vy = abs(group._vy)

        if delay:
            time.sleep(delay)

    def move_sprite_clamped(self, group: displayio.Group,
                             dx: int, dy: int,
                             sprite_w: int, sprite_h: int):
        """Move sprite by (dx, dy), clamping to display boundaries.

        Useful for IMU-driven movement where acceleration is mapped to delta.

        Parameters
        ----------
        group           : displayio.Group to move
        dx, dy          : pixel delta (can be positive or negative)
        sprite_w/h      : sprite dimensions for boundary clamping
        """
        group.x = max(0, min(WIDTH  - sprite_w, group.x + dx))
        group.y = max(0, min(HEIGHT - sprite_h, group.y + dy))
