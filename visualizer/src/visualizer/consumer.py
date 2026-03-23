"""Consumidor continuo de eventos desde Redis Streams.

Lee eventos del stream de mineria y actualiza los datos
agregados en Redis (sorted set + hash). Se ejecuta como
un proceso separado dentro del contenedor del visualizer
(lanzado por entrypoint.sh).
"""

from __future__ import annotations

import json
import logging
import signal
import sys
import time

import redis

from visualizer.redis_store import RedisStore
from visualizer.settings import load_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_shutdown = False


def _handle_signal(signum: int, _frame: object) -> None:
    """Maneja señales para detencion limpia."""
    global _shutdown
    logger.info("Señal %d recibida. Deteniendo consumer...", signum)
    _shutdown = True


def _ensure_consumer_group(
    r: redis.Redis, stream: str, group: str  # type: ignore[type-arg]
) -> None:
    """Crea el consumer group si no existe."""
    try:
        r.xgroup_create(stream, group, id="0", mkstream=True)
        logger.info("Consumer group '%s' creado.", group)
    except redis.ResponseError as exc:
        if "BUSYGROUP" in str(exc):
            logger.debug("Consumer group '%s' ya existe.", group)
        else:
            raise


def _process_event(store: RedisStore, event: dict[str, str]) -> None:
    """Procesa un evento individual y actualiza los agregados."""
    event_type = event.get("event_type", "")

    if event_type == "word_batch":
        word_counts_raw = event.get("word_counts_json", "{}")
        try:
            word_counts = json.loads(word_counts_raw)
        except json.JSONDecodeError:
            logger.warning("word_counts_json invalido: %s", word_counts_raw)
            return

        # Convertir valores a int.
        word_counts_int = {k: int(v) for k, v in word_counts.items()}
        store.increment_words(word_counts_int)
        logger.debug(
            "Actualizado ranking (repo=%s, path=%s, palabras=%d).",
            event.get("repo_full_name", "?"),
            event.get("path", "?"),
            sum(word_counts_int.values()),
        )

    elif event_type == "repo_processed":
        store.update_stats(
            repo_full_name=event.get("repo_full_name", "unknown"),
            repo_stars=int(event.get("repo_stars", "0")),
            python_files=int(event.get("python_files", "0")),
            java_files=int(event.get("java_files", "0")),
        )
        logger.info(
            "Repositorio procesado: %s (%s stars, status=%s).",
            event.get("repo_full_name", "?"),
            event.get("repo_stars", "?"),
            event.get("status", "?"),
        )

    else:
        logger.warning("event_type desconocido: '%s'", event_type)


def main() -> None:
    """Ejecuta el consumidor continuo de eventos."""
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    settings = load_settings()

    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    )
    store = RedisStore(settings)

    _ensure_consumer_group(r, settings.stream_name, settings.consumer_group)

    logger.info("Consumer iniciado. Stream: %s", settings.stream_name)

    while not _shutdown:
        try:
            # Leer eventos pendientes del consumer group.
            results = r.xreadgroup(
                groupname=settings.consumer_group,
                consumername=settings.consumer_name,
                streams={settings.stream_name: ">"},
                count=50,
                block=2000,  # Bloquear 2 segundos esperando mensajes.
            )
        except redis.ConnectionError:
            logger.warning("Conexion perdida con Redis. Reintentando en 3s...")
            time.sleep(3)
            continue

        if not results:
            continue

        for _stream_name, messages in results:
            for msg_id, fields in messages:
                _process_event(store, fields)
                # Confirmar que el mensaje fue procesado.
                r.xack(settings.stream_name, settings.consumer_group, msg_id)

    logger.info("Consumer detenido limpiamente.")


if __name__ == "__main__":
    main()
