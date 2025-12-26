# BeePlan - University Course Scheduling System

BeePlan is a desktop application for generating conflict-free course schedules for a 4-year Computer & Software Engineering curriculum. It uses Constraint Satisfaction Problem (CSP) algorithms with backtracking to ensure all scheduling constraints are satisfied.

## Features

- **Automatic Schedule Generation**: Uses CSP backtracking algorithm to generate conflict-free schedules
- **Visual Weekly Grid**: View schedules in an intuitive weekly grid (Monday-Friday, 09:20-17:20)
- **Constraint Validation**: Enforces all mandatory scheduling constraints
- **Conflict Detection**: Highlights conflicts in red with detailed error messages
- **Color-Coded Display**: Different colors for different course years
- **Export Functionality**: Export schedules to JSON format

## Requirements

- Python 3.8 or higher
- PyQt6

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Ensure `input_data.json` exists with your course, instructor, and room data (a sample is included)

2. Run the application:
```bash
python main.py
```

3. Click "Generate Schedule" to create a schedule automatically

4. Use "View Report" to see unscheduled courses or conflicts

5. Use "Export JSON" to save the schedule to a file

## Input Data Format

The `input_data.json` file should follow this structure:

```json
{
  "courses": [
    {
      "code": "SENG 201",
      "name": "Data Structures",
      "instructor": "B.Celikkale",
      "theory_hours": 3,
      "lab_hours": 2,
      "year": 2,
      "students": 60,
      "type": "mandatory"
    }
  ],
  "instructors": [
    {
      "name": "B.Celikkale",
      "max_theory_daily": 4
    }
  ],
  "rooms": [
    {
      "id": "L-205",
      "type": "lab",
      "capacity": 40
    }
  ]
}
```

### Course Types

- `mandatory`: Regular mandatory course
- `departmental_elective`: Departmental elective course
- `ceng_elective`: Computer Engineering elective
- `seng_elective`: Software Engineering elective

### Room Types

- `lab`: Laboratory room (strictly 40 student capacity)
- `classroom`: Regular classroom

## Scheduling Constraints

The system enforces the following constraints:

1. **Friday Ban**: No courses allowed on Friday between 13:20-15:10 (reserved for exams)

2. **Instructor Load**: Instructors cannot teach more than 4 hours of theory in a single day

3. **Lab Sequence**: If a course has lab hours, the lab session must occur after the theory session in the week (same day or later, and later time if same day)

4. **Conflicts**:
   - No instructor overlap (same instructor cannot teach two courses at the same time)
   - No room overlap (same room cannot be used by two courses at the same time)
   - 3rd-year courses must not overlap with departmental electives
   - CENG and SENG electives must not overlap

5. **Capacity**: Lab sessions are strictly limited to 40 students per section

## Project Structure

- `main.py`: Application entry point
- `models.py`: Data models (Course, Instructor, Room, TimeSlot, etc.)
- `algorithm.py`: Core scheduling algorithm with constraint checking
- `gui.py`: PyQt6 GUI implementation
- `utils.py`: JSON file handling utilities
- `input_data.json`: Input data file
- `requirements.txt`: Python dependencies

## License

This project is created for educational purposes.

## Author

BeePlan - University Course Scheduling System


