# logic/io_json.py
import json
from typing import Dict, List
from models.course import Course
from models.instructor import Instructor
from models.room import Room

def load_courses(path: str) -> Dict[str, Course]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    courses = {}
    for c in data:
        obj = Course(**c)
        courses[obj.code] = obj
    return courses

def load_instructors(path: str) -> Dict[str, Instructor]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {i["id"]: Instructor(**i) for i in data}

def load_rooms(path: str) -> List[Room]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Room(**r) for r in data]

def export_schedule(schedule, path: str) -> None:
    serial = []
    for (year, ts), item in schedule.grid.items():
        serial.append({
            "year": year,
            "day": ts.day,
            "hour_index": ts.hour_index,
            "course_code": item.course_code,
            "course_part": item.course_part,
            "room_id": item.room_id
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serial, f, indent=2, ensure_ascii=False)
