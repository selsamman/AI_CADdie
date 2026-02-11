import json
from pathlib import Path

def load_registries(bundle_root: Path) -> dict:
    reg_dir = bundle_root / "registry"
    prototypes = json.loads((reg_dir / "prototypes.json").read_text(encoding="utf-8"))
    operators  = json.loads((reg_dir / "operators.json").read_text(encoding="utf-8"))
    return {
        "prototypes": {p["name"]: p for p in prototypes},
        "operators":  {o["name"]: o for o in operators},
    }
