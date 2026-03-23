"""Planificador de rangos de stars para recorrer GitHub.

Genera rangos descendentes de stars para la API de busqueda de GitHub,
permitiendo recorrer repositorios de mayor a menor popularidad sin
depender de una unica consulta paginada (la API limita a 1000 resultados
por query).

Ejemplo de rangos generados:
    ">100000", "50000..100000", "10000..50000", "5000..10000", ...

Para cada rango se iteran todas las paginas disponibles.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterator

logger = logging.getLogger(__name__)

# Limites de stars en orden descendente.
# Cada par consecutivo define un rango: (limites[i+1], limites[i]).
_STAR_LIMITS = [
    1_000_000,
    100_000,
    50_000,
    20_000,
    10_000,
    5_000,
    2_000,
    1_000,
    500,
    100,
    10,
]


@dataclass
class StarRange:
    """Representa un rango de stars para la busqueda de GitHub."""

    query: str
    label: str


@dataclass
class RangeScheduler:
    """Genera rangos de stars descendentes para recorrer GitHub."""

    min_stars: int = 10
    _processed_repos: set[str] = field(default_factory=set)

    def iter_ranges(self) -> Iterator[StarRange]:
        """Genera rangos de stars en orden descendente.

        El primer rango es abierto (ej: ">100000"), los siguientes
        son cerrados (ej: "50000..100000").
        """
        # Filtrar limites segun el minimo configurado.
        limits = [s for s in _STAR_LIMITS if s >= self.min_stars]
        if not limits:
            limits = [self.min_stars]

        # Primer rango: mayor que el limite mas alto.
        yield StarRange(
            query=f">{limits[0]}",
            label=f">{limits[0]} stars",
        )

        # Rangos intermedios.
        for i in range(len(limits) - 1):
            high = limits[i]
            low = limits[i + 1]
            yield StarRange(
                query=f"{low}..{high}",
                label=f"{low}..{high} stars",
            )

    def is_processed(self, repo_full_name: str) -> bool:
        """Verifica si un repositorio ya fue procesado."""
        return repo_full_name in self._processed_repos

    def mark_processed(self, repo_full_name: str) -> None:
        """Marca un repositorio como procesado."""
        self._processed_repos.add(repo_full_name)
        logger.debug("Repositorio marcado: %s", repo_full_name)
