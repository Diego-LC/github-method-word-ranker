"""Tests para el consumer del visualizer.

Los tests que requieren Redis se marcan con pytest.mark.skipif
para evitar fallos cuando Redis no esta disponible.
"""

import json
from unittest.mock import MagicMock, patch

from visualizer.consumer import _process_event


class TestProcessEvent:
    """Tests para el procesamiento de eventos individuales."""

    def test_word_batch_increments_words(self) -> None:
        store = MagicMock()
        word_counts = {"get": 3, "user": 2}
        event = {
            "event_type": "word_batch",
            "repo_full_name": "owner/repo",
            "word_counts_json": json.dumps(word_counts),
            "path": "src/main.py",
        }
        _process_event(store, event)
        store.increment_words.assert_called_once_with({"get": 3, "user": 2})

    def test_repo_processed_updates_stats(self) -> None:
        store = MagicMock()
        event = {
            "event_type": "repo_processed",
            "repo_full_name": "owner/repo",
            "repo_stars": "1000",
            "python_files": "5",
            "java_files": "3",
            "status": "ok",
        }
        _process_event(store, event)
        store.update_stats.assert_called_once_with(
            repo_full_name="owner/repo",
            repo_stars=1000,
            python_files=5,
            java_files=3,
        )

    def test_unknown_event_type_does_not_crash(self) -> None:
        store = MagicMock()
        event = {"event_type": "unknown_type"}
        _process_event(store, event)
        store.increment_words.assert_not_called()
        store.update_stats.assert_not_called()

    def test_invalid_json_does_not_crash(self) -> None:
        store = MagicMock()
        event = {
            "event_type": "word_batch",
            "word_counts_json": "not valid json{{{",
        }
        _process_event(store, event)
        store.increment_words.assert_not_called()
