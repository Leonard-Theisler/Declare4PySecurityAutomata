import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).resolve().parents[4]
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

groq_module = types.ModuleType("groq")
groq_module.Groq = MagicMock
groq_module.GroqError = type("GroqError", (Exception,), {})
sys.modules.setdefault("groq", groq_module)

from Declare4Py.ProcessModels.TextualModel import TextualModel


class TextualModelGroqModelsTest(unittest.TestCase):
    def test_get_available_models_returns_sorted_model_ids(self):
        client = MagicMock()
        client.models.list.return_value.data = [
            types.SimpleNamespace(id="model-z"),
            types.SimpleNamespace(id="model-a"),
        ]

        self.assertEqual(
            TextualModel.get_available_models(client),
            ["model-a", "model-z"],
        )

    def test_select_best_model_prefers_large_general_purpose_model(self):
        available_models = [
            "whisper-large-v3",
            "meta-llama/llama-guard-4-12b",
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "general-purpose-120b",
        ]

        self.assertEqual(
            TextualModel.select_best_model(available_models),
            "general-purpose-120b",
        )

    def test_select_best_model_rejects_an_empty_model_list(self):
        with self.assertRaisesRegex(ValueError, "did not return any"):
            TextualModel.select_best_model([])

    @patch("Declare4Py.ProcessModels.TextualModel.Groq")
    def test_to_decl_reports_models_retrieved_from_groq(self, groq_class):
        client = groq_class.return_value
        client.models.list.return_value.data = [
            types.SimpleNamespace(id="available-model"),
            types.SimpleNamespace(id="another-model"),
        ]

        model = TextualModel("A process description")

        with self.assertRaisesRegex(
            ValueError,
            r"missing-model.*another-model.*available-model",
        ):
            model.to_decl(api_key="test-key", llm_model="missing-model")

        groq_class.assert_called_once_with(api_key="test-key")
        client.models.list.assert_called_once_with()
        client.chat.completions.create.assert_not_called()

    @patch("Declare4Py.ProcessModels.TextualModel.DeclareModel")
    @patch("Declare4Py.ProcessModels.TextualModel.Groq")
    def test_to_decl_selects_the_best_model_when_omitted(
        self,
        groq_class,
        declare_model_class,
    ):
        client = groq_class.return_value
        client.models.list.return_value.data = [
            types.SimpleNamespace(id="llama-3.1-8b-instant"),
            types.SimpleNamespace(id="llama-3.3-70b-versatile"),
        ]
        client.chat.completions.create.return_value = {
            "choices": [
                types.SimpleNamespace(
                    message=types.SimpleNamespace(
                        content=(
                            "Activities: A\n"
                            "Final Formal Declarative Constraints:\n"
                            "existence(A)"
                        )
                    )
                )
            ]
        }
        expected_model = declare_model_class.return_value.parse_from_string.return_value

        result = TextualModel("A process description").to_decl(api_key="test-key")

        self.assertIs(result, expected_model)
        client.chat.completions.create.assert_called_once()
        self.assertEqual(
            client.chat.completions.create.call_args.kwargs["model"],
            "llama-3.3-70b-versatile",
        )

    @patch("Declare4Py.ProcessModels.TextualModel.DeclareModel")
    @patch("Declare4Py.ProcessModels.TextualModel.Groq")
    @patch("builtins.input", side_effect=["Please clarify the result", "exit"])
    def test_interactive_to_decl_forwards_notebook_input_to_the_model(
        self,
        input_mock,
        groq_class,
        declare_model_class,
    ):
        client = groq_class.return_value
        client.models.list.return_value.data = [
            types.SimpleNamespace(id="llama-3.3-70b-versatile"),
        ]
        client.chat.completions.create.side_effect = [
            {
                "choices": [
                    types.SimpleNamespace(
                        message=types.SimpleNamespace(content="What should I clarify?")
                    )
                ]
            },
            {
                "choices": [
                    types.SimpleNamespace(
                        message=types.SimpleNamespace(
                            content=(
                                "Activities: A\n"
                                "Final Formal Declarative Constraints:\n"
                                "existence(A)"
                            )
                        )
                    )
                ]
            },
        ]
        expected_model = declare_model_class.return_value.parse_from_string.return_value

        result = TextualModel("A process description").to_decl(
            api_key="test-key",
            interactive=True,
        )

        self.assertIs(result, expected_model)
        self.assertEqual(client.chat.completions.create.call_count, 2)
        second_messages = client.chat.completions.create.call_args_list[1].kwargs[
            "messages"
        ]
        self.assertEqual(
            second_messages[-1],
            {"role": "user", "content": "Please clarify the result"},
        )
        self.assertEqual(input_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
