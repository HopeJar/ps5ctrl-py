# PS5 Controller Utilities

This project provides simple utilities for interacting with a PS5 DualSense controller using Python.

## Features

- Connect to a controller over USB using the [`pydualsense`](https://pypi.org/project/pydualsense/) library.
- Print live controller input to the terminal for debugging purposes.

## Getting Started

1. Install the required dependency:

```bash
pip install pydualsense
```

2. Run the debug script to see controller input in the terminal:

```bash
python scripts/debug_inputs.py
```

Press `CTRL+C` to stop listening for input.
