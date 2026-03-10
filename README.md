# PyKit Ruler — CircuitPython Module Library

## Hackathon Reference

This library converts the board hardware tests into reusable, importable
modules.  Pick the modules your project needs, drop them into the `/lib` folder in
`CIRCUITPY` drive, and call their APIs from your `code.py`.

---

## Directory Layout

```
modules/
├── dev_board/               ← Dev board modules
│   ├── digital_io.py
│   ├── analog_io.py
│   ├── pwm_out.py
│   ├── cap_touch.py
│   ├── servo_control.py
│   ├── uart_comms.py
│   ├── i2c_bus.py
│   ├── hid_input.py
│   ├── cpu_temp.py
│   ├── ble_uart.py
│   └── can_bus.py
└── ruler/              ← Ruler baseboard modules
    ├── neopixels.py
    ├── lcd_display.py
    ├── imu_sensor.py
    ├── audio_out.py
    └── sd_card.py
```

---

## Module Quick Reference

### Dev Board Modules

| Module            | Class(es)                                             | What it does                                                                         |
| ----------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `digital_io`    | `DigitalOutput`, `DigitalInput`, `EdgeDetector` | Read buttons/switches; drive LEDs and relays; detect press/release edges             |
| `analog_io`     | `AnalogInput`, `AnalogOutput`                     | Read voltages from sensors (A0–A5); output DC voltage from DAC (A5 only)            |
| `pwm_out`       | `PWMOutput`                                         | Variable duty-cycle signal; LED dimming; buzzer tones; motor speed control           |
| `cap_touch`     | `CapTouch`                                          | Capacitive touch detect/release on board.A5 (CAP1)                                   |
| `servo_control` | `ServoController`                                   | Position standard RC servo 0°–180°; sweep animations                              |
| `uart_comms`    | `UARTComms`                                         | Send/receive strings over hardware UART (DEBUG or any UART)                          |
| `i2c_bus`       | `I2CBus`                                            | Scan I2C bus; raw register reads/writes; returns bus object for Adafruit drivers     |
| `hid_input`     | `HIDKeyboard`, `HIDMouse`, `JoystickMouse`      | USB HID keyboard typing and key combos; mouse movement and clicks; joystick → mouse |
| `cpu_temp`      | `CPUTemperature`                                    | On-chip temperature in °C and °F; threshold checks; formatted logging strings      |
| `ble_uart`      | `BLEUart`                                           | Configure RNBD451 BLE module; send/receive strings wirelessly to a phone or PC       |
| `can_bus`       | `CANBus`                                            | Send and receive CAN frames at 250 kbps; bus state monitoring                        |

### Ruler Baseboard Modules

| Module          | Class(es)       | What it does                                                                                                          |
| --------------- | --------------- | --------------------------------------------------------------------------------------------------------------------- |
| `neopixels`   | `NeoPixels`   | Drive 5 RGB LEDs; solid colours; chase, rainbow, pulse animations; bar-graph value mapping                            |
| `lcd_display` | `LCDDisplay`  | Init 240×135 ST7789 LCD; backlight control; fill screen; load & position BMP sprites; bounce and IMU-driven movement |
| `imu_sensor`  | `IMUSensor`   | Read acceleration, gyro, magnetometer; tilt angles; tilt direction; sprite delta for IMU controls                     |
| `audio_out`   | `AudioOutput` | Sine tone generation at any frequency; WAV file playback; play scales                                                 |
| `sd_card`     | `SDCard`      | Mount SD card; read/write/append text files; CSV data logging; filesystem utilities                                   |

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
i2c_bus      ← I2C devices      lcd_display   → graphics
uart_comms   ← serial devices   audio_out     → sound / music
can_bus      ← CAN network      ble_uart      → wireless data
                                 sd_card       → data logging
                                 hid_input     → PC automation
```

---

## Installation

1. Copy the module files you need to the /lib folder of your `CIRCUITPY` drive.
2. Import them in `code.py`:

```python
from digital_io import DigitalInput, EdgeDetector
from neopixels  import NeoPixels, RED, GREEN
from imu_sensor import IMUSensor
```

3. You do **not** need to copy modules you are not using.

---

## Minimal Example — Tilt-controlled NeoPixel colours

```python
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
import time
from ble_uart import BLEUart
from cpu_temp import CPUTemperature

ble  = BLEUart()
temp = CPUTemperature()

ble.configure()   # configures RNBD451 and reboots into data mode

while True:
    ble.send(f"Temp: {temp.formatted_string()}\n")
    time.sleep(2)
```

---

## Notes

- **HID** requires `usb_hid.enable()` in `boot.py`.
- **WAV files** must be mono, 16-bit PCM, ≤ 22 050 Hz.
- **CAN** requires two boards (or a CAN analyser) to verify message exchange.
