from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def requests_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "requests.log"
    monkeypatch.setenv("REQUESTS_LOG_PATH", str(path))
    return path
