# PyKit Ruler — CircuitPython Module Library
## Workshop/Hackathon Reference

This library provides APIs for all of the hardware on the Microchip Curiosity PyKit Explorer.

- **Module Quick Reference** — find out what each module can do
- **Choosing Modules for Your Project** — work out which modules you need for a specific purpose
- **Minimal Examples** — copy-paste starting points to get up and running quickly

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
| `lcd_display` | `LCDDisplay` | Init 240×135 ST7789 LCD; backlight control; `make_group()` creates a persistent display group with swappable background colour; `add_label()` adds a centred text label to a group; load & position BMP sprites; bounce and IMU-driven movement |
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

import board
from digital_io import DigitalInput, EdgeDetector
from neopixels  import NeoPixels, RED, GREEN
from imu_sensor import IMUSensor
```

3. You do **not** need to copy modules you are not using.

---

## Minimal Example — Blink the onboard LED

```python
import sys, time
sys.path.append("/API")

import board
from digital_io import DigitalOutput

led = DigitalOutput(board.LED)

while True:
    led.on()
    time.sleep(0.5)
    led.off()
    time.sleep(0.5)
```

---

## Minimal Example — Tilt-controlled NeoPixel colours

```python
import sys
sys.path.append("/API")

import board
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

import board
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

import board
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

import board
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

import board
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




## Minimal Example — Display a BMP image on the LCD

Place your `.bmp` image files in the `/Images` folder on the CIRCUITPY drive.

```python
import sys
sys.path.append("/API")

from lcd_display import LCDDisplay

lcd = LCDDisplay()
lcd.backlight_on()

# load_sprite() loads the BMP and returns a positioned displayio.Group
group = lcd.load_sprite("/Images/Bluey_Family.BMP", 240, 135, x=0, y=0)
lcd.display.root_group = group

while True:
    pass
```

> **Note:** BMP images should match the display resolution (240×135) for best results.
> Supported format: indexed colour BMP (16 or 256 colours).

---

## Minimal Example — LCD as a serial terminal

CircuitPython automatically redirects `print()` output to an attached display.
This example initialises the LCD and then uses `print()` as a simple terminal.

```python
import sys, time
sys.path.append("/API")

from lcd_display import LCDDisplay

lcd = LCDDisplay()
lcd.backlight_on()

x = 0

while True:
    print("Hello World:", x)
    x += 1
    time.sleep(1)
```

> **Note:** Once the display is initialised, `print()` output appears on both
> the LCD and the USB serial console automatically.

---

## Minimal Example — Rolling coloured text labels on the LCD

Requires `adafruit_bitmap_font` and `adafruit_display_text` in `/lib`, and a
`.bdf` font file in the `/Fonts` folder on the CIRCUITPY drive.
Text strings rotate down through the four lines every second while
the line colours stay fixed.

```python
import sys, time
sys.path.append("/API")

import displayio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label

from lcd_display import LCDDisplay

lcd = LCDDisplay()
lcd.backlight_on()

# Load font
font = bitmap_font.load_font("/Fonts/Helvetica-Bold-16.bdf")

# Fixed line colours (purple, blue, red, green)
LINE_COLORS = [0xFF00FF, 0x0000FF, 0xFF0000, 0x00FF00]
LINE_Y = [20, 50, 80, 110]

# Create four text labels with fixed colours and positions
labels = []
for i in range(4):
    text_area = label.Label(font, text="", color=LINE_COLORS[i])
    text_area.x = 0
    text_area.y = LINE_Y[i]
    labels.append(text_area)

# Text strings that will roll through the lines
texts = [
    "Lorem ipsum dolor sit amet",
    "consectetur adipiscing elit",
    "sed do eiusmod tempor",
    "labore et dolore magna aliqua",
]

# Build display group
group = displayio.Group()
for lbl in labels:
    group.append(lbl)
lcd.display.root_group = group

# Assign initial text
for i in range(4):
    labels[i].text = texts[i]

while True:
    time.sleep(1)
    # Rotate text strings: last item moves to front
    texts = [texts[-1]] + texts[:-1]
    for i in range(4):
        labels[i].text = texts[i]
```

> **Note:** Colour values are 24-bit hex `0xRRGGBB`. Font files (`.bdf`) should be
> placed in the `/Fonts` folder on the CIRCUITPY drive.

---

## Minimal Example — Concurrent NeoPixel blinks with AsyncRunner

Requires the `asyncio` library in `/lib`.

```python
import sys
sys.path.append("/API")

import board
import neopixel
from async_tasks import AsyncRunner

pixels = neopixel.NeoPixel(board.NEOPIXEL, 5, brightness=0.05, auto_write=True)
OFF = (0, 0, 0)

async def blink(pixel: int, interval: float, count: int, color: tuple):
    for _ in range(count):
        pixels[pixel] = color
        await AsyncRunner.sleep(interval)
        pixels[pixel] = OFF
        await AsyncRunner.sleep(interval)

runner = AsyncRunner()
runner.add(blink(0, 0.30, 15, (255, 0, 255)))
runner.add(blink(1, 0.75, 10, (0, 255, 0)))
runner.add(blink(2, 1.00, 10, (255, 0, 0)))
runner.add(blink(3, 0.50, 10, (255, 150, 0)))
runner.add(blink(4, 0.25, 15, (0, 0, 255)))
runner.run()
```

> **Note:** All tasks run cooperatively — use `await AsyncRunner.sleep()` (not
> `time.sleep()`) to yield control between tasks.

---

## Minimal Example — CPU temperature on LCD, serial, and BLE

Combines `cpu_temp`, `lcd_display`, and `ble_uart` to read the CPU temperature
and display it on the LCD with colour-coded thresholds, print to the serial
console, and send over BLE. Strings sent from the connected BLE device are
displayed on the LCD for 5 seconds before reverting to the temperature readout.

`make_group()` creates the single persistent display group (set as `root_group`
once at startup). `add_label()` appends centred text labels to that group —
no raw `displayio` imports needed in `code.py`.

```python
import sys, time
sys.path.append("/API")

from cpu_temp    import CPUTemperature
from lcd_display import LCDDisplay
from ble_uart    import BLEUart

# Colour thresholds (°C)
THRESH_WARN = 30.0   # below → green, above → orange, 35+ → red
THRESH_HOT  = 35.0

# Initialise hardware
lcd  = LCDDisplay()
temp = CPUTemperature()
ble  = BLEUart()
lcd.backlight_on()

# Build a single persistent group — root_group is set once inside make_group()
group, bg = lcd.make_group(0x000000)

# Temperature label
temp_lbl = lcd.add_label(group, "--.- C", 120, 55, color=0x00FF00, scale=3)

# BLE received message label — hidden until a message arrives
ble_lbl        = lcd.add_label(group, "", 120, 55, color=0xFFFF00, scale=2)
ble_lbl.hidden = True

MSG_DURATION = 5.0
msg_until    = 0.0

while True:
    now = time.monotonic()
    c   = temp.celsius

    # Incoming BLE string — show it for MSG_DURATION seconds
    incoming = ble.receive()
    if incoming:
        temp_lbl.hidden = True
        ble_lbl.hidden  = False
        ble_lbl.text    = incoming.strip()[:20]
        bg[0]           = 0x000080   # dark blue background
        msg_until       = now + MSG_DURATION

    # Revert to temperature display after timeout
    if now >= msg_until:
        temp_lbl.hidden = False
        ble_lbl.hidden  = True
        bg[0]           = 0x000000   # black background

        # Update colour by threshold
        if c < THRESH_WARN:
            temp_lbl.color = 0x00FF00   # green
        elif c <= THRESH_HOT:
            temp_lbl.color = 0xFF8000   # orange
        else:
            temp_lbl.color = 0xFF0000   # red

        temp_lbl.text = f"{c:.1f} C"

    # Serial console
    print(f"CPU Temp: {c:.1f} C")

    # BLE broadcast
    if ble.connected:
        ble.send(f"Temp: {c:.1f}C\n")

    time.sleep(1)
```

---

- **HID** requires `usb_hid.enable()` in `boot.py`.

- **WAV files** must be mono, 16-bit PCM, ≤ 22 050 Hz.

- **CAN** requires two boards (or a CAN analyser) to verify message exchange.

- **Breakout modules** (`bme680`, `apds9960`) connect via the QWIIC connector and require `i2c_bus.py` on the drive. Always pass `i2c_bus_instance.bus` to the sensor constructor, not the `I2CBus` object itself.

- **APDS9960 modes** are mutually exclusive — always call `enable_proximity()`, `enable_gesture()`, or `enable_color()` before reading, and only one at a time.
