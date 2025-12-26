"""Main entry point for BeePlan application."""

import sys
from PyQt5.QtWidgets import QApplication
from utils import load_json, load_courses, load_instructors, load_rooms
from gui import BeePlanMainWindow


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Load data from JSON
    try:
        data = load_json("input_data.json")
        courses = load_courses(data)
        instructors = load_instructors(data)
        rooms = load_rooms(data)
        
        print(f"Loaded {len(courses)} courses, {len(instructors)} instructors, {len(rooms)} rooms")
        
    except FileNotFoundError:
        print("Error: input_data.json not found!")
        print("Please create input_data.json with course, instructor, and room data.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
    
    # Create and show main window
    window = BeePlanMainWindow(courses, instructors, rooms)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


