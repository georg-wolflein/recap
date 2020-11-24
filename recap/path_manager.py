from __future__ import annotations
from pathlib import Path, PurePath, _PosixFlavour
from typing import Callable
import logging
import functools
import abc
from contextlib import contextmanager
import re
import os

logger = logging.getLogger(__name__)


class _URIFlavour(_PosixFlavour):
    has_drv = True
    is_supported = True

    def splitroot(self, part, sep=_PosixFlavour.sep):
        assert sep == self.sep

        match = re.match(rf"(.*):{re.escape(sep)}{{2}}(.*)", part)
        if match:
            drive, path = match.groups()
            drive = drive + "://"
            root = ""
            return drive, root, path
        else:
            return super().splitroot(part, sep=sep)


class URIBase(Path):
    _flavour = _URIFlavour()

    @property
    def scheme(self) -> str:
        if not self.drive:
            return ""
        return self.drive[:-len("://")]

    @property
    def path(self) -> str:
        begin = 1 if self.drive or self.root else 0
        return self.root + self._flavour.join(self.parts[begin:])

    def __repr__(self) -> str:
        s = ""
        if self.scheme:
            s += self.scheme + ":" + self._flavour.sep * 2
        s += self.path
        return "{}({!r})".format(self.__class__.__name__, s)


class PathManagerBase:

    def __init__(self):
        self._handlers = {}
        self._previous_path_managers = []

    def resolve(self, path: os.PathLike) -> Path:
        if not isinstance(path, URIBase):
            path = URIBase(path)
        if path.scheme:
            if path.scheme not in self._handlers:
                raise NotImplementedError
            return self._handlers[path.scheme](path)
        else:
            return Path(path.path)

    def register_handler(self, scheme: str) -> Callable:
        def decorator(func: Callable[[os.PathLike], Path]):
            self._handlers[scheme] = func
            logger.debug(f"Registered path handler for scheme {scheme}")
            return func
        return decorator

    def __enter__(self):
        self._previous_path_managers.append(PathManager._instance)
        PathManager._instance = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        PathManager._instance = self._previous_path_managers.pop()


class PathManagerProxy(PathManagerBase):

    def __init__(self, instance: PathManagerBase):
        self._instance = instance

    def resolve(self, *args, **kwargs):
        return self._instance.resolve(*args, **kwargs)

    def register_handler(self, *args, **kwargs):
        return self._instance.register_handler(*args, **kwargs)

    def __enter__(self, *args, **kwargs):
        raise NotImplementedError

    def __exit__(self, *args, **kwargs):
        raise NotImplementedError


PathManager = PathManagerProxy(PathManagerBase())


class URI(URIBase):

    def _init(self, *args, **kwargs):
        self._local_path = PathManager.resolve(self)
        super()._init()

    def __str__(self) -> str:
        return str(self._local_path)


class PathTranslator(abc.ABC):

    def __init__(self, base_path: Path):
        self._base_path = base_path

    def __call__(self, url: URI) -> Path:
        return self._base_path / url.path


def register_translator(scheme: str, path: Path):
    class Translator(PathTranslator):
        def __init__(self):
            super().__init__(path)
    PathManager.register_handler(scheme)(Translator())
