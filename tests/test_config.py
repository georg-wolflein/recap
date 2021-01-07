from pathlib import Path
import pytest

from recap import CfgNode as CN

RESOURCES = Path(__file__).parent / "resources"


def test_load_yaml():
    cfg = CN.load_yaml_with_base(RESOURCES / "inherit_base.yaml")
    assert cfg.TEST == 1
    assert cfg.XYZ == "abc"


def test_inherit_yaml():
    cfg = CN.load_yaml_with_base(RESOURCES / "inherit_override.yaml")
    assert cfg.TEST == 2
    assert cfg.XYZ == "abc"


def test_data_type_override():
    with pytest.raises(ValueError):
        cfg = CN.load_yaml_with_base(RESOURCES / "data_type_override.yaml")
