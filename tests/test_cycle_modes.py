import os
import sys
from enum import Enum
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import ps5ctrl.controller as controller


class DummyEvent:
    def __init__(self):
        self._callbacks = []

    def __iadd__(self, cb):
        self._callbacks.append(cb)
        return self

    def __isub__(self, cb):
        self._callbacks.remove(cb)
        return self

    def __call__(self, *args, **kwargs):
        for cb in list(self._callbacks):
            cb(*args, **kwargs)


class DummyTrigger:
    def __init__(self):
        self.forces = [0] * 7
        self.mode = None
        self.force_calls = []

    def setMode(self, mode):
        self.mode = mode

    def setForce(self, slot, force):
        self.force_calls.append((slot, force))


class DummyDS:
    def __init__(self):
        self.triggerR = DummyTrigger()
        self.triggerL = DummyTrigger()
        self.circle_pressed = DummyEvent()
        self.square_pressed = DummyEvent()
        self.cross_pressed = DummyEvent()
        self.r2_value_changed = DummyEvent()
        self.left_joystick_changed = DummyEvent()
        self.state = SimpleNamespace(
            cross=True,
            circle=False,
            square=True,
            triangle=False,
            l1=True,
            r1=False,
            l3=True,
            r3=False,
            dpad_up=True,
            dpad_down=False,
            dpad_left=True,
            dpad_right=False,
            l2=12,
            r2=34,
            lx=1,
            ly=2,
            rx=3,
            ry=4,
        )

    def sendReport(self):
        # Simulate hardware re-emitting pressed events on report
        self.circle_pressed(True)
        self.square_pressed(True)


class DummyPyDualSense:
    def __call__(self):
        return DummyDS()


class DummyTriggerModes(Enum):
    Off = 0
    Rigid = 1
    Mode2 = 2


def create_controller():
    controller.pydualsense = DummyPyDualSense()
    controller.TriggerModes = DummyTriggerModes
    return controller.DualSenseController()


def test_cycle_modes_no_recursion():
    ctrl = create_controller()
    ctrl.ds.circle_pressed += ctrl._on_circle_pressed
    ctrl.ds.square_pressed += ctrl._on_square_pressed

    for _ in range(10):
        ctrl._on_circle_pressed(True)
        ctrl._on_square_pressed(True)


def test_explicit_state_helpers():
    ctrl = create_controller()

    assert ctrl.cross_pressed() is True
    assert ctrl.circle_pressed() is False
    assert ctrl.square_pressed() is True
    assert ctrl.triangle_pressed() is False
    assert ctrl.l1_pressed() is True
    assert ctrl.r1_pressed() is False
    assert ctrl.dpad_up_pressed() is True
    assert ctrl.dpad_down_pressed() is False
    assert ctrl.l2_value() == 12
    assert ctrl.r2_value() == 34
    assert ctrl.left_stick() == (1, 2)
    assert ctrl.right_stick() == (3, 4)


def test_generic_helpers_accept_enums_and_normalized_strings():
    ctrl = create_controller()

    assert ctrl.is_button_pressed(controller.Button.CROSS) is True
    assert ctrl.get_trigger_value(controller.Trigger.R2) == 34
    assert ctrl.get_joystick_state(controller.Stick.LEFT) == (1, 2)
    assert ctrl.is_button_pressed("dpad-up") is True


def test_force_validation():
    ctrl = create_controller()

    ctrl.set_r2_force(6)
    assert ctrl.ds.triggerR.force_calls[-1] == (6, 6)

    try:
        ctrl.set_r2_force(7)
    except ValueError as exc:
        assert "0 through 6" in str(exc)
    else:
        raise AssertionError("set_r2_force should reject force above 6")

    try:
        ctrl.set_l2_force("3")
    except TypeError as exc:
        assert "integer" in str(exc)
    else:
        raise AssertionError("set_l2_force should reject non-integer force")


def test_event_helpers_accept_enums():
    ctrl = create_controller()
    calls = []

    ctrl.on_button(controller.Button.CROSS, calls.append)
    ctrl.on_trigger(controller.Trigger.R2, calls.append)
    ctrl.on_stick(controller.Stick.LEFT, lambda x, y: calls.append((x, y)))

    ctrl.ds.cross_pressed(True)
    ctrl.ds.r2_value_changed(99)
    ctrl.ds.left_joystick_changed(5, 6)

    assert calls == [True, 99, (5, 6)]
