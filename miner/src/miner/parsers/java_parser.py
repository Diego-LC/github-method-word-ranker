"""Parser de Java basado en la libreria javalang.

Extrae nombres de metodos recorriendo el arbol de sintaxis
generado por javalang.parse.parse().
"""

from __future__ import annotations

import logging

import javalang

logger = logging.getLogger(__name__)


def extract_method_names(source: str) -> list[str]:
    """Extrae los nombres de todos los metodos declarados en codigo Java.

    Retorna una lista con los nombres tal como aparecen en el codigo.
    Si el archivo no se puede parsear, retorna una lista vacia.
    """
    try:
        tree = javalang.parse.parse(source)
    except (javalang.parser.JavaSyntaxError, Exception):
        logger.debug("No se pudo parsear el archivo Java.")
        return []

    names: list[str] = []
    for _, node in tree.filter(javalang.tree.MethodDeclaration):
        names.append(node.name)

    return names
