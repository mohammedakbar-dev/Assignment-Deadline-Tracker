import logging
import os
from storage import AssignmentRepository, configure_logging, get_default_paths
from tracker import (
    add_assignment,
    days_until_due,
    delete_assignment,
    export_to_csv_string,
    generate_status_chart,
    get_summary_counts,
    mark_completed,
    refresh_overdue_statuses,
    search_assignments,
    sort_by_urgency,
)

logger = logging.getLogger(__name__)
PATHS = get_default_paths(os.path.dirname(os.path.abspath(__file__)))
PAGE_SIZE = 5


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


def print_page(page_items, page_num, total_pages):
    print(f"\n--- Page {page_num} of {total_pages} ---")
    print("ID       | Assignment                     | Course     | Due Date   | Status    | Timing")
    print("-" * 96)
    for r in page_items:
        print(
            f"{r['id']:<8} | {r['assignment'][:30]:<30} | {r['course'][:10]:<10} | "
            f"{r['due_date']:<10} | {r['status']:<9} | {format_timing(r)}"
        )
    print()


def print_records(records, page_size=PAGE_SIZE):
    if not records:
        print("No assignments found.\n")
        return

    safe_size = max(1, int(page_size))
    total_pages = (len(records) + safe_size - 1) // safe_size

    if total_pages == 1:
        print_page(records, 1, 1)
        return

    page_idx = 0
    while True:
        start = page_idx * safe_size
        end = start + safe_size
        print_page(records[start:end], page_idx + 1, total_pages)
        nav = input("[N]ext page, [P]revious page, [Q]uit view: ").strip().lower()
        if nav in ("n", "next", ""):
            if page_idx + 1 < total_pages:
                page_idx += 1
            else:
                break
        elif nav in ("p", "prev", "previous"):
            if page_idx > 0:
                page_idx -= 1
        elif nav in ("q", "quit"):
            break
        else:
            print("Enter N, P, or Q.")


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
    configure_logging(PATHS["log_file"])
    repo = AssignmentRepository(PATHS["data_file"])

    records, changed = refresh_overdue_statuses(repo.load())
    if changed:
        repo.save(records)

    while True:
        print("=== Assignment Deadline Tracker (CLI) ===")
        print("1. Add Assignment")
        print("2. View All (Urgency Sorted) / Search Assignments")
        print("3. Mark Assignment as Completed")
        print("4. Delete Assignment")
        print("5. View Summary")
        print("6. Export CSV Report")
        print("7. Export Status Chart (PNG)")
        print("8. Exit")

        choice = input("Select an option (1-8): ").strip()

        if choice == "1":
            title = input("Assignment Name: ")
            course = input("Course Code (default GENERAL): ")
            due = input("Due Date (YYYY-MM-DD): ")
            try:
                records, created = add_assignment(records, title, course, due)
                repo.save(records)
                print(f"Saved {created['id']}: {created['assignment']} [{created['status']}]\n")
            except (ValueError, OSError, TimeoutError) as exc:
                logger.error("Add assignment failed: %s", exc)
                print(f"Error: {exc}\n")

        elif choice == "2":
            query = input("Search keyword (or press Enter for all): ")
            matched = search_assignments(records, query)
            print_records(sort_by_urgency(matched))

        elif choice == "3":
            print_records(sort_by_urgency(records))
            rec_id = input("Enter Assignment ID to mark completed (e.g. ASN-001): ")
            try:
                records = mark_completed(records, rec_id)
                repo.save(records)
                print(f"Marked {rec_id.strip().upper()} as Completed.\n")
            except (KeyError, OSError, TimeoutError) as exc:
                logger.error("Mark completed failed: %s", exc)
                print(f"Error: {exc}\n")

        elif choice == "4":
            print_records(sort_by_urgency(records))
            rec_id = input("Enter Assignment ID to delete (e.g. ASN-001): ")
            try:
                records = delete_assignment(records, rec_id)
                repo.save(records)
                print(f"Deleted {rec_id.strip().upper()}.\n")
            except (KeyError, OSError, TimeoutError) as exc:
                logger.error("Delete assignment failed: %s", exc)
                print(f"Error: {exc}\n")

        elif choice == "5":
            print_summary(records)

        elif choice == "6":
            try:
                csv_text = export_to_csv_string(records)
                with open(PATHS["csv_file"], "w", encoding="utf-8") as f:
                    f.write(csv_text)
                print(f"Exported {len(records)} records to {PATHS['csv_file']}.\n")
            except OSError as exc:
                logger.error("CSV export failed: %s", exc)
                print(f"Export Error: {exc}\n")

        elif choice == "7":
            if generate_status_chart(records, PATHS["chart_file"]):
                print(f"Chart saved to {PATHS['chart_file']}.\n")
            else:
                print("Matplotlib not installed; install matplotlib to generate PNG chart.\n")

        elif choice == "8":
            print("Exiting tracker. Goodbye!")
            break

        else:
            print("Invalid option. Please choose 1 to 8.\n")


if __name__ == "__main__":
    main()