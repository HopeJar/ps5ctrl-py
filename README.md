# PS5 Controller Utilities

This project provides simple utilities for interacting with a PS5 DualSense controller using Python.

## Features

- Connect to a controller over USB using the [`pydualsense`](https://pypi.org/project/pydualsense/) library.
- Print live controller input to the terminal for debugging purposes.

## Getting Started

1. Install the project requirements:

```bash
pip install -r requirements.txt
```

2. Run the debug script to see controller input in the terminal:

```bash
python scripts/debug_inputs.py
```

Press `CTRL+C` to stop listening for input.

## Documentation

Documentation is generated using [pdoc](https://pdoc.dev). After installing the
dependencies from `requirements.txt`, run:

```bash
tox -e py312
```

This will build HTML documentation under `reports/doc/`.
