import os
import sys
import unittest
from enum import Enum
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import ps5ctrl.controller as controller
from ps5ctrl import Button, DualSenseController, Stick, Trigger
from ps5ctrl import debug_inputs


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
        self.cross_pressed = DummyEvent()
        self.circle_pressed = DummyEvent()
        self.square_pressed = DummyEvent()
        self.triangle_pressed = DummyEvent()
        self.l1_changed = DummyEvent()
        self.r1_changed = DummyEvent()
        self.l3_changed = DummyEvent()
        self.r3_changed = DummyEvent()
        self.dpad_up = DummyEvent()
        self.dpad_down = DummyEvent()
        self.dpad_left = DummyEvent()
        self.dpad_right = DummyEvent()
        self.l2_value_changed = DummyEvent()
        self.r2_value_changed = DummyEvent()
        self.left_joystick_changed = DummyEvent()
        self.right_joystick_changed = DummyEvent()
        self.init_called = False
        self.close_called = False
        self.left_motor = None
        self.right_motor = None
        self.report_count = 0
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

    def init(self):
        self.init_called = True

    def close(self):
        self.close_called = True

    def setRightMotor(self, value):
        self.right_motor = value

    def setLeftMotor(self, value):
        self.left_motor = value

    def sendReport(self):
        self.report_count += 1
        # Simulate hardware re-emitting pressed events on report.
        self.circle_pressed(True)
        self.square_pressed(True)


class DummyPyDualSense:
    def __call__(self):
        return DummyDS()


class DummyTriggerModes(Enum):
    Off = 0
    Rigid = 1
    Mode2 = 2


class ControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.original_pydualsense = controller.pydualsense
        self.original_trigger_modes = getattr(controller, "TriggerModes", None)
        controller.pydualsense = DummyPyDualSense()
        controller.TriggerModes = DummyTriggerModes

    def tearDown(self):
        controller.pydualsense = self.original_pydualsense
        controller.TriggerModes = self.original_trigger_modes
        controller.time.sleep = self.original_sleep

    @property
    def original_sleep(self):
        return getattr(self, "_original_sleep", controller.time.sleep)

    def create_controller(self):
        return controller.DualSenseController()

    def test_top_level_exports(self):
        self.assertIs(DualSenseController, controller.DualSenseController)
        self.assertEqual(Button.CROSS.value, "cross")
        self.assertEqual(Trigger.R2.value, "r2")
        self.assertEqual(Stick.LEFT.value, "left")

    def test_missing_dependency_raises_import_error(self):
        controller.pydualsense = None
        with self.assertRaisesRegex(ImportError, "pydualsense is required"):
            controller.DualSenseController()

    def test_open_close_and_context_manager(self):
        ctrl = self.create_controller()
        ctrl.open()
        self.assertTrue(ctrl.ds.init_called)

        ctrl._listening = True
        ctrl.close()
        self.assertFalse(ctrl._listening)
        self.assertEqual(ctrl.ds.right_motor, 0)
        self.assertEqual(ctrl.ds.left_motor, 0)
        self.assertEqual(ctrl.ds.triggerR.mode, DummyTriggerModes.Off)
        self.assertEqual(ctrl.ds.triggerL.mode, DummyTriggerModes.Off)
        self.assertEqual(ctrl.ds.triggerR.forces, [0] * 7)
        self.assertEqual(ctrl.ds.triggerL.forces, [0] * 7)
        self.assertTrue(ctrl.ds.close_called)

        with self.create_controller() as managed:
            self.assertTrue(managed.ds.init_called)
        self.assertTrue(managed.ds.close_called)

    def test_explicit_state_helpers(self):
        ctrl = self.create_controller()

        self.assertTrue(ctrl.cross_pressed())
        self.assertFalse(ctrl.circle_pressed())
        self.assertTrue(ctrl.square_pressed())
        self.assertFalse(ctrl.triangle_pressed())
        self.assertTrue(ctrl.l1_pressed())
        self.assertFalse(ctrl.r1_pressed())
        self.assertTrue(ctrl.l3_pressed())
        self.assertFalse(ctrl.r3_pressed())
        self.assertTrue(ctrl.dpad_up_pressed())
        self.assertFalse(ctrl.dpad_down_pressed())
        self.assertTrue(ctrl.dpad_left_pressed())
        self.assertFalse(ctrl.dpad_right_pressed())
        self.assertEqual(ctrl.l2_value(), 12)
        self.assertEqual(ctrl.r2_value(), 34)
        self.assertEqual(ctrl.left_stick(), (1, 2))
        self.assertEqual(ctrl.right_stick(), (3, 4))

    def test_generic_helpers_accept_enums_and_normalized_strings(self):
        ctrl = self.create_controller()

        self.assertTrue(ctrl.is_button_pressed(Button.CROSS))
        self.assertEqual(ctrl.get_trigger_value(Trigger.R2), 34)
        self.assertEqual(ctrl.get_joystick_state(Stick.LEFT), (1, 2))
        self.assertTrue(ctrl.is_button_pressed("dpad-up"))
        self.assertEqual(ctrl.get_joystick_state("right"), (3, 4))

    def test_invalid_state_helper_names_raise_value_error(self):
        ctrl = self.create_controller()

        with self.assertRaisesRegex(ValueError, "Unknown button"):
            ctrl.is_button_pressed("share")
        with self.assertRaisesRegex(ValueError, "Unknown trigger"):
            ctrl.get_trigger_value("r4")
        with self.assertRaisesRegex(ValueError, "stick must be"):
            ctrl.get_joystick_state("middle")

    def test_missing_state_attributes_raise_value_error(self):
        ctrl = self.create_controller()
        delattr(ctrl.ds.state, "cross")
        with self.assertRaisesRegex(ValueError, "Button state attribute missing"):
            ctrl.cross_pressed()

        ctrl = self.create_controller()
        delattr(ctrl.ds.state, "r2")
        with self.assertRaisesRegex(ValueError, "Trigger state attribute missing"):
            ctrl.r2_value()

        ctrl = self.create_controller()
        delattr(ctrl.ds.state, "lx")
        with self.assertRaisesRegex(ValueError, "Joystick state attributes missing"):
            ctrl.left_stick()

    def test_callback_registration_and_unsubscribe(self):
        ctrl = self.create_controller()
        calls = []

        unsubscribe_button = ctrl.on_button(Button.CROSS, calls.append)
        unsubscribe_trigger = ctrl.on_trigger(Trigger.R2, calls.append)
        unsubscribe_stick = ctrl.on_stick(Stick.LEFT, lambda x, y: calls.append((x, y)))

        ctrl.ds.cross_pressed(True)
        ctrl.ds.r2_value_changed(99)
        ctrl.ds.left_joystick_changed(5, 6)
        self.assertEqual(calls, [True, 99, (5, 6)])

        unsubscribe_button()
        unsubscribe_trigger()
        unsubscribe_stick()
        unsubscribe_button()
        ctrl.ds.cross_pressed(False)
        ctrl.ds.r2_value_changed(0)
        ctrl.ds.left_joystick_changed(0, 0)
        self.assertEqual(calls, [True, 99, (5, 6)])

    def test_invalid_callback_names_raise_value_error(self):
        ctrl = self.create_controller()

        with self.assertRaisesRegex(ValueError, "Unknown button"):
            ctrl.on_button("bad", lambda value: None)
        with self.assertRaisesRegex(ValueError, "Unknown trigger"):
            ctrl.on_trigger("bad", lambda value: None)
        with self.assertRaisesRegex(ValueError, "Unknown stick"):
            ctrl.on_stick("bad", lambda x, y: None)

    def test_trigger_force_setters_and_validation(self):
        ctrl = self.create_controller()

        ctrl.set_r2_force(6)
        ctrl.set_l2_force(5)
        self.assertEqual(ctrl.ds.triggerR.mode, DummyTriggerModes.Rigid)
        self.assertEqual(ctrl.ds.triggerL.mode, DummyTriggerModes.Rigid)
        self.assertEqual(ctrl.ds.triggerR.force_calls[-1], (6, 6))
        self.assertEqual(ctrl.ds.triggerL.force_calls[-1], (6, 5))

        with self.assertRaisesRegex(ValueError, "0 through 6"):
            ctrl.set_r2_force(7)
        with self.assertRaisesRegex(ValueError, "0 through 6"):
            ctrl.set_l2_force(-1)
        with self.assertRaisesRegex(TypeError, "integer"):
            ctrl.set_l2_force("3")

    def test_trigger_cycle_helpers_and_reentrancy_guards(self):
        ctrl = self.create_controller()

        self.assertEqual(ctrl.cycle_r2_force(), 1)
        self.assertEqual(ctrl.cycle_l2_force(), 1)
        self.assertEqual(ctrl.ds.triggerR.force_calls[-1], (6, 1))
        self.assertEqual(ctrl.ds.triggerL.force_calls[-1], (6, 1))

        ctrl._handling_r2_force = True
        ctrl._handling_l2_force = True
        self.assertIsNone(ctrl.cycle_r2_force())
        self.assertIsNone(ctrl.cycle_l2_force())

    def test_trigger_mode_cycles_do_not_recurse(self):
        ctrl = self.create_controller()
        ctrl.ds.circle_pressed += ctrl._on_circle_pressed
        ctrl.ds.square_pressed += ctrl._on_square_pressed

        for _ in range(10):
            ctrl._on_circle_pressed(True)
            ctrl._on_square_pressed(True)

        self.assertIn(ctrl.ds.triggerR.mode, list(DummyTriggerModes))
        self.assertIn(ctrl.ds.triggerL.mode, list(DummyTriggerModes))

    def test_internal_button_handlers_ignore_false_values(self):
        ctrl = self.create_controller()
        ctrl._on_cross_pressed(False)
        ctrl._on_triangle_pressed(False)
        ctrl._on_circle_pressed(False)
        ctrl._on_square_pressed(False)
        self.assertEqual(ctrl.ds.triggerR.force_calls, [])
        self.assertEqual(ctrl.ds.triggerL.force_calls, [])

    def test_listen_stop_and_read_loop(self):
        ctrl = self.create_controller()
        sleep_calls = []
        self._original_sleep = controller.time.sleep

        def stop_after_one_sleep(interval):
            sleep_calls.append(interval)
            ctrl.stop()

        controller.time.sleep = stop_after_one_sleep
        ctrl.listen(poll_interval=0.25)
        self.assertEqual(sleep_calls, [0.25])
        self.assertFalse(ctrl._listening)

        ctrl = self.create_controller()
        sleep_calls.clear()
        controller.time.sleep = stop_after_one_sleep
        ctrl.read_loop(poll_interval=0.5)
        self.assertEqual(sleep_calls, [0.5])

    def test_list_trigger_modes(self):
        ctrl = self.create_controller()
        self.assertEqual(ctrl.list_trigger_modes(), ["Off", "Rigid", "Mode2"])


class DebugInputTestCase(unittest.TestCase):
    def test_debug_callback_factories_print_values(self):
        with patch("builtins.print") as print_mock:
            debug_inputs.print_button("cross")(True)
            debug_inputs.print_trigger("R2")(42)
            debug_inputs.print_stick("Left Stick")(1, 2)

        print_mock.assert_any_call("cross: True")
        print_mock.assert_any_call("R2 value: 42")
        print_mock.assert_any_call("Left Stick: x=1, y=2")

    def test_register_debug_callbacks(self):
        class FakeController:
            def __init__(self):
                self.buttons = []
                self.triggers = []
                self.sticks = []

            def on_button(self, button, callback):
                self.buttons.append((button, callback))

            def on_trigger(self, trigger, callback):
                self.triggers.append((trigger, callback))

            def on_stick(self, stick, callback):
                self.sticks.append((stick, callback))

        fake = FakeController()
        debug_inputs.register_debug_callbacks(fake)

        self.assertEqual(len(fake.buttons), 12)
        self.assertEqual([name for name, _ in fake.triggers], ["l2", "r2"])
        self.assertEqual([name for name, _ in fake.sticks], ["left", "right"])

    def test_main_opens_listens_and_closes_on_keyboard_interrupt(self):
        class FakeController:
            instance = None

            def __init__(self):
                FakeController.instance = self
                self.open_called = False
                self.close_called = False
                self.callbacks_registered = False

            def open(self):
                self.open_called = True

            def listen(self):
                raise KeyboardInterrupt

            def close(self):
                self.close_called = True

        def mark_callbacks(ctrl):
            ctrl.callbacks_registered = True

        with patch.object(debug_inputs, "DualSenseController", FakeController):
            with patch.object(debug_inputs, "register_debug_callbacks", mark_callbacks):
                with patch("builtins.print"):
                    debug_inputs.main()

        fake = FakeController.instance
        self.assertTrue(fake.open_called)
        self.assertTrue(fake.callbacks_registered)
        self.assertTrue(fake.close_called)


if __name__ == "__main__":
    unittest.main()
