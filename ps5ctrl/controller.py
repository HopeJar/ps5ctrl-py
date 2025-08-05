"""Utilities to connect to a PS5 DualSense controller via USB."""


from __future__ import annotations
import time
try:
    from pydualsense import pydualsense
except ImportError as e:  # pragma: no cover - optional dependency
    pydualsense = None


class DualSenseController:

    """Simple wrapper around :class:`pydualsense.pydualsense`.

    This class exposes basic methods for opening the connection and
    continuously reading the controller state. It is intentionally minimal
    so that projects can easily build additional functionality on top.
    """

    def __init__(self) -> None:
        """Create a new :class:`DualSenseController` instance."""

        if pydualsense is None:
            raise ImportError(
                "pydualsense is required. Install via 'pip install pydualsense'."
            )
        self.ds = pydualsense()

    def open(self) -> None:
        """Open the connection to the controller over USB."""
        self.ds.init()

    def close(self) -> None:

        """Close the connection to the controller."""

        self.ds.close()

    def read_loop(self) -> None:
        """Listen for controller events using pydualsense event handlers."""

        print("Listening for controller input. Press CTRL+C to stop.")

        # Register event callbacks
        self.ds.l1_changed += lambda val: print(f"L1: {val}")
        self.ds.r1_changed += lambda val: print(f"R1: {val}")
        self.ds.l2_value_changed += lambda val: print(f"L2: {val}")
        self.ds.r2_value_changed += lambda val: print(f"R2: {val}")
        self.ds.dpad_up += lambda _: print("D-Pad: Up")
        self.ds.dpad_down += lambda _: print("D-Pad: Down")
        self.ds.dpad_left += lambda _: print("D-Pad: Left")
        self.ds.dpad_right += lambda _: print("D-Pad: Right")
        self.ds.left_joystick_changed += lambda x, y: print(f"Left Stick: x={x}, y={y}")
        self.ds.right_joystick_changed += lambda x, y: print(f"Right Stick: x={x}, y={y}")
        self.ds.cross_pressed += lambda _: print("Cross Pressed")
        self.ds.circle_pressed += lambda _: print("Circle Pressed")
        self.ds.square_pressed += lambda _: print("Square Pressed")
        self.ds.triangle_pressed += lambda _: print("Triangle Pressed")

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping controller listener...")
        finally:
            self.close()
