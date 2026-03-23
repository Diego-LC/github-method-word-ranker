"""Separacion de nombres compuestos en palabras individuales.

Soporta las convenciones mas comunes:
- snake_case  (Python)
- camelCase   (Java)
- PascalCase  (Java)
- SCREAMING_SNAKE_CASE
- Nombres mixtos con numeros
"""

from __future__ import annotations

import re

# Patron que detecta limites entre palabras en identificadores.
# Cubre transiciones minuscula->mayuscula, mayuscula->mayuscula+minuscula,
# y separadores como guion bajo.
_SPLIT_RE = re.compile(
    r"""
    _+                       # separador snake_case
    | (?<=[a-z])(?=[A-Z])    # camelCase: minuscula -> mayuscula
    | (?<=[A-Z])(?=[A-Z][a-z])  # XMLParser -> XML + Parser
    | (?<=[a-zA-Z])(?=[0-9])    # get2 -> get + 2
    | (?<=[0-9])(?=[a-zA-Z])    # 2nd -> 2 + nd
    """,
    re.VERBOSE,
)

# Nombres dunder de Python que no representan decisiones del programador.
_DUNDER_RE = re.compile(r"^__\w+__$")

# Longitud minima para considerar una palabra significativa.
_MIN_WORD_LEN = 2


def is_dunder(name: str) -> bool:
    """Retorna True si el nombre es un dunder method de Python."""
    return bool(_DUNDER_RE.match(name))


def split_identifier(name: str) -> list[str]:
    """Divide un identificador en palabras normalizadas.

    Ejemplos:
        >>> split_identifier("make_response")
        ['make', 'response']
        >>> split_identifier("retainAll")
        ['retain', 'all']
        >>> split_identifier("XMLParser")
        ['xml', 'parser']
        >>> split_identifier("__init__")
        []
    """
    if not name or is_dunder(name):
        return []

    # Eliminar guiones bajos iniciales/finales (ej: _private, private_)
    stripped = name.strip("_")
    if not stripped:
        return []

    parts = _SPLIT_RE.split(stripped)
    words = [p.lower() for p in parts if p and len(p) >= _MIN_WORD_LEN]
    return words
