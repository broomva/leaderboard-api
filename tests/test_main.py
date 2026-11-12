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


def test_delete_existing_player_returns_204_with_empty_body() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    r = client.delete("/scores/ana")
    assert r.status_code == 204
    assert r.content == b""


def test_deleted_player_leaves_leaderboard() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.delete("/scores/ana")
    assert client.get("/leaderboard").json() == []


def test_delete_leaves_other_players_untouched() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    client.delete("/scores/ana")
    assert client.get("/leaderboard").json() == [{"name": "leo", "points": 30}]


def test_delete_unknown_name_returns_404() -> None:
    assert client.delete("/scores/ghost").status_code == 404


def test_second_delete_returns_404() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    assert client.delete("/scores/ana").status_code == 204
    assert client.delete("/scores/ana").status_code == 404


def test_readd_after_delete_starts_from_zero() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.delete("/scores/ana")
    r = client.post("/scores", json={"name": "ana", "points": 5})
    assert r.json() == {"name": "ana", "total": 5}


def test_delete_rejects_bad_names_like_post() -> None:
    too_long = "x" * 41
    assert client.delete(f"/scores/{too_long}").status_code == 422
    assert client.delete("/scores/").status_code == 422


def test_delete_name_containing_slash() -> None:
    client.post("/scores", json={"name": "a/b", "points": 10})
    assert client.delete("/scores/a/b").status_code == 204
    assert client.get("/leaderboard").json() == []


def test_failed_delete_does_not_create_player() -> None:
    assert client.delete("/scores/ghost").status_code == 404
    assert STORE.total("ghost") == 0
    assert client.get("/leaderboard").json() == []
