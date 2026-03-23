"""Tests para el consumer del visualizer."""

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

    def test_repo_processed_updates_stats_and_details(self) -> None:
        store = MagicMock()
        event = {
            "event_type": "repo_processed",
            "repo_full_name": "owner/repo",
            "repo_stars": "1000",
            "python_files": "5",
            "java_files": "3",
            "total_functions": "42",
            "total_words": "128",
            "top_word": "get",
            "status": "ok",
        }
        _process_event(store, event)
        store.update_stats.assert_called_once_with(
            repo_full_name="owner/repo",
            repo_stars=1000,
            python_files=5,
            java_files=3,
        )
        store.save_repo_detail.assert_called_once_with(
            repo_full_name="owner/repo",
            repo_stars=1000,
            python_files=5,
            java_files=3,
            total_functions=42,
            total_words=128,
            top_word="get",
            status="ok",
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

    def test_repo_processed_default_fields(self) -> None:
        """Los campos nuevos deben tener defaults seguros."""
        store = MagicMock()
        event = {
            "event_type": "repo_processed",
            "repo_full_name": "owner/repo",
            "repo_stars": "500",
            "python_files": "2",
            "java_files": "0",
            "status": "ok",
            # total_functions, total_words y top_word no estan presentes.
        }
        _process_event(store, event)
        store.save_repo_detail.assert_called_once()
        call_kwargs = store.save_repo_detail.call_args.kwargs
        assert call_kwargs["total_functions"] == 0
        assert call_kwargs["total_words"] == 0
        assert call_kwargs["top_word"] == ""
