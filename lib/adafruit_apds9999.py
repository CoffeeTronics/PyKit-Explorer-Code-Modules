# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_apds9999`
================================================================================

CircuitPython driver for Broadcom APDS-9999 Light + RGB + Proximity


* Author(s): Tim Cocks

Implementation Notes
--------------------

**Hardware:**

* `APDS9999 <https://www.adafruit.com/product/6461>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

__version__ = "1.2.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_APDS9999.git"

import time

from adafruit_bus_device import i2c_device
from adafruit_register.i2c_bit import RWBit
from adafruit_register.i2c_bits import ROBits, RWBits
from adafruit_register.i2c_struct import UnaryStruct
from adafruit_simplemath import map_range
from micropython import const

try:
    from typing import Optional, Tuple

    import busio
except ImportError:
    pass

# Default I2C address
_APDS9999_DEFAULT_ADDR = const(0x52)

# Register addresses
_APDS9999_REG_MAIN_CTRL = const(0x00)  # Main control register
_APDS9999_REG_PS_VCSEL = const(0x01)  # PS VCSEL control register
_APDS9999_REG_PS_PULSES = const(0x02)  # PS pulses control register
_APDS9999_REG_PS_MEAS_RATE = const(0x03)  # PS measurement rate
_APDS9999_REG_LS_MEAS_RATE = const(0x04)  # LS measurement rate
_APDS9999_REG_LS_GAIN = const(0x05)  # LS gain control
_APDS9999_REG_PART_ID = const(0x06)  # Part ID register
_APDS9999_REG_MAIN_STATUS = const(0x07)  # Main status register
_APDS9999_REG_PS_DATA_0 = const(0x08)  # PS data low byte
_APDS9999_REG_PS_DATA_1 = const(0x09)  # PS data high byte
_APDS9999_REG_LS_DATA_IR_0 = const(0x0A)  # IR data low byte
_APDS9999_REG_LS_DATA_IR_1 = const(0x0B)  # IR data middle byte
_APDS9999_REG_LS_DATA_IR_2 = const(0x0C)  # IR data high byte
_APDS9999_REG_LS_DATA_GREEN_0 = const(0x0D)  # Green data low byte
_APDS9999_REG_LS_DATA_GREEN_1 = const(0x0E)  # Green data middle byte
_APDS9999_REG_LS_DATA_GREEN_2 = const(0x0F)  # Green data high byte
_APDS9999_REG_LS_DATA_BLUE_0 = const(0x10)  # Blue data low byte
_APDS9999_REG_LS_DATA_BLUE_1 = const(0x11)  # Blue data middle byte
_APDS9999_REG_LS_DATA_BLUE_2 = const(0x12)  # Blue data high byte
_APDS9999_REG_LS_DATA_RED_0 = const(0x13)  # Red data low byte
_APDS9999_REG_LS_DATA_RED_1 = const(0x14)  # Red data middle byte
_APDS9999_REG_LS_DATA_RED_2 = const(0x15)  # Red data high byte
_APDS9999_REG_INT_CFG = const(0x19)  # Interrupt configuration
_APDS9999_REG_INT_PST = const(0x1A)  # Interrupt persistence
_APDS9999_REG_PS_THRES_UP_0 = const(0x1B)  # PS upper threshold low byte
_APDS9999_REG_PS_THRES_UP_1 = const(0x1C)  # PS upper threshold high byte
_APDS9999_REG_PS_THRES_LOW_0 = const(0x1D)  # PS lower threshold low byte
_APDS9999_REG_PS_THRES_LOW_1 = const(0x1E)  # PS lower threshold high byte
_APDS9999_REG_PS_CAN_0 = const(0x1F)  # PS cancellation level low byte
_APDS9999_REG_PS_CAN_1 = const(0x20)  # PS cancellation level high byte
_APDS9999_REG_LS_THRES_UP_0 = const(0x21)  # LS upper threshold low byte
_APDS9999_REG_LS_THRES_UP_1 = const(0x22)  # LS upper threshold middle byte
_APDS9999_REG_LS_THRES_UP_2 = const(0x23)  # LS upper threshold high byte
_APDS9999_REG_LS_THRES_LOW_0 = const(0x24)  # LS lower threshold low byte
_APDS9999_REG_LS_THRES_LOW_1 = const(0x25)  # LS lower threshold middle byte
_APDS9999_REG_LS_THRES_LOW_2 = const(0x26)  # LS lower threshold high byte
_APDS9999_REG_LS_THRES_VAR = const(0x27)  # LS variance threshold

# Expected value of the full PART_ID register (0x06) upper nibble 0xC = part,
# lower nibble 0x2 = revision.
_APDS9999_PART_ID = const(0xC2)


class CV:
    """Constant value class helper for enums."""

    @classmethod
    def is_valid(cls, value: int) -> bool:
        """Validate that a given value is a member."""
        IGNORE_LIST = [cls.__module__, cls.__name__]
        if value in cls.__dict__.values() and value not in IGNORE_LIST:
            return True
        return False

    @classmethod
    def get_name(cls, value: int) -> str:
        """Get the name for a given value."""
        name_dict = {}
        for _key, _value in cls.__dict__.items():
            name_dict[_value] = _key
        return name_dict[value]


class LightResolution(CV):
    """Light sensor ADC resolution settings for the LS_MEAS_RATE register (0x04), bits 6:4.

    Higher resolution increases accuracy but also increases conversion time.

    +--------------------------------------+-------------+------------------+
    | Setting                              | Resolution  | Conversion time  |
    +======================================+=============+==================+
    | :py:const:`LightResolution.RES_20BIT`| 20-bit      | 400 ms           |
    +--------------------------------------+-------------+------------------+
    | :py:const:`LightResolution.RES_19BIT`| 19-bit      | 200 ms           |
    +--------------------------------------+-------------+------------------+
    | :py:const:`LightResolution.RES_18BIT`| 18-bit      | 100 ms           |
    +--------------------------------------+-------------+------------------+
    | :py:const:`LightResolution.RES_17BIT`| 17-bit      | 50 ms            |
    +--------------------------------------+-------------+------------------+
    | :py:const:`LightResolution.RES_16BIT`| 16-bit      | 25 ms            |
    +--------------------------------------+-------------+------------------+
    | :py:const:`LightResolution.RES_13BIT`| 13-bit      | 3.125 ms         |
    +--------------------------------------+-------------+------------------+
    """

    RES_20BIT = 0x00  # 20-bit resolution (400 ms conversion)
    RES_19BIT = 0x01  # 19-bit resolution (200 ms conversion)
    RES_18BIT = 0x02  # 18-bit resolution (100 ms conversion)
    RES_17BIT = 0x03  # 17-bit resolution (50 ms conversion)
    RES_16BIT = 0x04  # 16-bit resolution (25 ms conversion)
    RES_13BIT = 0x05  # 13-bit resolution (3.125 ms conversion)


class LightVariance(CV):
    """Light sensor variance threshold settings for the LS_THRES_VAR register (0x27), bits 2:0.

    Sets the count variance required to trigger a light interrupt when
    :attr:`light_variance_mode` is enabled.

    +------------------------------------+-----------------+
    | Setting                            | Variance count  |
    +====================================+=================+
    | :py:const:`LightVariance.VAR_8`    | 8               |
    +------------------------------------+-----------------+
    | :py:const:`LightVariance.VAR_16`   | 16              |
    +------------------------------------+-----------------+
    | :py:const:`LightVariance.VAR_32`   | 32              |
    +------------------------------------+-----------------+
    | :py:const:`LightVariance.VAR_64`   | 64              |
    +------------------------------------+-----------------+
    | :py:const:`LightVariance.VAR_128`  | 128             |
    +------------------------------------+-----------------+
    | :py:const:`LightVariance.VAR_256`  | 256             |
    +------------------------------------+-----------------+
    | :py:const:`LightVariance.VAR_512`  | 512             |
    +------------------------------------+-----------------+
    | :py:const:`LightVariance.VAR_1024` | 1024            |
    +------------------------------------+-----------------+
    """

    VAR_8 = 0x00  # 8 count variance
    VAR_16 = 0x01  # 16 count variance
    VAR_32 = 0x02  # 32 count variance
    VAR_64 = 0x03  # 64 count variance
    VAR_128 = 0x04  # 128 count variance
    VAR_256 = 0x05  # 256 count variance
    VAR_512 = 0x06  # 512 count variance
    VAR_1024 = 0x07  # 1024 count variance


class LightInterruptChannel(CV):
    """Light sensor interrupt channel settings for the INT_CFG register (0x19), bits 5:4.

    Selects which light sensor channel is compared against the interrupt thresholds.

    +-----------------------------------------------+-----------------+
    | Setting                                       | Channel         |
    +===============================================+=================+
    | :py:const:`LightInterruptChannel.IR`          | IR channel      |
    +-----------------------------------------------+-----------------+
    | :py:const:`LightInterruptChannel.GREEN`       | Green channel   |
    +-----------------------------------------------+-----------------+
    | :py:const:`LightInterruptChannel.RED`         | Red channel     |
    +-----------------------------------------------+-----------------+
    | :py:const:`LightInterruptChannel.BLUE`        | Blue channel    |
    +-----------------------------------------------+-----------------+
    """

    IR = 0x00  # IR channel
    GREEN = 0x01  # Green channel
    RED = 0x02  # Red channel
    BLUE = 0x03  # Blue channel


class LedCurrent(CV):
    """LED drive current settings for the PS_VCSEL register (0x01), bits 2:0.

    Controls the IR LED current used during proximity measurements.

    +----------------------------------+------------+
    | Setting                          | Current    |
    +==================================+============+
    | :py:const:`LedCurrent.MA_10`     | 10 mA      |
    +----------------------------------+------------+
    | :py:const:`LedCurrent.MA_25`     | 25 mA      |
    +----------------------------------+------------+
    """

    MA_10 = 0x02  # 10 mA
    MA_25 = 0x03  # 25 mA


class LedFrequency(CV):
    """LED pulse frequency settings for the PS_VCSEL register (0x01), bits 6:4.

    Controls the modulation frequency of the IR LED pulses used during
    proximity measurements.

    +----------------------------------+------------+
    | Setting                          | Frequency  |
    +==================================+============+
    | :py:const:`LedFrequency.KHZ_60`  | 60 kHz     |
    +----------------------------------+------------+
    | :py:const:`LedFrequency.KHZ_70`  | 70 kHz     |
    +----------------------------------+------------+
    | :py:const:`LedFrequency.KHZ_80`  | 80 kHz     |
    +----------------------------------+------------+
    | :py:const:`LedFrequency.KHZ_90`  | 90 kHz     |
    +----------------------------------+------------+
    | :py:const:`LedFrequency.KHZ_100` | 100 kHz    |
    +----------------------------------+------------+
    """

    KHZ_60 = 0x03  # 60 kHz
    KHZ_70 = 0x04  # 70 kHz
    KHZ_80 = 0x05  # 80 kHz
    KHZ_90 = 0x06  # 90 kHz
    KHZ_100 = 0x07  # 100 kHz


class LightMeasurementRate(CV):
    """Light sensor measurement rate settings for the LS_MEAS_RATE register (0x04), bits 2:0.

    Controls how frequently the light sensor takes a reading. The measurement
    rate should be set equal to or slower than the resolution's conversion time
    to avoid reading stale data.

    +-----------------------------------------------+-------------------+
    | Setting                                       | Rate              |
    +===============================================+===================+
    | :py:const:`LightMeasurementRate.RATE_25MS`    | 25 ms             |
    +-----------------------------------------------+-------------------+
    | :py:const:`LightMeasurementRate.RATE_50MS`    | 50 ms             |
    +-----------------------------------------------+-------------------+
    | :py:const:`LightMeasurementRate.RATE_100MS`   | 100 ms (default)  |
    +-----------------------------------------------+-------------------+
    | :py:const:`LightMeasurementRate.RATE_200MS`   | 200 ms            |
    +-----------------------------------------------+-------------------+
    | :py:const:`LightMeasurementRate.RATE_500MS`   | 500 ms            |
    +-----------------------------------------------+-------------------+
    | :py:const:`LightMeasurementRate.RATE_1000MS`  | 1000 ms           |
    +-----------------------------------------------+-------------------+
    | :py:const:`LightMeasurementRate.RATE_2000MS`  | 2000 ms           |
    +-----------------------------------------------+-------------------+
    """

    RATE_25MS = 0x00  # 25 ms measurement rate
    RATE_50MS = 0x01  # 50 ms measurement rate
    RATE_100MS = 0x02  # 100 ms measurement rate (default)
    RATE_200MS = 0x03  # 200 ms measurement rate
    RATE_500MS = 0x04  # 500 ms measurement rate
    RATE_1000MS = 0x05  # 1000 ms measurement rate
    RATE_2000MS = 0x06  # 2000 ms measurement rate


class ProximityResolution(CV):
    """Proximity sensor ADC resolution settings for the PS_MEAS_RATE register (0x03), bits 4:3.

    Higher resolution increases accuracy at the cost of a longer conversion time.

    +------------------------------------------+-------------+
    | Setting                                  | Resolution  |
    +==========================================+=============+
    | :py:const:`ProximityResolution.RES_8BIT` | 8-bit       |
    +------------------------------------------+-------------+
    | :py:const:`ProximityResolution.RES_9BIT` | 9-bit       |
    +------------------------------------------+-------------+
    | :py:const:`ProximityResolution.RES_10BIT`| 10-bit      |
    +------------------------------------------+-------------+
    | :py:const:`ProximityResolution.RES_11BIT`| 11-bit      |
    +------------------------------------------+-------------+
    """

    RES_8BIT = 0x00  # 8-bit resolution (hardware default)
    RES_9BIT = 0x01  # 9-bit resolution
    RES_10BIT = 0x02  # 10-bit resolution
    RES_11BIT = 0x03  # 11-bit resolution


class ProximityMeasurementRate(CV):
    """Proximity sensor measurement rate settings for the PS_MEAS_RATE register (0x03), bits 2:0.

    Controls how frequently the proximity sensor takes a reading.

    .. note::
        CircuitPython makes no guarantee about realtime
        behavior, the faster measurement rates may take
        longer than indicated.

    +--------------------------------------------------+-------------------+
    | Setting                                          | Rate              |
    +==================================================+===================+
    | :py:const:`ProximityMeasurementRate.RATE_6MS`    | 6.25 ms           |
    +--------------------------------------------------+-------------------+
    | :py:const:`ProximityMeasurementRate.RATE_12MS`   | 12.5 ms           |
    +--------------------------------------------------+-------------------+
    | :py:const:`ProximityMeasurementRate.RATE_25MS`   | 25 ms             |
    +--------------------------------------------------+-------------------+
    | :py:const:`ProximityMeasurementRate.RATE_50MS`   | 50 ms             |
    +--------------------------------------------------+-------------------+
    | :py:const:`ProximityMeasurementRate.RATE_100MS`  | 100 ms (default)  |
    +--------------------------------------------------+-------------------+
    | :py:const:`ProximityMeasurementRate.RATE_200MS`  | 200 ms            |
    +--------------------------------------------------+-------------------+
    | :py:const:`ProximityMeasurementRate.RATE_400MS`  | 400 ms            |
    +--------------------------------------------------+-------------------+
    """

    RATE_6MS = 0x01  # 6.25 ms measurement rate
    RATE_12MS = 0x02  # 12.5 ms measurement rate
    RATE_25MS = 0x03  # 25 ms measurement rate
    RATE_50MS = 0x04  # 50 ms measurement rate
    RATE_100MS = 0x05  # 100 ms measurement rate (default)
    RATE_200MS = 0x06  # 200 ms measurement rate
    RATE_400MS = 0x07  # 400 ms measurement rate


class LightGain(CV):
    """Light sensor gain settings for the LS_GAIN register (0x05).

    Controls the analogue gain applied to the light sensor channels.

    +--------------------------------+----------+
    | Setting                        | Gain     |
    +================================+==========+
    | :py:const:`LightGain.GAIN_1X`  | 1x gain  |
    +--------------------------------+----------+
    | :py:const:`LightGain.GAIN_3X`  | 3x gain  |
    +--------------------------------+----------+
    | :py:const:`LightGain.GAIN_6X`  | 6x gain  |
    +--------------------------------+----------+
    | :py:const:`LightGain.GAIN_9X`  | 9x gain  |
    +--------------------------------+----------+
    | :py:const:`LightGain.GAIN_18X` | 18x gain |
    +--------------------------------+----------+
    """

    GAIN_1X = 0x00  # 1x gain
    GAIN_3X = 0x01  # 3x gain
    GAIN_6X = 0x02  # 6x gain
    GAIN_9X = 0x03  # 9x gain
    GAIN_18X = 0x04  # 18x gain


class APDS9999:
    """CircuitPython driver for the Broadcom APDS-9999 Digital Proximity and
    RGB Color Sensor.

    :param ~busio.I2C i2c_bus: The I2C bus the device is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x52`.

    **Quickstart: Importing and using the device**

        Here is an example of using the :class:`APDS9999`.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import board
            from adafruit_apds9999 import APDS9999

        Once this is done you can define your `board.I2C` object and define your sensor object

        .. code-block:: python

            i2c = board.I2C()  # uses board.SCL and board.SDA
            sensor = APDS9999(i2c)

        Now you have access to the sensor data

        .. code-block:: python

            r, g, b, ir = sensor.color_data
            proximity = sensor.proximity
    """

    # PART_ID register (0x06) full 8-bit read-only value.
    # Upper nibble (bits 7:4) = part number (0xC for APDS-9999).
    # Lower nibble (bits 3:0) = revision ID.
    _part_id = ROBits(8, _APDS9999_REG_PART_ID, 0)

    # MAIN_CTRL register (0x00), bit 4 software reset
    _reset = RWBit(_APDS9999_REG_MAIN_CTRL, 4)

    # MAIN_CTRL register (0x00), bit 1 enables the light (ALS/RGB) sensor.
    light_sensor_enabled = RWBit(_APDS9999_REG_MAIN_CTRL, 1)
    """Enable or disable the light sensor"""

    # MAIN_CTRL register (0x00), bit 0 enables the proximity sensor.
    proximity_sensor_enabled = RWBit(_APDS9999_REG_MAIN_CTRL, 0)
    """Enable or disable the proximity sensor"""

    # MAIN_CTRL register (0x00), bit 2 selects RGB mode (True) vs ALS mode (False).
    rgb_mode = RWBit(_APDS9999_REG_MAIN_CTRL, 2)
    """Enable or disable RGB mode. True is RGB mode, False is ALS mode"""

    # MAIN_CTRL register (0x00), bit 6 sleep after proximity interrupt.
    proximity_sleep_after_interrupt = RWBit(_APDS9999_REG_MAIN_CTRL, 6)
    """Disable the proximity sensor after interrupt. You must also read ``main_status``
    after the interrupt for the sleep to take effect. Once asleep, the sensor can be
    re-enabled with ``proximity_sensor_enabled``"""

    # MAIN_CTRL register (0x00), bit 5 sleep after light interrupt.
    light_sleep_after_interrupt = RWBit(_APDS9999_REG_MAIN_CTRL, 5)
    """Disable the light sensor after interrupt. You must also read ``main_status``
    after the interrupt for the sleep to take effect. Once asleep, the sensor can be
    re-enabled with ``light_sensor_enabled``"""

    # LS_GAIN register (0x05), bits 2:0 analogue gain for the light sensor channels.
    _light_gain = RWBits(3, _APDS9999_REG_LS_GAIN, 0)

    # LS_MEAS_RATE register (0x04), bits 6:4 ADC resolution of the light sensor.
    _light_resolution = RWBits(3, _APDS9999_REG_LS_MEAS_RATE, 4)

    # LS_MEAS_RATE register (0x04), bits 2:0 how frequently the light sensor measures.
    _light_measurement_rate = RWBits(3, _APDS9999_REG_LS_MEAS_RATE, 0)

    # PS_MEAS_RATE register (0x03), bits 4:3 ADC resolution of the proximity sensor.
    _proximity_resolution = RWBits(2, _APDS9999_REG_PS_MEAS_RATE, 3)

    # PS_MEAS_RATE register (0x03), bits 2:0 measurement rate of the proximity sensor.
    _proximity_measurement_rate = RWBits(3, _APDS9999_REG_PS_MEAS_RATE, 0)

    # PS_DATA_0/1 registers (0x08-0x09) raw 16-bit proximity data word, little-endian.
    # Bits 10:0 are the 11-bit proximity count; bit 11 is the overflow flag.
    _proximity_data = UnaryStruct(_APDS9999_REG_PS_DATA_0, "<H")

    # INT_CFG register (0x19), bit 0 enables the proximity sensor interrupt.
    proximity_interrupt_enabled = RWBit(_APDS9999_REG_INT_CFG, 0)
    """Enable or disable the proximity interrupt. You must also read ``main_status`` after the
interrupt is triggered to reset it."""

    # INT_CFG register (0x19), bit 1 proximity logic mode.
    # Intended behavior from datasheet:
    # False (default): Normal interrupt — INT latches active-low until MAIN_STATUS is read.
    # True: PS Logic Output Mode — INT is updated after every measurement and reflects
    # the current comparison state (no latching).
    #
    # Observed behavior does not match. INT pin seems stuck triggered
    # when PS Logic Output Mode is used.
    _proximity_logic_mode = RWBit(_APDS9999_REG_INT_CFG, 1)

    # INT_CFG register (0x19), bit 2 enables the light sensor interrupt.
    light_interrupt_enabled = RWBit(_APDS9999_REG_INT_CFG, 2)
    """Enable or disable the light sensor interrupt"""

    # INT_CFG register (0x19), bit 3 selects variance mode
    # (True) vs threshold mode (False) for the light interrupt.
    light_variance_mode = RWBit(_APDS9999_REG_INT_CFG, 3)
    """Variance mode (True) vs threshold mode (False) for the light interrupt."""

    # INT_CFG register (0x19), bits 5:4 selects which light channel
    # is compared against the interrupt thresholds.
    _light_interrupt_channel = RWBits(2, _APDS9999_REG_INT_CFG, 4)

    # INT_PST register (0x1A), bits 3:0 number of consecutive out-of-threshold proximity
    # readings required before the interrupt flag is asserted (0-15).
    _proximity_persistence = RWBits(4, _APDS9999_REG_INT_PST, 0)

    # INT_PST register (0x1A), bits 7:4 number of consecutive out-of-threshold light
    # readings required before the interrupt flag is asserted (0-15).
    _light_persistence = RWBits(4, _APDS9999_REG_INT_PST, 4)

    # PS_THRES_UP_0/1 registers (0x1B-0x1C) 11-bit upper proximity interrupt threshold.
    proximity_threshold_high = RWBits(11, _APDS9999_REG_PS_THRES_UP_0, 0, register_width=2)
    """Proximity threshold high 11 bits"""

    # PS_THRES_LOW_0/1 registers (0x1D-0x1E) 11-bit lower proximity interrupt threshold.
    proximity_threshold_low = RWBits(11, _APDS9999_REG_PS_THRES_LOW_0, 0, register_width=2)
    """Proximity threshold low 11 bits"""

    # LS_THRES_UP_0/1/2 registers (0x21-0x23) 20-bit upper light sensor interrupt threshold.
    light_threshold_high = RWBits(20, _APDS9999_REG_LS_THRES_UP_0, 0, register_width=3)
    """Light threshold high 20 bits"""

    # LS_THRES_LOW_0/1/2 registers (0x24-0x26) 20-bit lower light sensor interrupt threshold.
    light_threshold_low = RWBits(20, _APDS9999_REG_LS_THRES_LOW_0, 0, register_width=3)
    """Light threshold low 20 bits"""

    # LS_THRES_VAR register (0x27), bits 2:0 variance threshold for light interrupt.
    _light_variance = RWBits(3, _APDS9999_REG_LS_THRES_VAR, 0)

    # PS_CAN_0/1 registers (0x1F-0x20), bits 10:0 11-bit digital proximity cancellation
    # level. Bits 7:3 of PS_CAN_1 (analog cancellation) are preserved by the RWBits
    # read-modify-write.
    proximity_cancellation = RWBits(11, _APDS9999_REG_PS_CAN_0, 0, register_width=2)
    """Digital proximity cancellation level 11 bits"""

    # PS_CAN_1 register (0x20), bits 7:3 5-bit analog proximity cancellation level.
    # Bits 2:0 of PS_CAN_1 (digital cancellation high bits) are preserved by RWBits.
    proximity_analog_cancellation = RWBits(5, _APDS9999_REG_PS_CAN_1, 3)
    """Analog proximity cancellation level 5 bits"""

    # MAIN_STATUS register (0x07), bits 5:0 all status flags in one read.
    # Reading this register clears all status bits.
    _main_status = ROBits(6, _APDS9999_REG_MAIN_STATUS, 0)

    # PS_VCSEL register (0x01), bits 2:0 IR LED drive current.
    _led_current = RWBits(3, _APDS9999_REG_PS_VCSEL, 0)

    # PS_VCSEL register (0x01), bits 6:4 IR LED pulse modulation frequency.
    _led_frequency = RWBits(3, _APDS9999_REG_PS_VCSEL, 4)

    # PS_PULSES register (0x02) number of LED pulses emitted per proximity measurement.
    led_pulses = UnaryStruct(_APDS9999_REG_PS_PULSES, "B")
    """number of LED pulses emitted per proximity measurement"""

    # LS_DATA registers (0x0A-0x15) all 12 bytes of light sensor data read as a
    # single 96-bit value.  With lsb_first=True the channels sit at:
    #   bits  0-23 : IR   (3 bytes, 20-bit significant)
    #   bits 24-47 : Green
    #   bits 48-71 : Blue
    #   bits 72-95 : Red
    _ls_data_raw = ROBits(96, _APDS9999_REG_LS_DATA_IR_0, 0, register_width=12)

    def __init__(self, i2c_bus: "busio.I2C", address: int = _APDS9999_DEFAULT_ADDR) -> None:
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)

        # Verify we are talking to the correct chip.
        if self._part_id != _APDS9999_PART_ID:
            raise RuntimeError(
                "Failed to find APDS9999 check your wiring! "
                + f"Expected PART_ID 0x{_APDS9999_PART_ID:02X}, "
                + f"got 0x{self._part_id:02X}."
            )

        # Stores the overflow bit captured during the last proximity read.
        self._proximity_read_overflow = False

    @property
    def light_gain(self) -> int:
        """The analogue gain applied to all light sensor channels.

        Must be a :class:`LightGain` value:

        * ``LightGain.GAIN_1X``
        * ``LightGain.GAIN_3X``
        * ``LightGain.GAIN_6X``
        * ``LightGain.GAIN_9X``
        * ``LightGain.GAIN_18X``
        """
        return self._light_gain

    @light_gain.setter
    def light_gain(self, value: int) -> None:
        if not LightGain.is_valid(value):
            raise ValueError("light_gain must be a LightGain value")
        self._light_gain = value

    @property
    def light_resolution(self) -> int:
        """The ADC resolution of the light sensor channels.

        Must be a :class:`LightResolution` value:

        * ``LightResolution.RES_20BIT`` 20-bit, 400 ms conversion
        * ``LightResolution.RES_19BIT`` 19-bit, 200 ms conversion
        * ``LightResolution.RES_18BIT`` 18-bit, 100 ms conversion
        * ``LightResolution.RES_17BIT`` 17-bit, 50 ms conversion
        * ``LightResolution.RES_16BIT`` 16-bit, 25 ms conversion
        * ``LightResolution.RES_13BIT`` 13-bit, 3.125 ms conversion
        """
        return self._light_resolution

    @light_resolution.setter
    def light_resolution(self, value: int) -> None:
        if not LightResolution.is_valid(value):
            raise ValueError("light_resolution must be a LightResolution value")
        self._light_resolution = value

    @property
    def light_measurement_rate(self) -> int:
        """How frequently the light sensor takes a reading.

        Must be a :class:`LightMeasurementRate` value:

        * ``LightMeasurementRate.RATE_25MS``
        * ``LightMeasurementRate.RATE_50MS``
        * ``LightMeasurementRate.RATE_100MS`` (default)
        * ``LightMeasurementRate.RATE_200MS``
        * ``LightMeasurementRate.RATE_500MS``
        * ``LightMeasurementRate.RATE_1000MS``
        * ``LightMeasurementRate.RATE_2000MS``
        """
        return self._light_measurement_rate

    @light_measurement_rate.setter
    def light_measurement_rate(self, value: int) -> None:
        if not LightMeasurementRate.is_valid(value):
            raise ValueError("light_measurement_rate must be a LightMeasurementRate value")
        self._light_measurement_rate = value

    @property
    def proximity_resolution(self) -> int:
        """The ADC resolution of the proximity sensor.

        Must be a :class:`ProximityResolution` value:

        * ``ProximityResolution.RES_8BIT`` (hardware default)
        * ``ProximityResolution.RES_9BIT``
        * ``ProximityResolution.RES_10BIT``
        * ``ProximityResolution.RES_11BIT``
        """
        return self._proximity_resolution

    @proximity_resolution.setter
    def proximity_resolution(self, value: int) -> None:
        if not ProximityResolution.is_valid(value):
            raise ValueError("proximity_resolution must be a ProximityResolution value")
        self._proximity_resolution = value

    @property
    def proximity_measurement_rate(self) -> int:
        """How frequently the proximity sensor takes a reading.

        Must be a :class:`ProximityMeasurementRate` value:

        * ``ProximityMeasurementRate.RATE_6MS``   6.25 ms
        * ``ProximityMeasurementRate.RATE_12MS``  12.5 ms
        * ``ProximityMeasurementRate.RATE_25MS``  25 ms
        * ``ProximityMeasurementRate.RATE_50MS``  50 ms
        * ``ProximityMeasurementRate.RATE_100MS`` 100 ms (default)
        * ``ProximityMeasurementRate.RATE_200MS`` 200 ms
        * ``ProximityMeasurementRate.RATE_400MS`` 400 ms

        .. note::
            CircuitPython makes no guarantee about realtime
            behavior, the faster measurement rates may take
            longer than indicated.
        """
        return self._proximity_measurement_rate

    @proximity_measurement_rate.setter
    def proximity_measurement_rate(self, value: int) -> None:
        if not ProximityMeasurementRate.is_valid(value):
            raise ValueError("proximity_measurement_rate must be a ProximityMeasurementRate value")
        self._proximity_measurement_rate = value

    @property
    def proximity(self) -> int:
        """The current proximity sensor reading as an 11-bit count (0–2047).

        Each time this property is read the overflow flag is captured and can be
        checked immediately afterward via :attr:`proximity_read_overflow`.
        """
        raw = self._proximity_data
        self._proximity_read_overflow = bool(raw & 0x0800)
        return raw & 0x07FF

    def calculate_lux(self, green_count: int) -> float:
        """Calculate illuminance in lux from a raw green channel count.

        Reads the current :attr:`light_gain` and :attr:`light_resolution`
        settings from the device and applies the appropriate scale factor from
        the lookup table below.  ``RES_13BIT`` is not supported and will raise
        a ``ValueError``.

        Lux factor table (rows = gain, columns = resolution):

        +------------------+---------+---------+---------+---------+---------+
        |                  | 20-bit  | 19-bit  | 18-bit  | 17-bit  | 16-bit  |
        +==================+=========+=========+=========+=========+=========+
        | ``GAIN_1X``      | 0.136   | 0.273   | 0.548   | 1.099   | 2.193   |
        +------------------+---------+---------+---------+---------+---------+
        | ``GAIN_3X``      | 0.045   | 0.090   | 0.180   | 0.359   | 0.722   |
        +------------------+---------+---------+---------+---------+---------+
        | ``GAIN_6X``      | 0.022   | 0.045   | 0.090   | 0.179   | 0.360   |
        +------------------+---------+---------+---------+---------+---------+
        | ``GAIN_9X``      | 0.015   | 0.030   | 0.059   | 0.119   | 0.239   |
        +------------------+---------+---------+---------+---------+---------+
        | ``GAIN_18X``     | 0.007   | 0.015   | 0.029   | 0.059   | 0.117   |
        +------------------+---------+---------+---------+---------+---------+

        :param int green_count: Raw green channel value from :attr:`rgb_ir`.
        :return: Illuminance in lux.
        :rtype: float
        """
        # Rows indexed by LightGain value (GAIN_1X=0 … GAIN_18X=4).
        # Columns indexed by LightResolution value (RES_20BIT=0 … RES_16BIT=4).
        # RES_13BIT (0x05) is not included, lux calculation is unsupported at
        # that resolution.
        _LUX_FACTORS = (
            # 20-bit   19-bit   18-bit   17-bit   16-bit
            (0.136, 0.273, 0.548, 1.099, 2.193),  # GAIN_1X
            (0.045, 0.090, 0.180, 0.359, 0.722),  # GAIN_3X
            (0.022, 0.045, 0.090, 0.179, 0.360),  # GAIN_6X
            (0.015, 0.030, 0.059, 0.119, 0.239),  # GAIN_9X
            (0.007, 0.015, 0.029, 0.059, 0.117),  # GAIN_18X
        )

        gain = self.light_gain  # 0–4, directly usable as a row index
        res = self.light_resolution  # 0–5, 5 = RES_13BIT (unsupported)

        if res == LightResolution.RES_13BIT:
            raise ValueError("calculate_lux() does not support LightResolution.RES_13BIT")

        return green_count * _LUX_FACTORS[gain][res]

    @property
    def led_current(self) -> int:
        """The IR LED drive current used during proximity measurements.

        Must be a :class:`LedCurrent` value:

        * ``LedCurrent.MA_10`` 10 mA
        * ``LedCurrent.MA_25`` 25 mA
        """
        return self._led_current

    @property
    def light_interrupt_channel(self) -> int:
        """The light sensor channel compared against the interrupt thresholds.

        Must be a :class:`LightInterruptChannel` value:

        * ``LightInterruptChannel.IR``
        * ``LightInterruptChannel.GREEN``
        * ``LightInterruptChannel.RED``
        * ``LightInterruptChannel.BLUE``
        """
        return self._light_interrupt_channel

    @light_interrupt_channel.setter
    def light_interrupt_channel(self, value: int) -> None:
        if not LightInterruptChannel.is_valid(value):
            raise ValueError("light_interrupt_channel must be a LightInterruptChannel value")
        self._light_interrupt_channel = value

    @property
    def proximity_persistence(self) -> int:
        """Number of consecutive out-of-threshold proximity readings before the
        interrupt flag is asserted.

        Valid range is 0–15.
        """
        return self._proximity_persistence

    @proximity_persistence.setter
    def proximity_persistence(self, value: int) -> None:
        if not 0 <= value <= 15:
            raise ValueError("proximity_persistence must be 0–15")
        self._proximity_persistence = value

    @property
    def light_persistence(self) -> int:
        """Number of consecutive out-of-threshold light readings before the
        interrupt flag is asserted.

        Valid range is 0–15.
        """
        return self._light_persistence

    @light_persistence.setter
    def light_persistence(self, value: int) -> None:
        if not 0 <= value <= 15:
            raise ValueError("light_persistence must be 0–15")
        self._light_persistence = value

    @property
    def light_variance(self) -> int:
        """The count variance required to trigger a light interrupt when
        :attr:`light_variance_mode` is enabled.

        Must be a :class:`LightVariance` value:

        * ``LightVariance.VAR_8``
        * ``LightVariance.VAR_16``
        * ``LightVariance.VAR_32``
        * ``LightVariance.VAR_64``
        * ``LightVariance.VAR_128``
        * ``LightVariance.VAR_256``
        * ``LightVariance.VAR_512``
        * ``LightVariance.VAR_1024``
        """
        return self._light_variance

    @light_variance.setter
    def light_variance(self, value: int) -> None:
        if not LightVariance.is_valid(value):
            raise ValueError("light_variance must be a LightVariance value")
        self._light_variance = value

    @led_current.setter
    def led_current(self, value: int) -> None:
        if not LedCurrent.is_valid(value):
            raise ValueError("led_current must be a LedCurrent value")
        self._led_current = value

    @property
    def led_frequency(self) -> int:
        """The IR LED pulse modulation frequency used during proximity measurements.

        Must be a :class:`LedFrequency` value:

        * ``LedFrequency.KHZ_60``
        * ``LedFrequency.KHZ_70``
        * ``LedFrequency.KHZ_80``
        * ``LedFrequency.KHZ_90``
        * ``LedFrequency.KHZ_100``
        """
        return self._led_frequency

    @led_frequency.setter
    def led_frequency(self, value: int) -> None:
        if not LedFrequency.is_valid(value):
            raise ValueError("led_frequency must be a LedFrequency value")
        self._led_frequency = value

    @property
    def proximity_read_overflow(self) -> bool:
        """``True`` if the proximity sensor was saturated during the last read of
        :attr:`proximity`.  Updated on every :attr:`proximity` read; read-only.
        """
        return self._proximity_read_overflow

    def reset(self):
        """
        Software reset the APDS9999
        """
        self._reset = True
        time.sleep(0.01)

        # first read after reset will time out
        try:
            _ = self.proximity_cancellation
        except OSError:
            pass

    @property
    def main_status(self) -> Tuple[bool, bool, bool, bool, bool, bool]:
        """Read all status flags from the MAIN_STATUS register in a single I2C transaction.
        Main status must be read after an interrupt is triggered to reset the interrupt.

        .. warning::
            Reading this register clears all status bits on the device.

        Returns a tuple of six booleans:
        ``(proximity_data_ready, proximity_interrupt, proximity_logic,
        light_data_ready, light_interrupt, power_on_reset)``

        * ``proximity_data_ready`` new proximity data is available
        * ``proximity_interrupt`` proximity interrupt has been triggered
        * ``proximity_logic`` current state of the proximity logic signal
        * ``light_data_ready`` new light sensor data is available
        * ``light_interrupt`` light sensor interrupt has been triggered
        * ``power_on_reset`` a power-on reset has occurred since last read
        """
        raw = self._main_status
        return (
            bool(raw & 0x01),  # proximity_data_ready  (bit 0)
            bool(raw & 0x02),  # proximity_interrupt    (bit 1)
            bool(raw & 0x04),  # proximity_logic        (bit 2)
            bool(raw & 0x08),  # light_data_ready       (bit 3)
            bool(raw & 0x10),  # light_interrupt        (bit 4)
            bool(raw & 0x20),  # power_on_reset         (bit 5)
        )

    @property
    def rgb_ir(self) -> Tuple[int, int, int, int]:
        """All four light sensor channels as a tuple ``(red, green, blue, ir)``.

        Each value is up to 20-bit count (0–1048575) read in a single 12-byte
        burst starting at the IR data register. See ``light_resolution`` for
        bit depth setting, lower resolution will result in lower maximum values.
        """
        raw = self._ls_data_raw
        ir = raw & 0x0FFFFF
        g = (raw >> 24) & 0x0FFFFF
        b = (raw >> 48) & 0x0FFFFF
        r = (raw >> 72) & 0x0FFFFF
        return r, g, b, ir

    @property
    def rgb(self) -> Tuple[int, int, int]:
        """The RGB light sensor channels as a tuple ``(red, green, blue)``
        mapped to the range 0-255. For full 20bit resolution set
        ``light_resolution`` to ``LightResolution.RES_20BIT`` and use
        ``rgb_ir`` instead of ``rgb```

        :return: (red, gree, blue)
        """
        r, g, b, _ = self.rgb_ir

        max_lut = {
            LightResolution.RES_20BIT: 0b11111111111111111111,
            LightResolution.RES_19BIT: 0b1111111111111111111,
            LightResolution.RES_18BIT: 0b111111111111111111,
            LightResolution.RES_17BIT: 0b11111111111111111,
            LightResolution.RES_16BIT: 0b1111111111111111,
            LightResolution.RES_13BIT: 0b1111111111111,
        }
        in_max = max_lut[self.light_resolution]
        r = int(map_range(r, 0, in_max, 0, 255))
        g = int(map_range(g, 0, in_max, 0, 255))
        b = int(map_range(b, 0, in_max, 0, 255))
        return r, g, b
