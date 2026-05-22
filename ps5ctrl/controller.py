"""Utilities to connect to a PS5 DualSense controller via USB."""

from __future__ import annotations

import time
from collections.abc import Callable
from enum import Enum
from typing import Any

try:
    from pydualsense.enums import TriggerModes
    from pydualsense import pydualsense
except ImportError:  # pragma: no cover - optional dependency
    pydualsense = None
    TriggerModes = None


ButtonCallback = Callable[[bool], None]
TriggerCallback = Callable[[int], None]
StickCallback = Callable[[int, int], None]
UnsubscribeCallback = Callable[[], None]
ControlName = str | Enum


class Button(str, Enum):
    """Supported button names."""

    CROSS = "cross"
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"
    L1 = "l1"
    R1 = "r1"
    L3 = "l3"
    R3 = "r3"
    DPAD_UP = "dpad_up"
    DPAD_DOWN = "dpad_down"
    DPAD_LEFT = "dpad_left"
    DPAD_RIGHT = "dpad_right"


class Trigger(str, Enum):
    """Supported analog trigger names."""

    L2 = "l2"
    R2 = "r2"


class Stick(str, Enum):
    """Supported joystick names."""

    LEFT = "left"
    RIGHT = "right"


class DualSenseController:
    """Simple wrapper around :class:`pydualsense.pydualsense`.

    This class exposes a small event-registration API plus explicit state
    helpers so projects can build controller behavior without depending
    directly on pydualsense event or state names.
    """

    _BUTTON_EVENTS = {
        Button.CROSS.value: "cross_pressed",
        Button.CIRCLE.value: "circle_pressed",
        Button.SQUARE.value: "square_pressed",
        Button.TRIANGLE.value: "triangle_pressed",
        Button.L1.value: "l1_changed",
        Button.R1.value: "r1_changed",
        Button.L3.value: "l3_changed",
        Button.R3.value: "r3_changed",
        Button.DPAD_UP.value: "dpad_up",
        Button.DPAD_DOWN.value: "dpad_down",
        Button.DPAD_LEFT.value: "dpad_left",
        Button.DPAD_RIGHT.value: "dpad_right",
    }
    _BUTTON_STATES = {
        Button.CROSS.value: "cross",
        Button.CIRCLE.value: "circle",
        Button.SQUARE.value: "square",
        Button.TRIANGLE.value: "triangle",
        Button.L1.value: "l1",
        Button.R1.value: "r1",
        Button.L3.value: "l3",
        Button.R3.value: "r3",
        Button.DPAD_UP.value: "dpad_up",
        Button.DPAD_DOWN.value: "dpad_down",
        Button.DPAD_LEFT.value: "dpad_left",
        Button.DPAD_RIGHT.value: "dpad_right",
    }
    _TRIGGER_EVENTS = {
        Trigger.L2.value: "l2_value_changed",
        Trigger.R2.value: "r2_value_changed",
    }
    _TRIGGER_STATES = {
        Trigger.L2.value: "l2",
        Trigger.R2.value: "r2",
    }
    _STICK_EVENTS = {
        Stick.LEFT.value: "left_joystick_changed",
        Stick.RIGHT.value: "right_joystick_changed",
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
        self._listening = False

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
        self.stop()
        self.ds.setRightMotor(0)
        self.ds.setLeftMotor(0)

        self.ds.triggerR.setMode(TriggerModes.Off)
        self.ds.triggerR.forces = [0] * 7

        self.ds.triggerL.setMode(TriggerModes.Off)
        self.ds.triggerL.forces = [0] * 7

        self.ds.sendReport()
        self.ds.close()

    def on_button(
        self, button: ControlName, callback: ButtonCallback
    ) -> UnsubscribeCallback:
        """Register a callback for a button event.

        ``button`` may be a :class:`Button` value or a supported button name.
        The callback receives a single boolean indicating whether the button is
        currently pressed. The returned function unregisters the callback.
        """
        event = self._get_event(self._BUTTON_EVENTS, button, "button")
        event += callback
        return self._make_unsubscribe(event, callback)

    def on_trigger(
        self, trigger: ControlName, callback: TriggerCallback
    ) -> UnsubscribeCallback:
        """Register a callback for a trigger value event.

        ``trigger`` may be a :class:`Trigger` value or ``"l2"``/``"r2"``.
        The callback receives the trigger value reported by pydualsense. The
        returned function unregisters the callback.
        """
        event = self._get_event(self._TRIGGER_EVENTS, trigger, "trigger")
        event += callback
        return self._make_unsubscribe(event, callback)

    def on_stick(
        self, stick: ControlName, callback: StickCallback
    ) -> UnsubscribeCallback:
        """Register a callback for a joystick movement event.

        ``stick`` may be a :class:`Stick` value or ``"left"``/``"right"``.
        The callback receives the ``x`` and ``y`` axis values. The returned
        function unregisters the callback.
        """
        event = self._get_event(self._STICK_EVENTS, stick, "stick")
        event += callback
        return self._make_unsubscribe(event, callback)

    def _make_unsubscribe(
        self, event: Any, callback: ButtonCallback | TriggerCallback | StickCallback
    ) -> UnsubscribeCallback:
        unsubscribed = False

        def unsubscribe() -> None:
            nonlocal event, unsubscribed
            if unsubscribed:
                return
            try:
                event -= callback
            except ValueError:
                pass
            unsubscribed = True

        return unsubscribe

    def _get_event(self, mapping: dict[str, str], name: ControlName, kind: str) -> Any:
        normalized = self._normalize_name(name)
        try:
            event_name = mapping[normalized]
        except KeyError as exc:
            valid = ", ".join(sorted(mapping))
            raise ValueError(f"Unknown {kind}: {name}. Valid values: {valid}") from exc
        return getattr(self.ds, event_name)
    def set_r2_force(self, force: int) -> None:
        """Set R2 resistance using slot 6 and send report."""
        self._validate_force(force)
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
        self._validate_force(force)
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

    def _validate_force(self, force: int) -> None:
        if not isinstance(force, int):
            raise TypeError("force must be an integer from 0 through 6")
        if not 0 <= force <= 6:
            raise ValueError("force must be from 0 through 6")

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

    def is_button_pressed(self, button: ControlName) -> bool:
        """Return ``True`` if the given button is pressed.

        ``button`` may be a :class:`Button` value or a supported button name.
        """
        normalized = self._normalize_name(button)
        try:
            attr = self._BUTTON_STATES[normalized]
        except KeyError as exc:
            valid = ", ".join(sorted(self._BUTTON_STATES))
            raise ValueError(f"Unknown button: {button}. Valid values: {valid}") from exc
        try:
            return bool(getattr(self.ds.state, attr))
        except AttributeError as exc:
            raise ValueError(f"Button state attribute missing: {attr}") from exc

    def get_trigger_value(self, trigger: ControlName) -> int:
        """Return the value of a trigger.

        ``trigger`` may be a :class:`Trigger` value or ``"l2"``/``"r2"``.
        """
        normalized = self._normalize_name(trigger)
        try:
            attr = self._TRIGGER_STATES[normalized]
        except KeyError as exc:
            valid = ", ".join(sorted(self._TRIGGER_STATES))
            raise ValueError(f"Unknown trigger: {trigger}. Valid values: {valid}") from exc
        try:
            return int(getattr(self.ds.state, attr))
        except AttributeError as exc:
            raise ValueError(f"Trigger state attribute missing: {attr}") from exc

    def get_joystick_state(self, stick: ControlName) -> tuple[int, int]:
        """Return the ``(x, y)`` position for the given joystick."""
        normalized = self._normalize_name(stick)
        if normalized not in {Stick.LEFT.value, Stick.RIGHT.value}:
            raise ValueError("stick must be 'left' or 'right'")
        prefix = "l" if normalized == Stick.LEFT.value else "r"
        x_attr = f"{prefix}x"
        y_attr = f"{prefix}y"
        try:
            x = getattr(self.ds.state, x_attr)
            y = getattr(self.ds.state, y_attr)
        except AttributeError as exc:
            raise ValueError("Joystick state attributes missing") from exc
        return int(x), int(y)

    def cross_pressed(self) -> bool:
        """Return whether the cross button is pressed."""
        return self.is_button_pressed(Button.CROSS)

    def circle_pressed(self) -> bool:
        """Return whether the circle button is pressed."""
        return self.is_button_pressed(Button.CIRCLE)

    def square_pressed(self) -> bool:
        """Return whether the square button is pressed."""
        return self.is_button_pressed(Button.SQUARE)

    def triangle_pressed(self) -> bool:
        """Return whether the triangle button is pressed."""
        return self.is_button_pressed(Button.TRIANGLE)

    def l1_pressed(self) -> bool:
        """Return whether L1 is pressed."""
        return self.is_button_pressed(Button.L1)

    def r1_pressed(self) -> bool:
        """Return whether R1 is pressed."""
        return self.is_button_pressed(Button.R1)

    def l3_pressed(self) -> bool:
        """Return whether L3 is pressed."""
        return self.is_button_pressed(Button.L3)

    def r3_pressed(self) -> bool:
        """Return whether R3 is pressed."""
        return self.is_button_pressed(Button.R3)

    def dpad_up_pressed(self) -> bool:
        """Return whether D-pad up is pressed."""
        return self.is_button_pressed(Button.DPAD_UP)

    def dpad_down_pressed(self) -> bool:
        """Return whether D-pad down is pressed."""
        return self.is_button_pressed(Button.DPAD_DOWN)

    def dpad_left_pressed(self) -> bool:
        """Return whether D-pad left is pressed."""
        return self.is_button_pressed(Button.DPAD_LEFT)

    def dpad_right_pressed(self) -> bool:
        """Return whether D-pad right is pressed."""
        return self.is_button_pressed(Button.DPAD_RIGHT)

    def l2_value(self) -> int:
        """Return the current L2 trigger value."""
        return self.get_trigger_value(Trigger.L2)

    def r2_value(self) -> int:
        """Return the current R2 trigger value."""
        return self.get_trigger_value(Trigger.R2)

    def left_stick(self) -> tuple[int, int]:
        """Return the current left stick ``(x, y)`` position."""
        return self.get_joystick_state(Stick.LEFT)

    def right_stick(self) -> tuple[int, int]:
        """Return the current right stick ``(x, y)`` position."""
        return self.get_joystick_state(Stick.RIGHT)

    def _normalize_name(self, name: ControlName) -> str:
        if isinstance(name, Enum):
            name = name.value
        return str(name).lower().replace("-", "_")

    def list_trigger_modes(self) -> list[str]:
        """Return the available trigger mode names."""
        return [mode.name for mode in self._trigger_modes]

    def listen(self, poll_interval: float = 0.1) -> None:
        """Keep the process alive while pydualsense dispatches registered events."""
        self._listening = True
        try:
            while self._listening:
                time.sleep(poll_interval)
        finally:
            self._listening = False

    def stop(self) -> None:
        """Request that the active listener loop stop."""
        self._listening = False

    def read_loop(self, poll_interval: float = 0.1) -> None:
        """Backward-compatible alias for :meth:`listen`."""
        self.listen(poll_interval=poll_interval)
