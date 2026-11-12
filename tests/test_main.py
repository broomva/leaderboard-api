from fastapi.testclient import TestClient

from app.main import app
from app.store import STORE

client = TestClient(app)


def setup_function() -> None:
    STORE.reset()


def test_health() -> None:
    assert client.get("/health").json() == {"ok": True}


def test_add_score_accumulates() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    r = client.post("/scores", json={"name": "ana", "points": 5})
    assert r.json() == {"name": "ana", "total": 15}


def test_leaderboard_sorted() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    top = client.get("/leaderboard").json()
    assert top[0] == {"name": "leo", "points": 30}


def test_reading_a_total_does_not_add_a_player() -> None:
    assert STORE.total("ghost") == 0
    assert client.get("/leaderboard").json() == []


def test_rejects_bad_input() -> None:
    assert client.post("/scores", json={"name": "", "points": 10}).status_code == 422
    assert client.get("/leaderboard?limit=0").status_code == 422


def test_stats_empty_store_returns_zeros() -> None:
    r = client.get("/stats").json()
    assert r == {"players": 0, "average": 0.0}
    assert isinstance(r["average"], float)


def test_stats_player_count_and_average() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    assert client.get("/stats").json() == {"players": 2, "average": 20.0}


def test_stats_average_is_true_float_division() -> None:
    client.post("/scores", json={"name": "ana", "points": 1})
    client.post("/scores", json={"name": "leo", "points": 2})
    assert client.get("/stats").json() == {"players": 2, "average": 1.5}


def test_stats_repeated_scores_count_once_per_player() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "ana", "points": 5})
    client.post("/scores", json={"name": "leo", "points": 0})
    assert client.get("/stats").json() == {"players": 2, "average": 7.5}


def test_stats_does_not_add_players() -> None:
    assert client.get("/stats").json() == {"players": 0, "average": 0.0}
    assert client.get("/leaderboard").json() == []
