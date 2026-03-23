"""Acceso a datos agregados en Redis.

Provee funciones para:
- Actualizar el sorted set de ranking de palabras.
- Actualizar estadisticas globales de mineria.
- Leer el top-N de palabras.
- Leer estadisticas de mineria.
"""

from __future__ import annotations

import redis

from visualizer.settings import Settings


class RedisStore:
    """Maneja lectura y escritura de datos agregados en Redis."""

    def __init__(self, settings: Settings) -> None:
        self._redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
        self._ranking_key = settings.word_ranking_key
        self._stats_key = settings.mining_stats_key

    # ------------------------------------------------------------------
    # Escritura (usado por el consumer)
    # ------------------------------------------------------------------

    def increment_words(self, word_counts: dict[str, int]) -> None:
        """Incrementa los conteos de palabras en el sorted set."""
        pipe = self._redis.pipeline()
        for word, count in word_counts.items():
            pipe.zincrby(self._ranking_key, count, word)
        pipe.execute()

    def update_stats(
        self,
        *,
        repo_full_name: str,
        repo_stars: int,
        python_files: int,
        java_files: int,
    ) -> None:
        """Actualiza las estadisticas globales de mineria."""
        pipe = self._redis.pipeline()
        pipe.hincrby(self._stats_key, "total_repos", 1)
        pipe.hincrby(self._stats_key, "total_python_files", python_files)
        pipe.hincrby(self._stats_key, "total_java_files", java_files)
        pipe.hset(self._stats_key, "last_repo", repo_full_name)
        pipe.hset(self._stats_key, "last_repo_stars", str(repo_stars))
        pipe.execute()

    # ------------------------------------------------------------------
    # Lectura (usado por la UI de Streamlit)
    # ------------------------------------------------------------------

    def get_top_words(self, top_n: int = 10) -> list[tuple[str, float]]:
        """Retorna las top-N palabras con sus conteos.

        Retorna una lista de tuplas (palabra, conteo) ordenada
        de mayor a menor.
        """
        results = self._redis.zrevrange(
            self._ranking_key, 0, top_n - 1, withscores=True
        )
        return [(word, score) for word, score in results]

    def get_total_words(self) -> int:
        """Retorna el total de palabras unicas registradas."""
        return self._redis.zcard(self._ranking_key)

    def get_stats(self) -> dict[str, str]:
        """Retorna las estadisticas globales de mineria."""
        return self._redis.hgetall(self._stats_key)
