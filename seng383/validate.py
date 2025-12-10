# beeplan/core/validate.py
from typing import List, Set
from .models import BeePlanConfig, Course, Instructor, Room, CommonSchedule, TimeSlot
from .errors import InvalidInputError

def validate_config(config: BeePlanConfig) -> None:
    """
    Validate presence and consistency of config data.

    Raises:
        InvalidInputError: if invalid fields or duplicates detected.
    """
    if not config.common.days or config.common.slots_per_day <= 0:
        raise InvalidInputError("Common schedule days/slots_per_day must be provided and > 0.")

    # Unique IDs
    course_ids: Set[str] = set()
    instructor_ids: Set[str] = set()
    room_ids: Set[str] = set()

    for c in config.courses:
        if not c.id or c.year not in {1, 2, 3, 4}:
            raise InvalidInputError(f"Course '{c.name}' missing id or invalid year.")
        if c.weekly_theory_hours < 0 or c.weekly_lab_hours < 0:
            raise InvalidInputError(f"Course {c.id} has negative weekly hours.")
        if c.instructor_id == "":
            raise InvalidInputError(f"Course {c.id} missing instructor_id.")
        if c.id in course_ids:
            raise InvalidInputError(f"Duplicate course id: {c.id}")
        course_ids.add(c.id)

    for i in config.instructors:
        if not i.id or not i.name:
            raise InvalidInputError("Instructor missing id or name.")
        if not i.availability:
            raise InvalidInputError(f"Instructor {i.id} has empty availability.")
        instructor_ids.add(i.id)

    for r in config.rooms:
        if not r.id or r.capacity <= 0 or r.type not in {"theory", "lab"}:
            raise InvalidInputError(f"Room {r.id} invalid capacity/type.")
        room_ids.add(r.id)

    # Referential integrity
    for c in config.courses:
        if c.instructor_id not in instructor_ids:
            raise InvalidInputError(f"Course {c.id} references unknown instructor {c.instructor_id}.")

    # Timeslot domain check
    valid_slots = {(d, i) for d in config.common.days for i in range(1, config.common.slots_per_day + 1)}
    for ins in config.instructors:
        for ts in ins.availability:
            if (ts.day, ts.index) not in valid_slots:
                raise InvalidInputError(f"Instructor {ins.id} availability out of grid: {ts}.")
    for ts in config.common.forbidden_slots:
        if (ts.day, ts.index) not in valid_slots:
            raise InvalidInputError(f"Forbidden slot out of grid: {ts}.")
