"""
can_bus.py — CAN Bus Communication
=====================================
Board: Dev Board

Wraps the canio library for transmitting and receiving CAN frames.
Handles optional standby and boost converter pins automatically.

Hardware
--------
  board.CAN_TX, board.CAN_RX — dedicated CAN peripheral pins
  board.CAN_STANDBY          — transceiver standby (deasserted on init)
  board.BOOST_ENABLE         — optional boost converter enable

Default baud rate: 250 kbps (common for automotive and robotics applications)

Use this module for:
  - Vehicle/automotive network interfacing
  - Multi-board robotics communication
  - Industrial sensor networks
  - Any application requiring reliable multi-master messaging
"""

import board
import canio
import digitalio
import struct
import time

# Workaround for CircuitPython 10.1 canio on SAMx5: closing a canio.Listener
# frees its RX FIFO but never its hardware filter, so after about 4 listeners
# canio raises "Filters too complex" until a hard reset (and only 2 can be open
# at once).  CANBus therefore opens ONE unfiltered hardware listener and filters
# by ID in software; frames not yet asked for wait in a small queue.
# The hardware FIFO holds only 3 frames (all IDs together), so keep calling
# receive() / in_waiting() while frames are arriving; once read, frames for
# other IDs wait in the software queue.
# Re-check on CircuitPython 11.x: if canio frees filters there, listener() can
# go back to returning canio.Listener objects directly.
_QUEUE_MAX = 32       # frames kept for IDs nobody has asked for yet (oldest dropped)


class _Listener:
    """Returned by CANBus.listener(): behaves like a canio.Listener for one ID (or all)."""

    def __init__(self, bus, match_id, timeout):
        self._bus = bus
        self._id = match_id
        self.timeout = timeout

    def receive(self):
        """Return the next matching message, or None if none arrives within timeout."""
        return self._bus._take(self._id, self.timeout)

    def in_waiting(self) -> int:
        """Number of matching messages that can be received without waiting."""
        return self._bus._waiting(self._id)

    def deinit(self):
        """Nothing to release: the shared hardware listener stays open."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.deinit()


class CANBus:
    """Send and receive CAN frames.

    Parameters
    ----------
    baudrate    : CAN bus speed in bps (default 250_000)
    auto_restart: automatically restart after bus-off condition

    Example - Transmitter - Send CAN frames and packed counters
    ----------------------
import pykit_explorer
from can_bus import CANBus
can = CANBus()
while True:
    can.check_bus_state()
    can.send(0x408, b"hello!")
    can.send_packed(0x408, count=1, timestamp_ms=1000)
    time.sleep(0.5)

    Example - Receiver - Listen for and print CAN messages
    ------------------
import pykit_explorer
from can_bus import CANBus
can = CANBus()
can.check_bus_state()
with can.listener(match_id=0x408) as listener:
    while True:
        can.check_bus_state()
        msg = listener.receive()
        if msg:
            print("ID:", hex(msg.id), "Data:", msg.data)
    """

    def __init__(self, baudrate: int = 250_000, auto_restart: bool = True):
        # Bring transceiver out of standby if the board has a standby pin.
        # Must be stored as instance attributes — local vars would be GC'd after
        # __init__ returns, deinit()ing the pin and floating STBY high = standby.
        self._standby = None
        _standby_pin = (getattr(board, "CAN_STANDBY", None)
                        or getattr(board, "CAN_STDBY", None))
        if _standby_pin is not None:
            self._standby = digitalio.DigitalInOut(_standby_pin)
            self._standby.switch_to_output(False)

        self._boost = None
        if hasattr(board, "BOOST_ENABLE"):
            self._boost = digitalio.DigitalInOut(board.BOOST_ENABLE)
            self._boost.switch_to_output(True)

        self._can = canio.CAN(rx=board.CAN_RX, tx=board.CAN_TX,
                              baudrate=baudrate, auto_restart=auto_restart)
        self._last_bus_state = None
        self._hw_listener = None      # the one shared canio.Listener (opened on first use)
        self._queue = []              # received frames not yet handed out

    # -- Transmit ------------------------------------------------------------

    def send(self, msg_id: int, data: bytes):
        """Send a raw CAN frame.

        Parameters
        ----------
        msg_id : 11-bit CAN ID (0x000–0x7FF)
        data   : up to 8 bytes of payload
        """
        message = canio.Message(id=msg_id, data=data)
        self._can.send(message)

    def send_packed(self, msg_id: int, count: int, timestamp_ms: int):
        """Send a 8-byte frame packed as two 32-bit unsigned integers.

        This matches the format used in the CAN test scripts:
            [count : uint32_le][timestamp_ms : uint32_le]

        Parameters
        ----------
        msg_id       : CAN message ID
        count        : message sequence counter
        timestamp_ms : millisecond timestamp (use time.monotonic_ns() // 1_000_000)
        """
        data = struct.pack("<II", count, timestamp_ms)
        self.send(msg_id, data)

    # -- Bus state monitoring ------------------------------------------------

    def check_bus_state(self, verbose: bool = True) -> str:
        """Return the current bus state string and optionally print a change.

        Returns one of: 'ERROR_ACTIVE', 'ERROR_WARNING', 'ERROR_PASSIVE',
        'BUS_OFF', 'CLOSED'
        """
        state = str(self._can.state).split(".")[-1]
        if verbose and state != self._last_bus_state:
            print(f"CAN bus state changed to: {state}")
            self._last_bus_state = state
        return state

    # -- Receive (context manager) -------------------------------------------

    def listener(self, match_id: int = None, timeout: float = 0.9):
        """Return a listener (context manager) for one CAN ID, or for all IDs.

        It works like a canio.Listener (receive(), in_waiting(), timeout), and
        can be created as often as you like: every listener shares one hardware
        listener and filters by ID in software.  A frame is handed to the first
        listener that asks for it.

        Parameters
        ----------
        match_id : CAN ID to filter for (None = accept all)
        timeout  : receive timeout in seconds

        Usage
        -----
with can.listener(match_id=0x408) as listener:
    msg = listener.receive()   # returns None on timeout
        """
        return _Listener(self, match_id, timeout)

    def receive_once(self, match_id: int = None,
                     timeout: float = 0.9) -> canio.Message:
        """Block until one matching message is received or timeout expires.

        Returns the canio.Message or None on timeout.
        """
        return self._take(match_id, timeout)

    # -- Shared hardware listener (see the note at the top of this file) -----

    def _pump(self):
        """Move every frame waiting in the hardware FIFO into the queue."""
        if self._hw_listener is None:
            self._hw_listener = self._can.listen(timeout=0)
        hw = self._hw_listener
        while hw.in_waiting():
            msg = hw.receive()
            if msg is not None:
                self._queue.append(msg)
        if len(self._queue) > _QUEUE_MAX:
            del self._queue[:len(self._queue) - _QUEUE_MAX]

    def _waiting(self, match_id):
        self._pump()
        if match_id is None:
            return len(self._queue)
        return sum(1 for m in self._queue if m.id == match_id)

    def _take(self, match_id, timeout):
        end = time.monotonic() + timeout
        while True:
            self._pump()
            for i, msg in enumerate(self._queue):
                if match_id is None or msg.id == match_id:
                    return self._queue.pop(i)
            if time.monotonic() >= end:
                return None

    def deinit(self):
        if self._hw_listener is not None:
            self._hw_listener.deinit()
            self._hw_listener = None
        self._queue = []
        self._can.deinit()
        if self._standby:
            self._standby.deinit()
        if self._boost:
            self._boost.deinit()
