from recap.config_classes import Config
import pytest


def test_asdict():
    class CONFIG(Config):
        DEF: str = "f"
        A = None

        class TRAIN:
            LEARNING_RATE: float = .01
            NUM_EPOCHS = 1

        class EVAL:
            ABC: str = "s"
    assert CONFIG.asdict() == {
        "DEF": "f",
        "A": None,
        "TRAIN": {
            "LEARNING_RATE": .01,
            "NUM_EPOCHS": 1
        },
        "EVAL": {
            "ABC": "s"
        }
    }


def test_immutability():
    class CONFIG(Config):
        ABC = "f"
    with pytest.raises(AttributeError):
        CONFIG.ABC = "g"
