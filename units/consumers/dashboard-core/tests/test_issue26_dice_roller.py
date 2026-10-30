import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.app import PAGE, api_modules
from dashboard.modules.registry import get_module


class DiceRollerModuleTests(unittest.TestCase):
    def test_dice_roller_is_registered_in_the_api_catalog(self):
        module = get_module("dice-roller")
        self.assertIsNotNone(module)
        self.assertEqual(module["type"], "dice-roller")
        self.assertEqual(api_modules()["count"], len(api_modules()["modules"]))
        self.assertIn(module, api_modules()["modules"])

    def test_dice_roller_has_bounded_accessible_controls(self):
        self.assertIn('module.type === "dice-roller"', PAGE)
        self.assertIn('countInput.max = "100"', PAGE)
        self.assertIn('sidesInput.max = "1000"', PAGE)
        self.assertIn('setAttribute("aria-live", "polite")', PAGE)
        self.assertIn('await invokeModule(module.id, {count, sides}, slot.id)', PAGE)
        self.assertIn('output.rolls.join(" + ")', PAGE)


if __name__ == "__main__":
    unittest.main()
