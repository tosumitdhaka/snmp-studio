"""
core/stats_store.py
~~~~~~~~~~~~~~~~~~~
Lightweight, file-backed stats store shared by all backend modules.

All modules (simulator, traps, walker, mibs) write events here via
increment(), set_field(), or update_module(). The /api/stats router
reads from here to serve dashboard-facing stats.

File location: data/configs/stats.json  (volume-mounted, persists across restarts)

Thread safety:
  - API process: _lock (threading.Lock) guards all reads + writes.
  - Worker subprocesses (snmp_simulator, trap_receiver): they write directly
    to the JSON file using atomic rename (tempfile + os.replace) via
    worker_increment() / worker_set_field() / worker_update_fields() to avoid
    partial-write corruption.
  - Cross-process safety relies on os.replace() being atomic on POSIX.
"""

import json
import os
import tempfile
from copy import deepcopy
from threading import Lock
from typing import Any
from core.config import settings

_lock = Lock()

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
# All keys that every module tracks. New keys added here will automatically
# appear in existing stats.json files on the next load() (merge-with-defaults).
#
# NOT included (runtime-enriched only, never persisted):
#   mibs: loaded_mibs, failed_mibs, total_mibs  <- from mib_service.get_status()
#   simulator: running, pid, port, community     <- from SimulatorManager.status()
#   traps: running, pid                          <- from trap_manager.get_status()
# ---------------------------------------------------------------------------

DEFAULT_STATS: dict = {
    "simulator": {
        "start_count": 0,
        "stop_count": 0,
        "restart_count": 0,
        "oids_loaded": 0,            # OID instances generated on last start
        "total_oids_simulated": 0,   # cumulative OIDs served (GET + GETNEXT)
        "snmp_requests_served": 0,   # cumulative SNMP requests handled
        "simulator_run_seconds": 0,  # cumulative seconds simulator was running
        "last_request_at": None,     # ISO timestamp of last SNMP request handled
    },
    "traps": {
        "receiver_start_count": 0,
        "receiver_stop_count": 0,
        "traps_received_total": 0,   # cumulative traps received (worker)
        "traps_sent_total": 0,       # cumulative traps sent via POST /traps/send
        "traps_cleared_count": 0,
        "receiver_run_seconds": 0,   # cumulative seconds receiver was running
    },
    "walker": {
        "walks_executed": 0,
        "walks_failed": 0,
        "oids_returned": 0,          # OID count from last successful walk
    },
    "mibs": {
        "reload_count": 0,
        "upload_count": 0,           # cumulative files uploaded
        "delete_count": 0,
    },
}

VALID_MODULES = set(DEFAULT_STATS.keys())


# ---------------------------------------------------------------------------
# Internal helpers  (call only while _lock is held)
# ---------------------------------------------------------------------------

def _load_unsafe() -> dict:
    """Load stats.json and merge with DEFAULT_STATS. No lock acquired."""
    if not settings.STATS_FILE.exists():
        return deepcopy(DEFAULT_STATS)
    try:
        with open(settings.STATS_FILE, "r") as f:
            on_disk = json.load(f)
        merged = deepcopy(DEFAULT_STATS)
        for module, values in on_disk.items():
            if module in merged and isinstance(values, dict):
                merged[module].update(values)
        return merged
    except Exception:
        return deepcopy(DEFAULT_STATS)


def _save_unsafe(stats: dict) -> None:
    """Write stats atomically via tempfile + os.replace. No lock acquired."""
    stats_path = settings.STATS_FILE
    os.makedirs(stats_path.parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=stats_path.parent, prefix="stats_", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(stats, f, indent=2, default=str)
        os.replace(tmp_path, stats_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Public API  (routers + services inside the API process)
# ---------------------------------------------------------------------------

def load() -> dict:
    """Return a full copy of current stats merged with defaults."""
    with _lock:
        return _load_unsafe()


def save(stats: dict) -> None:
    """Overwrite entire stats file. Prefer update_module() for partial updates."""
    with _lock:
        _save_unsafe(stats)


def increment(module: str, key: str, by: int = 1) -> None:
    """Atomically increment a single integer counter."""
    with _lock:
        stats = _load_unsafe()
        stats.setdefault(module, {})
        stats[module][key] = stats[module].get(key, 0) + by
        _save_unsafe(stats)


def set_field(module: str, key: str, value: Any) -> None:
    """Atomically set a single field."""
    with _lock:
        stats = _load_unsafe()
        stats.setdefault(module, {})
        stats[module][key] = value
        _save_unsafe(stats)


def update_module(module: str, updates: dict) -> None:
    """
    Atomically apply multiple field updates for one module in a single
    read-modify-write cycle. Preferred when updating counter + runtime
    value together (e.g. stop_count + simulator_run_seconds).
    """
    with _lock:
        stats = _load_unsafe()
        stats.setdefault(module, {})
        stats[module].update(updates)
        _save_unsafe(stats)


def reset() -> None:
    """Reset all stats to zero defaults."""
    with _lock:
        _save_unsafe(deepcopy(DEFAULT_STATS))


# ---------------------------------------------------------------------------
# Worker-safe helpers  (subprocess workers: snmp_simulator, trap_receiver)
# ---------------------------------------------------------------------------
# Workers run as separate processes and cannot share the in-process _lock.
# They use the same atomic-rename pattern. Cross-process safety relies on
# os.replace() being atomic on POSIX (Linux/macOS).

def _worker_load(stats_file: str) -> dict:
    """Load stats from file in worker context. Returns DEFAULT_STATS copy on any error."""
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return deepcopy(DEFAULT_STATS)


def _worker_save(stats_file: str, stats: dict) -> None:
    """Atomically write stats in worker context."""
    parent = os.path.dirname(stats_file) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix="stats_", suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(stats, f, indent=2, default=str)
    os.replace(tmp, stats_file)


def worker_increment(stats_file: str, module: str, key: str, by: int = 1) -> None:
    """Increment a counter from a worker subprocess."""
    try:
        stats = _worker_load(stats_file)
        stats.setdefault(module, {})
        stats[module][key] = stats[module].get(key, 0) + by
        _worker_save(stats_file, stats)
    except Exception:
        pass  # never crash a worker over stats


def worker_set_field(stats_file: str, module: str, key: str, value: Any) -> None:
    """Set a single field from a worker subprocess."""
    try:
        stats = _worker_load(stats_file)
        stats.setdefault(module, {})
        stats[module][key] = value
        _worker_save(stats_file, stats)
    except Exception:
        pass


def worker_update_module(stats_file: str, module: str, updates: dict) -> None:
    """Atomically apply multiple field updates from a worker subprocess."""
    try:
        stats = _worker_load(stats_file)
        stats.setdefault(module, {})
        stats[module].update(updates)
        _worker_save(stats_file, stats)
    except Exception:
        pass


def worker_update_fields(
    stats_file: str,
    module: str,
    increments: dict = None,
    sets: dict = None,
) -> None:
    """
    Atomically apply counter increments AND absolute field sets in one
    read-modify-write cycle. Preferred over calling worker_increment +
    worker_set_field separately (halves the number of file writes).

      increments: {key: delta}   – adds delta to the stored counter value
      sets:       {key: value}   – overwrites the field directly (timestamps, gauges)
    """
    try:
        stats = _worker_load(stats_file)
        stats.setdefault(module, {})
        if increments:
            for key, delta in increments.items():
                stats[module][key] = stats[module].get(key, 0) + delta
        if sets:
            stats[module].update(sets)
        _worker_save(stats_file, stats)
    except Exception:
        pass  # never crash a worker over stats
