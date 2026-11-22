from contextlib import contextmanager
import json
import logging
import os
import tempfile
from typing import Any, Dict, Iterator, List

logger = logging.getLogger(__name__)


def get_default_paths(base_dir: str) -> Dict[str, str]:
    root = os.path.abspath(base_dir)
    return {
        "base_dir": root,
        "data_file": resolve_safe_path(root, "assignments.json"),
        "csv_file": resolve_safe_path(root, "assignments.csv"),
        "chart_file": resolve_safe_path(root, "status_chart.png"),
        "log_file": resolve_safe_path(root, "tracker.log"),
    }


def configure_logging(log_file: str) -> None:
    root_logger = logging.getLogger()
    if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == os.path.abspath(log_file) for h in root_logger.handlers):
        root_logger.setLevel(logging.INFO)
        fh = logging.FileHandler(log_file, encoding="utf-8")
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
def atomic_write_stream(file_path: str) -> Iterator[Any]:
    if not file_path:
        raise ValueError("Storage file path cannot be empty.")
    parent_dir = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(parent_dir, exist_ok=True)
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