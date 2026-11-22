import json
import os
import tempfile
from typing import Any, Dict, List


def resolve_safe_path(base_dir: str, file_name: str) -> str:
    if not file_name or not isinstance(file_name, str):
        raise ValueError("Invalid file name.")
    raw = file_name.strip()
    if not raw:
        raise ValueError("File name cannot be empty.")

    normalized_parts = raw.replace("\\", "/").split("/")
    if ".." in normalized_parts or os.path.isabs(raw):
        raise ValueError("Unsafe file path detected.")

    base_abs = os.path.abspath(base_dir)
    target_abs = os.path.abspath(os.path.join(base_abs, raw))
    if os.path.commonpath([base_abs, target_abs]) != base_abs:
        raise ValueError("Unsafe file path detected.")
    return target_abs


def load_records(file_path: str) -> List[Dict[str, Any]]:
    if not file_path or not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        corrupt_backup = f"{file_path}.corrupt.bak"
        try:
            os.replace(file_path, corrupt_backup)
        except OSError:
            pass
        return []
    except OSError:
        return []


def save_records_atomic(file_path: str, records: List[Dict[str, Any]]) -> None:
    if not file_path:
        raise ValueError("Storage file path cannot be empty.")
    parent_dir = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(parent_dir, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(prefix=".tmp_asn_", suffix=".json", dir=parent_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(records, tmp_file, indent=4)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise