"""Tests para el parser de Java."""

from miner.parsers.java_parser import extract_method_names


class TestExtractMethodNames:
    """Tests para la extraccion de nombres de metodos Java."""

    def test_simple_method(self) -> None:
        source = (
            "public class Foo {\n"
            "    public boolean retainAll(Collection<?> c) {\n"
            "        return false;\n"
            "    }\n"
            "}\n"
        )
        names = extract_method_names(source)
        assert "retainAll" in names

    def test_multiple_methods(self) -> None:
        source = (
            "public class Foo {\n"
            "    public void doSomething() {}\n"
            "    private int getValue() { return 0; }\n"
            "}\n"
        )
        names = extract_method_names(source)
        assert "doSomething" in names
        assert "getValue" in names

    def test_static_method(self) -> None:
        source = (
            "public class Foo {\n"
            "    public static void main(String[] args) {}\n"
            "}\n"
        )
        names = extract_method_names(source)
        assert "main" in names

    def test_syntax_error_returns_empty(self) -> None:
        source = "public class { broken"
        assert extract_method_names(source) == []

    def test_empty_source(self) -> None:
        assert extract_method_names("") == []

    def test_no_methods(self) -> None:
        source = (
            "public class Foo {\n"
            "    int x = 42;\n"
            "}\n"
        )
        assert extract_method_names(source) == []
