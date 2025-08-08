# PS5 Controller Utilities

This project provides simple utilities for interacting with a PS5 DualSense controller using Python.

## Features

- Connect to a controller over USB using the [`pydualsense`](https://pypi.org/project/pydualsense/) library.
- Print live controller input to the terminal for debugging purposes.
- Cycle trigger modes/forces using controller buttons and query current button
  or joystick state through simple helper methods.

## Getting Started

1. Install the project requirements:

```
pip install -r requirements.txt

2. Run the debug script to see controller input in the terminal:

```
python scripts/debug_inputs.py
```

Press `CTRL+C` to stop listening for input.


## Documentation

Documentation is generated using [pdoc](https://pdoc.dev). After installing the
dependencies from `requirements.txt`, run:

```
tox
```

This will build HTML documentation under `reports/doc/`.
=======

