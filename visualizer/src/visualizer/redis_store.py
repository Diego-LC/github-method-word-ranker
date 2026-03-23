"""Acceso a datos agregados en Redis.

Provee funciones para:
- Actualizar el sorted set de ranking de palabras.
- Actualizar estadisticas globales de mineria.
- Guardar y leer detalles de repositorios individuales.
- Leer el top-N de palabras.
"""

from __future__ import annotations

import json

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
        self._repo_details_key = settings.repo_details_key

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

    def save_repo_detail(
        self,
        *,
        repo_full_name: str,
        repo_stars: int,
        python_files: int,
        java_files: int,
        total_functions: int,
        total_words: int,
        top_word: str,
        status: str,
    ) -> None:
        """Guarda las estadisticas detalladas de un repositorio."""
        detail = json.dumps({
            "stars": repo_stars,
            "python_files": python_files,
            "java_files": java_files,
            "total_functions": total_functions,
            "total_words": total_words,
            "top_word": top_word,
            "status": status,
        })
        self._redis.hset(self._repo_details_key, repo_full_name, detail)

    # ------------------------------------------------------------------
    # Lectura (usado por la UI de Streamlit)
    # ------------------------------------------------------------------

    def get_top_words(self, top_n: int = 10) -> list[tuple[str, float]]:
        """Retorna las top-N palabras con sus conteos."""
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

    def get_all_repos(self) -> list[dict]:
        """Retorna todos los repositorios con sus detalles, ordenados por stars."""
        raw = self._redis.hgetall(self._repo_details_key)
        repos = []
        for repo_name, detail_json in raw.items():
            try:
                detail = json.loads(detail_json)
                detail["repo_full_name"] = repo_name
                repos.append(detail)
            except json.JSONDecodeError:
                continue

        # Ordenar por stars descendente.
        repos.sort(key=lambda r: r.get("stars", 0), reverse=True)
        return repos
