"""Tests para el parser de Python."""

from miner.parsers.python_parser import extract_function_names


class TestExtractFunctionNames:
    """Tests para la extraccion de nombres de funciones Python."""

    def test_simple_function(self) -> None:
        source = "def make_response():\n    pass\n"
        assert extract_function_names(source) == ["make_response"]

    def test_multiple_functions(self) -> None:
        source = (
            "def foo():\n    pass\n\n"
            "def bar():\n    pass\n"
        )
        names = extract_function_names(source)
        assert "foo" in names
        assert "bar" in names

    def test_async_function(self) -> None:
        source = "async def fetch_data():\n    pass\n"
        assert extract_function_names(source) == ["fetch_data"]

    def test_method_in_class(self) -> None:
        source = (
            "class MyClass:\n"
            "    def __init__(self):\n"
            "        pass\n"
            "    def get_name(self):\n"
            "        pass\n"
        )
        names = extract_function_names(source)
        assert "__init__" in names
        assert "get_name" in names

    def test_nested_function(self) -> None:
        source = (
            "def outer():\n"
            "    def inner():\n"
            "        pass\n"
            "    pass\n"
        )
        names = extract_function_names(source)
        assert "outer" in names
        assert "inner" in names

    def test_syntax_error_returns_empty(self) -> None:
        source = "def broken(\n"
        assert extract_function_names(source) == []

    def test_empty_source(self) -> None:
        assert extract_function_names("") == []

    def test_no_functions(self) -> None:
        source = "x = 42\nprint(x)\n"
        assert extract_function_names(source) == []
