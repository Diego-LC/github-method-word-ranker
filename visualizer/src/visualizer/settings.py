"""Configuracion del componente visualizer.

Carga variables de entorno para Redis, intervalo de refresco
y parametros del ranking.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Parametros de configuracion del visualizer."""

    redis_host: str = os.environ.get("REDIS_HOST", "redis")
    redis_port: int = int(os.environ.get("REDIS_PORT", "6379"))
    stream_name: str = os.environ.get("STREAM_NAME", "mining_events")
    top_n_default: int = int(os.environ.get("TOP_N_DEFAULT", "10"))
    ui_refresh_seconds: int = int(os.environ.get("UI_REFRESH_SECONDS", "3"))

    # Consumer group para Redis Streams.
    consumer_group: str = "visualizer_group"
    consumer_name: str = "visualizer_consumer_1"

    # Claves de Redis para datos agregados.
    word_ranking_key: str = "word_ranking"
    mining_stats_key: str = "mining_stats"


def load_settings() -> Settings:
    """Retorna una instancia inmutable de Settings."""
    return Settings()
