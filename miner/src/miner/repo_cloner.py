"""Clonador de repositorios de GitHub.

Realiza shallow clones (--depth 1) a directorios temporales
para parsear archivos localmente sin consumir quota de la API REST.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def clone_repo(clone_url: str, clone_base_dir: str | None = None) -> Path | None:
    """Clona un repositorio con depth=1 a un directorio temporal.

    Args:
        clone_url: URL HTTPS del repositorio (ej: https://github.com/owner/repo.git).
        clone_base_dir: Directorio base para clones. Si es None, usa el temp del sistema.

    Returns:
        Path al directorio clonado, o None si fallo.
    """
    try:
        tmpdir = tempfile.mkdtemp(dir=clone_base_dir, prefix="miner_")
        result = subprocess.run(
            [
                "git", "clone",
                "--depth", "1",
                "--single-branch",
                "--quiet",
                clone_url,
                tmpdir,
            ],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutos maximo.
        )
        if result.returncode != 0:
            logger.warning(
                "Error clonando %s: %s", clone_url, result.stderr.strip()
            )
            cleanup_clone(tmpdir)
            return None

        logger.info("Clonado %s -> %s", clone_url, tmpdir)
        return Path(tmpdir)

    except subprocess.TimeoutExpired:
        logger.warning("Timeout clonando %s", clone_url)
        cleanup_clone(tmpdir)
        return None
    except Exception:
        logger.exception("Error inesperado clonando %s", clone_url)
        return None


def cleanup_clone(clone_path: str | Path) -> None:
    """Elimina el directorio de un clon temporal."""
    try:
        shutil.rmtree(clone_path, ignore_errors=True)
        logger.debug("Limpiado %s", clone_path)
    except Exception:
        logger.warning("No se pudo limpiar %s", clone_path)


def find_source_files(repo_path: Path) -> list[Path]:
    """Busca archivos .py y .java en el repositorio clonado.

    Excluye directorios comunes de dependencias y build.
    """
    exclude_dirs = {
        ".git", "node_modules", "vendor", "venv", ".venv",
        "__pycache__", ".tox", "build", "dist", ".eggs",
        "target",  # Maven/Gradle
    }

    source_files: list[Path] = []
    for ext in ("*.py", "*.java"):
        for f in repo_path.rglob(ext):
            # Excluir archivos en directorios no deseados.
            if not any(part in exclude_dirs for part in f.parts):
                source_files.append(f)

    return source_files
