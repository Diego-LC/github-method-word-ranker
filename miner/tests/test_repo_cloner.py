"""Tests para el clonador de repositorios."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from miner.repo_cloner import find_source_files, cleanup_clone


class TestFindSourceFiles:
    """Tests para la busqueda de archivos fuente."""

    def test_finds_python_files(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("pass")
        files = find_source_files(tmp_path)
        assert len(files) == 2
        assert all(f.suffix == ".py" for f in files)

    def test_finds_java_files(self, tmp_path: Path) -> None:
        (tmp_path / "Main.java").write_text("class Main {}")
        files = find_source_files(tmp_path)
        assert len(files) == 1
        assert files[0].suffix == ".java"

    def test_finds_nested_files(self, tmp_path: Path) -> None:
        sub = tmp_path / "src" / "pkg"
        sub.mkdir(parents=True)
        (sub / "App.java").write_text("class App {}")
        (sub / "helper.py").write_text("pass")
        files = find_source_files(tmp_path)
        assert len(files) == 2

    def test_excludes_git_dir(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git" / "objects"
        git_dir.mkdir(parents=True)
        (git_dir / "script.py").write_text("pass")
        (tmp_path / "real.py").write_text("pass")
        files = find_source_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "real.py"

    def test_excludes_node_modules(self, tmp_path: Path) -> None:
        nm = tmp_path / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.py").write_text("pass")
        (tmp_path / "app.py").write_text("pass")
        files = find_source_files(tmp_path)
        assert len(files) == 1

    def test_excludes_venv(self, tmp_path: Path) -> None:
        venv = tmp_path / "venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "lib.py").write_text("pass")
        files = find_source_files(tmp_path)
        assert len(files) == 0

    def test_empty_repo(self, tmp_path: Path) -> None:
        files = find_source_files(tmp_path)
        assert files == []


class TestCleanupClone:
    """Tests para la limpieza de clones."""

    def test_removes_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "clone"
        target.mkdir()
        (target / "file.txt").write_text("data")
        cleanup_clone(target)
        assert not target.exists()
