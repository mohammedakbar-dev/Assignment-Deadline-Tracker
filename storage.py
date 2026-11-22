from contextlib import contextmanager
import json
import logging
import os
import tempfile
import time
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


def get_default_paths(
    base_dir: str,
    data_name: str = "assignments.json",
    csv_name: str = "assignments.csv",
    chart_name: str = "status_chart.png",
    log_name: str = "tracker.log",
) -> Dict[str, str]:
    root = os.path.abspath(base_dir)
    env_data = os.environ.get("TRACKER_DATA_FILE")
    env_csv = os.environ.get("TRACKER_CSV_FILE")
    env_chart = os.environ.get("TRACKER_CHART_FILE")
    env_log = os.environ.get("TRACKER_LOG_FILE")

    return {
        "base_dir": root,
        "data_file": os.path.abspath(env_data) if env_data else resolve_safe_path(root, data_name),
        "csv_file": os.path.abspath(env_csv) if env_csv else resolve_safe_path(root, csv_name),
        "chart_file": os.path.abspath(env_chart) if env_chart else resolve_safe_path(root, chart_name),
        "log_file": os.path.abspath(env_log) if env_log else resolve_safe_path(root, log_name),
    }


def configure_logging(log_file: str) -> None:
    root_logger = logging.getLogger()
    target_abs = os.path.abspath(log_file)
    if not any(
        isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == target_abs
        for h in root_logger.handlers
    ):
        root_logger.setLevel(logging.INFO)
        fh = logging.FileHandler(target_abs, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        root_logger.addHandler(fh)


def resolve_safe_path(base_dir: str, file_name: str) -> str:
    if not file_name or not isinstance(file_name, str):
        raise ValueError("Invalid file name.")
    raw = file_name.strip()
    if not raw:
        raise ValueError("File name cannot be empty.")

    parts = raw.replace("\\", "/").split("/")
    if ".." in parts or os.path.isabs(raw):
        raise ValueError("Unsafe file path detected.")

    base_abs = os.path.abspath(base_dir)
    target_abs = os.path.abspath(os.path.join(base_abs, raw))
    if os.path.commonpath([base_abs, target_abs]) != base_abs:
        raise ValueError("Unsafe file path detected.")
    return target_abs


@contextmanager
def acquire_file_lock(file_path: str, timeout: float = 5.0, poll_interval: float = 0.05) -> Iterator[None]:
    lock_path = f"{os.path.abspath(file_path)}.lock"
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    deadline = time.monotonic() + timeout
    fd: Optional[int] = None

    while fd is None:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("utf-8"))
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for file lock on {file_path}")
            time.sleep(poll_interval)

    try:
        yield
    finally:
        try:
            if fd is not None:
                os.close(fd)
        finally:
            if os.path.exists(lock_path):
                try:
                    os.remove(lock_path)
                except OSError as exc:
                    logger.warning("Failed to remove lock file %s: %s", lock_path, exc)


@contextmanager
def atomic_write_stream(file_path: str) -> Iterator[Any]:
    if not file_path:
        raise ValueError("Storage file path cannot be empty.")
    parent_dir = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(parent_dir, exist_ok=True)

    with acquire_file_lock(file_path):
        fd, temp_path = tempfile.mkstemp(prefix=".tmp_asn_", suffix=".json", dir=parent_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                yield tmp_file
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.replace(temp_path, file_path)
        except (OSError, TypeError, ValueError) as exc:
            logger.error("Atomic write failed for %s: %s", file_path, exc)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError as cleanup_err:
                    logger.warning("Failed to remove temp file %s: %s", temp_path, cleanup_err)
            raise


def load_records(file_path: str) -> List[Dict[str, Any]]:
    if not file_path or not os.path.exists(file_path):
        return []
    with acquire_file_lock(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    logger.warning("Expected JSON list in %s; returning empty list.", file_path)
                    return []
                return data
        except json.JSONDecodeError as exc:
            backup_path = f"{file_path}.corrupt.bak"
            logger.warning("Corrupt JSON in %s (%s); backing up to %s.", file_path, exc, backup_path)
            try:
                os.replace(file_path, backup_path)
            except OSError as bak_err:
                logger.error("Failed to back up corrupt file %s: %s", file_path, bak_err)
            return []
        except OSError as exc:
            logger.error("Failed reading %s: %s", file_path, exc)
            return []


def save_records_atomic(file_path: str, records: List[Dict[str, Any]]) -> None:
    with atomic_write_stream(file_path) as tmp_file:
        json.dump(records, tmp_file, indent=4)
    logger.info("Saved %d records atomically to %s.", len(records), file_path)


class AssignmentRepository:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def load(self) -> List[Dict[str, Any]]:
        return load_records(self.file_path)

    def save(self, records: List[Dict[str, Any]]) -> None:
        save_records_atomic(self.file_path, records)