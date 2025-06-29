"""Script to print PS5 controller input for debugging."""

from ps5ctrl.controller import DualSenseController


def main() -> None:
    controller = DualSenseController()
    controller.open()
    controller.read_loop()


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
