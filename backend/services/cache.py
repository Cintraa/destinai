import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


def _read(cache_file: Path) -> dict[str, Any]:
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def cache_get(cache_file: Path, key: str, ttl: int) -> Any | None:
    """Return the cached value, or None if missing or expired."""
    entry = _read(cache_file).get(key)
    if not isinstance(entry, dict) or "value" not in entry:
        return None
    if time.time() - entry.get("ts", 0) >= ttl:
        return None
    return entry["value"]


def cache_set(cache_file: Path, key: str, value: Any) -> None:
    data = _read(cache_file)
    data[key] = {"ts": time.time(), "value": value}
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError as e:
        logger.warning("Could not write cache %s: %s", cache_file, e)
