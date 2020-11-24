from recap.path_manager import URI, PathManager, PathManagerBase, register_translator
from pathlib import Path


def test_uri_is_path():
    assert isinstance(URI(), Path)


def test_uri_concat():
    a = URI("/path/a") / "b"
    assert str(a) == "/path/a/b"


def test_virtual_uri():
    with PathManagerBase():
        test_dir = Path("/a/b/test")
        register_translator("test", test_dir)
        uri = URI("test://a/b")
        assert str(uri) == str(test_dir / "a" / "b")


def test_path_manager_register():
    manager = PathManagerBase()
    assert len(manager._handlers) == 0

    @manager.register_handler("abc")
    def abc():
        pass

    assert len(manager._handlers) == 1


def test_path_manager_resolve_simple():
    manager = PathManagerBase()
    p = "/a/b/c/d"
    assert str(manager.resolve(p)) == str(Path(p))


def test_path_manager_resolve_custom_handler():
    manager = PathManagerBase()

    @manager.register_handler("abc")
    def abc(path: URI) -> Path:
        return Path("/def") / path.path

    assert str(manager.resolve("abc://d/e")) == str(Path("/def/d/e"))
