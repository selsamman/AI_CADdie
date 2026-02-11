import json
from pathlib import Path

def load_registries(bundle_root: Path) -> dict:
    reg_dir = bundle_root / "registry"
    prototypes = json.loads((reg_dir / "prototypes.json").read_text(encoding="utf-8"))
    operators  = json.loads((reg_dir / "operators.json").read_text(encoding="utf-8"))
    lumber_profiles_path = reg_dir / "lumber_profiles.json"
    lumber_profiles = json.loads(lumber_profiles_path.read_text(encoding="utf-8")) if lumber_profiles_path.exists() else {}
    return {
        "prototypes": {p["name"]: p for p in prototypes},
        "operators":  {o["name"]: o for o in operators},
        "lumber_profiles": lumber_profiles,
    }
