# 🐝 BeePlan - University Course Scheduling System

**BeePlan** is a desktop application developed to automate the course scheduling process for Computer Engineering departments. It utilizes **Constraint Satisfaction Problems (CSP)** and a **Backtracking Algorithm** to generate conflict-free timetables, considering instructor availability, room capacities, and pedagogical constraints (Theory > Lab).

---

## 📂 Repository Structure

This repository is organized as follows:

````text
BeePlan/
├── src/                # Source Codes (Python & PyQt5)
│   ├── main.py         # Entry point of the application
│   ├── gui.py          # User Interface logic (Clean Code & Error Handling)
│   ├── algorithm.py    # Backtracking logic & Constraint Checks
│   ├── models.py       # Data classes (Course, Room, Instructor)
│   └── input_data.json # JSON-based database
│
├── docs/               # Documentation & Diagrams
│   ├── UML_Class_Diagram.png
│   ├── Activity_Diagram.png
│   └── Project_Report.pdf
│
├── video/              # Final Presentation
│   └── Demo_Video.mp4  # User scenario and features walkthrough
│
└── README.md           # Project Documentation
---

## 🚀 1.Features & Capabilities

* **Automated Scheduling:** Generates a full weekly schedule with a single click.
* **Constraint Handling:**
    * **Hard Constraints:** Room capacity checks, Instructor daily load limits (max 4 hours).
    * **Soft Constraints:** Balanced distribution for students.
* **Pedagogical Logic:** Ensures **Laboratory sessions** are always scheduled *after* **Theoretical sessions**.
* **Conflict Detection:** Prevents double-booking for Rooms and Instructors.
* **Interactive GUI:** Filter schedules by Year (1st, 2nd, 3rd, 4th class) and view details.
* **Error Handling:** Visual alerts (Pop-ups) for capacity overflows or constraint violations.

---

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.8 or higher
* `pip` package manager

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/BeePlan-Frontend.git](https://github.com/YOUR_USERNAME/BeePlan-Frontend.git)
cd BeePlan-Frontend
2. Install Dependencies
The project relies on PyQt5 for the interface.
pip install PyQt5
3. Run the Application
Navigate to the src folder and run the main script.
cd src
python main.py

-Usage Guide-
1.Launch: Run main.py to open the BeePlan Interface.

2.Generate: Click the "Generate Schedule" button.

The algorithm will process the data from input_data.json.

3.View: The schedule table will be populated.

Blue Cells: Laboratory Sessions.

White Cells: Theoretical Sessions.

4.Filter: Use the "Select Year" dropdown to view a specific class's timetable (e.g., Year 3).

--Algorithm Logic--
The core logic resides in algorithm.py. It uses a Backtracking approach:

1.Sorts courses by priority (Theory first, then Lab).

2.Tries to assign a course to the first available Time Slot & Room.

3.Checks validity (is_valid function):

Is the room empty?

Is the instructor free?

Is the room capacity sufficient?

Is the Lab placed after Theory?

4.Backtracks if a conflict arises later, trying a different combination.

..AUTHOR
..Beril Aşçi-Project Developer
````
