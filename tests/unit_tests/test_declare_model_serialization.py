import tempfile
from pathlib import Path
import sys
import types
import unittest

project_root = Path(__file__).resolve().parents[2]
declare4py_module = types.ModuleType("Declare4Py")
declare4py_module.__path__ = [str(project_root / "Declare4Py")]
process_models_module = types.ModuleType("Declare4Py.ProcessModels")
process_models_module.__path__ = [str(project_root / "Declare4Py" / "ProcessModels")]
utils_module = types.ModuleType("Declare4Py.Utils")
utils_module.__path__ = [str(project_root / "Declare4Py" / "Utils")]

sys.modules.setdefault("Declare4Py", declare4py_module)
sys.modules.setdefault("Declare4Py.ProcessModels", process_models_module)
sys.modules.setdefault("Declare4Py.Utils", utils_module)

logaut_module = types.ModuleType("logaut")
logaut_module.ltl2dfa = lambda *args, **kwargs: None
pylogics_module = types.ModuleType("pylogics")
pylogics_parsers_module = types.ModuleType("pylogics.parsers")
pylogics_parsers_module.parse_ltl = lambda formula: formula
pylogics_module.parsers = pylogics_parsers_module

sys.modules.setdefault("logaut", logaut_module)
sys.modules.setdefault("pylogics", pylogics_module)
sys.modules.setdefault("pylogics.parsers", pylogics_parsers_module)

from Declare4Py.ProcessModels.DeclareModel import DeclareModel, DeclareModelTemplate


class DeclareModelSerializationTest(unittest.TestCase):
    def test_binary_constraints_are_serialized_with_three_condition_slots(self):
        model = DeclareModel()
        model.activities = ["A", "B"]
        model.constraints = [
            {
                "template": DeclareModelTemplate.RESPONSE,
                "activities": ["A", "B"],
                "condition": ("", ""),
            }
        ]

        model.set_constraints()

        self.assertEqual(model.serialized_constraints, ["Response[A, B] | | |"])

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = f"{tmpdir}/binary_model.decl"
            model.to_file(model_path)

            reloaded_model = DeclareModel().parse_from_file(model_path)

        self.assertEqual(reloaded_model.serialized_constraints, model.serialized_constraints)

    def test_unary_constraints_are_serialized_with_two_condition_slots(self):
        model = DeclareModel()
        model.activities = ["A"]
        model.constraints = [
            {
                "template": DeclareModelTemplate.INIT,
                "activities": ["A"],
                "condition": ("",),
            }
        ]

        model.set_constraints()

        self.assertEqual(model.serialized_constraints, ["Init[A] | |"])

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = f"{tmpdir}/unary_model.decl"
            model.to_file(model_path)

            reloaded_model = DeclareModel().parse_from_file(model_path)

        self.assertEqual(reloaded_model.serialized_constraints, model.serialized_constraints)


if __name__ == "__main__":
    unittest.main()
