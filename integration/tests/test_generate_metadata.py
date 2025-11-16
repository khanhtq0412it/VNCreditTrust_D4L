import json
import importlib.util
from pathlib import Path


def load_generate_metadata_module() -> object:
    """Dynamically load the generate_metadata.py module for testing.

    This keeps the tests independent from package installation and mirrors how
    the scripts are used in the repository.
    """
    repo_root = Path(__file__).parents[1]
    module_path = repo_root / "python-batching" / "generate_metadata.py"
    spec = importlib.util.spec_from_file_location("generate_metadata", str(module_path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_find_json_keys_with_dict_and_list(tmp_path):
    module = load_generate_metadata_module()

    # create a dict JSON
    p1 = tmp_path / "a.json"
    p1.write_text(json.dumps({"a": 1, "b": 2}), encoding="utf-8")

    # create a list-of-dict JSON
    p2 = tmp_path / "b.json"
    p2.write_text(json.dumps([{"x": 1}, {"y": 2, "z": 3}]), encoding="utf-8")

    keys1 = module.find_json_keys(p1)
    assert sorted(keys1) == ["a", "b"]

    keys2 = module.find_json_keys(p2)
    assert sorted(keys2) == ["x", "y", "z"]
