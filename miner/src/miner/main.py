"""Punto de entrada del componente miner.

Orquesta el flujo principal:
1. Obtener repositorios de GitHub en orden descendente de stars.
2. Para cada repositorio, descargar archivos .py y .java.
3. Parsear el codigo fuente y extraer nombres de funciones/metodos.
4. Dividir nombres en palabras y publicar eventos en Redis Stream.

El proceso se ejecuta de forma continua hasta recibir SIGINT/SIGTERM.
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from collections import Counter

from miner.config import load_settings
from miner.github_client import GitHubClient
from miner.parsers.java_parser import extract_method_names
from miner.parsers.python_parser import extract_function_names
from miner.publisher import EventPublisher
from miner.range_scheduler import RangeScheduler
from miner.splitter import split_identifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Extensiones de archivos que nos interesan.
_TARGET_EXTENSIONS = {".py", ".java"}

# Flag global para detencion limpia.
_shutdown = False


def _handle_signal(signum: int, _frame: object) -> None:
    """Maneja señales de interrupcion para detencion limpia."""
    global _shutdown
    logger.info("Señal %d recibida. Deteniendo miner...", signum)
    _shutdown = True


def _get_language(path: str) -> str | None:
    """Determina el lenguaje de un archivo por su extension."""
    if path.endswith(".py"):
        return "python"
    if path.endswith(".java"):
        return "java"
    return None


def _process_file(
    content: str,
    language: str,
) -> tuple[list[str], Counter[str]]:
    """Parsea un archivo y retorna nombres de funciones y conteo de palabras."""
    # Extraer nombres de funciones/metodos segun el lenguaje.
    if language == "python":
        names = extract_function_names(content)
    elif language == "java":
        names = extract_method_names(content)
    else:
        return [], Counter()

    # Dividir cada nombre en palabras.
    word_counts: Counter[str] = Counter()
    for name in names:
        words = split_identifier(name)
        word_counts.update(words)

    return names, word_counts


def _process_repo(
    github: GitHubClient,
    publisher: EventPublisher,
    repo: dict,
) -> None:
    """Procesa un repositorio completo: descarga, parsea y publica."""
    full_name = repo["full_name"]
    owner, repo_name = full_name.split("/")
    stars = repo.get("stargazers_count", 0)
    default_branch = repo.get("default_branch", "main")

    logger.info("Procesando %s (%d stars)...", full_name, stars)

    # Obtener el arbol de archivos.
    try:
        tree = github.get_file_tree(owner, repo_name, default_branch)
    except Exception:
        logger.warning("No se pudo obtener el arbol de %s.", full_name)
        publisher.publish_repo_processed(
            repo_full_name=full_name,
            repo_stars=stars,
            python_files=0,
            java_files=0,
            status="error_tree",
        )
        return

    # Filtrar archivos relevantes por extension.
    target_files = [
        item
        for item in tree
        if item.get("type") == "blob"
        and any(item["path"].endswith(ext) for ext in _TARGET_EXTENSIONS)
    ]

    py_count = 0
    java_count = 0

    for item in target_files:
        if _shutdown:
            break

        path = item["path"]
        language = _get_language(path)
        if not language:
            continue

        # Descargar contenido del archivo.
        content = github.get_file_content(owner, repo_name, path)
        if not content:
            continue

        # Parsear y extraer palabras.
        names, word_counts = _process_file(content, language)

        if language == "python":
            py_count += 1
        else:
            java_count += 1

        # Publicar evento word_batch.
        if word_counts:
            publisher.publish_word_batch(
                repo_full_name=full_name,
                repo_stars=stars,
                language=language,
                path=path,
                word_counts=word_counts,
                functions_found=len(names),
            )

    # Publicar evento repo_processed.
    publisher.publish_repo_processed(
        repo_full_name=full_name,
        repo_stars=stars,
        python_files=py_count,
        java_files=java_count,
        status="ok",
    )


def main() -> None:
    """Ejecuta el miner de forma continua."""
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    settings = load_settings()
    github = GitHubClient(settings)
    publisher = EventPublisher(settings)
    scheduler = RangeScheduler(min_stars=settings.min_stars)

    logger.info("Miner iniciado. Token GitHub: %s", "si" if settings.github_token else "no")

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
                logger.exception("Error buscando repos en %s pagina %d.", star_range.label, page)
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

                _process_repo(github, publisher, repo)
                scheduler.mark_processed(full_name)

                # Pausa corta entre repositorios para no saturar la API.
                time.sleep(1)

            page += 1
            # Limite de la API de GitHub Search: 1000 resultados (34 paginas de 30).
            if page > 34:
                break

    logger.info("Miner detenido limpiamente.")


if __name__ == "__main__":
    main()
