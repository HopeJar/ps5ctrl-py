# ps5ctrl

`ps5ctrl` is a small Python wrapper for using a PS5 DualSense controller in your own projects. It keeps the public API readable while relying on [`pydualsense`](https://pypi.org/project/pydualsense/) for the low-level HID connection.

## Features

- Connect to a DualSense controller over USB.
- Register callbacks for buttons, triggers, and joysticks.
- Query current button, trigger, and joystick state.
- Adjust adaptive trigger force and trigger modes.
- Run a debug script that prints live controller input to the terminal.

## Requirements

- Python 3.10 or newer.
- A PS5 DualSense controller connected over USB.
- `pydualsense` and its HID dependencies.

Linux systems may also need HIDAPI development/runtime packages before `pydualsense` can access the controller. On Debian or Ubuntu, install them with:

```bash
sudo apt install libhidapi-hidraw0 libhidapi-dev
```

On Windows, install the Python dependencies first. If the controller is detected by Windows but unavailable to Python, check the `pydualsense` setup guidance for driver/HID access requirements.

## Installation

From the project root:

```bash
pip install -e .
```

For local development and documentation tools:

```bash
pip install -r requirements.txt
```

## Quick Start

Use callbacks to connect controller input to your own application behavior:

```python
from ps5ctrl import DualSenseController


def jump(pressed: bool) -> None:
    if pressed:
        print("jump")


def throttle(value: int) -> None:
    print(f"r2 throttle: {value}")


with DualSenseController() as controller:
    controller.on_button("cross", jump)
    controller.on_trigger("r2", throttle)
    controller.on_stick("left", lambda x, y: print(f"move: {x}, {y}"))
    controller.listen()
```

Press `CTRL+C` to stop the process while using the simple listener loop.

## API Overview

### Connection

```python
controller = DualSenseController()
controller.open()
controller.close()
```

You can also use the controller as a context manager:

```python
with DualSenseController() as controller:
    controller.listen()
```

### Event Callbacks

```python
controller.on_button("cross", callback)
controller.on_trigger("r2", callback)
controller.on_stick("left", callback)
```

Button callbacks receive `bool`, trigger callbacks receive `int`, and stick callbacks receive `x, y` integer values.

Supported button names:

```text
cross, circle, square, triangle, l1, r1, l3, r3,
dpad_up, dpad_down, dpad_left, dpad_right
```

Supported trigger names:

```text
l2, r2
```

Supported stick names:

```text
left, right
```

### State Queries

```python
controller.is_button_pressed("cross")
controller.get_trigger_value("r2")
controller.get_joystick_state("left")
```

### Adaptive Triggers

```python
controller.set_r2_force(5)
controller.set_l2_force(5)

new_level = controller.cycle_r2_force()
new_mode = controller.cycle_l2_mode()
```

`list_trigger_modes()` returns the available trigger mode names.

## Debugging Controller Input

To print live controller input in the terminal, run:

```bash
python scripts/debug_inputs.py
```

This script is intentionally where terminal printing lives. The library itself exposes callbacks and state helpers so your project can decide how to handle input.

## Troubleshooting

### The controller is not found

- Confirm the controller is connected over USB.
- Try a different USB cable; some cables only provide power.
- Confirm the controller appears in your operating system's device list.
- Close other programs that may be exclusively using the controller.

### Permission or HID access errors on Linux

- Install HIDAPI packages:

```bash
sudo apt install libhidapi-hidraw0 libhidapi-dev
```

- You may need udev rules or elevated permissions depending on your distribution.
- Reconnect the controller after changing HID permissions.

### Import errors

Install the package and dependencies from the project root:

```bash
pip install -e .
pip install -r requirements.txt
```

If `pydualsense` still fails to import, reinstall it directly:

```bash
pip install pydualsense
```

## Documentation

Documentation is generated using [pdoc](https://pdoc.dev). After installing the development dependencies, run:

```bash
tox
```

Generated HTML documentation is written to `reports/doc/`.
