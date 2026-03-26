"""
ble_uart.py — BLE UART via RNBD451 Module
=========================================
Board: Dev Board

Manages the Microchip RNBD451 BLE module connected to the dev board via:
  board.BLE_TX, board.BLE_RX  — UART data bus
  board.BLE_CLR               — hardware reset pin

The RNBD451 is configured using its ASCII command interface.  Once in data
mode, any bytes written to the UART are transparently forwarded over BLE to
a connected central device (phone, PC, etc.).

Typical workflow
----------------
  1. Create a BLEUart instance  → resets module into data mode
  2. Call send() / receive() to exchange data with the BLE central

BLE Connection from phone
-------------------------
  Use the "MBD" (Microchip Bluetooth Data) app or any BLE UART terminal app.
  The device advertises as "RNBD451-xxxx" by default.

Use this module for:
  - Wireless serial data to a smartphone or PC
  - Sending sensor readings over BLE
  - Receiving commands from a BLE central device
"""

import board
import busio
import digitalio
import time


class BLEUart:
    """Communicate wirelessly via the RNBD451 BLE UART module.

    Parameters
    ----------
    baudrate : UART baud rate (default 115200, matching RNBD451 default)

    Example
    -------
    >>> from ble_uart import BLEUart
    >>> ble = BLEUart()
    >>> while True:
    ...     reply = ble.receive()
    ...     if ble.connected:
    ...         ble.send("Hello BLE!\\n")
    ...     if reply:
    ...         print("Got:", reply)
    ...     time.sleep(1)
    """

    def __init__(self, baudrate: int = 115200):
        # Release pins in case they are still held from a previous run
        for pin in (board.BLE_TX, board.BLE_RX, board.BLE_CLR):
            try:
                tmp = digitalio.DigitalInOut(pin)
                tmp.deinit()
            except ValueError:
                pass

        self._uart = busio.UART(board.BLE_TX, board.BLE_RX,
                                baudrate=baudrate, timeout=0.5)
        self._reset_pin = digitalio.DigitalInOut(board.BLE_CLR)
        self._reset_pin.direction = digitalio.Direction.OUTPUT
        self._connected = False
        self._rx_buf = ""
        self._reset()

    # -- Initialisation ------------------------------------------------------

    def _reset(self):
        """Hardware reset the RNBD451 module (200 ms LOW pulse)."""
        self._reset_pin.value = False
        time.sleep(0.2)
        self._reset_pin.value = True
        time.sleep(1.0)

    # -- Connection status -----------------------------------------------------

    @property
    def connected(self) -> bool:
        """True if a BLE central device is currently connected."""
        return self._connected

    def _parse_status(self, text: str) -> str:
        """Strip RNBD451 status messages from text and update connection state.

        The module sends %CONNECT,<params>% on connection and
        %DISCONNECT% on disconnection.  Returns the text with
        status messages removed so only user data remains.
        """
        self._rx_buf += text
        user_data = ""
        while "%" in self._rx_buf:
            before, _, rest = self._rx_buf.partition("%")
            user_data += before
            if "%" not in rest:
                # incomplete status message — keep in buffer for next read
                self._rx_buf = "%" + rest
                return user_data
            msg, _, rest = rest.partition("%")
            if msg.startswith("CONNECT"):
                self._connected = True
            elif msg.startswith("DISCONNECT"):
                self._connected = False
            self._rx_buf = rest
        user_data += self._rx_buf
        self._rx_buf = ""
        return user_data

    # -- Data mode send / receive --------------------------------------------

    def send(self, text: str, encoding: str = "ascii"):
        """Send a string over BLE to the connected central device."""
        self._uart.write(bytes(text, encoding))

    def send_bytes(self, data: bytes):
        """Send raw bytes over BLE."""
        self._uart.write(data)

    def receive(self, num_bytes: int = 64) -> str:
        """Read incoming BLE data and return as a string.

        Returns an empty string if nothing is available.
        Status messages from the RNBD451 are parsed and stripped automatically.
        """
        data = self._uart.read(num_bytes)
        if data is None:
            return self._parse_status("")
        raw_text = "".join([chr(b) for b in data])
        return self._parse_status(raw_text)

    def _read_raw(self, num_bytes: int = 20):
        return self._uart.read(num_bytes)

    def deinit(self):
        self._uart.deinit()
        self._reset_pin.deinit()
