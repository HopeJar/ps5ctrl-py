"""Utilities to connect to a PS5 DualSense controller via USB."""


from __future__ import annotations
import time
try:
    from pydualsense.enums import TriggerModes
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
        self._r2_force_level = 0
        self._r2_mode_index = 0
        self._trigger_modes = list(TriggerModes)

    def open(self) -> None:
        """Open the connection to the controller over USB."""
        self.ds.init()

    def close(self) -> None:
        """Close the connection to the controller."""
        # Stop vibration motors
        self.ds.setRightMotor(0)
        self.ds.setLeftMotor(0)

        # Reset trigger forces and modes
        self.ds.triggerR.setMode(TriggerModes.Off)
        self.ds.triggerR.forces = [0] * 7

        self.ds.triggerL.setMode(TriggerModes.Off)
        self.ds.triggerL.forces = [0] * 7

        # Send reset state to controller before closing
        self.ds.sendReport()

        self.ds.close()


    def set_r2_force(self, force: int) -> None:
        """Set R2 resistance using slot 6 and send report."""
        self.ds.triggerR.setMode(TriggerModes.Rigid)
        self.ds.triggerR.setForce(6, force)
        self.ds.sendReport()

    def cycle_r2_force(self) -> None:
        """Cycle through R2 trigger force levels 0–6."""
        self._r2_force_level = (self._r2_force_level + 1) % 7
        self.set_r2_force(self._r2_force_level)
        print(f"R2 force set to {self._r2_force_level}")

    def cycle_r2_mode(self) -> None:
        """Cycle through R2 trigger modes."""
        self._r2_mode_index = (self._r2_mode_index + 1) % len(self._trigger_modes)
        mode = self._trigger_modes[self._r2_mode_index]
        self.ds.triggerR.setMode(mode)
        self.ds.sendReport()
        print(f"R2 trigger mode set to: {mode.name}")

    def list_trigger_modes(self) -> None:
        "Print out the available trigger modes"
        print("Available trigger modes:")
        for mode in self._trigger_modes:
            print(f"- {mode.name}")

    def read_loop(self) -> None:
        """Listen for controller events using pydualsense event handlers."""

        print("Listening for controller input. Press CTRL+C to stop.")

        # Register event callbacks
        self.ds.l1_changed += lambda val: print(f"L1: {val}")
        self.ds.r1_changed += lambda val: print(f"R1: {val}")
        # self.ds.l2_value_changed += lambda val: print(f"L2: {val}")
        # self.ds.r2_value_changed += lambda val: print(f"R2: {val}")
        # self.ds.r2_value_changed += lambda val: self.ds.setRightMotor(255 - val)
        # self.ds.l2_value_changed += lambda val: self.ds.setLeftMotor(255 - val)
        self.ds.l2_value_changed += lambda val: print(f"L2 value: {val}")
        self.ds.r2_value_changed += lambda val: print(f"R2 value: {val}")

        self.ds.l3_changed += lambda val: print(f"L3: {val}")
        self.ds.r3_changed += lambda val: print(f"R3: {val}")
        self.ds.dpad_up += lambda _: print("D-Pad: Up")
        self.ds.dpad_down += lambda _: print("D-Pad: Down")
        self.ds.dpad_left += lambda _: print("D-Pad: Left")
        self.ds.dpad_right += lambda _: print("D-Pad: Right")
        self.ds.left_joystick_changed += lambda x, y: print(f"Left Stick: x={x}, y={y}")
        self.ds.right_joystick_changed += lambda x, y: print(f"Right Stick: x={x}, y={y}")
        self.ds.cross_pressed += lambda _: print("Cross Pressed")
        self.ds.circle_pressed += lambda _: print("Circle Pressed")
        
        self.ds.square_pressed += lambda val: self.cycle_r2_mode() if val else None
        # self.ds.square_pressed += lambda _: print("Square Pressed")
        # self.ds.triangle_pressed += lambda _: print("Triangle Pressed")
        self.ds.triangle_pressed += lambda val: self.cycle_r2_force() if val else None


        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping controller listener...")
        finally:
            self.close()
