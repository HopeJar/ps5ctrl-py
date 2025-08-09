import os
import sys
from enum import Enum

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
    def setMode(self, mode):
        pass

    def setForce(self, slot, force):
        pass


class DummyDS:
    def __init__(self):
        self.triggerR = DummyTrigger()
        self.triggerL = DummyTrigger()
        self.circle_pressed = DummyEvent()
        self.square_pressed = DummyEvent()

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
