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
    ├── async_tasks.py       ← Utility modules
    ├── pwm_waveform_explorer.py  ← Tools
    └── synthio_sound_lab.py
```

---

## Module Quick Reference

### Dev Board Modules

| Module            | Class(es)                                             | What it does                                                                          |
| ----------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `digital_io`    | `DigitalOutput`, `DigitalInput`, `EdgeDetector` | Read buttons/switches; drive LEDs and relays; detect press/release edges              |
| `analog_io`     | `AnalogInput`, `AnalogOutput`                     | Read voltages from sensors (A0–A5); output DC voltage from DAC (board.DAC only)      |
| `pwm_out`       | `PWMOutput`                                         | Variable duty-cycle signal; LED dimming; buzzer tones; motor speed control            |
| `cap_touch`     | `CapTouch`                                          | Capacitive touch detect/release on board.A5 (CAP1)                                    |
| `servo_control` | `ServoController`                                   | Position standard RC servo 0°–180°; sweep animations                               |
| `uart_comms`    | `UARTComms`                                         | Send/receive strings over hardware UART (DEBUG or any UART)                           |
| `i2c_bus`       | `I2CBus`                                            | Scan I2C bus; raw register reads/writes; returns bus object for Adafruit drivers      |
| `hid_input`     | `HIDKeyboard`, `HIDMouse`, `JoystickMouse`      | USB HID keyboard typing and key combos; mouse movement and clicks; joystick → mouse  |
| `cpu_temp`      | `CPUTemperature`                                    | On-chip temperature in °C and °F; threshold checks; formatted logging strings       |
| `ble_uart`      | `BLEUart`                                           | Reset RNBD451 BLE module; send/receive strings wirelessly; connection status tracking |
| `spi_bus`       | `SPIBus`                                            | General-purpose SPI transactions with automatic CS and bus locking                    |
| `can_bus`       | `CANBus`                                            | Send and receive CAN frames at 250 kbps; bus state monitoring                         |

### Ruler Baseboard Modules

| Module          | Class(es)       | What it does                                                                                                                                                                                                                                        |
| --------------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `neopixels`   | `NeoPixels`   | Drive 5 RGB LEDs; solid colours; chase, rainbow, pulse animations; bar-graph value mapping                                                                                                                                                          |
| `lcd_display` | `LCDDisplay`  | Init 240×135 ST7789 LCD; backlight control;`make_group()` creates a persistent display group with swappable background colour; `add_label()` adds a centred text label to a group; load & position BMP sprites; bounce and IMU-driven movement |
| `imu_sensor`  | `IMUSensor`   | Read acceleration, gyro, magnetometer; tilt angles; tilt direction; sprite delta for IMU controls                                                                                                                                                   |
| `audio_out`   | `AudioOutput` | Sine tone generation at any frequency; WAV file playback; play scales                                                                                                                                                                               |
| `sd_card`     | `SDCard`      | Mount SD card; read/write/append text files; CSV data logging; filesystem utilities                                                                                                                                                                 |

### I2C Breakout Modules (QWIIC)

Both breakout modules require an `I2CBus` instance from `i2c_bus.py`. Pass its
`.bus` property when constructing a sensor object.

| Module       | Class(es)          | What it does                                                                                                                                                                                                                    |
| ------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bme680`   | `BME680Sensor`   | Read temperature, humidity, barometric pressure (sea-level adjusted), and gas resistance (VOC / air quality); threshold level helpers; formatted strings for LCD or logging                                                     |
| `apds9960` | `APDS9960Sensor` | Three modes switchable at runtime:**Proximity** (0–255 distance), **Gesture** (UP/DOWN/LEFT/RIGHT swipe detection), **Color** (16-bit RGBC with 8-bit NeoPixel conversion); constants for all gesture values |

### Utility Modules

| Module          | Class(es)       | What it does                                                                             |
| --------------- | --------------- | ---------------------------------------------------------------------------------------- |
| `async_tasks` | `AsyncRunner` | Lightweight asyncio wrapper; add coroutines and run them concurrently with a single call |

### Tools

Ready-to-run programs that combine multiple modules. Each exposes a single
`run()` entry point.

| Tool                      | What it does                                                                                                                                                                            |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pwm_waveform_explorer` | Interactive oscilloscope: D3 steps frequency (100–3 kHz), A5 steps duty cycle (0–100 %);`<br>`live waveform on LCD, sine tone through speaker, LED brightness tracks duty cycle   |
| `synthio_sound_lab`     | Theremin synthesiser: IMU tilt y → pitch, tilt x → volume (3° dead zone), APDS proximity → pitch bend up;`<br>`D3 cycles waveform (SINE/SQUA/SAW/TRI); optional USB MIDI output |

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
spi_bus      ← SPI devices      synthio       → real-time synthesis
uart_comms   ← serial devices
can_bus      ← CAN network
```

Common multi-module patterns:

| Goal                 | Modules                                                          |
| -------------------- | ---------------------------------------------------------------- |
| Theremin synthesiser | `imu_sensor` + `apds9960` + `synthio` + `lcd_display`    |
| PWM visualiser       | `digital_io` + `cap_touch` + `audio_out` + `lcd_display` |
| Data logger          | `bme680` + `sd_card` + `lcd_display`                       |
| BLE sensor stream    | `imu_sensor` + `bme680` + `ble_uart`                       |
| Gesture game         | `apds9960` + `neopixels` + `lcd_display`                   |

---

## How to use the API

1. At the top of `code.py`, add `import pykit_explorer`. This allows the user to leverage the functionality of the API to greatly simplify their project.
2. To use individual libraries in the API, import that filename and the name of the class and/or variables you want to use. See example below.

```python
import pykit_explorer
from digital_io import DigitalInput, EdgeDetector
from neopixels  import NeoPixels, RED, GREEN
from imu_sensor import IMUSensor
```

3. You do **not** need to copy modules you are not using.

---

## Minimal Example — Blink the onboard LED

```python
import pykit_explorer
from digital_io import DigitalOutput

led = DigitalOutput(board.LED)

while True:
    led.on()
    time.sleep(0.5)
    led.off()
    time.sleep(0.5)
```

---

## Minimal Example — Read User Button

```python
import pykit_explorer
from digital_io import DigitalInput

btn = DigitalInput(board.D3)

while True:
    print(f'Value:	    {btn.value}')
    print(f'is pressed: {btn.is_pressed()}')
```

---

## Minimal Example — Tilt-controlled NeoPixel colours

```python
import pykit_explorer
from imu_sensor import IMUSensor
from neopixels  import NeoPixels, Colors, OFF

imu = IMUSensor()
px  = NeoPixels()

while True:
    direction = imu.tilt_direction()
    if direction == "LEFT":
        px.fill(Colors.RED)
    elif direction == "RIGHT":
        px.fill(Colors.BLUE)
    elif direction == "UP":
        px.fill(Colors.GREEN)
    elif direction == "DOWN":
        px.fill(Colors.YELLOW)
    else:
        px.off()

```

---

## Minimal Example — BLE temperature logger

```python
import pykit_explorer
from ble_uart import BLEUart
from cpu_temp import CPUTemperature

ble  = BLEUart()
temp = CPUTemperature()

while True:
    ble.poll()  # process connection status messages
    if ble.connected:
        ble.send(f"Temp: {temp.formatted_string()}\n")
    time.sleep(2)
```

## Minimal Example — BME680 air quality display

```python
import pykit_explorer
from i2c_bus import I2CBus
from bme680 import BME680Sensor
from neopixels import NeoPixels, Colors

my_i2c = I2CBus()
sensor = BME680Sensor(my_i2c.bus, elevation_m=362)
px     = NeoPixels()

while True:
    sensor.print_all()
    level = sensor.temperature_level()
    if level == "LOW":
        px.fill(Colors.BLUE)
    elif level == "MED":
        px.fill(Colors.GREEN)
    elif level == "HIGH":
        px.fill(Colors.YELLOW)
    else:
        px.fill(Colors.RED)
    time.sleep(1)

```

---

## Minimal Example — APDS9960 gesture → WAV audio

```python
import pykit_explorer
from i2c_bus import I2CBus
from apds9960 import APDS9960Sensor, Gestures, Gesture_Names
from audio_out import AudioOutput

my_i2c = I2CBus()
sensor = APDS9960Sensor(my_i2c.bus)
audio  = AudioOutput()

sensor.enable_gesture()

while True:
    g = sensor.wait_for_gesture()
    if g == Gestures.GESTURE_UP:
        audio.play_wav("AudioFiles/304.wav")
    elif g == Gestures.GESTURE_DOWN:
        audio.play_wav("AudioFiles/140.wav")
    elif g == Gestures.GESTURE_LEFT:
        audio.play_wav("AudioFiles/210.wav")
    elif g == Gestures.GESTURE_RIGHT:
        audio.play_wav("AudioFiles/320.wav")

```

---

## Minimal Example — APDS9960 color → NeoPixels

```python
import pykit_explorer
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
import pykit_explorer
from lcd_display import LCDDisplay

lcd = LCDDisplay()
lcd.backlight_on()

# load_sprite() loads the BMP and returns a positioned displayio.Group
group = lcd.load_sprite("/Images/Bluey_Family.BMP")
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
import pykit_explorer
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
import pykit_explorer
import displayio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from lcd_display import LCDDisplay, Colors

lcd = LCDDisplay()
lcd.backlight_on()

# Load font
font = bitmap_font.load_font("/Fonts/Helvetica-Bold-16.bdf")

LINE_COLORS = [Colors.PURPLE, Colors.BLUE, Colors.RED, Colors.GREEN] # Colours for each line of text
LINE_Y = [20, 50, 80, 110] # Y positions for each line of text

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
import pykit_explorer
from neopixels import NeoPixels, Colors, OFF
from async_tasks import AsyncRunner

pixels = NeoPixels()

async def blink(pixel: int, interval: float, count: int, color: tuple):
    for _ in range(count):
        pixels.set(pixel, color)
        await AsyncRunner.sleep(interval)
        pixels.set(pixel, OFF)
        await AsyncRunner.sleep(interval)

runner = AsyncRunner()
runner.add(blink(0, 0.30, 15, Colors.PURPLE))
runner.add(blink(1, 0.75, 10, Colors.GREEN))
runner.add(blink(2, 1.00, 10, Colors.RED))
runner.add(blink(3, 0.50, 10, Colors.YELLOW))
runner.add(blink(4, 0.25, 15, Colors.BLUE))
runner.run()

```

> **Note:** All tasks run cooperatively — use `await AsyncRunner.sleep()` (not
> `time.sleep()`) to yield control between tasks.

---

## Minimal Example — CPU temperature on LCD, serial, and BLE

Combines `cpu_temp`, `lcd_display`, and `ble_uart` to read the CPU temperature
and display it on the LCD with colour-coded thresholds, print to the serial
console, and send over BLE. Messages received from the connected device are
displayed on the LCD and scrolled automatically if longer than 20 characters,
with the duration calculated so the full message always completes one pass.
Connection and disconnection events show a status banner. The display reverts
to the temperature readout when the message expires.

`make_group()` creates the single persistent display group. `add_label()`
creates the temperature label. `make_scroll_label()` creates the BLE message
label — it owns all scroll state internally so the main loop stays simple.

```python
import pykit_explorer
from cpu_temp    import CPUTemperature
from lcd_display import LCDDisplay, Colors
from ble_uart    import BLEUart

# Colour thresholds (°C)
THRESH_WARN   = 30.0
THRESH_HOT    = 35.0
TEMP_INTERVAL = 1.0

# Initialise hardware
lcd  = LCDDisplay()
temp = CPUTemperature()
ble  = BLEUart()
lcd.backlight_on()

group, bg = lcd.make_group(Colors.BLACK)

temp_lbl = lcd.add_label(group, "--.- C", 120, 55, color=Colors.GREEN, scale=3)
ble_lbl  = lcd.make_scroll_label(group, 120, 55)

temp_next = 0.0

while True:
    now      = time.monotonic()
    incoming = ble.poll()

    if ble.just_connected:
        bg[0] = Colors.BLACK
        ble_lbl.set("Connected")

    if ble.just_disconnected:
        bg[0] = Colors.BLACK
        ble_lbl.set("Disconnected")

    if incoming:
        bg[0] = Colors.DARK_BLUE
        ble_lbl.set(incoming.strip())

    if now >= temp_next:
        c         = temp.celsius
        temp_next = now + TEMP_INTERVAL

        if c < THRESH_WARN:
            temp_lbl.color = Colors.GREEN
        elif c <= THRESH_HOT:
            temp_lbl.color = Colors.ORANGE
        else:
            temp_lbl.color = Colors.RED
        temp_lbl.text = f"{c:.1f} C"
        print(f"CPU Temp: {c:.1f} C")
        if ble.connected:
            ble.send(f"Temp: {c:.1f}C\n")

    if ble_lbl.update(now):
        temp_lbl.hidden = True
    else:
        temp_lbl.hidden = False
        bg[0]           = Colors.BLACK


```

---

## Tools

Standalone diagnostic scripts that help you explore and verify hardware
capabilities on the PyKit Explorer. Copy the script into `code.py` and run it
to inspect your board — no extra libraries needed beyond the `/API` modules.

---

### PWM Pin Identifier

Scans every pin on the PyKit Explorer and reports which pins are available for
PWM output, which are PWM-capable but blocked by a board-level peripheral,
and which have no PWM support at all.
Results are printed in a consistent order: working PWM pins first, then
prevented pins with the reason, then non-PWM pins. Useful before writing any
PWM-based driver to confirm which pins are actually free to use.

```python
import pykit_explorer

from pwm_pins import PWMPinScanner

scanner = PWMPinScanner()
scanner.scan()
scanner.report()
```

### I2C Bus Scanner

Scans the I2C bus and reports every device address found, a candidate device
name based on a built-in address lookup table, and a confirmed device name read
directly from the hardware via the WHO_AM_I or chip ID register.

Covers all on-board devices (ICM-20948 IMU, BME680, APDS9960) as well as a
wide range of common QWIIC breakout modules.

```python
import pykit_explorer
from i2c_scan import I2CScanner

scanner = I2CScanner()
scanner.scan()
scanner.report()
scanner.deinit()
```

**Reading the output:**

Each found device prints as two lines:

```text
  0x69  ICM-20948 (IMU)
        WHO_AM_I @ 0x00: 0xEA → ICM-20948
```

- The first line shows the hex address and the candidate name from the address
  lookup table. Where multiple devices share an address, all possibilities are
  listed separated by `/`.
- The second line shows the WHO_AM_I register address, the raw value read back,
  and the confirmed device name. If the value does not match any known ID,
  `unrecognised` is shown — this may indicate a device variant not yet in the
  lookup table. If no WHO_AM_I register is defined for that address, the second
  line is omitted.

Results are also available programmatically via `scanner.results`, a list of
dicts with keys `address`, `candidate`, `who_am_i`, and `confirmed`.

### Register-Level Peek / Poke

A REPL-friendly utility for reading and writing individual hardware registers
on any I2C or SPI device by address. Think of it as a lightweight version of
what you would do with Microchip's MPLAB Data Visualizer, but running entirely
in Python on the board itself. Useful for exploring a device's register map,
verifying that a configuration write took effect, or reading raw sensor output
without a full driver.

Both `I2CDevice` and `SPIDevice` expose the same interface:

| Method                     | Description                                            |
| -------------------------- | ------------------------------------------------------ |
| `peek(register)`         | Read one register and print its value                  |
| `peek(register, length)` | Burst-read and print*length* consecutive registers   |
| `poke(register, value)`  | Write one byte and confirm with an automatic readback  |
| `dump(start, end)`       | Read and print every register from*start* to *end* |

Values are always shown as hex, decimal, and binary so they can be read
directly against a datasheet register map.

**I2C example — ICM-20948 IMU at address 0x69:**

```python
import pykit_explorer

from reg_peek_poke import I2CDevice

imu = I2CDevice(0x69)

imu.peek(0x00)           # Read WHO_AM_I — should return 0xEA
imu.dump(0x00, 0x06)     # Dump the first 7 registers
imu.poke(0x06, 0x01)     # Write PWR_MGMT_1 to wake the IMU from sleep

imu.deinit()
```

**SPI example — generic sensor on board.CS:**

```python
import pykit_explorer
import board

from reg_peek_poke import SPIDevice

# Default convention: bit 7 = 1 for read, bit 7 = 0 for write.
# Works with ICM-20948, LSM6DS, BMI160, and most MEMS sensors.
# Override read_bit / write_mask for devices with a different protocol.
dev = SPIDevice(board.CS)

dev.peek(0x0F)            # Read the WHO_AM_I / device ID register
dev.dump(0x00, 0x1F)      # Dump the first 32 registers
dev.poke(0x10, 0x00)      # Write 0x00 to register 0x10

dev.deinit()
```

**Reading the output:**

`peek` and `dump` print one line per register in a fixed-column table:

```text
  Addr   Hex    Dec  Bin
  ---------------------------------
  0x00   0xEA  234  1110 1010
  0x01   0x00    0  0000 0000
```

`poke` prints the written value followed by an immediate readback. If the
readback does not match what was written, a warning is shown — this is normal
for read-only bits, reserved fields, or registers where the hardware masks
certain bits:

```text
  Wrote 0x01 → register 0x06
  Readback:  0x01    1  0000 0001
```

All methods also return their results for programmatic use: `peek` returns an
int (or bytearray when *length* > 1), and `dump` returns a dict mapping each
register address to its value.

### PWM Waveform Explorer

An interactive oscilloscope-style tool for understanding PWM signals.
Students adjust frequency and duty cycle in real time and see the effect
across three simultaneous feedback channels: a scrolling graphical waveform
on the LCD, a sine tone through the speaker, and LED brightness — all
updating instantly with every button press.

**Controls**

| Input              | Action                                                         |
| ------------------ | -------------------------------------------------------------- |
| USER button (D3)   | Step frequency: 100 → 200 → 500 → 1k → 2k → 3k Hz (wraps) |
| CAP TOUCH pad (A5) | Step duty cycle: 0 → 10 → 20 → … → 100 → 0 % (wraps)     |

**What you see on the LCD**

```
PWM WAVEFORM EXPLORER
FREQ   1000 Hz          ← flashes white on change
DUTY     50 %           ← flashes white on change

══════════              ← HIGH signal (bright green, scrolling)

══════════              ← LOW signal  (bright green, scrolling)

USER=freq   CAP TOUCH=duty
```

The waveform scrolls continuously left so the signal appears live.
When a parameter changes, the corresponding row briefly flashes white
to confirm which value was updated. The speaker volume scales with
duty cycle — 0 % is silent, 100 % is loudest.

```python
import pykit_explorer
from pwm_waveform_explorer import run

run()
```

---

### Synthio Sound Lab

A real-time theremin-style synthesizer driven entirely by onboard sensors.
Tilt the board to sweep pitch across four octaves, tilt the opposite axis to
control volume, and hover your hand over the proximity sensor to bend the note
up by up to two semitones — all while watching the parameters update live on
the LCD.  Four waveforms (sine, square, sawtooth, triangle) let students hear
how waveshape changes timbre.  Optional USB MIDI output is enabled
automatically when the host supports it.

The note plays continuously. Tilting forward or back controls volume —
a 3° dead zone around flat keeps the output silent until you intentionally
tilt. Keeping the board flat silences the output without stopping synthesis.

**Controls**

| Input                        | Action                                                    |
| ---------------------------- | --------------------------------------------------------- |
| USER button (D3)             | Cycle waveform: SINE → SQUARE → SAW → TRIANGLE (wraps) |
| Tilt left / right (Y-axis)   | Pitch sweep across the selected range                     |
| Tilt forward / back (X-axis) | Volume: <3° = silent, 45° = full                        |
| Hand near APDS proximity     | Pitch bends up by 0 to +2 semitones (closer = more bend)  |

**What you see on the LCD**

```
   SYNTHIO SOUND LAB
   WAVE  SINE               <- current waveform (purple)
   NOTE C4    262Hz         <- note name + frequency (cyan)

VOL |||||||||               <- green bar, width = volume
BND ||                      <- orange bar, width = bend amount
    ----------|----------   <- cyan needle tracks tilt position

   D3=wave   TILT=vol
```

Requires the ICM20948 IMU (on-board) and an APDS9960 proximity breakout
connected to the QWIIC connector.

```python
import pykit_explorer
from synthio_sound_lab import run

run()
```

---

- **HID** requires `usb_hid.enable()` in `boot.py`.
- **WAV files** must be mono, 16-bit PCM, ≤ 22 050 Hz.
- **CAN** requires two boards (or a CAN analyser) to verify message exchange.
- **Breakout modules** (`bme680`, `apds9960`) connect via the QWIIC connector and require `i2c_bus.py` on the drive. Always pass `i2c_bus_instance.bus` to the sensor constructor, not the `I2CBus` object itself.
- **APDS9960 modes** are mutually exclusive — always call `enable_proximity()`, `enable_gesture()`, or `enable_color()` before reading, and only one at a time.
