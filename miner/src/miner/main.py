"""Punto de entrada del componente miner.

Orquesta el flujo principal:
1. Obtener repositorios de GitHub en orden descendente de stars.
2. Clonar cada repositorio con shallow clone (depth=1).
3. Buscar archivos .py y .java localmente.
4. Parsear en paralelo con multiprocessing.Pool.
5. Publicar eventos en Redis Stream.
6. Limpiar el clon temporal.

El proceso se ejecuta de forma continua hasta recibir SIGINT/SIGTERM.
"""

from __future__ import annotations

import logging
import multiprocessing
import os
import signal
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from miner.config import load_settings
from miner.github_client import GitHubClient
from miner.parsers.java_parser import extract_method_names
from miner.parsers.python_parser import extract_function_names
from miner.publisher import EventPublisher
from miner.range_scheduler import RangeScheduler
from miner.repo_cloner import cleanup_clone, clone_repo, find_source_files
from miner.splitter import split_identifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Flag global para detencion limpia.
_shutdown = False


def _handle_signal(signum: int, _frame: object) -> None:
    """Maneja señales de interrupcion para detencion limpia."""
    global _shutdown
    logger.info("Señal %d recibida. Deteniendo miner...", signum)
    _shutdown = True


def _get_language(path: Path) -> str | None:
    """Determina el lenguaje de un archivo por su extension."""
    suffix = path.suffix
    if suffix == ".py":
        return "python"
    if suffix == ".java":
        return "java"
    return None


def _parse_file(file_path: Path) -> dict[str, Any]:
    """Parsea un archivo individual y retorna el resultado.

    Esta funcion se ejecuta en un proceso worker del Pool.
    Retorna un diccionario con los resultados del parseo.
    """
    language = _get_language(file_path)
    if not language:
        return {"ok": False}

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"ok": False}

    # Extraer nombres de funciones/metodos segun el lenguaje.
    if language == "python":
        names = extract_function_names(content)
    elif language == "java":
        names = extract_method_names(content)
    else:
        return {"ok": False}

    # Dividir cada nombre en palabras.
    word_counts: Counter[str] = Counter()
    for name in names:
        words = split_identifier(name)
        word_counts.update(words)

    return {
        "ok": True,
        "language": language,
        "path": str(file_path),
        "names": names,
        "word_counts": dict(word_counts),
    }


def _process_repo(
    publisher: EventPublisher,
    repo: dict,
    clone_dir: str,
    max_workers: int,
) -> None:
    """Procesa un repositorio: clona, parsea en paralelo y publica."""
    full_name = repo["full_name"]
    stars = repo.get("stargazers_count", 0)
    clone_url = repo.get("clone_url", f"https://github.com/{full_name}.git")

    logger.info("Procesando %s (%d stars)...", full_name, stars)

    # 1. Clonar el repositorio.
    repo_path = clone_repo(clone_url, clone_base_dir=clone_dir)
    if repo_path is None:
        publisher.publish_repo_processed(
            repo_full_name=full_name,
            repo_stars=stars,
            python_files=0,
            java_files=0,
            status="error_clone",
        )
        return

    try:
        # 2. Buscar archivos fuente.
        source_files = find_source_files(repo_path)

        if not source_files:
            logger.info("No se encontraron archivos .py/.java en %s.", full_name)
            publisher.publish_repo_processed(
                repo_full_name=full_name,
                repo_stars=stars,
                python_files=0,
                java_files=0,
                status="ok",
            )
            return

        # 3. Parsear en paralelo con multiprocessing.
        workers = min(max_workers, len(source_files))
        with multiprocessing.Pool(processes=workers) as pool:
            results = pool.map(_parse_file, source_files)

        # 4. Agregar resultados y publicar eventos.
        py_count = 0
        java_count = 0
        total_functions = 0
        total_word_counts: Counter[str] = Counter()

        for result in results:
            if not result.get("ok"):
                continue

            language = result["language"]
            word_counts = Counter(result["word_counts"])
            names = result["names"]

            if language == "python":
                py_count += 1
            else:
                java_count += 1

            total_functions += len(names)
            total_word_counts.update(word_counts)

            # Publicar evento word_batch por archivo.
            if word_counts:
                publisher.publish_word_batch(
                    repo_full_name=full_name,
                    repo_stars=stars,
                    language=language,
                    path=result["path"],
                    word_counts=word_counts,
                    functions_found=len(names),
                )

        # Determinar la palabra mas frecuente del repositorio.
        top_word = total_word_counts.most_common(1)[0][0] if total_word_counts else ""

        # 5. Publicar evento repo_processed con estadisticas.
        publisher.publish_repo_processed(
            repo_full_name=full_name,
            repo_stars=stars,
            python_files=py_count,
            java_files=java_count,
            total_functions=total_functions,
            total_words=sum(total_word_counts.values()),
            top_word=top_word,
            status="ok",
        )

    finally:
        # 6. Limpiar el clon temporal.
        cleanup_clone(repo_path)


def main() -> None:
    """Ejecuta el miner de forma continua."""
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    settings = load_settings()
    github = GitHubClient(settings)
    publisher = EventPublisher(settings)
    scheduler = RangeScheduler(min_stars=settings.min_stars)

    # Asegurar que el directorio de clones existe.
    os.makedirs(settings.clone_dir, exist_ok=True)

    logger.info(
        "Miner iniciado. Token GitHub: %s | Workers: %d",
        "si" if settings.github_token else "no",
        settings.max_workers,
    )

    for star_range in scheduler.iter_ranges():
        if _shutdown:
            break

        logger.info("Rango actual: %s", star_range.label)
        page = 1

        while not _shutdown:
            try:
                repos = github.search_repos(
                    stars_range=star_range.query,
                    page=page,
                )
            except Exception:
                logger.exception(
                    "Error buscando repos en %s pagina %d.", star_range.label, page
                )
                time.sleep(10)
                break

            if not repos:
                logger.info("No hay mas repositorios en %s.", star_range.label)
                break

            for repo in repos:
                if _shutdown:
                    break

                full_name = repo.get("full_name", "")
                if scheduler.is_processed(full_name):
                    continue

                _process_repo(publisher, repo, settings.clone_dir, settings.max_workers)
                scheduler.mark_processed(full_name)

                # Pausa corta entre repositorios.
                time.sleep(1)

            page += 1
            # Limite de la API de GitHub Search: 1000 resultados (34 paginas de 30).
            if page > 34:
                break

    logger.info("Miner detenido limpiamente.")


if __name__ == "__main__":
    main()
