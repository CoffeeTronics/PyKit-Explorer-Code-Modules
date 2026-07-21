"""
imu_sensor.py — BNO085 9-Axis IMU with Sensor Fusion
============================================================
Board: Ruler Baseboard / Custom PCB

Wraps the adafruit_bno08x library for the BNO085 IMU with built-in sensor
fusion (accelerometer, gyroscope, magnetometer, quaternion, etc.) via I2C.

Hardware
--------
  board.I2C()       — shared I2C bus (SCL / SDA)
  I2C address: 0x4A (default) or 0x4B (alternate)

Provides
--------
  - Raw acceleration (m/s²), gyroscope (rad/s), magnetometer (µT)
  - Quaternion orientation (rotation vector, game quaternion, geomagnetic)
  - Linear acceleration (gravity removed)
  - Gravity vector
  - Activity classification (walking, running, still, etc.)
  - Stability classification (on table, stationary, stable, in motion)
  - Step counter
  - Shake detection
  - Tilt angles computed from the accelerometer
  - Gesture-style helper: detect tilt direction

Use this module for:
  - Motion-controlled games (tilt to move)
  - Orientation tracking with sensor fusion
  - Activity monitoring (step counting, activity detection)
  - Shake/tap detection
  - Inclinometers / levelling tools
"""

import board
import busio
import math
import time

from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
    BNO_REPORT_ROTATION_VECTOR,
    BNO_REPORT_GAME_ROTATION_VECTOR,
    BNO_REPORT_GEOMAGNETIC_ROTATION_VECTOR,
    BNO_REPORT_LINEAR_ACCELERATION,
    BNO_REPORT_GRAVITY,
    BNO_REPORT_STEP_COUNTER,
    BNO_REPORT_STABILITY_CLASSIFIER,
    BNO_REPORT_ACTIVITY_CLASSIFIER,
    BNO_REPORT_SHAKE_DETECTOR,
)
from adafruit_bno08x.i2c import BNO08X_I2C


# Valid I2C addresses for the BNO085
_VALID_ADDRESSES = (0x4A, 0x4B)
_DEFAULT_ADDRESS = 0x4A
_ALTERNATE_ADDRESS = 0x4B


class InvalidAddressError(Exception):
    """Raised when an invalid I2C address is provided."""
    pass


class IMUSensor:
    """Read acceleration, gyroscope, magnetometer, and sensor fusion data from the BNO085.

    Parameters
    ----------
    i2c : busio.I2C, optional
        I2C bus instance. If None, creates one using board.I2C().
    address : int, optional
        I2C address of the BNO085. Default is 0x4A.
        Alternate address 0x4B can be used for non-hardwired PCBs.
    enable_all : bool, optional
        If True, enables accelerometer, gyroscope, and magnetometer on init.
        If False (default), you must call enable_* methods manually.

    Raises
    ------
    InvalidAddressError
        If address is not 0x4A or 0x4B.

    Example
    -------
    import pykit_explorer
    from imu_sensor import IMUSensor

    # Default address (0x4A)
    imu = IMUSensor()
    imu.enable_accelerometer()

    while True:
        ax, ay, az = imu.acceleration
        print(f"Accel: ({ax:.2f}, {ay:.2f}, {az:.2f}) m/s²")
        time.sleep(0.1)
    """

    # Tilt thresholds for gesture detection (m/s²)
    TILT_THRESHOLD = 3.0

    def __init__(self, i2c=None, address=_DEFAULT_ADDRESS, enable_all=False):
        # Validate address
        if address not in _VALID_ADDRESSES:
            raise InvalidAddressError(
                f"Invalid I2C address 0x{address:02X}. "
                f"Please use the default address 0x{_DEFAULT_ADDRESS:02X} "
                f"or alternate address 0x{_ALTERNATE_ADDRESS:02X}."
            )

        if i2c is None:
            i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)

        self._address = address
        if address == _ALTERNATE_ADDRESS:
            self._bno = BNO08X_I2C(i2c, address=address)
        else:
            self._bno = BNO08X_I2C(i2c)

        # Track which features are enabled
        self._enabled_features = set()

        if enable_all:
            self.enable_basic_sensors()

    # -- Feature enable methods ----------------------------------------------

    def enable_feature(self, feature):
        """Enable a specific BNO report feature."""
        self._bno.enable_feature(feature)
        self._enabled_features.add(feature)

    def enable_accelerometer(self):
        """Enable accelerometer only."""
        self.enable_feature(BNO_REPORT_ACCELEROMETER)

    def enable_gyroscope(self):
        """Enable gyroscope only."""
        self.enable_feature(BNO_REPORT_GYROSCOPE)

    def enable_magnetometer(self):
        """Enable magnetometer only."""
        self.enable_feature(BNO_REPORT_MAGNETOMETER)

    def enable_basic_sensors(self):
        """Enable accelerometer, gyroscope, and magnetometer."""
        self.enable_accelerometer()
        self.enable_gyroscope()
        self.enable_magnetometer()

    def enable_rotation_vector(self):
        """Enable the rotation vector (quaternion with magnetometer)."""
        self.enable_feature(BNO_REPORT_ROTATION_VECTOR)

    def enable_game_rotation_vector(self):
        """Enable game rotation vector (quaternion without magnetometer drift correction)."""
        self.enable_feature(BNO_REPORT_GAME_ROTATION_VECTOR)

    def enable_geomagnetic_rotation_vector(self):
        """Enable geomagnetic rotation vector."""
        self.enable_feature(BNO_REPORT_GEOMAGNETIC_ROTATION_VECTOR)

    def enable_linear_acceleration(self):
        """Enable linear acceleration (gravity removed)."""
        self.enable_feature(BNO_REPORT_LINEAR_ACCELERATION)

    def enable_gravity(self):
        """Enable gravity vector."""
        self.enable_feature(BNO_REPORT_GRAVITY)

    def enable_step_counter(self):
        """Enable step counter."""
        self.enable_feature(BNO_REPORT_STEP_COUNTER)

    def enable_stability_classifier(self):
        """Enable stability classification."""
        self.enable_feature(BNO_REPORT_STABILITY_CLASSIFIER)

    def enable_activity_classifier(self):
        """Enable activity classification."""
        self.enable_feature(BNO_REPORT_ACTIVITY_CLASSIFIER)

    def enable_shake_detector(self):
        """Enable shake detection."""
        self.enable_feature(BNO_REPORT_SHAKE_DETECTOR)

    def enable_all_features(self):
        """Enable all available sensor features."""
        self.enable_basic_sensors()
        self.enable_rotation_vector()
        self.enable_game_rotation_vector()
        self.enable_geomagnetic_rotation_vector()
        self.enable_linear_acceleration()
        self.enable_gravity()
        self.enable_step_counter()
        self.enable_stability_classifier()
        self.enable_activity_classifier()
        self.enable_shake_detector()

    # -- Raw sensor data -----------------------------------------------------

    @property
    def acceleration(self) -> tuple:
        """Acceleration in m/s² as (x, y, z)."""
        return self._bno.acceleration

    @property
    def gyro(self) -> tuple:
        """Angular velocity in rad/s as (x, y, z)."""
        return self._bno.gyro

    @property
    def magnetic(self) -> tuple:
        """Magnetic field in µT as (x, y, z)."""
        return self._bno.magnetic

    # -- Sensor fusion data --------------------------------------------------

    @property
    def quaternion(self) -> tuple:
        """Rotation vector as quaternion (w, x, y, z).

        Requires enable_rotation_vector() to be called first.
        """
        return self._bno.quaternion

    @property
    def game_quaternion(self) -> tuple:
        """Game rotation vector as quaternion (w, x, y, z).

        This quaternion does not use magnetometer correction,
        making it more stable for gaming applications.
        Requires enable_game_rotation_vector() to be called first.
        """
        return self._bno.game_quaternion

    @property
    def geomagnetic_quaternion(self) -> tuple:
        """Geomagnetic rotation vector as quaternion (w, x, y, z).

        Requires enable_geomagnetic_rotation_vector() to be called first.
        """
        return self._bno.geomagnetic_quaternion

    @property
    def linear_acceleration(self) -> tuple:
        """Linear acceleration (gravity removed) in m/s² as (x, y, z).

        Requires enable_linear_acceleration() to be called first.
        """
        return self._bno.linear_acceleration

    @property
    def gravity(self) -> tuple:
        """Gravity vector in m/s² as (x, y, z).

        Requires enable_gravity() to be called first.
        """
        return self._bno.gravity

    # -- Activity and stability ----------------------------------------------

    @property
    def steps(self) -> int:
        """Step count since last reset.

        Requires enable_step_counter() to be called first.
        """
        return self._bno.steps

    @property
    def stability_classification(self) -> str:
        """Stability state: 'Unknown', 'On Table', 'Stationary', 'Stable', or 'In motion'.

        Requires enable_stability_classifier() to be called first.
        """
        return self._bno.stability_classification

    @property
    def activity_classification(self) -> dict:
        """Activity classification with confidence levels.

        Returns dict with keys: 'most_likely', and confidence values for
        'Unknown', 'In-Vehicle', 'On-Bicycle', 'On-Foot', 'Still',
        'Tilting', 'Walking', 'Running', 'OnStairs'.

        Requires enable_activity_classifier() to be called first.
        """
        return self._bno.activity_classification

    @property
    def shake(self) -> bool:
        """True if a shake was detected (latching, resets on read).

        Requires enable_shake_detector() to be called first.
        """
        return self._bno.shake

    # -- Calibration ---------------------------------------------------------

    @property
    def calibration_status(self) -> int:
        """Calibration status (0=unreliable, 1=low, 2=medium, 3=high)."""
        return self._bno.calibration_status

    def begin_calibration(self):
        """Begin the calibration process."""
        self._bno.begin_calibration()

    def save_calibration_data(self):
        """Save calibration data to the sensor's flash memory."""
        self._bno.save_calibration_data()

    # -- Computed orientation ------------------------------------------------

    @property
    def tilt_angle_x(self) -> float:
        """Board tilt about the X-axis in degrees (-90 to +90)."""
        ax, ay, az = self._bno.acceleration
        return math.degrees(math.atan2(ay, math.sqrt(ax ** 2 + az ** 2)))

    @property
    def tilt_angle_y(self) -> float:
        """Board tilt about the Y-axis in degrees (-90 to +90)."""
        ax, ay, az = self._bno.acceleration
        return math.degrees(math.atan2(ax, math.sqrt(ay ** 2 + az ** 2)))

    @property
    def euler_angles(self) -> tuple:
        """Euler angles (roll, pitch, yaw) in degrees computed from quaternion.

        Requires enable_rotation_vector() to be called first.
        Returns (roll, pitch, yaw) tuple.
        """
        qw, qx, qy, qz = self._bno.quaternion

        # Roll (x-axis rotation)
        sinr_cosp = 2 * (qw * qx + qy * qz)
        cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
        roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

        # Pitch (y-axis rotation)
        sinp = 2 * (qw * qy - qz * qx)
        if abs(sinp) >= 1:
            pitch = math.copysign(90, sinp)
        else:
            pitch = math.degrees(math.asin(sinp))

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (qw * qz + qx * qy)
        cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
        yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))

        return (roll, pitch, yaw)

    # -- Gesture / direction detection ----------------------------------------

    def tilt_direction(self) -> str:
        """Return a coarse tilt direction string: 'LEFT', 'RIGHT', 'UP', 'DOWN', or 'FLAT'."""
        ax, ay, _ = self._bno.acceleration
        if ax > self.TILT_THRESHOLD:
            return "RIGHT"
        if ax < -self.TILT_THRESHOLD:
            return "LEFT"
        if ay > self.TILT_THRESHOLD:
            return "DOWN"
        if ay < -self.TILT_THRESHOLD:
            return "UP"
        return "FLAT"

    def is_shaking(self, threshold: float = 15.0) -> bool:
        """Return True if total acceleration magnitude exceeds *threshold* m/s².

        Gravity (~9.8 m/s²) is always present, so threshold should be > 9.8.
        Default 15.0 catches moderate shaking.
        """
        ax, ay, az = self._bno.acceleration
        magnitude = math.sqrt(ax ** 2 + ay ** 2 + az ** 2)
        return magnitude > threshold

    # -- Display-friendly delta for sprite control ---------------------------

    def sprite_delta(self, scale: float = 1.0) -> tuple:
        """Return (dx, dy) pixel deltas suitable for moving a display sprite.

        Maps X/Y accelerometer axes to screen coordinates:
          board tilted right → dx positive (sprite moves right)
          board tilted forward → dy negative (sprite moves up)

        Parameters
        ----------
        scale : multiplier applied to the integer-cast acceleration values

        Returns
        -------
        (dx, dy) tuple of ints
        """
        ax, ay, _ = self._bno.acceleration
        return (int(ax * scale), -int(ay * scale))

    # -- Device info ---------------------------------------------------------

    @property
    def address(self) -> int:
        """Return the I2C address of this sensor."""
        return self._address

    @property
    def enabled_features(self) -> set:
        """Return the set of enabled feature report constants."""
        return self._enabled_features.copy()

    # -- Logging -------------------------------------------------------------

    def print_all(self):
        """Print all basic sensor axes to the console."""
        ax, ay, az = self._bno.acceleration
        gx, gy, gz = self._bno.gyro
        mx, my, mz = self._bno.magnetic
        print(f"Accel  X:{ax:6.2f} Y:{ay:6.2f} Z:{az:6.2f} m/s²")
        print(f"Gyro   X:{gx:6.2f} Y:{gy:6.2f} Z:{gz:6.2f} rad/s")
        print(f"Mag    X:{mx:6.2f} Y:{my:6.2f} Z:{mz:6.2f} µT")

    def print_orientation(self):
        """Print orientation data (requires rotation vector enabled)."""
        roll, pitch, yaw = self.euler_angles
        print(f"Roll: {roll:6.2f}°  Pitch: {pitch:6.2f}°  Yaw: {yaw:6.2f}°")

    def log_loop(self, interval: float = 0.2):
        """Continuously print sensor readings (blocking)."""
        while True:
            self.print_all()
            print()
            time.sleep(interval)
