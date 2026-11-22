from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple


def parse_due_date(date_str: str) -> date:
    if not isinstance(date_str, str) or not date_str.strip():
        raise ValueError("Due date is required (YYYY-MM-DD).")
    return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()


def generate_next_id(records: List[Dict[str, Any]]) -> str:
    max_num = 0
    for rec in records:
        rec_id = str(rec.get("id", ""))
        if rec_id.startswith("ASN-"):
            suffix = rec_id.removeprefix("ASN-")
            if suffix.isdigit():
                max_num = max(max_num, int(suffix))
    return f"ASN-{max_num + 1:03d}"


def days_until_due(due_date_str: str, today: Optional[date] = None) -> int:
    ref_date = today or date.today()
    due = parse_due_date(due_date_str)
    return (due - ref_date).days


def refresh_overdue_statuses(
    records: List[Dict[str, Any]], today: Optional[date] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    ref_date = today or date.today()
    changed = False
    updated: List[Dict[str, Any]] = []

    for item in records:
        copy_item = dict(item)
        status = copy_item.get("status", "Pending")
        due_raw = copy_item.get("due_date", "")
        try:
            due = parse_due_date(due_raw)
            if status != "Completed" and due < ref_date and status != "Overdue":
                copy_item["status"] = "Overdue"
                changed = True
        except ValueError:
            pass
        updated.append(copy_item)

    return updated, changed


def add_assignment(
    records: List[Dict[str, Any]],
    title: str,
    course: str,
    due_date_str: str,
    today: Optional[date] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    clean_title = title.strip() if isinstance(title, str) else ""
    if not clean_title:
        raise ValueError("Assignment name cannot be empty.")

    due = parse_due_date(due_date_str)
    ref_date = today or date.today()
    clean_course = course.strip().upper() if isinstance(course, str) and course.strip() else "GENERAL"
    status = "Overdue" if due < ref_date else "Pending"

    new_record = {
        "id": generate_next_id(records),
        "assignment": clean_title,
        "course": clean_course,
        "due_date": due.isoformat(),
        "status": status,
    }

    return list(records) + [new_record], new_record


def search_assignments(records: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    q = query.strip().lower() if isinstance(query, str) else ""
    if not q:
        return list(records)
    return [
        r for r in records
        if q in str(r.get("id", "")).lower()
        or q in str(r.get("assignment", "")).lower()
        or q in str(r.get("course", "")).lower()
        or q in str(r.get("status", "")).lower()
    ]


def mark_completed(records: List[Dict[str, Any]], record_id: str) -> List[Dict[str, Any]]:
    target = record_id.strip().upper() if isinstance(record_id, str) else ""
    found = False
    updated: List[Dict[str, Any]] = []
    for r in records:
        item = dict(r)
        if str(item.get("id", "")).upper() == target:
            item["status"] = "Completed"
            found = True
        updated.append(item)
    if not found:
        raise KeyError(f"Assignment ID '{record_id}' not found.")
    return updated


def delete_assignment(records: List[Dict[str, Any]], record_id: str) -> List[Dict[str, Any]]:
    target = record_id.strip().upper() if isinstance(record_id, str) else ""
    filtered = [r for r in records if str(r.get("id", "")).upper() != target]
    if len(filtered) == len(records):
        raise KeyError(f"Assignment ID '{record_id}' not found.")
    return filtered


def get_summary_counts(records: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "total": len(records),
        "pending": sum(1 for r in records if r.get("status") == "Pending"),
        "overdue": sum(1 for r in records if r.get("status") == "Overdue"),
        "completed": sum(1 for r in records if r.get("status") == "Completed"),
    }


def export_to_csv_string(records: List[Dict[str, Any]]) -> str:
    lines = ["ID,Assignment,Course,Due Date,Status"]
    for r in records:
        lines.append(
            f"\"{r.get('id', '')}\",\"{r.get('assignment', '')}\",\"{r.get('course', '')}\",\"{r.get('due_date', '')}\",\"{r.get('status', '')}\""
        )
    return "\n".join(lines)