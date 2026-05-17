"""Utilities to connect to a PS5 DualSense controller via USB."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

try:
    from pydualsense.enums import TriggerModes
    from pydualsense import pydualsense
except ImportError:  # pragma: no cover - optional dependency
    pydualsense = None


ButtonCallback = Callable[[bool], None]
TriggerCallback = Callable[[int], None]
StickCallback = Callable[[int, int], None]


class DualSenseController:
    """Simple wrapper around :class:`pydualsense.pydualsense`.

    This class exposes a small event-registration API plus basic state helpers
    so projects can build controller behavior without depending directly on
    pydualsense event names.
    """

    _BUTTON_EVENTS = {
        "cross": "cross_pressed",
        "circle": "circle_pressed",
        "square": "square_pressed",
        "triangle": "triangle_pressed",
        "l1": "l1_changed",
        "r1": "r1_changed",
        "l3": "l3_changed",
        "r3": "r3_changed",
        "dpad_up": "dpad_up",
        "dpad_down": "dpad_down",
        "dpad_left": "dpad_left",
        "dpad_right": "dpad_right",
    }
    _TRIGGER_EVENTS = {
        "l2": "l2_value_changed",
        "r2": "r2_value_changed",
    }
    _STICK_EVENTS = {
        "left": "left_joystick_changed",
        "right": "right_joystick_changed",
    }

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
        self._handling_r2_force = False
        self._handling_l2_force = False
        self._last_left_stick = (None, None)
        self._last_right_stick = (None, None)

    def __enter__(self) -> "DualSenseController":
        """Open the controller connection when used as a context manager."""
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Close the controller connection when leaving a context manager."""
        self.close()

    def open(self) -> None:
        """Open the connection to the controller over USB."""
        self.ds.init()

    def close(self) -> None:
        """Close the connection to the controller."""
        self.ds.setRightMotor(0)
        self.ds.setLeftMotor(0)

        self.ds.triggerR.setMode(TriggerModes.Off)
        self.ds.triggerR.forces = [0] * 7

        self.ds.triggerL.setMode(TriggerModes.Off)
        self.ds.triggerL.forces = [0] * 7

        self.ds.sendReport()
        self.ds.close()

    def on_button(self, button: str, callback: ButtonCallback) -> None:
        """Register a callback for a button event.

        The callback receives a single boolean indicating whether the button is
        currently pressed.
        """
        event = self._get_event(self._BUTTON_EVENTS, button, "button")
        event += callback

    def on_trigger(self, trigger: str, callback: TriggerCallback) -> None:
        """Register a callback for a trigger value event.

        The callback receives the trigger value reported by pydualsense.
        """
        event = self._get_event(self._TRIGGER_EVENTS, trigger, "trigger")
        event += callback

    def on_stick(self, stick: str, callback: StickCallback) -> None:
        """Register a callback for a joystick movement event.

        The callback receives the ``x`` and ``y`` axis values.
        """
        event = self._get_event(self._STICK_EVENTS, stick, "stick")
        event += callback

    def _get_event(self, mapping: dict[str, str], name: str, kind: str) -> Any:
        normalized = name.lower().replace("-", "_")
        try:
            event_name = mapping[normalized]
        except KeyError as exc:
            valid = ", ".join(sorted(mapping))
            raise ValueError(f"Unknown {kind}: {name}. Valid values: {valid}") from exc
        return getattr(self.ds, event_name)

    def set_r2_force(self, force: int) -> None:
        """Set R2 resistance using slot 6 and send report."""
        self.ds.triggerR.setMode(TriggerModes.Rigid)
        self.ds.triggerR.setForce(6, force)
        self.ds.sendReport()

    def cycle_r2_force(self) -> int | None:
        """Cycle through R2 trigger force levels 0-6 and return the new level."""
        if self._handling_r2_force:
            return None
        self._handling_r2_force = True
        try:
            self._r2_force_level = (self._r2_force_level + 1) % 7
            self.set_r2_force(self._r2_force_level)
            return self._r2_force_level
        finally:
            self._handling_r2_force = False

    def cycle_r2_mode(self) -> TriggerModes:
        """Cycle through R2 trigger modes and return the new mode."""
        self._r2_mode_index = (self._r2_mode_index + 1) % len(self._trigger_modes)
        mode = self._trigger_modes[self._r2_mode_index]
        self.ds.triggerR.setMode(mode)
        self.ds.circle_pressed -= self._on_circle_pressed
        try:
            self.ds.sendReport()
        finally:
            self.ds.circle_pressed += self._on_circle_pressed
        return mode

    def set_l2_force(self, force: int) -> None:
        """Set L2 resistance using slot 6 and send report."""
        self.ds.triggerL.setMode(TriggerModes.Rigid)
        self.ds.triggerL.setForce(6, force)
        self.ds.sendReport()

    def cycle_l2_force(self) -> int | None:
        """Cycle through L2 trigger force levels 0-6 and return the new level."""
        if self._handling_l2_force:
            return None
        self._handling_l2_force = True
        try:
            self._l2_force_level = (self._l2_force_level + 1) % 7
            self.set_l2_force(self._l2_force_level)
            return self._l2_force_level
        finally:
            self._handling_l2_force = False

    def cycle_l2_mode(self) -> TriggerModes:
        """Cycle through L2 trigger modes and return the new mode."""
        self._l2_mode_index = (self._l2_mode_index + 1) % len(self._trigger_modes)
        mode = self._trigger_modes[self._l2_mode_index]
        self.ds.triggerL.setMode(mode)
        self.ds.square_pressed -= self._on_square_pressed
        try:
            self.ds.sendReport()
        finally:
            self.ds.square_pressed += self._on_square_pressed
        return mode

    def _on_cross_pressed(self, val: bool) -> None:
        """Handle cross button presses to cycle R2 force."""
        if val:
            self.cycle_r2_force()

    def _on_circle_pressed(self, val: bool) -> None:
        """Handle circle button presses to cycle R2 mode."""
        if val:
            self.cycle_r2_mode()

    def _on_square_pressed(self, val: bool) -> None:
        """Handle square button presses to cycle L2 mode."""
        if val:
            self.cycle_l2_mode()

    def _on_triangle_pressed(self, val: bool) -> None:
        """Handle triangle button presses to cycle L2 force."""
        if val:
            self.cycle_l2_force()

    def is_button_pressed(self, button: str) -> bool:
        """Return ``True`` if the given button is pressed."""
        try:
            return bool(getattr(self.ds.state, button))
        except AttributeError:
            raise ValueError(f"Unknown button: {button}")

    def get_trigger_value(self, trigger: str) -> int:
        """Return the value of a trigger, such as ``'l2'`` or ``'r2'``."""
        try:
            return int(getattr(self.ds.state, trigger))
        except AttributeError:
            raise ValueError(f"Unknown trigger: {trigger}")

    def get_joystick_state(self, stick: str) -> tuple[int, int]:
        """Return the ``(x, y)`` position for the given joystick."""
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

    def list_trigger_modes(self) -> list[str]:
        """Return the available trigger mode names."""
        return [mode.name for mode in self._trigger_modes]

    def listen(self, poll_interval: float = 0.1) -> None:
        """Keep the process alive while pydualsense dispatches registered events."""
        while True:
            time.sleep(poll_interval)

    def read_loop(self, poll_interval: float = 0.1) -> None:
        """Backward-compatible alias for :meth:`listen`."""
        self.listen(poll_interval=poll_interval)
