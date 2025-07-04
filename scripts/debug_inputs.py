"""Utility script for printing PS5 controller input."""

from ps5ctrl.controller import DualSenseController


def main() -> None:
    """Run the debug listener until the user stops the process."""
    controller = DualSenseController()
    controller.open()
    controller.read_loop()


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
