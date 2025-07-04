"""Utilities to connect to a PS5 DualSense controller via USB."""


from __future__ import annotations

try:
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

    def open(self) -> None:
        """Open the connection to the controller over USB."""
        self.ds.init()

    def close(self) -> None:

        """Close the connection to the controller."""

        self.ds.close()

    def read_loop(self) -> None:
        """Print controller events until interrupted."""
        print("Listening for controller input. Press CTRL+C to stop.")
        try:
            while True:
                self.ds.update()
                print(
                    f"LX: {self.ds.LX} LY: {self.ds.LY} "
                    f"RX: {self.ds.RX} RY: {self.ds.RY} "
                    f"Buttons: {self.ds.buttons}"
                )
        except KeyboardInterrupt:
            print("Stopping controller listener...")
        finally:
            self.close()
