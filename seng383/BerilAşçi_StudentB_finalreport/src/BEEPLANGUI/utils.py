"""Utility functions for JSON file handling."""

import json
from typing import List, Dict, Any
from models import Course, Instructor, Room


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: str) -> None:
    """Save data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_courses(data: Dict[str, Any]) -> List[Course]:
    """Load courses from JSON data."""
    courses = []
    for course_data in data.get("courses", []):
        course = Course(
            code=course_data["code"],
            name=course_data["name"],
            instructor=course_data["instructor"],
            theory_hours=course_data["theory_hours"],
            lab_hours=course_data.get("lab_hours", 0),
            year=course_data["year"],
            students=course_data["students"],
            type=course_data["type"]
        )
        courses.append(course)
    return courses


def load_instructors(data: Dict[str, Any]) -> List[Instructor]:
    """Load instructors from JSON data."""
    instructors = []
    for inst_data in data.get("instructors", []):
        instructor = Instructor(
            name=inst_data["name"],
            max_theory_daily=inst_data.get("max_theory_daily", 4)
        )
        instructors.append(instructor)
    return instructors


def load_rooms(data: Dict[str, Any]) -> List[Room]:
    """Load rooms from JSON data."""
    rooms = []
    for room_data in data.get("rooms", []):
        room = Room(
            id=room_data["id"],
            type=room_data["type"],
            capacity=room_data["capacity"]
        )
        rooms.append(room)
    return rooms


def export_schedule_to_json(courses: List[Course], file_path: str) -> None:
    """Export scheduled courses to JSON file."""
    schedule_data = {
        "courses": []
    }
    
    for course in courses:
        course_data = {
            "code": course.code,
            "name": course.name,
            "instructor": course.instructor,
            "theory_hours": course.theory_hours,
            "lab_hours": course.lab_hours,
            "year": course.year,
            "students": course.students,
            "type": course.type,
            "theory_schedule": None,
            "lab_schedule": None
        }
        
        if course.theory_slot and course.theory_room:
            course_data["theory_schedule"] = {
                "day": course.theory_slot.day,
                "time": course.theory_slot.to_string(),
                "room": course.theory_room.id,
                "duration_hours": course.theory_hours
            }
        
        if course.lab_slot and course.lab_room:
            course_data["lab_schedule"] = {
                "day": course.lab_slot.day,
                "time": course.lab_slot.to_string(),
                "room": course.lab_room.id,
                "duration_hours": course.lab_hours
            }
        
        schedule_data["courses"].append(course_data)
    
    save_json(schedule_data, file_path)


