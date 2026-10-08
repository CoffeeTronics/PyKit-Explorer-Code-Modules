"""
apds9999.py — APDS9999 Proximity, Light & RGB Color Sensor
===========================================================
Breakout: Adafruit APDS9999 (I2C, QWIIC/STEMMA connector)

The APDS9999 is the successor to the APDS9960, offering improved proximity
and light sensing capabilities:

  1. Proximity  — measures distance (0–2047) with 8-11 bit resolution
  2. Light/RGB  — measures Red, Green, Blue, and IR channels (up to 20-bit)
  3. Lux        — calculates illuminance from the green channel

Unlike the APDS9960, the APDS9999 does NOT have gesture detection.
Both proximity and light sensing can run simultaneously.

Hardware
--------
  Connect the APDS9999 breakout to the QWIIC/STEMMA connector on the
  Ruler baseboard. Uses the shared I2C bus (board.SCL / board.SDA).

  Hardware Interrupt Pin (optional):
    For event-driven interrupts using the physical INT pin, the breakout
    must be placed in a breadboard with manual wiring of the I2C bus
    (SDA, SCL, VCC, GND) plus the INT pin to a digital input on your board.
    For most use cases, use check_interrupts() to poll via I2C instead.

Requires
--------
  adafruit_apds9999 library

Usage
-----
  Pass the .bus property from an i2c_bus.I2CBus instance:

import pykit_explorer
import time
from i2c_bus import I2CBus
from apds9999 import APDS9999Sensor
my_i2c = I2CBus()
sensor = APDS9999Sensor(my_i2c.bus)
while True:
     print("Prox", sensor.proximity)
     print("Lux", sensor.lux)
     print("Color (R,G,B,IR)", sensor.color)
     print()
     time.sleep(0.1)

Use this module for:
  - Proximity-triggered events and distance sensing
  - Color matching and color-driven NeoPixel reproduction
  - Ambient light measurement (lux)
  - Presence detection with light-level awareness
  - Combined proximity + color interactive projects
"""

import time
from adafruit_apds9999 import APDS9999

# Re-export library enums for user convenience
from adafruit_apds9999 import (
    LightGain,
    LightResolution,
    LightMeasurementRate,
    LightVariance,
    LightInterruptChannel,
    LedCurrent,
    LedFrequency,
    ProximityResolution,
    ProximityMeasurementRate,
)


class APDS9999Sensor:
    """Interface to the APDS9999 proximity and RGB color/light sensor.

    Parameters
    ----------
    i2c : raw busio.I2C object — pass i2c_bus_instance.bus

    Both proximity and light sensors are enabled by default with sensible
    settings (18-bit light resolution, 3x gain, 100ms measurement rate).

Example 1 - Basic Combined Reading
----------------------------------
Read both proximity and color values in a single loop.

import pykit_explorer
from i2c_bus import I2CBus
from apds9999 import APDS9999Sensor
my_i2c = I2CBus()
sensor = APDS9999Sensor(my_i2c.bus)
while True:
    print(f"Proximity: {sensor.proximity}  Lux: {sensor.lux:.1f}")
    r, g, b, ir = sensor.color
    print(f"R={r} G={g} B={b} IR={ir}")
    time.sleep(0.5)


Example 2 - Proximity-Scaled Color Display
------------------------------------------
NeoPixels show detected color with brightness scaled by proximity.
Closer objects make the LEDs brighter.

import pykit_explorer
from i2c_bus import I2CBus
from neopixels import NeoPixels
from apds9999 import APDS9999Sensor
my_i2c = I2CBus()
sensor = APDS9999Sensor(my_i2c.bus)
px = NeoPixels()
while True:
    r, g, b = sensor.color_as_neopixel()
    prox = sensor.proximity
    brightness = min(1.0, prox / 1000)  # Scale 0-1000 to 0.0-1.0
    scaled = (int(r * brightness), int(g * brightness), int(b * brightness))
    px.fill(scaled)
    time.sleep(0.05)


Example 3 - Light-Aware Proximity Alarm
---------------------------------------
Proximity triggers an alert only when the room is dark.
Useful for motion detection that ignores daytime activity.

import pykit_explorer
from i2c_bus import I2CBus
from apds9999 import APDS9999Sensor
my_i2c = I2CBus()
sensor = APDS9999Sensor(my_i2c.bus)
LUX_THRESHOLD = 50      # Consider "dark" below 50 lux
PROX_THRESHOLD = 500    # Trigger when something is close
while True:
    if sensor.lux < LUX_THRESHOLD and sensor.proximity > PROX_THRESHOLD:
        print("ALERT: Motion detected in dark room!")
    time.sleep(0.1)


Example 4 - Color Theremin
--------------------------
Proximity controls audio pitch, detected color drives NeoPixel strip.
Combines both sensors for an interactive musical instrument.

import pykit_explorer
from i2c_bus import I2CBus
from neopixels import NeoPixels
from apds9999 import APDS9999Sensor
from audio import Audio
my_i2c = I2CBus()
sensor = APDS9999Sensor(my_i2c.bus)
px = NeoPixels()
audio = Audio()
while True:
    # Proximity controls pitch (closer = higher pitch)
    dac_value = sensor.proximity_to_dac()
    audio.tone(dac_value)
    # Color controls NeoPixels
    px.fill(sensor.color_as_neopixel())
    time.sleep(0.02)


Example 5 - Presence + Ambient Logger
-------------------------------------
Log proximity and light levels for occupancy and environment monitoring.
Useful for data collection and analysis.

import pykit_explorer
from i2c_bus import I2CBus
from apds9999 import APDS9999Sensor
my_i2c = I2CBus()
sensor = APDS9999Sensor(my_i2c.bus)
print("Time(s), Proximity, Lux, R, G, B, IR")
start = time.monotonic()
while True:
    elapsed = time.monotonic() - start
    prox = sensor.proximity
    lux = sensor.lux
    r, g, b, ir = sensor.color
    print(f"{elapsed:.1f}, {prox}, {lux:.1f}, {r}, {g}, {b}, {ir}")
    time.sleep(1.0)
    """

    def __init__(self, i2c):
        self._apds = APDS9999(i2c)
        # Enable both sensors with sensible defaults
        self._apds.light_sensor_enabled = True
        self._apds.proximity_sensor_enabled = True
        self._apds.rgb_mode = True
        # Set sensible defaults for good balance of speed and accuracy
        self._apds.light_resolution = LightResolution.RES_18BIT
        self._apds.light_gain = LightGain.GAIN_3X
        self._apds.light_measurement_rate = LightMeasurementRate.RATE_100MS
        self._apds.proximity_resolution = ProximityResolution.RES_11BIT
        self._apds.proximity_measurement_rate = ProximityMeasurementRate.RATE_100MS

    # =========================================================================
    # Simple Properties — immediate use for beginners
    # =========================================================================

    @property
    def proximity(self) -> int:
        """Proximity reading as an 11-bit value (0–2047).

        0 = nothing detected, 2047 = very close.
        """
        return self._apds.proximity

    @property
    def proximity_overflow(self) -> bool:
        """True if the proximity sensor was saturated during the last read.

        Check this after reading proximity to detect if the object was
        too close for accurate measurement.
        """
        return self._apds.proximity_read_overflow

    @property
    def color(self) -> tuple:
        """Raw RGBIR color data as (red, green, blue, ir).

        Values are up to 20-bit (0–1048575) depending on light_resolution.
        Default 18-bit resolution gives values 0–262143.
        """
        return self._apds.rgb_ir

    @property
    def rgb(self) -> tuple:
        """RGB color data scaled to 8-bit (0–255) as (red, green, blue).

        Automatically scales based on current light_resolution setting.
        """
        return self._apds.rgb

    @property
    def lux(self) -> float:
        """Calculated illuminance in lux.

        Uses the green channel with current gain and resolution settings.
        Not available with RES_13BIT resolution (raises ValueError).
        """
        _, g, _, _ = self._apds.rgb_ir
        return self._apds.calculate_lux(g)

    # =========================================================================
    # Convenience Methods — common operations made easy
    # =========================================================================

    def color_as_neopixel(self) -> tuple:
        """Convert the RGB reading to an 8-bit (R, G, B) NeoPixel tuple.

        Returns
        -------
        (r, g, b) tuple with values 0–255, ready for NeoPixel fill()
        """
        return self._apds.rgb

    def color_as_hex(self) -> int:
        """Convert the RGB reading to a single 24-bit hex color integer.

        Returns
        -------
        Integer in the form 0xRRGGBB, usable directly with NeoPixel fill()
        or display text label color properties.
        """
        r, g, b = self._apds.rgb
        return (r << 16) | (g << 8) | b

    def proximity_to_dac(self) -> int:
        """Map the 11-bit proximity value to a 16-bit DAC value (0–65535).

        Useful for driving an analog tone pitch proportional to distance.
        """
        return min(self._apds.proximity << 5, 65535)

    def is_near(self, threshold: int = 500) -> bool:
        """Check if something is within proximity threshold.

        Parameters
        ----------
        threshold : proximity value to consider "near" (default 500)

        Returns
        -------
        True if proximity >= threshold
        """
        return self._apds.proximity >= threshold

    def wait_for_proximity(self, threshold: int = 500, timeout: float = 5.0) -> bool:
        """Block until proximity exceeds threshold or timeout expires.

        Parameters
        ----------
        threshold : proximity value to trigger on (default 500)
        timeout : maximum seconds to wait (default 5.0)

        Returns
        -------
        True if threshold was reached, False on timeout
        """
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self._apds.proximity >= threshold:
                return True
            time.sleep(0.01)
        return False

    # =========================================================================
    # Interrupt Support — I2C polling mode
    # =========================================================================

    def set_proximity_thresholds(self, low: int = 0, high: int = 2047):
        """Set proximity interrupt thresholds.

        An interrupt triggers when proximity goes below low or above high.

        Parameters
        ----------
        low : lower threshold (0–2047), default 0
        high : upper threshold (0–2047), default 2047
        """
        self._apds.proximity_threshold_low = low
        self._apds.proximity_threshold_high = high
        self._apds.proximity_interrupt_enabled = True

    def set_light_thresholds(self, low: int = 0, high: int = 1048575):
        """Set light sensor interrupt thresholds.

        An interrupt triggers when the selected channel goes below low
        or above high. Use light_interrupt_channel to select which
        channel (IR, Green, Red, or Blue) is compared.

        Parameters
        ----------
        low : lower threshold (0–1048575 for 20-bit), default 0
        high : upper threshold (0–1048575 for 20-bit), default max
        """
        self._apds.light_threshold_low = low
        self._apds.light_threshold_high = high
        self._apds.light_interrupt_enabled = True

    def check_interrupts(self) -> dict:
        """Check interrupt status flags via I2C.

        Reading this clears the interrupt flags on the device.

        Returns
        -------
        Dictionary with keys:
          - proximity_ready: new proximity data available
          - proximity_interrupt: proximity threshold crossed
          - light_ready: new light data available
          - light_interrupt: light threshold crossed
          - power_on_reset: device was reset since last check
        """
        status = self._apds.main_status
        return {
            "proximity_ready": status[0],
            "proximity_interrupt": status[1],
            "proximity_logic": status[2],
            "light_ready": status[3],
            "light_interrupt": status[4],
            "power_on_reset": status[5],
        }

    def clear_interrupts(self):
        """Clear all interrupt flags by reading main_status."""
        _ = self._apds.main_status

    # =========================================================================
    # Advanced Configuration — for power users
    # =========================================================================

    @property
    def light_gain(self) -> int:
        """Light sensor analog gain.

        Values: LightGain.GAIN_1X, GAIN_3X, GAIN_6X, GAIN_9X, GAIN_18X
        Higher gain = more sensitivity in low light, but saturates faster.
        """
        return self._apds.light_gain

    @light_gain.setter
    def light_gain(self, value: int):
        self._apds.light_gain = value

    @property
    def light_resolution(self) -> int:
        """Light sensor ADC resolution.

        Values: LightResolution.RES_20BIT (400ms), RES_19BIT (200ms),
                RES_18BIT (100ms), RES_17BIT (50ms), RES_16BIT (25ms),
                RES_13BIT (3.125ms)
        Higher resolution = more accuracy but slower conversion.
        """
        return self._apds.light_resolution

    @light_resolution.setter
    def light_resolution(self, value: int):
        self._apds.light_resolution = value

    @property
    def light_measurement_rate(self) -> int:
        """How frequently the light sensor takes readings.

        Values: LightMeasurementRate.RATE_25MS through RATE_2000MS
        Should be >= conversion time for the selected resolution.
        """
        return self._apds.light_measurement_rate

    @light_measurement_rate.setter
    def light_measurement_rate(self, value: int):
        self._apds.light_measurement_rate = value

    @property
    def proximity_resolution(self) -> int:
        """Proximity sensor ADC resolution.

        Values: ProximityResolution.RES_8BIT, RES_9BIT, RES_10BIT, RES_11BIT
        Higher resolution = finer distance discrimination.
        """
        return self._apds.proximity_resolution

    @proximity_resolution.setter
    def proximity_resolution(self, value: int):
        self._apds.proximity_resolution = value

    @property
    def proximity_measurement_rate(self) -> int:
        """How frequently the proximity sensor takes readings.

        Values: ProximityMeasurementRate.RATE_6MS through RATE_400MS
        """
        return self._apds.proximity_measurement_rate

    @proximity_measurement_rate.setter
    def proximity_measurement_rate(self, value: int):
        self._apds.proximity_measurement_rate = value

    @property
    def led_current(self) -> int:
        """IR LED drive current for proximity sensing.

        Values: LedCurrent.MA_10 (10mA), LedCurrent.MA_25 (25mA)
        Higher current = stronger signal, more range, more power.
        """
        return self._apds.led_current

    @led_current.setter
    def led_current(self, value: int):
        self._apds.led_current = value

    @property
    def led_frequency(self) -> int:
        """IR LED pulse modulation frequency.

        Values: LedFrequency.KHZ_60 through KHZ_100
        """
        return self._apds.led_frequency

    @led_frequency.setter
    def led_frequency(self, value: int):
        self._apds.led_frequency = value

    @property
    def led_pulses(self) -> int:
        """Number of IR LED pulses per proximity measurement (0–255)."""
        return self._apds.led_pulses

    @led_pulses.setter
    def led_pulses(self, value: int):
        self._apds.led_pulses = value

    @property
    def light_interrupt_channel(self) -> int:
        """Which light channel is compared against interrupt thresholds.

        Values: LightInterruptChannel.IR, GREEN, RED, BLUE
        """
        return self._apds.light_interrupt_channel

    @light_interrupt_channel.setter
    def light_interrupt_channel(self, value: int):
        self._apds.light_interrupt_channel = value

    @property
    def proximity_cancellation(self) -> int:
        """Digital proximity cancellation level (0–2047).

        Subtracts this value from raw proximity readings to compensate
        for crosstalk or ambient IR.
        """
        return self._apds.proximity_cancellation

    @proximity_cancellation.setter
    def proximity_cancellation(self, value: int):
        self._apds.proximity_cancellation = value

    # =========================================================================
    # Sensor Control
    # =========================================================================

    def enable_proximity(self):
        """Enable the proximity sensor."""
        self._apds.proximity_sensor_enabled = True

    def disable_proximity(self):
        """Disable the proximity sensor to save power."""
        self._apds.proximity_sensor_enabled = False

    def enable_light(self):
        """Enable the light/RGB sensor."""
        self._apds.light_sensor_enabled = True

    def disable_light(self):
        """Disable the light/RGB sensor to save power."""
        self._apds.light_sensor_enabled = False

    def disable_all(self):
        """Disable both sensors to enter low-power standby mode."""
        self._apds.proximity_sensor_enabled = False
        self._apds.light_sensor_enabled = False

    def reset(self):
        """Perform a software reset of the sensor.

        Re-initializes the sensor to default hardware state.
        You will need to re-enable sensors and reconfigure settings.

        Note: Software reset may fail on some hardware configurations.
        If reset fails, the sensor continues operating normally.
        """
        # I2C bus may need settling; retry with increasing delays
        for attempt in range(5):
            try:
                # Read to ensure I2C bus is responsive before reset
                _ = self._apds.proximity
                time.sleep(0.02 * (attempt + 1))
                self._apds.reset()
                time.sleep(0.15)
                self._apds.light_sensor_enabled = True
                self._apds.proximity_sensor_enabled = True
                self._apds.rgb_mode = True
                return
            except OSError:
                time.sleep(0.1 * (attempt + 1))
                if attempt == 4:
                    raise

    # =========================================================================
    # Logging / Debug
    # =========================================================================

    def print_proximity(self):
        """Print the current proximity reading to the console."""
        prox = self.proximity
        overflow = " (OVERFLOW)" if self.proximity_overflow else ""
        print(f"Proximity: {prox}{overflow}")

    def print_color(self):
        """Print the current color and light readings to the console."""
        r, g, b, ir = self.color
        r8, g8, b8 = self.rgb
        print(f"Raw:      R={r}  G={g}  B={b}  IR={ir}")
        print(f"8-bit:    R={r8}  G={g8}  B={b8}")
        print(f"Hex:      0x{self.color_as_hex():06X}")
        try:
            print(f"Lux:      {self.lux:.1f}")
        except ValueError:
            print("Lux:      N/A (use RES_16BIT or higher)")

    def print_status(self):
        """Print full sensor status and configuration."""
        print("=== APDS9999 Status ===")
        self.print_proximity()
        self.print_color()
        print(f"Light Gain:       {LightGain.get_name(self.light_gain)}")
        print(f"Light Resolution: {LightResolution.get_name(self.light_resolution)}")
        print(f"Prox Resolution:  {ProximityResolution.get_name(self.proximity_resolution)}")
