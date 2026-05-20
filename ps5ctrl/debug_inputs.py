"""Console helpers for inspecting live DualSense controller input."""

from __future__ import annotations

from ps5ctrl.controller import DualSenseController


def print_button(name: str):
    """Return a button callback that prints its current state."""
    return lambda pressed: print(f"{name}: {pressed}")


def print_trigger(name: str):
    """Return a trigger callback that prints its current value."""
    return lambda value: print(f"{name} value: {value}")


def print_stick(name: str):
    """Return a joystick callback that prints its current position."""
    return lambda x, y: print(f"{name}: x={x}, y={y}")


def register_debug_callbacks(controller: DualSenseController) -> None:
    """Register terminal-print callbacks for every supported input."""
    for button in (
        "l1",
        "r1",
        "l3",
        "r3",
        "dpad_up",
        "dpad_down",
        "dpad_left",
        "dpad_right",
        "cross",
        "circle",
        "square",
        "triangle",
    ):
        controller.on_button(button, print_button(button))

    controller.on_trigger("l2", print_trigger("L2"))
    controller.on_trigger("r2", print_trigger("R2"))
    controller.on_stick("left", print_stick("Left Stick"))
    controller.on_stick("right", print_stick("Right Stick"))


def main() -> None:
    """Run the debug listener until the user stops the process."""
    controller = DualSenseController()
    controller.open()
    register_debug_callbacks(controller)

    print("Listening for controller input. Press CTRL+C to stop.")
    try:
        controller.listen()
    except KeyboardInterrupt:
        print("Stopping controller listener...")
    finally:
        controller.close()