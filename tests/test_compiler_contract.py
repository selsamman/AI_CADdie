import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class TestCompilerContract(unittest.TestCase):
    def test_supported_operators_matches_registry(self):
        from engine.scene import SUPPORTED_OPERATORS

        ops = json.loads((REPO / "registry" / "operators.json").read_text(encoding="utf-8"))
        registry_ops = {o["name"] for o in ops}

        self.assertEqual(
            set(SUPPORTED_OPERATORS),
            registry_ops,
            "Operator contract drift: engine.scene.SUPPORTED_OPERATORS must exactly match registry/operators.json",
        )

    def test_supported_prototypes_matches_registry(self):
        from engine.constraints import COMPILER_SUPPORTED_PROTOTYPES

        protos = json.loads((REPO / "registry" / "prototypes.json").read_text(encoding="utf-8"))
        registry_protos = {p["name"] for p in protos}

        self.assertEqual(
            set(COMPILER_SUPPORTED_PROTOTYPES),
            registry_protos,
            "Prototype contract drift: engine.constraints.COMPILER_SUPPORTED_PROTOTYPES must exactly match registry/prototypes.json",
        )


if __name__ == "__main__":
    unittest.main()
