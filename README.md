# Assignment Deadline Tracker

An SRS-compliant **Assignment Deadline Tracker** built in **Python** with a modular **Command-Line Interface (CLI)**, unique assignment IDs (`ASN-XXX`), urgency-based sorting, automatic overdue tracking, atomic JSON persistence via a context manager, structured logging, CSV export, optional status chart export, and automated unit tests.

## Architecture & Design

- **`cli.py` (Presentation Layer):** Manages the interactive menu (`1–8`), user prompts, formatted tables with timing indicators, summary warnings, and chart/CSV export triggers.
- **`tracker.py` (Business Logic Layer):** Handles unique ID generation (`ASN-001`, `ASN-002`, ...), input validation, automatic overdue status updates, urgency sorting (`Overdue` -> `Pending` -> `Completed` by due date), keyword search, completion, deletion, summary counts, CSV formatting, and optional Matplotlib status chart generation.
- **`storage.py` (Data & Persistence Layer):** Provides centralized path configuration, path traversal protection (`resolve_safe_path`), `AssignmentRepository`, structured `logging` configuration, corrupt JSON backup (`.corrupt.bak`), and atomic JSON writes (`atomic_write_stream` using a temp file, `flush()`, `os.fsync()`, and `os.replace()`).
- **`test_tracker.py` (Automated Unit Tests):** Verifies unique IDs, validation errors, overdue transitions, urgency sorting, CRUD operations, CSV export, `AssignmentRepository`, atomic file writes, and path safety.

## Features

- **Unique Record Identifiers:** Auto-generates sequential IDs such as `ASN-001` and `ASN-002`.
- **Input Validation & Path Safety:** Validates non-empty titles and `YYYY-MM-DD` due dates, blocks unsafe path traversal, and handles invalid IDs or malformed inputs cleanly.
- **Automatic Overdue Detection & Urgency Sorting:** Updates past-due incomplete assignments to `Overdue` and orders views by urgency.
- **Search, Complete & Delete:** Filter records by ID, title, course, or status; mark items `Completed`; or delete records.
- **Summary, CSV & Optional Chart Export:** Displays `Total`, `Pending`, `Overdue`, and `Completed` counts, exports `assignments.csv`, and optionally exports `status_chart.png` when `matplotlib` is installed.
- **Atomic Persistence & Logging:** Uses temporary files, `os.fsync()`, and `os.replace()` to prevent partial writes, while logging events and errors to `tracker.log`.

## Project Structure

```text
assignment-deadline-tracker/
├── cli.py              # CLI presentation layer
├── tracker.py          # Business logic, urgency sorting & chart helper
├── storage.py          # Repository, atomic writes, path safety & logging
├── test_tracker.py     # Automated unit tests
└── README.md           # Project documentation