"""Parser de Python basado en el modulo ast de la libreria estandar.

Extrae nombres de funciones (def) y funciones async (async def)
recorriendo el AST del codigo fuente.
"""

from __future__ import annotations

import ast
import logging

logger = logging.getLogger(__name__)


def extract_function_names(source: str) -> list[str]:
    """Extrae los nombres de todas las funciones y metodos definidos.

    Retorna una lista con los nombres tal como aparecen en el codigo,
    sin modificar. La normalizacion y division en palabras se realiza
    en el modulo splitter.

    Si el archivo no se puede parsear, retorna una lista vacia.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        logger.debug("No se pudo parsear el archivo Python (SyntaxError).")
        return []

    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)

    return names
