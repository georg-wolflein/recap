import typing
from inspect import isclass
import yaml
import copy


def parse_attribute_types(cfg):
    types = dict()
    attributes = [x for x in dir(cfg) if not x.startswith("_")]
    type_hints = typing.get_type_hints(cfg)

    for name in attributes:
        value = getattr(cfg, name)
        if hasattr(value, "__recap_ignore__"):
            continue
        attr_type = type(value)
        if name in type_hints:
            attr_type = type_hints[name]
        if isclass(value):
            attr_type = parse_attribute_types(value)
        if value is None:
            attr_type = typing.Any

        types[name] = attr_type
    return types


def parse_attribute_value(cfg):
    if isclass(cfg):
        values = dict()
        attributes = [x for x in dir(cfg) if not x.startswith("_")]

        for name in attributes:
            attr = getattr(cfg, name)
            if hasattr(attr, "__recap_ignore__"):
                continue
            values[name] = parse_attribute_value(attr)

        return values
    return cfg


def _no_config(func):
    func.__recap_ignore__ = True
    return func


IMMUTABLE_ERROR = AttributeError("object is immutable")


class ConfigMeta(type):
    def __setattr__(self, name, value):
        if name in self._types:
            raise IMMUTABLE_ERROR
        super().__setattr__(name, value)

    def __getattribute__(self, name):
        if name != "_types" and name in self._types and name in self._values:
            return self.get(name)
        return super().__getattribute__(name)

    def __str__(self):
        return yaml.dump(self._values)


class Accessor:
    def __init__(self, path: list, root: "Config"):
        self._path = path
        self._root = root

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            raise IMMUTABLE_ERROR

    def __getattribute__(self, name: str):
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._root.get(*self._path, name)

    def __str__(self):
        return yaml.dump(self._root._get(*self._path))


class Config(metaclass=ConfigMeta):

    _types = dict()
    _values = dict()
    _default_values = dict()

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._types = parse_attribute_types(cls)
        cls._values = parse_attribute_value(cls)
        cls._default_values = copy.deepcopy(cls._values)

    @classmethod
    @_no_config
    def reset(cls):
        cls._values = copy.deepcopy(cls._default_values)

    @classmethod
    def _get(cls, *path):
        current = cls._values
        for key in path:
            current = current[key]
        return current

    @classmethod
    @_no_config
    def get(cls, *path):
        current = cls._get(*path)
        if isinstance(current, dict):
            return Accessor(path, cls)
        return current

    @classmethod
    @_no_config
    def set(cls, *path, value):
        *path, key = path
        current = cls._get(*path)
        if isinstance(current[key], dict):
            raise AttributeError("attempting to set dict")
        current[key] = value

    @classmethod
    @_no_config
    def asdict(cls) -> dict:
        return copy.deepcopy(cls._values)
