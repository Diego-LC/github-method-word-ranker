"""Publicador de eventos en Redis Streams.

Emite dos tipos de evento segun el contrato definido en
docs/event-contract.md:
- word_batch : lote de palabras extraidas de un archivo.
- repo_processed : resumen de un repositorio procesado.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone

import redis

from miner.config import Settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publica eventos de mineria en un Redis Stream."""

    def __init__(self, settings: Settings) -> None:
        self._redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
        self._stream = settings.stream_name

    def publish_word_batch(
        self,
        *,
        repo_full_name: str,
        repo_stars: int,
        language: str,
        path: str,
        word_counts: Counter[str],
        functions_found: int,
    ) -> None:
        """Publica un evento word_batch con las palabras de un archivo."""
        if not word_counts:
            return

        entry = {
            "event_type": "word_batch",
            "repo_full_name": repo_full_name,
            "repo_stars": str(repo_stars),
            "language": language,
            "path": path,
            "word_counts_json": json.dumps(dict(word_counts)),
            "functions_found": str(functions_found),
            "emitted_at": datetime.now(timezone.utc).isoformat(),
        }
        self._redis.xadd(self._stream, entry)
        logger.info(
            "Publicado word_batch: %s %s (%d palabras, %d funciones)",
            repo_full_name,
            path,
            sum(word_counts.values()),
            functions_found,
        )

    def publish_repo_processed(
        self,
        *,
        repo_full_name: str,
        repo_stars: int,
        python_files: int,
        java_files: int,
        total_functions: int = 0,
        total_words: int = 0,
        top_word: str = "",
        status: str = "ok",
    ) -> None:
        """Publica un evento repo_processed al terminar un repositorio."""
        entry = {
            "event_type": "repo_processed",
            "repo_full_name": repo_full_name,
            "repo_stars": str(repo_stars),
            "python_files": str(python_files),
            "java_files": str(java_files),
            "total_functions": str(total_functions),
            "total_words": str(total_words),
            "top_word": top_word,
            "status": status,
            "emitted_at": datetime.now(timezone.utc).isoformat(),
        }
        self._redis.xadd(self._stream, entry)
        logger.info(
            "Publicado repo_processed: %s (py=%d, java=%d, funcs=%d, words=%d, status=%s)",
            repo_full_name,
            python_files,
            java_files,
            total_functions,
            total_words,
            status,
        )
