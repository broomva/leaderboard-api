"""Audit log for accepted POST /scores requests. Logs validated fields only, never the raw body or headers."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_PATH = "logs/requests.log"


def log_path() -> Path:
    return Path(os.environ.get("REQUESTS_LOG_PATH") or DEFAULT_LOG_PATH)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def log_score(name: str, points: int) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"ts": utc_timestamp(), "name": name, "points": points})
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
