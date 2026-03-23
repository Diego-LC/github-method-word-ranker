"""Cliente HTTP para la API de GitHub.

Provee acceso a:
- Busqueda de repositorios ordenados por stars (descendente).
- Arbol recursivo de archivos de un repositorio.
- Contenido raw de archivos individuales.

Incluye manejo de rate limiting con backoff exponencial.
"""

from __future__ import annotations

import base64
import logging
import time
from typing import Any

import requests

from miner.config import Settings

logger = logging.getLogger(__name__)

# Tiempo de espera base entre reintentos (segundos).
_BASE_BACKOFF = 5
_MAX_RETRIES = 5


class GitHubClient:
    """Cliente para la REST API v3 de GitHub."""

    API_BASE = "https://api.github.com"

    def __init__(self, settings: Settings) -> None:
        self._session = requests.Session()
        self._session.headers.update(settings.github_headers)
        self._settings = settings

    # ------------------------------------------------------------------
    # Busqueda de repositorios
    # ------------------------------------------------------------------

    def search_repos(
        self,
        stars_range: str,
        page: int = 1,
        per_page: int | None = None,
    ) -> list[dict[str, Any]]:
        """Busca repositorios por rango de stars.

        Args:
            stars_range: Rango de stars (ej: ">10000", "5000..10000").
            page: Pagina de resultados.
            per_page: Resultados por pagina.

        Returns:
            Lista de diccionarios con datos de cada repositorio.
        """
        per_page = per_page or self._settings.repos_per_page
        params = {
            "q": f"stars:{stars_range}",
            "sort": "stars",
            "order": "desc",
            "page": page,
            "per_page": per_page,
        }
        data = self._get(f"{self.API_BASE}/search/repositories", params=params)
        return data.get("items", [])

    # ------------------------------------------------------------------
    # Arbol de archivos
    # ------------------------------------------------------------------

    def get_file_tree(
        self, owner: str, repo: str, default_branch: str = "main"
    ) -> list[dict[str, Any]]:
        """Obtiene el arbol recursivo de archivos del repositorio.

        Intenta con la rama proporcionada y hace fallback a 'master'.
        """
        url = f"{self.API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}"
        try:
            data = self._get(url, params={"recursive": "1"})
            return data.get("tree", [])
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                # Intentar con 'master' como fallback.
                if default_branch != "master":
                    return self.get_file_tree(owner, repo, "master")
            raise

    # ------------------------------------------------------------------
    # Contenido de archivos
    # ------------------------------------------------------------------

    def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        """Descarga el contenido de un archivo via la API de contenidos.

        Retorna el contenido decodificado como string, o None si falla.
        """
        url = f"{self.API_BASE}/repos/{owner}/{repo}/contents/{path}"
        try:
            data = self._get(url)
        except requests.HTTPError:
            logger.debug("No se pudo obtener %s/%s/%s", owner, repo, path)
            return None

        encoding = data.get("encoding", "")
        content = data.get("content", "")

        if encoding == "base64" and content:
            try:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            except Exception:
                return None

        return None

    # ------------------------------------------------------------------
    # Request con retry
    # ------------------------------------------------------------------

    def _get(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Realiza un GET con reintentos y manejo de rate limiting."""
        for attempt in range(1, _MAX_RETRIES + 1):
            resp = self._session.get(url, params=params, timeout=30)

            # Rate limit secundario o primario.
            if resp.status_code in (403, 429):
                wait = self._rate_limit_wait(resp, attempt)
                logger.warning(
                    "Rate limit alcanzado (%s). Esperando %.0fs (intento %d/%d).",
                    resp.status_code,
                    wait,
                    attempt,
                    _MAX_RETRIES,
                )
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

        # Si agotamos reintentos, forzar raise del ultimo response.
        resp.raise_for_status()
        return {}  # pragma: no cover

    @staticmethod
    def _rate_limit_wait(resp: requests.Response, attempt: int) -> float:
        """Calcula el tiempo de espera basado en headers de rate limit."""
        # Header Retry-After (rate limit secundario).
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            return float(retry_after)

        # Header x-ratelimit-reset (rate limit primario).
        reset = resp.headers.get("x-ratelimit-reset")
        if reset:
            wait = float(reset) - time.time()
            if wait > 0:
                return min(wait, 300)  # Maximo 5 minutos.

        # Backoff exponencial como fallback.
        return _BASE_BACKOFF * (2 ** (attempt - 1))
