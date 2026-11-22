import os
import tempfile
import unittest
from datetime import date

from storage import AssignmentRepository, get_default_paths, load_records, resolve_safe_path, save_records_atomic
from tracker import (
    add_assignment,
    days_until_due,
    delete_assignment,
    export_to_csv_string,
    get_summary_counts,
    mark_completed,
    refresh_overdue_statuses,
    search_assignments,
    sort_by_urgency,
)


class TestAssignmentTracker(unittest.TestCase):
    def test_add_and_unique_id(self):
        today = date(2026, 11, 22)
        recs, r1 = add_assignment([], "Math HW 1", "math101", "2026-11-25", today=today)
        recs, r2 = add_assignment(recs, "Python Lab", "", "2026-11-20", today=today)

        self.assertEqual(r1["id"], "ASN-001")
        self.assertEqual(r1["course"], "MATH101")
        self.assertEqual(r1["status"], "Pending")

        self.assertEqual(r2["id"], "ASN-002")
        self.assertEqual(r2["course"], "GENERAL")
        self.assertEqual(r2["status"], "Overdue")

    def test_invalid_inputs_raise_value_error(self):
        with self.assertRaises(ValueError):
            add_assignment([], "   ", "CS101", "2026-11-25")
        with self.assertRaises(ValueError):
            add_assignment([], "Valid Title", "CS101", "22-11-2026")

    def test_overdue_refresh_complete_and_urgency_sort(self):
        today = date(2026, 11, 22)
        records = [
            {"id": "ASN-001", "assignment": "Future Task", "course": "CS101", "due_date": "2026-11-26", "status": "Pending"},
            {"id": "ASN-002", "assignment": "Late Task", "course": "CS101", "due_date": "2026-11-20", "status": "Pending"},
            {"id": "ASN-003", "assignment": "Done Task", "course": "CS101", "due_date": "2026-11-18", "status": "Completed"},
        ]
        refreshed, changed = refresh_overdue_statuses(records, today=today)
        self.assertTrue(changed)
        sorted_recs = sort_by_urgency(refreshed, today=today)
        self.assertEqual([r["id"] for r in sorted_recs], ["ASN-002", "ASN-001", "ASN-003"])

        completed = mark_completed(refreshed, "ASN-002")
        self.assertEqual(completed[1]["status"], "Completed")
        counts = get_summary_counts(completed)
        self.assertEqual(counts["completed"], 2)
        self.assertEqual(counts["overdue"], 0)

    def test_search_delete_and_days_left(self):
        today = date(2026, 11, 22)
        recs, _ = add_assignment([], "Physics Lab", "PHY101", "2026-11-25", today=today)
        self.assertEqual(days_until_due("2026-11-25", today=today), 3)
        self.assertEqual(len(search_assignments(recs, "phy101")), 1)
        self.assertEqual(len(search_assignments(recs, "missing")), 0)

        csv_out = export_to_csv_string(recs)
        self.assertIn("ASN-001", csv_out)

        after_del = delete_assignment(recs, "ASN-001")
        self.assertEqual(len(after_del), 0)

        with self.assertRaises(KeyError):
            delete_assignment(after_del, "ASN-999")

    def test_atomic_save_load_repository_and_path_safety(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = get_default_paths(tmpdir)
            repo = AssignmentRepository(paths["data_file"])
            recs, _ = add_assignment([], "Persist Test", "CS101", "2026-11-25", today=date(2026, 11, 22))
            repo.save(recs)
            self.assertEqual(repo.load(), recs)
            self.assertEqual(load_records(paths["data_file"]), recs)

            with self.assertRaises(ValueError):
                resolve_safe_path(tmpdir, "../../evil.json")


if __name__ == "__main__":
    unittest.main()