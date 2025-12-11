# logic/constraints.py
from typing import List, Tuple
from models.timeslot import TimeSlot, DAYS
from models.course import Course
from models.room import Room
from models.schedule import Schedule, ScheduledItem
from models.instructor import Instructor

FRIDAY_EXAM_FORBIDDEN = [(6,7)]  # hour indices overlapping 13:20–15:10
# Using our blocks, forbid hours 6 and 7 on Friday

def violates_friday_exam(ts: TimeSlot) -> bool:
    return ts.day == "Fri" and ts.hour_index in (6,7)

def instructor_theory_limit(schedule: Schedule, instructor: Instructor, ts: TimeSlot, course: Course) -> bool:
    # Count existing theory hours for instructor on ts.day
    count = 0
    for (year, tslot), item in schedule.grid.items():
        if tslot.day != ts.day: 
            continue
        if item.course_part != "theory":
            continue
        if item.course_code == course.code:
            # same course, still counts
            pass
        # Here we need a mapping course_code -> instructor_id externally; handled by validators calling us with needed context
    # This function will be completed in validators where we have course/instructor maps
    return False
