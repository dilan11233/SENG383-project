# beeplan/core/validate.py
from typing import Set
from .models import BeePlanConfig, TimeSlot
from .errors import InvalidInputError

def validate_config(config: BeePlanConfig) -> None:
    if not config.common.days or config.common.slots_per_day <= 0:
        raise InvalidInputError("Days and slots_per_day must be set.")
    valid = {(d, i) for d in config.common.days for i in range(1, config.common.slots_per_day + 1)}
    # Courses
    seen_courses: Set[str] = set()
    for c in config.courses:
        if not c.id or c.year not in {1, 2, 3, 4}:
            raise InvalidInputError(f"Course '{c.name}' invalid id/year.")
        if c.weekly_theory_hours < 0 or c.weekly_lab_hours < 0:
            raise InvalidInputError(f"Course {c.id} has negative hours.")
        if c.id in seen_courses:
            raise InvalidInputError(f"Duplicate course id {c.id}.")
        seen_courses.add(c.id)
    # Instructors
    seen_instructors: Set[str] = set()
    for i in config.instructors:
        if not i.id or not i.name:
            raise InvalidInputError("Instructor missing id/name.")
        if not i.availability:
            raise InvalidInputError(f"Instructor {i.id} has empty availability.")
        for ts in i.availability:
            if (ts.day, ts.index) not in valid:
                raise InvalidInputError(f"Instructor {i.id} availability out of grid: {ts.day}-{ts.index}.")
        seen_instructors.add(i.id)
    # Rooms
    seen_rooms: Set[str] = set()
    for r in config.rooms:
        if not r.id or r.capacity <= 0 or r.type not in {"theory", "lab"}:
            raise InvalidInputError(f"Room {r.id} invalid definition.")
        seen_rooms.add(r.id)
    # References
    for c in config.courses:
        if c.instructor_id not in seen_instructors:
            raise InvalidInputError(f"Course {c.id} references unknown instructor {c.instructor_id}.")
    for ts in config.common.forbidden_slots:
        if (ts.day, ts.index) not in valid:
            raise InvalidInputError(f"Forbidden slot out of grid: {ts.day}-{ts.index}.")
