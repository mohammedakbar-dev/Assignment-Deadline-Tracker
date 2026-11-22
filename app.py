from datetime import date, datetime
import json
import os
import matplotlib.pyplot as plt
import streamlit as st

FILE_NAME = "assignments.json"

def load_assignments():
    if not os.path.exists(FILE_NAME):
        return []
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_assignments(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def update_overdue_status(data):
    today = date.today()
    changed = False
    for item in data:
        due = datetime.strptime(item["Due Date"], "%Y-%m-%d").date()
        if item["Status"] != "Completed" and due < today:
            if item["Status"] != "Overdue":
                item["Status"] = "Overdue"
                changed = True
    if changed:
        save_assignments(data)
    return data

def make_csv(data):
    lines = ["Assignment,Course,Due Date,Status"]
    for a in data:
        lines.append(f"\"{a['Assignment']}\",\"{a['Course']}\",\"{a['Due Date']}\",\"{a['Status']}\"")
    return "\n".join(lines)

st.title("Assignment Deadline Tracker")

assignments = update_overdue_status(load_assignments())

# Summary numbers at the top
total = len(assignments)
overdue_count = sum(1 for a in assignments if a["Status"] == "Overdue")
completed_count = sum(1 for a in assignments if a["Status"] == "Completed")

if overdue_count > 0:
    st.error(f"Warning: You have {overdue_count} overdue assignment(s)!")

c1, c2, c3 = st.columns(3)
c1.metric("Total", total)
c2.metric("Overdue", overdue_count)
c3.metric("Completed", completed_count)

# Form to add a new assignment
with st.form("add_form", clear_on_submit=True):
    title = st.text_input("Assignment Name")
    course = st.text_input("Course (e.g. CS101)")
    due_date = st.date_input("Due Date")
    submitted = st.form_submit_button("Add Assignment")

    if submitted:
        if title.strip() == "":
            st.error("Please enter an assignment name!")
        else:
            initial_status = "Overdue" if due_date < date.today() else "Pending"
            assignments.append({
                "Assignment": title.strip(),
                "Course": course.strip().upper() or "GENERAL",
                "Due Date": str(due_date),
                "Status": initial_status
            })
            save_assignments(assignments)
            st.success("Assignment saved!")
            st.rerun()

# Search & Table
if assignments:
    st.subheader("Your Assignments")
    search = st.text_input("Search by assignment name or course")

    if search.strip():
        q = search.strip().lower()
        shown = [
            a for a in assignments
            if q in a["Assignment"].lower() or q in a["Course"].lower()
        ]
    else:
        shown = assignments

    if shown:
        st.table(shown)
    else:
        st.info("No matching assignments.")

    # Complete or Delete an assignment
    options = [f"{i}: {a['Assignment']} ({a['Status']})" for i, a in enumerate(assignments)]
    chosen = st.selectbox("Pick an assignment", options)
    idx = int(chosen.split(":")[0])

    col_a, col_b = st.columns(2)
    if col_a.button("Mark as Completed"):
        assignments[idx]["Status"] = "Completed"
        save_assignments(assignments)
        st.rerun()

    if col_b.button("Delete Assignment"):
        assignments.pop(idx)
        save_assignments(assignments)
        st.rerun()

    # Simple Chart + CSV Download
    st.subheader("Status Chart & Export")
    statuses = ["Pending", "Overdue", "Completed"]
    counts = [sum(1 for a in assignments if a["Status"] == s) for s in statuses]

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(statuses, counts)
    ax.set_ylabel("Number of Assignments")
    st.pyplot(fig)

    st.download_button(
        label="Download CSV Report",
        data=make_csv(assignments),
        file_name="assignments.csv",
        mime="text/csv"
    )
else:
    st.info("No assignments saved yet. Add one above!")