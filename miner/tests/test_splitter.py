"""Tests para el modulo splitter."""

import pytest

from miner.splitter import is_dunder, split_identifier


class TestIsDunder:
    """Tests para la funcion is_dunder."""

    def test_init(self) -> None:
        assert is_dunder("__init__") is True

    def test_str(self) -> None:
        assert is_dunder("__str__") is True

    def test_enter(self) -> None:
        assert is_dunder("__enter__") is True

    def test_regular_name(self) -> None:
        assert is_dunder("get_user") is False

    def test_single_underscore(self) -> None:
        assert is_dunder("_private") is False

    def test_double_leading_only(self) -> None:
        assert is_dunder("__mangled") is False


class TestSplitIdentifier:
    """Tests para la funcion split_identifier."""

    # -- snake_case --

    def test_snake_case_simple(self) -> None:
        assert split_identifier("make_response") == ["make", "response"]

    def test_snake_case_multiple(self) -> None:
        assert split_identifier("get_user_by_id") == ["get", "user", "by", "id"]

    # -- camelCase --

    def test_camel_case(self) -> None:
        assert split_identifier("retainAll") == ["retain", "all"]

    def test_camel_case_multiple(self) -> None:
        assert split_identifier("getUserById") == ["get", "user", "by", "id"]

    # -- PascalCase --

    def test_pascal_case(self) -> None:
        assert split_identifier("RetainAll") == ["retain", "all"]

    # -- Acronimos --

    def test_xml_parser(self) -> None:
        assert split_identifier("XMLParser") == ["xml", "parser"]

    def test_get_html_content(self) -> None:
        assert split_identifier("getHTMLContent") == ["get", "html", "content"]

    # -- SCREAMING_SNAKE_CASE --

    def test_screaming_snake(self) -> None:
        assert split_identifier("MAX_RETRY_COUNT") == ["max", "retry", "count"]

    # -- Casos especiales --

    def test_dunder_returns_empty(self) -> None:
        assert split_identifier("__init__") == []

    def test_empty_string(self) -> None:
        assert split_identifier("") == []

    def test_single_word(self) -> None:
        assert split_identifier("run") == ["run"]

    def test_single_char_filtered(self) -> None:
        """Palabras de un solo caracter se filtran."""
        assert split_identifier("a") == []

    def test_leading_underscore(self) -> None:
        assert split_identifier("_private_method") == ["private", "method"]

    def test_double_leading_underscore(self) -> None:
        assert split_identifier("__mangled_name") == ["mangled", "name"]

    def test_numbers(self) -> None:
        result = split_identifier("get2ndItem")
        assert "get" in result
        assert "item" in result
