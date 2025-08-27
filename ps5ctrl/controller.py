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
        self._l2_force_level = 0
        self._l2_mode_index = 0
        self._trigger_modes = list(TriggerModes)
        # Reentrancy guards for trigger force cycling
        self._handling_r2_force = False
        self._handling_l2_force = False

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
        """Set the resistance of the R2 trigger.

        Args:
            force: Resistance value (0-255) applied to slot 6.
        """
        self.ds.triggerR.setMode(TriggerModes.Rigid)
        self.ds.triggerR.setForce(6, force)
        self.ds.sendReport()

    def cycle_r2_force(self) -> None:
        """Advance to the next R2 trigger force preset."""
        if self._handling_r2_force:
            return
        self._handling_r2_force = True
        try:
            self._r2_force_level = (self._r2_force_level + 1) % 7
            self.set_r2_force(self._r2_force_level)
            print(f"R2 force set to {self._r2_force_level}")
        finally:
            self._handling_r2_force = False

    def cycle_r2_mode(self) -> None:
        """Advance to the next R2 trigger mode."""
        self._r2_mode_index = (self._r2_mode_index + 1) % len(self._trigger_modes)
        mode = self._trigger_modes[self._r2_mode_index]
        self.ds.triggerR.setMode(mode)
        self.ds.circle_pressed -= self._on_circle_pressed
        try:
            self.ds.sendReport()
        finally:
            self.ds.circle_pressed += self._on_circle_pressed
        print(f"R2 trigger mode set to: {mode.name}")

    def set_l2_force(self, force: int) -> None:
        """Set the resistance of the L2 trigger.

        Args:
            force: Resistance value (0-255) applied to slot 6.
        """
        self.ds.triggerL.setMode(TriggerModes.Rigid)
        self.ds.triggerL.setForce(6, force)
        self.ds.sendReport()

    def cycle_l2_force(self) -> None:
        """Advance to the next L2 trigger force preset."""
        if self._handling_l2_force:
            return
        self._handling_l2_force = True
        try:
            self._l2_force_level = (self._l2_force_level + 1) % 7
            self.set_l2_force(self._l2_force_level)
            print(f"L2 force set to {self._l2_force_level}")
        finally:
            self._handling_l2_force = False

    def cycle_l2_mode(self) -> None:
        """Advance to the next L2 trigger mode."""
        self._l2_mode_index = (self._l2_mode_index + 1) % len(self._trigger_modes)
        mode = self._trigger_modes[self._l2_mode_index]
        self.ds.triggerL.setMode(mode)
        self.ds.square_pressed -= self._on_square_pressed
        try:
            self.ds.sendReport()
        finally:
            self.ds.square_pressed += self._on_square_pressed
        print(f"L2 trigger mode set to: {mode.name}")

    def _on_cross_pressed(self, val: bool) -> None:
        """Respond to cross button events.

        When pressed, the R2 trigger force is cycled.

        Args:
            val: ``True`` if the button is pressed.
        """
        if val:
            self.cycle_r2_force()

    def _on_circle_pressed(self, val: bool) -> None:
        """Respond to circle button events.

        When pressed, the R2 trigger mode is cycled.

        Args:
            val: ``True`` if the button is pressed.
        """
        if val:
            self.cycle_r2_mode()

    def _on_square_pressed(self, val: bool) -> None:
        """Respond to square button events.

        When pressed, the L2 trigger mode is cycled.

        Args:
            val: ``True`` if the button is pressed.
        """
        if val:
            self.cycle_l2_mode()

    def _on_triangle_pressed(self, val: bool) -> None:
        """Respond to triangle button events.

        When pressed, the L2 trigger force is cycled.

        Args:
            val: ``True`` if the button is pressed.
        """
        if val:
            self.cycle_l2_force()

    # ------------------------------------------------------------------
    # State query helpers
    def is_button_pressed(self, button: str) -> bool:
        """Check whether a button is currently pressed.

        Args:
            button: Name of the button attribute in ``pydualsense.state``.

        Returns:
            ``True`` if the button is pressed.
        """
        try:
            return bool(getattr(self.ds.state, button))
        except AttributeError:
            raise ValueError(f"Unknown button: {button}")

    def get_trigger_value(self, trigger: str) -> int:
        """Return the current value of a trigger.

        Args:
            trigger: Name of the trigger attribute (e.g., ``"l2"`` or ``"r2"``).

        Returns:
            Integer position of the trigger from 0 to 255.
        """
        try:
            return int(getattr(self.ds.state, trigger))
        except AttributeError:
            raise ValueError(f"Unknown trigger: {trigger}")

    def get_joystick_state(self, stick: str) -> tuple[int, int]:
        """Return the ``(x, y)`` position for a joystick.

        Args:
            stick: Which joystick to query: ``"left"`` or ``"right"``.

        Returns:
            Tuple ``(x, y)`` representing the joystick position.
        """
        stick = stick.lower()
        if stick not in {"left", "right"}:
            raise ValueError("stick must be 'left' or 'right'")
        prefix = "l" if stick == "left" else "r"
        x_attr = f"{prefix}x"
        y_attr = f"{prefix}y"
        try:
            x = getattr(self.ds.state, x_attr)
            y = getattr(self.ds.state, y_attr)
        except AttributeError as exc:
            raise ValueError("Joystick state attributes missing") from exc
        return int(x), int(y)

    def list_trigger_modes(self) -> None:
        """Print the available trigger modes to stdout."""
        print("Available trigger modes:")
        for mode in self._trigger_modes:
            print(f"- {mode.name}")

    def read_loop(self) -> None:
        """Listen for controller events and print them.

        This method blocks until interrupted by ``CTRL+C``.
        """

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

        self.ds.cross_pressed += self._on_cross_pressed
        self.ds.circle_pressed += self._on_circle_pressed
        self.ds.square_pressed += self._on_square_pressed
        self.ds.triangle_pressed += self._on_triangle_pressed


        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping controller listener...")
        finally:
            self.close()
