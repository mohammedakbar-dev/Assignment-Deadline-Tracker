# Assignment Deadline Tracker

An SRS-compliant **Assignment Deadline Tracker** built in **Python** with a modular **Command-Line Interface (CLI)**, unique assignment IDs (`ASN-XXX`), automatic overdue tracking, atomic JSON persistence, CSV export, and automated unit tests[span_1](start_span)[span_1](end_span).

## Architecture (3-Tier / Separation of Concerns)

- **`cli.py` (Presentation Layer):** Handles the interactive CLI menu, user prompts, formatted tables, and summary output[span_2](start_span)[span_2](end_span).
- **`tracker.py` (Business Logic Layer):** Handles unique ID generation (`ASN-001`, `ASN-002`, ...), input validation, due-date and overdue status updates, search/filtering, completion, deletion, summary counts, and CSV formatting.
- **`storage.py` (Data Layer):** Handles safe file path resolution, loading/saving JSON records, corrupt JSON backup, and atomic file writes using temporary files and `os.replace()`[span_3](start_span)[span_3](end_span).
- **`test_tracker.py` (Automated Tests):** Unit test suite verifying ID generation, validation, overdue transitions, CRUD operations, CSV export, path safety, and atomic persistence[span_4](start_span)[span_4](end_span).

## Features

- **Unique Record Identifiers:** Auto-generates sequential IDs such as `ASN-001` and `ASN-002`.
- **Input Validation & Error Handling:** Validates non-empty assignment names, `YYYY-MM-DD` due dates, and valid record IDs without crashing.
- **Automatic Overdue Detection:** Compares due dates against the current date and automatically updates incomplete past-due tasks to `Overdue`.
- **Search & Status Management:** Search assignments by ID, name, course, or status; mark tasks as `Completed`; or delete records.
- **Summary & CSV Export:** Displays counts for `Total`, `Pending`, `Overdue`, and `Completed` assignments, plus exports records to `assignments.csv`.
- **Atomic Persistence:** Uses temporary files, `os.fsync()`, and `os.replace()` to protect `assignments.json` against partial writes or corruption.

## Project Structure

```text
assignment-deadline-tracker/
├── cli.py              # CLI presentation layer
├── tracker.py          # Business logic and validation
├── storage.py          # Atomic JSON storage and path safety
├── test_tracker.py     # Automated unit tests
└── README.md           # Project documentation