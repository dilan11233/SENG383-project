# logic/validators.py
from typing import List, Dict
from models.schedule import Schedule, ScheduledItem
from models.course import Course
from models.room import Room
from models.timeslot import TimeSlot
from models.instructor import Instructor

class ValidationIssue:
    def __init__(self, message: str, severity: str = "error", context: Dict = None):
        self.message = message
        self.severity = severity
        self.context = context or {}

def validate_capacity(course: Course, room: Room) -> List[ValidationIssue]:
    issues = []
    if room.room_type == "lab":
        if course.capacity and course.capacity > 40:
            issues.append(ValidationIssue(f"Lab capacity exceeds 40 for {course.code}"))
        if room.capacity < (course.capacity or 0):
            issues.append(ValidationIssue(f"Room {room.name} capacity insufficient for {course.code}"))
    return issues

def validate_friday_exam(ts: TimeSlot) -> List[ValidationIssue]:
    if ts.day == "Fri" and ts.hour_index in (6,7):
        return [ValidationIssue("Friday exam block conflict (13:20–15:10)")]
    return []

def validate_instructor_theory_limit(schedule: Schedule, courses: Dict[str, Course], instructors: Dict[str, Instructor]) -> List[ValidationIssue]:
    issues = []
    # Count theory per instructor per day
    per_day: Dict[str, Dict[str, int]] = {}
    for (year, ts), item in schedule.grid.items():
        course = courses[item.course_code]
        instr = instructors[course.instructor_id]
        if item.course_part == "theory":
            per_day.setdefault(instr.id, {}).setdefault(ts.day, 0)
            per_day[instr.id][ts.day] += 1
            if per_day[instr.id][ts.day] > 4:
                issues.append(ValidationIssue(f"Instructor {instr.name} exceeds 4 theory hours on {ts.day}"))
    return issues

def validate_lab_after_theory(schedule: Schedule, courses: Dict[str, Course]) -> List[ValidationIssue]:
    issues = []
    for code, course in courses.items():
        items = sorted([ (ts.day, ts.hour_index, item) 
                         for (_, ts), item in schedule.grid.items() 
                         if item.course_code == code ],
                       key=lambda x: (x[0], x[1]))
        # Ensure any lab occurs after at least one theory block earlier in the week or same day before
        has_theory_before = False
        for day in ["Mon","Tue","Wed","Thu","Fri"]:
            day_items = [i for i in items if i[0]==day]
            for _, h, it in day_items:
                if it.course_part == "theory":
                    has_theory_before = True
                if it.course_part == "lab" and not has_theory_before:
                    issues.append(ValidationIssue(f"Lab before theory for {code} on {day}"))
            # reset per day, but keep weekly memory if you want stricter “after in week”
    return issues

def validate_year_elective_overlap(schedule: Schedule, courses: Dict[str, Course]) -> List[ValidationIssue]:
    issues = []
    # 3rd-year courses should not overlap with electives; CENG and SENG electives must not overlap
    # Check per timeslot: collect courses scheduled across years
    per_ts: Dict[str, List[Course]] = {}
    for (year, ts), item in schedule.grid.items():
        key = f"{ts.day}-{ts.hour_index}"
        per_ts.setdefault(key, [])
        per_ts[key].append(courses[item.course_code])

    for key, cs in per_ts.items():
        # 3rd-year vs electives
        has3rd = any(c.year == 3 and not c.is_elective for c in cs)
        hasElective = any(c.is_elective for c in cs)
        if has3rd and hasElective:
            issues.append(ValidationIssue(f"3rd-year course overlaps with elective at {key}"))
        # CENG vs SENG elective overlap
        ceng_elective = any(c.department == "CENG" and c.is_elective for c in cs)
        seng_elective = any(c.department == "SENG" and c.is_elective for c in cs)
        if ceng_elective and seng_elective:
            issues.append(ValidationIssue(f"CENG and SENG electives overlap at {key}"))
    return issues
