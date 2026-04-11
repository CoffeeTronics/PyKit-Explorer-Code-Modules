"""
audio_out.py — DAC & WAV Audio Output
=======================================
Board: Ruler Baseboard

Provides two audio output modes:
  1. **Sine tone** — generates a pure sine wave at a specified frequency
     using the on-board DAC (board.DAC).
  2. **WAV playback** — plays a mono 16-bit PCM WAV file (≤22 kHz) from the
     CIRCUITPY filesystem or SD card.

Hardware
--------
  board.DAC  — dedicated audio DAC output pin (connect to audio amplifier or
               speaker with coupling capacitor)
  board.D3   — onboard user button (used as trigger in the original test)

Requires
--------
  audiocore (built-in), audioio (built-in)

WAV file requirements
----------------------
  Mono, 16-bit PCM, 22 050 Hz or less.
  Stereo files and compressed formats (MP3, AAC) are NOT supported.

Use this module for:
  - Sound effects in games
  - Alert tones and notifications
  - Voice / music playback from SD card
  - Synthesised tones for musical instruments
"""

import array
import math
import board
import digitalio
import time
from audiocore import RawSample, WaveFile

try:
    from audioio import AudioOut
except ImportError:
    try:
        from audiopwmio import PWMAudioOut as AudioOut
    except ImportError:
        AudioOut = None


class AudioOutput:
    """Play sine tones and WAV files through the board DAC.

    Parameters
    ----------
    pin         : audio output pin (default board.DAC)

    Example — tone
    --------------
    >>> from audio_out import AudioOutput
    >>> audio = AudioOutput()
    >>> audio.play_tone(440, duration=1.0)     # 440 Hz for 1 second
    >>> audio.play_tone(880)                   # start 880 Hz, non-blocking
    >>> audio.stop()

    Example — WAV
    -------------
    >>> audio.play_wav("AudioFiles/chime.wav")
    >>> audio.play_wav("AudioFiles/alert.wav", loop=False)
    """

    def __init__(self, pin=board.DAC):
        if AudioOut is None:
            raise RuntimeError("No AudioOut or PWMAudioOut available on this board.")
        self._audio = AudioOut(pin)
        self._tone_sample = None

    # -- Sine tone -----------------------------------------------------------

    def _make_sine(self, frequency: int, volume: float = 0.1) -> RawSample:
        """Build a RawSample buffer containing an integer number of sine cycles.

        Uses GCD(sample_rate, frequency) to find the shortest buffer that holds
        a whole number of complete cycles, so the loop point is always exact.

        Example — 3000 Hz at 8000 Hz sample rate:
            gcd(8000, 3000) = 1000  →  3 cycles in 8 samples  →  3000 Hz ✓
            (the naive 8000 // 3000 = 2 samples produces two equal DC values
            because sin(0) ≈ sin(π) ≈ 0, so the speaker never moves)
        """
        sample_rate = 8000
        a, b = sample_rate, frequency
        while b:
            a, b = b, a % b
        g = a
        num_cycles = frequency // g        # complete sine cycles in the buffer
        length     = sample_rate // g      # samples needed
        buf = array.array("H", [0] * length)
        for i in range(length):
            buf[i] = int((1 + math.sin(math.pi * 2 * num_cycles * i / length))
                         * volume * (2 ** 15 - 1))
        return RawSample(buf)

    def play_tone(self, frequency: int = 1000, volume: float = 0.1,
                  duration: float = None):
        """Generate and play a sine wave tone.

        Parameters
        ----------
        frequency : tone frequency in Hz (default 1000)
        volume    : amplitude 0.0–1.0 (default 0.1 — DAC output is loud!)
        duration  : seconds to play, then stop (default None = play until stop())
        """
        sample = self._make_sine(frequency, volume)
        self._audio.play(sample, loop=True)
        if duration is not None:
            time.sleep(duration)
            self.stop()

    def play_scale(self, notes: list = None, duration_each: float = 0.3,
                   volume: float = 0.1):
        """Play a list of frequencies in sequence (blocking).

        Default plays a C-major scale.
        """
        if notes is None:
            notes = [262, 294, 330, 349, 392, 440, 494, 523]  # C4–C5
        for freq in notes:
            self.play_tone(freq, volume=volume, duration=duration_each)

    # -- WAV playback --------------------------------------------------------

    def play_wav(self, path: str, loop: bool = False):
        """Play a WAV file from the filesystem.

        Parameters
        ----------
        path : path to WAV file, e.g. "AudioFiles/beep.wav"
        loop : if True, loop the file continuously until stop() is called

        Note: WAV must be mono, 16-bit PCM, ≤22 050 Hz.
        """
        wave_file = open(path, "rb")
        wave = WaveFile(wave_file)
        self._audio.play(wave, loop=loop)
        if not loop:
            while self._audio.playing:
                pass
            wave_file.close()

    def play_wav_list(self, paths: list, delay: float = 0.0):
        """Play a list of WAV files in sequence (blocking).

        Parameters
        ----------
        paths : list of file path strings
        delay : seconds to pause between files
        """
        for path in paths:
            self.play_wav(path, loop=False)
            if delay:
                time.sleep(delay)

    # -- Control -------------------------------------------------------------

    def stop(self):
        """Stop any currently playing audio."""
        self._audio.stop()

    @property
    def is_playing(self) -> bool:
        """True while audio is currently playing."""
        return self._audio.playing

    def deinit(self):
        self._audio.deinit()
