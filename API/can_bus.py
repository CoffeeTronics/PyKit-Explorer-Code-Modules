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


class CANBus:
    """Send and receive CAN frames.

    Parameters
    ----------
    baudrate    : CAN bus speed in bps (default 250_000)
    auto_restart: automatically restart after bus-off condition

    Example — Transmitter
    ----------------------
    >>> from can_bus import CANBus
    >>> can = CANBus()
    >>> can.send(0x408, b"hello!")
    >>> can.send_packed(0x408, count=1, timestamp_ms=1000)

    Example — Receiver
    ------------------
    >>> from can_bus import CANBus
    >>> can = CANBus()
    >>> with can.listener(match_id=0x408) as listener:
    ...     while True:
    ...         msg = listener.receive()
    ...         if msg:
    ...             print("ID:", hex(msg.id), "Data:", msg.data)
    """

    def __init__(self, baudrate: int = 250_000, auto_restart: bool = True):
        # Bring transceiver out of standby if the board has a standby pin
        if hasattr(board, "CAN_STANDBY"):
            standby = digitalio.DigitalInOut(board.CAN_STANDBY)
            standby.switch_to_output(False)

        # Enable boost converter if present
        if hasattr(board, "BOOST_ENABLE"):
            boost = digitalio.DigitalInOut(board.BOOST_ENABLE)
            boost.switch_to_output(True)

        self._can = canio.CAN(rx=board.CAN_RX, tx=board.CAN_TX,
                              baudrate=baudrate, auto_restart=auto_restart)
        self._last_bus_state = None

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
        state = str(self._can.state)
        if verbose and state != self._last_bus_state:
            print(f"CAN bus state changed to: {state}")
            self._last_bus_state = state
        return state

    # -- Receive (context manager) -------------------------------------------

    def listener(self, match_id: int = None, timeout: float = 0.9):
        """Return a canio.Listener context manager.

        Parameters
        ----------
        match_id : CAN ID to filter for (None = accept all)
        timeout  : receive timeout in seconds

        Usage
        -----
        >>> with can.listener(match_id=0x408) as listener:
        ...     msg = listener.receive()   # returns None on timeout
        """
        if match_id is not None:
            matches = [canio.Match(match_id)]
        else:
            matches = []
        return self._can.listen(matches=matches, timeout=timeout)

    def receive_once(self, match_id: int = None,
                     timeout: float = 0.9) -> canio.Message:
        """Block until one matching message is received or timeout expires.

        Returns the canio.Message or None on timeout.
        """
        with self.listener(match_id=match_id, timeout=timeout) as listener:
            return listener.receive()

    def deinit(self):
        self._can.deinit()
