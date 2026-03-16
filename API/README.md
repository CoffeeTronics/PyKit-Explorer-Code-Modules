# PyKit Ruler — CircuitPython Module Library
## Hackathon Reference

This library converts the board hardware tests into reusable, importable
modules.  Pick the modules your project needs, place them in the `/API`
folder on your `CIRCUITPY` drive, and call their APIs from your `code.py`.

---

## Directory Layout

All modules live flat in `/API` on the CIRCUITPY drive (Adafruit libraries stay in `/lib`):

```text
CIRCUITPY/
├── code.py
├── lib/                     ← Adafruit / third-party libraries
│   ├── asyncio/
│   ├── adafruit_st7789.mpy
│   └── ...
└── API/                     ← PyKit Ruler modules
    ├── digital_io.py        ← Dev board modules
    ├── analog_io.py
    ├── pwm_out.py
    ├── cap_touch.py
    ├── servo_control.py
    ├── uart_comms.py
    ├── i2c_bus.py
    ├── spi_bus.py
    ├── hid_input.py
    ├── cpu_temp.py
    ├── ble_uart.py
    ├── can_bus.py
    ├── neopixels.py         ← Ruler baseboard modules
    ├── lcd_display.py
    ├── imu_sensor.py
    ├── audio_out.py
    ├── sd_card.py
    ├── bme680.py            ← I2C breakout modules (QWIIC)
    ├── apds9960.py
    └── async_tasks.py       ← Utility modules
```

---

## Module Quick Reference

### Dev Board Modules

| Module | Class(es) | What it does |
|--------|-----------|-------------|
| `digital_io` | `DigitalOutput`, `DigitalInput`, `EdgeDetector` | Read buttons/switches; drive LEDs and relays; detect press/release edges |
| `analog_io` | `AnalogInput`, `AnalogOutput` | Read voltages from sensors (A0–A5); output DC voltage from DAC (board.DAC only) |
| `pwm_out` | `PWMOutput` | Variable duty-cycle signal; LED dimming; buzzer tones; motor speed control |
| `cap_touch` | `CapTouch` | Capacitive touch detect/release on board.A5 (CAP1) |
| `servo_control` | `ServoController` | Position standard RC servo 0°–180°; sweep animations |
| `uart_comms` | `UARTComms` | Send/receive strings over hardware UART (DEBUG or any UART) |
| `i2c_bus` | `I2CBus` | Scan I2C bus; raw register reads/writes; returns bus object for Adafruit drivers |
| `hid_input` | `HIDKeyboard`, `HIDMouse`, `JoystickMouse` | USB HID keyboard typing and key combos; mouse movement and clicks; joystick → mouse |
| `cpu_temp` | `CPUTemperature` | On-chip temperature in °C and °F; threshold checks; formatted logging strings |
| `ble_uart` | `BLEUart` | Reset RNBD451 BLE module; send/receive strings wirelessly; connection status tracking |
| `spi_bus` | `SPIBus` | General-purpose SPI transactions with automatic CS and bus locking |
| `can_bus` | `CANBus` | Send and receive CAN frames at 250 kbps; bus state monitoring |

### Ruler Baseboard Modules

| Module | Class(es) | What it does |
|--------|-----------|-------------|
| `neopixels` | `NeoPixels` | Drive 5 RGB LEDs; solid colours; chase, rainbow, pulse animations; bar-graph value mapping |
| `lcd_display` | `LCDDisplay` | Init 240×135 ST7789 LCD; backlight control; fill screen; load & position BMP sprites; bounce and IMU-driven movement |
| `imu_sensor` | `IMUSensor` | Read acceleration, gyro, magnetometer; tilt angles; tilt direction; sprite delta for IMU controls |
| `audio_out` | `AudioOutput` | Sine tone generation at any frequency; WAV file playback; play scales |
| `sd_card` | `SDCard` | Mount SD card; read/write/append text files; CSV data logging; filesystem utilities |

### I2C Breakout Modules (QWIIC)

Both breakout modules require an `I2CBus` instance from `i2c_bus.py`. Pass its
`.bus` property when constructing a sensor object.

| Module | Class(es) | What it does |
|--------|-----------|-------------|
| `bme680` | `BME680Sensor` | Read temperature, humidity, barometric pressure (sea-level adjusted), and gas resistance (VOC / air quality); threshold level helpers; formatted strings for LCD or logging |
| `apds9960` | `APDS9960Sensor` | Three modes switchable at runtime: **Proximity** (0–255 distance), **Gesture** (UP/DOWN/LEFT/RIGHT swipe detection), **Color** (16-bit RGBC with 8-bit NeoPixel conversion); constants for all gesture values |

### Utility Modules

| Module | Class(es) | What it does |
|--------|-----------|-------------|
| `async_tasks` | `AsyncRunner` | Lightweight asyncio wrapper; add coroutines and run them concurrently with a single call |

---

## Choosing Modules for Your Project

Think through what your project needs to **sense**, **process**, and **output**:

```
INPUTS                          OUTPUTS
──────                          ───────
digital_io   ← buttons          digital_io    → LEDs, relays
analog_io    ← sensors          pwm_out       → motors, buzzers
cap_touch    ← touch pad        servo_control → servo position
imu_sensor   ← motion/tilt      neopixels     → RGB feedback
bme680       ← temp/humidity    lcd_display   → graphics
apds9960     ← proximity        audio_out     → sound / music
apds9960     ← gesture          ble_uart      → wireless data
apds9960     ← color            sd_card       → data logging
i2c_bus      ← I2C devices      hid_input     → PC automation
spi_bus      ← SPI devices
uart_comms   ← serial devices
can_bus      ← CAN network
```

---

## Installation

1. Copy the module files you need into the `/API` folder on your `CIRCUITPY` drive.
2. At the top of `code.py`, add `/API` to the module search path, then import as normal:

```python
import sys
sys.path.append("/API")

from digital_io import DigitalInput, EdgeDetector
from neopixels  import NeoPixels, RED, GREEN
from imu_sensor import IMUSensor
```

3. You do **not** need to copy modules you are not using.

---

## Minimal Example — Tilt-controlled NeoPixel colours

```python
import sys
sys.path.append("/API")

from imu_sensor import IMUSensor
from neopixels  import NeoPixels, RED, GREEN, BLUE, YELLOW, OFF

imu = IMUSensor()
px  = NeoPixels()

while True:
    direction = imu.tilt_direction()
    if direction == "LEFT":
        px.fill(RED)
    elif direction == "RIGHT":
        px.fill(BLUE)
    elif direction == "UP":
        px.fill(GREEN)
    elif direction == "DOWN":
        px.fill(YELLOW)
    else:
        px.off()
```

---

## Minimal Example — BLE temperature logger

```python
import sys, time
sys.path.append("/API")

from ble_uart import BLEUart
from cpu_temp import CPUTemperature

ble  = BLEUart()
temp = CPUTemperature()

while True:
    ble.receive()  # process connection status messages
    if ble.connected:
        ble.send(f"Temp: {temp.formatted_string()}\n")
    time.sleep(2)
```

## Minimal Example — BME680 air quality display

```python
import sys, time
sys.path.append("/API")

from i2c_bus import I2CBus
from bme680 import BME680Sensor
from neopixels import NeoPixels, GREEN, YELLOW, RED, BLUE

my_i2c = I2CBus()
sensor = BME680Sensor(my_i2c.bus, elevation_m=362)
px     = NeoPixels()

while True:
    sensor.print_all()
    level = sensor.temperature_level()
    if level == "LOW":
        px.fill(BLUE)
    elif level == "MED":
        px.fill(GREEN)
    elif level == "HIGH":
        px.fill(YELLOW)
    else:
        px.fill(RED)
    time.sleep(1)
```

---

## Minimal Example — APDS9960 gesture → WAV audio

```python
import sys
sys.path.append("/API")

from i2c_bus import I2CBus
from apds9960 import APDS9960Sensor, GESTURE_UP, GESTURE_DOWN, GESTURE_LEFT, GESTURE_RIGHT
from audio_out import AudioOutput

my_i2c = I2CBus()
sensor = APDS9960Sensor(my_i2c.bus)
audio  = AudioOutput()

sensor.enable_gesture()

while True:
    g = sensor.gesture()
    if g == GESTURE_UP:
        audio.play_wav("AudioFiles/304.wav")
    elif g == GESTURE_DOWN:
        audio.play_wav("AudioFiles/140.wav")
    elif g == GESTURE_LEFT:
        audio.play_wav("AudioFiles/210.wav")
    elif g == GESTURE_RIGHT:
        audio.play_wav("AudioFiles/320.wav")
```

---

## Minimal Example — APDS9960 color → NeoPixels

```python
import sys, time
sys.path.append("/API")

from i2c_bus import I2CBus
from apds9960 import APDS9960Sensor
from neopixels import NeoPixels

my_i2c = I2CBus()
sensor = APDS9960Sensor(my_i2c.bus)
px     = NeoPixels()

sensor.enable_color()

while True:
    px.fill(sensor.color_as_neopixel())
    time.sleep(0.1)
```

---




- **HID** requires `usb_hid.enable()` in `boot.py`.

- **WAV files** must be mono, 16-bit PCM, ≤ 22 050 Hz.

- **CAN** requires two boards (or a CAN analyser) to verify message exchange.

- **Breakout modules** (`bme680`, `apds9960`) connect via the QWIIC connector and require `i2c_bus.py` on the drive. Always pass `i2c_bus_instance.bus` to the sensor constructor, not the `I2CBus` object itself.

- **APDS9960 modes** are mutually exclusive — always call `enable_proximity()`, `enable_gesture()`, or `enable_color()` before reading, and only one at a time.
