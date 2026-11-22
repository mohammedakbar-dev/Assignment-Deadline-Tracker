# Assignment Deadline Tracker

An interactive web-based **Assignment Deadline Tracker** built with **Python** and **Streamlit** to help students manage coursework, track overdue tasks automatically, visualize status counts, and export reports.

## Features

- **Add & Validate Assignments:** Add assignments with name, course code (defaults to `GENERAL` if left blank), and due date, with validation against empty assignment names.
- **Automatic Overdue Detection:** Compares each assignment's due date against the current date (`datetime`) and automatically marks past-due incomplete tasks as `Overdue` with a warning banner.
- **Local Persistence (`assignments.json`):** Saves, loads, updates, and deletes assignments locally in `assignments.json` so changes remain across browser refreshes and restarts.
- **Search & Filter:** Filter assignments live by assignment name or course code.
- **Status Updates & Deletion:** Mark any assignment as `Completed` or delete an assignment from the list.
- **Summary Metrics & Bar Chart:** View `Total`, `Overdue`, and `Completed` counts at the top along with a `Matplotlib` bar chart comparing `Pending`, `Overdue`, and `Completed` items.
- **CSV Export:** Download all assignment records as `assignments.csv`.

## Tech Stack & Libraries

- **Python** (`datetime`, `json`, `os`)
- **Streamlit** (interactive web UI)
- **Matplotlib** (status bar chart)
- **VS Code** & local browser (`localhost:8501`)

## Project Structure

```text
assignment-deadline-tracker/
├── app.py              # Main Streamlit application
├── assignments.json    # Local JSON storage (created automatically on save)
└── README.md           # Project documentation