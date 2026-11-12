import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import STORE

client = TestClient(app)


def setup_function() -> None:
    STORE.reset()


def read_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def test_one_line_per_accepted_post(requests_log: Path) -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    lines = requests_log.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert set(entry) == {"ts", "name", "points"}
    assert entry["name"] == "ana"
    assert entry["points"] == 10


def test_timestamp_is_utc_iso_with_z(requests_log: Path) -> None:
    before = datetime.now(timezone.utc)
    client.post("/scores", json={"name": "ana", "points": 10})
    after = datetime.now(timezone.utc)
    ts = read_entries(requests_log)[0]["ts"]
    assert ts.endswith("Z")
    parsed = datetime.fromisoformat(ts[:-1] + "+00:00")
    assert before <= parsed <= after


def test_each_post_appends_a_line_in_order(requests_log: Path) -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    entries = read_entries(requests_log)
    assert [(e["name"], e["points"]) for e in entries] == [("ana", 10), ("leo", 30)]


def test_extra_body_fields_are_not_logged(requests_log: Path) -> None:
    client.post("/scores", json={"name": "ana", "points": 10, "token": "x"})
    raw = requests_log.read_text()
    assert "token" not in raw
    assert set(read_entries(requests_log)[0]) == {"ts", "name", "points"}


def test_headers_are_not_logged(requests_log: Path) -> None:
    client.post(
        "/scores",
        json={"name": "ana", "points": 10},
        headers={"X-Secret": "abc123"},
    )
    raw = requests_log.read_text()
    assert "abc123" not in raw
    assert "X-Secret" not in raw


def test_invalid_requests_write_nothing(requests_log: Path) -> None:
    r = client.post("/scores", json={"name": "", "points": 10})
    assert r.status_code == 422
    assert read_entries(requests_log) == []


def test_path_is_configurable_and_parent_is_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "nested" / "dir" / "req.log"
    monkeypatch.setenv("REQUESTS_LOG_PATH", str(target))
    r = client.post("/scores", json={"name": "ana", "points": 10})
    assert r.status_code == 200
    assert len(read_entries(target)) == 1


def test_response_is_unchanged(requests_log: Path) -> None:
    r = client.post("/scores", json={"name": "ana", "points": 10})
    assert r.json() == {"name": "ana", "total": 10}
