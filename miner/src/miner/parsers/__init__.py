"""Paquete de parsers para extraccion de nombres de funciones y metodos."""

from miner.parsers.java_parser import extract_method_names
from miner.parsers.python_parser import extract_function_names

__all__ = ["extract_function_names", "extract_method_names"]
