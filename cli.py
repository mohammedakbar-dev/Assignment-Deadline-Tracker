import os
from storage import load_records, resolve_safe_path, save_records_atomic
from tracker import (
    add_assignment,
    days_until_due,
    delete_assignment,
    export_to_csv_string,
    get_summary_counts,
    mark_completed,
    refresh_overdue_statuses,
    search_assignments,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = resolve_safe_path(BASE_DIR, "assignments.json")
CSV_FILE = resolve_safe_path(BASE_DIR, "assignments.csv")


def format_timing(record):
    try:
        diff = days_until_due(record["due_date"])
        if record.get("status") == "Completed":
            return "Done"
        if diff < 0:
            return f"{abs(diff)}d late"
        if diff == 0:
            return "Due today"
        return f"{diff}d left"
    except ValueError:
        return "Invalid date"


def print_records(records):
    if not records:
        print("No assignments found.\n")
        return
    print("\nID       | Assignment                     | Course     | Due Date   | Status    | Timing")
    print("-" * 96)
    for r in records:
        print(
            f"{r['id']:<8} | {r['assignment'][:30]:<30} | {r['course'][:10]:<10} | "
            f"{r['due_date']:<10} | {r['status']:<9} | {format_timing(r)}"
        )
    print()


def print_summary(records):
    counts = get_summary_counts(records)
    print(
        f"\nSummary -> Total: {counts['total']} | Pending: {counts['pending']} | "
        f"Overdue: {counts['overdue']} | Completed: {counts['completed']}"
    )
    if counts["overdue"] > 0:
        print(f"WARNING: You have {counts['overdue']} overdue assignment(s)!")
    print()


def main():
    records, changed = refresh_overdue_statuses(load_records(DATA_FILE))
    if changed:
        save_records_atomic(DATA_FILE, records)

    while True:
        print("=== Assignment Deadline Tracker (CLI) ===")
        print("1. Add Assignment")
        print("2. View All / Search Assignments")
        print("3. Mark Assignment as Completed")
        print("4. Delete Assignment")
        print("5. View Summary")
        print("6. Export CSV Report")
        print("7. Exit")

        choice = input("Select an option (1-7): ").strip()

        if choice == "1":
            title = input("Assignment Name: ")
            course = input("Course Code (default GENERAL): ")
            due = input("Due Date (YYYY-MM-DD): ")
            try:
                records, created = add_assignment(records, title, course, due)
                save_records_atomic(DATA_FILE, records)
                print(f"Saved {created['id']}: {created['assignment']} [{created['status']}]\n")
            except (ValueError, OSError) as exc:
                print(f"Error: {exc}\n")

        elif choice == "2":
            query = input("Search keyword (or press Enter for all): ")
            print_records(search_assignments(records, query))

        elif choice == "3":
            print_records(records)
            rec_id = input("Enter Assignment ID to mark completed (e.g. ASN-001): ")
            try:
                records = mark_completed(records, rec_id)
                save_records_atomic(DATA_FILE, records)
                print(f"Marked {rec_id.strip().upper()} as Completed.\n")
            except (KeyError, OSError) as exc:
                print(f"Error: {exc}\n")

        elif choice == "4":
            print_records(records)
            rec_id = input("Enter Assignment ID to delete (e.g. ASN-001): ")
            try:
                records = delete_assignment(records, rec_id)
                save_records_atomic(DATA_FILE, records)
                print(f"Deleted {rec_id.strip().upper()}.\n")
            except (KeyError, OSError) as exc:
                print(f"Error: {exc}\n")

        elif choice == "5":
            print_summary(records)

        elif choice == "6":
            try:
                csv_text = export_to_csv_string(records)
                with open(CSV_FILE, "w", encoding="utf-8") as f:
                    f.write(csv_text)
                print(f"Exported {len(records)} records to {CSV_FILE}.\n")
            except OSError as exc:
                print(f"Export Error: {exc}\n")

        elif choice == "7":
            print("Exiting tracker. Goodbye!")
            break

        else:
            print("Invalid option. Please choose 1 to 7.\n")


if __name__ == "__main__":
    main()