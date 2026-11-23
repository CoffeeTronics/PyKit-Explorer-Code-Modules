"""
drum_sound_lab.py — Drum Sound Lab
==================================
Board: Dev Board / Ruler Baseboard

A motion-controlled drum machine using synthesized percussion sounds.
Shake the board in different axes to trigger different drum sounds.
Based on drum synthesis from Cap-Touch-SynthDrums by pranavtadikonda6-lang.

Hardware
--------
  board.D3    — User button   (press  → toggle mode / mute)
  board.DAC   — Speaker output (synthio audio chain)
  LCD         — 240 × 135 ST7789 via Ruler baseboard
  IMU         — BNO085 (Ruler baseboard) on shared I2C bus (acceleration sensing)

Drum Mapping (IMU Acceleration)
-------------------------------
  +X axis (shake right)   : Kick Drum
  -X axis (shake left)    : Snare
  +Y axis (shake forward) : Closed Hi-Hat
  -Y axis (shake back)    : Open Hi-Hat
  +Z axis (shake up)      : Cowbell
  -Z axis (shake down)    : Tom

Controls
--------
  D3 press          : Toggle mute on/off

Display
-------
  DRUM row     : last triggered drum name, scale 2
  X/Y/Z bars   : acceleration magnitude indicators
  Trigger indicators for each axis direction

Audio chain
-----------
  synthio.Synthesizer → audioio.AudioOut(board.DAC)
  Sample rate: 22 050 Hz, mono 16-bit signed

Example Usage
-----
import pykit_explorer
from drum_sound_lab import run
run()

"""

import board
import time
import displayio
import vectorio
import terminalio
from adafruit_display_text import label as _label

import audioio
import synthio

from lcd_display import LCDDisplay, Colors
from digital_io import EdgeDetector
from i2c_bus import I2CBus
from imu_sensor import IMUSensor

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE = 22050
SAMPLE_SIZE = 200

# Acceleration thresholds for triggering drums (in m/s^2)
ACCEL_THRESHOLD = 12.0    # minimum acceleration to trigger a drum hit
ACCEL_COOLDOWN = 0.15     # seconds between triggers on same axis

DISPLAY_INTERVAL = 0.05   # seconds between display updates

# ---------------------------------------------------------------------------
# Waveform generation (from Cap-Touch-SynthDrums)
# ---------------------------------------------------------------------------

try:
    import ulab.numpy as np
    _HAS_ULAB = True
except ImportError:
    import array
    import math
    import random
    _HAS_ULAB = False


def _make_waveforms():
    """Generate waveform tables for drum synthesis."""
    if _HAS_ULAB:
        # Using ulab for efficient waveform generation
        sinwave1 = np.array(np.sin(np.linspace(0, 2*np.pi, SAMPLE_SIZE, endpoint=False)) * 32767, dtype=np.int16)
        sinwave2 = np.array(np.sin(np.linspace(np.pi/2, 2.5*np.pi, SAMPLE_SIZE, endpoint=False)) * 32767, dtype=np.int16)

        noisewave_list = []
        import random
        for i in range(SAMPLE_SIZE):
            noisewave_list.append(random.randint(-32767, 32767))
        noisewave = np.array(noisewave_list, dtype=np.int16)

        w1_list = []
        for i in range(SAMPLE_SIZE):
            mixed = sinwave1[i] + (noisewave[i] / 2.0)
            w1_list.append(int(max(min(mixed, 32767), -32767)))
        w1 = np.array(w1_list, dtype=np.int16)

        squarewave_list = []
        for i in range(SAMPLE_SIZE):
            squarewave_list.append(32767 if i < SAMPLE_SIZE // 2 else -32767)
        squarewave = np.array(squarewave_list, dtype=np.int16)

        downwave = np.linspace(32767, -32767, num=3, dtype=np.int16)
    else:
        # Fallback using array module
        sinwave1 = array.array("h", [0] * SAMPLE_SIZE)
        sinwave2 = array.array("h", [0] * SAMPLE_SIZE)
        for i in range(SAMPLE_SIZE):
            sinwave1[i] = int(math.sin(2 * math.pi * i / SAMPLE_SIZE) * 32767)
            sinwave2[i] = int(math.sin(math.pi/2 + 2 * math.pi * i / SAMPLE_SIZE) * 32767)

        noisewave = array.array("h", [0] * SAMPLE_SIZE)
        for i in range(SAMPLE_SIZE):
            noisewave[i] = random.randint(-32767, 32767)

        w1 = array.array("h", [0] * SAMPLE_SIZE)
        for i in range(SAMPLE_SIZE):
            mixed = sinwave1[i] + (noisewave[i] / 2.0)
            w1[i] = int(max(min(mixed, 32767), -32767))

        squarewave = array.array("h", [0] * SAMPLE_SIZE)
        for i in range(SAMPLE_SIZE):
            squarewave[i] = 32767 if i < SAMPLE_SIZE // 2 else -32767

        downwave = array.array("h", [32767, 0, -32767])

    return {
        "sinwave1": sinwave1,
        "sinwave2": sinwave2,
        "noisewave": noisewave,
        "w1": w1,
        "squarewave": squarewave,
        "downwave": downwave,
    }


# ---------------------------------------------------------------------------
# Drum classes (adapted from Cap-Touch-SynthDrums)
# ---------------------------------------------------------------------------

class KickDrum:
    """Bass drum using low frequency sine wave with pitch bend."""

    def __init__(self, synth, waves):
        self.synth = synth
        self.waves = waves
        self.name = "KICK"

    def play(self):
        lfo = synthio.LFO(waveform=self.waves["downwave"])
        lfo.once = True
        lfo.offset = 0.33
        lfo.scale = 0.3
        lfo.rate = 20
        lfo.retrigger()

        amp_env = synthio.Envelope(
            attack_time=0.0, decay_time=0.075, release_time=0,
            attack_level=1, sustain_level=0
        )
        note = synthio.Note(
            frequency=53, envelope=amp_env,
            waveform=self.waves["sinwave2"], bend=lfo
        )
        self.synth.press((note,))


class Snare:
    """Snare drum using noise-based waveform."""

    def __init__(self, synth, waves):
        self.synth = synth
        self.waves = waves
        self.name = "SNARE"

    def play(self):
        lfo = synthio.LFO(waveform=self.waves["downwave"])
        lfo.once = True
        lfo.offset = 0.33
        lfo.scale = 0.3
        lfo.rate = 20
        lfo.retrigger()

        amp_env = synthio.Envelope(
            attack_time=0.0, decay_time=0.115, release_time=0,
            attack_level=1, sustain_level=0
        )
        note = synthio.Note(
            frequency=90, envelope=amp_env,
            waveform=self.waves["w1"], bend=lfo
        )
        self.synth.press((note,))


class HighHat:
    """Hi-hat using noise for crisp percussive sound."""

    def __init__(self, synth, waves, decay=0.08):
        self.synth = synth
        self.waves = waves
        self.decay = decay
        self.name = "HI-HAT" if decay < 0.1 else "OPEN-HH"

    def play(self):
        amp_env = synthio.Envelope(
            attack_time=0.0, decay_time=self.decay, release_time=0,
            attack_level=1, sustain_level=0
        )
        note = synthio.Note(
            frequency=90, envelope=amp_env,
            waveform=self.waves["noisewave"]
        )
        self.synth.press((note,))


class Cowbell:
    """Cowbell using square wave for metallic tone."""

    def __init__(self, synth, waves):
        self.synth = synth
        self.waves = waves
        self.name = "COWBELL"

    def play(self):
        lfo = synthio.LFO(waveform=self.waves["downwave"])
        lfo.once = True
        lfo.offset = 0.33
        lfo.scale = 0.3
        lfo.rate = 20
        lfo.retrigger()

        amp_env = synthio.Envelope(
            attack_time=0.0, decay_time=0.055, release_time=0,
            attack_level=1, sustain_level=0
        )
        note = synthio.Note(
            frequency=540, envelope=amp_env,
            waveform=self.waves["squarewave"], bend=lfo
        )
        self.synth.press((note,))


class Tom:
    """Tom drum using sine wave with pitch bend."""

    def __init__(self, synth, waves):
        self.synth = synth
        self.waves = waves
        self.name = "TOM"

    def play(self):
        lfo = synthio.LFO(waveform=self.waves["downwave"])
        lfo.once = True
        lfo.offset = 0.33
        lfo.scale = 0.25
        lfo.rate = 15
        lfo.retrigger()

        amp_env = synthio.Envelope(
            attack_time=0.0, decay_time=0.12, release_time=0,
            attack_level=1, sustain_level=0
        )
        note = synthio.Note(
            frequency=120, envelope=amp_env,
            waveform=self.waves["sinwave1"], bend=lfo
        )
        self.synth.press((note,))


# ---------------------------------------------------------------------------
# Display geometry (pixels)
# ---------------------------------------------------------------------------

BAR_LABEL_X = 4
BAR_X = 28
BAR_W = 100
BAR_H = 10
BAR_GAP = 16

INDICATOR_SIZE = 12
INDICATOR_GAP = 8

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run():
    """Initialize hardware and enter the Drum Sound Lab main loop.

    Blocks indefinitely — call this as the last statement in code.py.
    """

    # -- Waveforms -----------------------------------------------------------
    waves = _make_waveforms()

    # -- Audio chain ---------------------------------------------------------
    audio = audioio.AudioOut(board.DAC)
    synth = synthio.Synthesizer(sample_rate=SAMPLE_RATE)
    audio.play(synth)

    # -- Create drum instances -----------------------------------------------
    drums = {
        "+X": KickDrum(synth, waves),      # shake right
        "-X": Snare(synth, waves),          # shake left
        "+Y": HighHat(synth, waves, 0.08),  # shake forward (closed hi-hat)
        "-Y": HighHat(synth, waves, 0.15),  # shake back (open hi-hat)
        "+Z": Cowbell(synth, waves),        # shake up
        "-Z": Tom(synth, waves),            # shake down
    }

    # -- Hardware ------------------------------------------------------------
    lcd = LCDDisplay()
    btn = EdgeDetector(board.D3)
    i2c = I2CBus()
    imu = IMUSensor(i2c=i2c.bus)

    lcd.backlight_on()

    # -- LCD layout ----------------------------------------------------------
    group, _ = lcd.make_group(Colors.BLACK)

    lcd.add_label(group, "DRUM SOUND LAB",
                  120, 2, color=Colors.WHITE, scale=1)
    drum_lbl = lcd.add_label(group, "SHAKE TO PLAY!",
                              120, 18, color=Colors.CYAN, scale=2)

    # Axis labels and mapping info
    lcd.add_label(group, "+X:KICK  -X:SNARE",
                  120, 42, color=Colors.GRAY, scale=1)
    lcd.add_label(group, "+Y:HI-HT -Y:OPEN-HH",
                  120, 54, color=Colors.GRAY, scale=1)
    lcd.add_label(group, "+Z:CWBLL -Z:TOM",
                  120, 66, color=Colors.GRAY, scale=1)

    # Accel bar labels
    group.append(_label.Label(
        terminalio.FONT, text="X", color=Colors.RED, scale=1,
        anchor_point=(0.0, 0.0), anchored_position=(BAR_LABEL_X, 82)))
    group.append(_label.Label(
        terminalio.FONT, text="Y", color=Colors.GREEN, scale=1,
        anchor_point=(0.0, 0.0), anchored_position=(BAR_LABEL_X, 96)))
    group.append(_label.Label(
        terminalio.FONT, text="Z", color=Colors.BLUE, scale=1,
        anchor_point=(0.0, 0.0), anchored_position=(BAR_LABEL_X, 110)))

    # -- Vectorio bars for acceleration visualization ------------------------

    # X axis bar (red)
    x_pal = displayio.Palette(2)
    x_pal[0] = 0x300000
    x_pal[1] = 0xFF0000
    group.append(vectorio.Rectangle(
        pixel_shader=x_pal, color_index=0,
        x=BAR_X, y=82, width=BAR_W, height=BAR_H))
    x_bar_pos = vectorio.Rectangle(
        pixel_shader=x_pal, color_index=1,
        x=BAR_X + BAR_W // 2, y=82, width=2, height=BAR_H)
    group.append(x_bar_pos)

    # Y axis bar (green)
    y_pal = displayio.Palette(2)
    y_pal[0] = 0x003000
    y_pal[1] = 0x00FF00
    group.append(vectorio.Rectangle(
        pixel_shader=y_pal, color_index=0,
        x=BAR_X + BAR_W + 10, y=82, width=BAR_W, height=BAR_H))
    y_bar_pos = vectorio.Rectangle(
        pixel_shader=y_pal, color_index=1,
        x=BAR_X + BAR_W + 10 + BAR_W // 2, y=82, width=2, height=BAR_H)
    group.append(y_bar_pos)

    # Z axis bar (blue)
    z_pal = displayio.Palette(2)
    z_pal[0] = 0x000030
    z_pal[1] = 0x0000FF
    group.append(vectorio.Rectangle(
        pixel_shader=z_pal, color_index=0,
        x=BAR_X, y=96, width=BAR_W, height=BAR_H))
    z_bar_pos = vectorio.Rectangle(
        pixel_shader=z_pal, color_index=1,
        x=BAR_X + BAR_W // 2, y=96, width=2, height=BAR_H)
    group.append(z_bar_pos)

    # Status indicator
    status_lbl = lcd.add_label(group, "D3=MUTE",
                                120, 120, color=Colors.GRAY, scale=1)

    # -- State ---------------------------------------------------------------
    muted = False
    last_drum = "---"
    last_trigger = {axis: 0.0 for axis in drums.keys()}
    next_display = time.monotonic()

    # -- Main loop -----------------------------------------------------------
    while True:
        now = time.monotonic()

        btn.update()

        # D3: toggle mute
        if btn.fell:
            muted = not muted
            status_lbl.text = "MUTED" if muted else "D3=MUTE"
            status_lbl.color = Colors.RED if muted else Colors.GRAY

        # -- Read IMU acceleration -------------------------------------------
        accel = imu.acceleration
        if accel is None:
            continue

        ax, ay, az = accel

        # -- Check for shake triggers ----------------------------------------
        triggered_axis = None
        triggered_drum = None

        # Check X axis
        if ax > ACCEL_THRESHOLD and now - last_trigger["+X"] > ACCEL_COOLDOWN:
            triggered_axis = "+X"
            triggered_drum = drums["+X"]
            last_trigger["+X"] = now
        elif ax < -ACCEL_THRESHOLD and now - last_trigger["-X"] > ACCEL_COOLDOWN:
            triggered_axis = "-X"
            triggered_drum = drums["-X"]
            last_trigger["-X"] = now

        # Check Y axis
        if ay > ACCEL_THRESHOLD and now - last_trigger["+Y"] > ACCEL_COOLDOWN:
            triggered_axis = "+Y"
            triggered_drum = drums["+Y"]
            last_trigger["+Y"] = now
        elif ay < -ACCEL_THRESHOLD and now - last_trigger["-Y"] > ACCEL_COOLDOWN:
            triggered_axis = "-Y"
            triggered_drum = drums["-Y"]
            last_trigger["-Y"] = now

        # Check Z axis (subtract gravity ~9.8)
        az_adj = az - 9.8  # Remove gravity bias when board is flat
        if az_adj > ACCEL_THRESHOLD and now - last_trigger["+Z"] > ACCEL_COOLDOWN:
            triggered_axis = "+Z"
            triggered_drum = drums["+Z"]
            last_trigger["+Z"] = now
        elif az_adj < -ACCEL_THRESHOLD and now - last_trigger["-Z"] > ACCEL_COOLDOWN:
            triggered_axis = "-Z"
            triggered_drum = drums["-Z"]
            last_trigger["-Z"] = now

        # Play the triggered drum
        if triggered_drum is not None and not muted:
            triggered_drum.play()
            last_drum = triggered_drum.name
            drum_lbl.text = last_drum
            drum_lbl.color = Colors.YELLOW

        # -- Update display (throttled) --------------------------------------
        if now >= next_display:
            next_display = now + DISPLAY_INTERVAL

            # Update acceleration bars (centered, showing positive/negative)
            # Map acceleration to bar position: center = 0, edges = +/- 20 m/s^2
            max_accel = 20.0

            # X bar
            x_norm = max(-1.0, min(1.0, ax / max_accel))
            x_pos = int(BAR_X + BAR_W // 2 + x_norm * (BAR_W // 2 - 2))
            x_bar_pos.x = min(x_pos, BAR_X + BAR_W // 2) if x_norm < 0 else BAR_X + BAR_W // 2
            x_bar_pos.width = max(2, abs(int(x_norm * (BAR_W // 2))))

            # Y bar
            y_norm = max(-1.0, min(1.0, ay / max_accel))
            y_base = BAR_X + BAR_W + 10
            y_pos = int(y_base + BAR_W // 2 + y_norm * (BAR_W // 2 - 2))
            y_bar_pos.x = min(y_pos, y_base + BAR_W // 2) if y_norm < 0 else y_base + BAR_W // 2
            y_bar_pos.width = max(2, abs(int(y_norm * (BAR_W // 2))))

            # Z bar (adjusted for gravity)
            z_norm = max(-1.0, min(1.0, az_adj / max_accel))
            z_pos = int(BAR_X + BAR_W // 2 + z_norm * (BAR_W // 2 - 2))
            z_bar_pos.x = min(z_pos, BAR_X + BAR_W // 2) if z_norm < 0 else BAR_X + BAR_W // 2
            z_bar_pos.width = max(2, abs(int(z_norm * (BAR_W // 2))))

            # Fade drum label back to cyan after trigger
            if drum_lbl.color == Colors.YELLOW:
                drum_lbl.color = Colors.CYAN
