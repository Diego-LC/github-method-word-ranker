"""Configuracion del componente miner.

Carga variables de entorno con valores por defecto sensibles
para ejecucion en Docker Compose.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Parametros de configuracion del miner."""

    # GitHub
    github_token: str = os.environ.get("GITHUB_TOKEN", "")

    # Redis
    redis_host: str = os.environ.get("REDIS_HOST", "redis")
    redis_port: int = int(os.environ.get("REDIS_PORT", "6379"))
    stream_name: str = os.environ.get("STREAM_NAME", "mining_events")

    # Traversal
    min_stars: int = int(os.environ.get("MIN_STARS", "10"))
    repos_per_page: int = int(os.environ.get("REPOS_PER_PAGE", "30"))

    # Clonado y paralelismo
    clone_dir: str = os.environ.get("CLONE_DIR", "/tmp/miner_clones")
    max_workers: int = int(os.environ.get("MAX_WORKERS", "4"))
    max_file_size_bytes: int = int(
        os.environ.get("MAX_FILE_SIZE_BYTES", str(512 * 1024))
    )

    @property
    def github_headers(self) -> dict[str, str]:
        """Headers HTTP para la API de GitHub."""
        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        return headers


def load_settings() -> Settings:
    """Retorna una instancia inmutable de Settings."""
    return Settings()
