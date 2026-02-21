import importlib
import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _import_dotted(path: str):
    if not path or "." not in path:
        raise ValueError(f"Invalid dotted import path: {path!r}")
    mod_path, attr = path.rsplit(".", 1)
    mod = importlib.import_module(mod_path)
    if not hasattr(mod, attr):
        raise AttributeError(f"Attribute '{attr}' not found in module '{mod_path}'")
    return getattr(mod, attr)


class TestRegistryIntegrity(unittest.TestCase):
    def test_prototypes_registry_integrity(self):
        protos_path = REPO / "registry" / "prototypes.json"
        protos = json.loads(protos_path.read_text(encoding="utf-8"))

        for p in protos:
            name = p.get("name")
            schema_path = p.get("schema_path")
            resolver = p.get("resolver")

            self.assertTrue(name, "Prototype missing 'name'")
            self.assertTrue(schema_path, f"Prototype '{name}' missing 'schema_path'")
            self.assertTrue(resolver, f"Prototype '{name}' missing 'resolver'")

            # schema_path exists
            self.assertTrue(
                (REPO / schema_path).exists(),
                f"Prototype '{name}' schema_path missing: {schema_path}",
            )

            # resolver imports
            try:
                fn = _import_dotted(resolver)
            except Exception as e:
                raise AssertionError(f"Prototype '{name}' resolver failed to import: {resolver}\n{e}") from e
            self.assertTrue(callable(fn), f"Prototype '{name}' resolver is not callable: {resolver}")

    def test_operators_registry_integrity(self):
        ops_path = REPO / "registry" / "operators.json"
        ops = json.loads(ops_path.read_text(encoding="utf-8"))

        for o in ops:
            name = o.get("name")
            schema_path = o.get("schema_path")
            handler = o.get("handler")

            self.assertTrue(name, "Operator missing 'name'")
            self.assertTrue(schema_path, f"Operator '{name}' missing 'schema_path'")
            self.assertTrue(handler, f"Operator '{name}' missing 'handler'")

            # schema_path exists
            self.assertTrue(
                (REPO / schema_path).exists(),
                f"Operator '{name}' schema_path missing: {schema_path}",
            )

            # handler imports
            try:
                fn = _import_dotted(handler)
            except Exception as e:
                raise AssertionError(f"Operator '{name}' handler failed to import: {handler}\n{e}") from e
            self.assertTrue(callable(fn), f"Operator '{name}' handler is not callable: {handler}")


if __name__ == "__main__":
    unittest.main()
