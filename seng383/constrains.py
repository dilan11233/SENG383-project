# beeplan/core/constraints.py
from typing import Dict, List, Tuple
from collections import defaultdict
from .models import Schedule, Course, Instructor, Room, CommonSchedule, Violation, TimeSlot, SessionType

def no_friday_exam_period(schedule: Schedule, common: CommonSchedule) -> List[Violation]:
    forb = {(ts.day, ts.index) for ts in common.forbidden_slots}
    v: List[Violation] = []
    for p in schedule.placements:
        if (p.slot.day, p.slot.index) in forb:
            v.append(Violation(
                type="FORBIDDEN_SLOT",
                message=f"{p.atom.course_id} scheduled in forbidden slot {p.slot.day}-{p.slot.index}",
                slot=p.slot,
                course_ids=[p.atom.course_id],
                room_id=p.room_id,
                severity="hard",
            ))
    return v

def room_type_and_capacity(schedule: Schedule, courses: Dict[str, Course], rooms: Dict[str, Room]) -> List[Violation]:
    v: List[Violation] = []
    for p in schedule.placements:
        r = rooms[p.room_id]
        c = courses[p.atom.course_id]
        if p.atom.session_type == "lab":
            if r.type != "lab":
                v.append(Violation("ROOM_TYPE", f"Lab in non-lab room {r.name}", slot=p.slot, course_ids=[c.id], room_id=r.id))
            if r.capacity > 40:
                v.append(Violation("LAB_CAPACITY", f"Lab capacity exceeds 40 in {r.name} ({r.capacity})",
                                   slot=p.slot, course_ids=[c.id], room_id=r.id))
        else:
            if r.type != "theory":
                v.append(Violation("ROOM_TYPE", f"Theory in lab room {r.name}", slot=p.slot, course_ids=[c.id], room_id=r.id))
        # Optional: theory room capacity vs expected_students
        if c.expected_students and r.capacity < c.expected_students and p.atom.session_type == "theory":
            v.append(Violation("ROOM_CAPACITY", f"Room {r.name} capacity {r.capacity} < expected {c.expected_students}",
                               slot=p.slot, course_ids=[c.id], room_id=r.id))
    return v

def instructor_overlap_and_daily_cap(schedule: Schedule, instructors: Dict[str, Instructor]) -> List[Violation]:
    v: List[Violation] = []
    slot_map: Dict[Tuple[str, str, int], List[str]] = defaultdict(list)
    daily_theory_hours: Dict[Tuple[str, str], int] = defaultdict(int)

    for p in schedule.placements:
        slot_map[(p.atom.instructor_id, p.slot.day, p.slot.index)].append(p.atom.course_id)
        if p.atom.session_type == "theory":
            daily_theory_hours[(p.atom.instructor_id, p.slot.day)] += 1

    for (ins_id, day, index), courses in slot_map.items():
        if len(courses) > 1:
            v.append(Violation("INSTRUCTOR_OVERLAP", f"Instructor {ins_id} overlap at {day}-{index}",
                               slot=TimeSlot(day=day, index=index), instructor_id=ins_id, course_ids=courses))
    for (ins_id, day), hours in daily_theory_hours.items():
        max_hours = instructors[ins_id].max_daily_theory_hours
        if hours > max_hours:
            v.append(Violation("INSTRUCTOR_THEORY_CAP", f"Instructor {ins_id} exceeds {max_hours} theory hours on {day} ({hours})",
                               slot=None, instructor_id=ins_id))
    return v

def lab_after_theory(schedule: Schedule) -> List[Violation]:
    v: List[Violation] = []
    earliest_theory_slot: Dict[str, int] = {}
    earliest_lab_slot: Dict[str, int] = {}

    for p in schedule.placements:
        if p.atom.session_type == "theory":
            earliest_theory_slot[p.atom.course_id] = min(earliest_theory_slot.get(p.atom.course_id, p.slot.index), p.slot.index)
        else:
            earliest_lab_slot[p.atom.course_id] = min(earliest_lab_slot.get(p.atom.course_id, p.slot.index), p.slot.index)

    for cid, lab_idx in earliest_lab_slot.items():
        t_idx = earliest_theory_slot.get(cid)
        if t_idx is None or lab_idx <= t_idx:
            v.append(Violation("LAB_AFTER_THEORY", f"Lab scheduled before theory for {cid}",
                               course_ids=[cid], severity="hard"))
    return v

def cohort_and_elective_constraints(schedule: Schedule, courses: Dict[str, Course]) -> List[Violation]:
    v: List[Violation] = []
    by_slot = schedule.by_slot()
    for (day, idx), placements in by_slot.items():
        # Same-year overlap
        years = [courses[p.atom.course_id].year for p in placements]
        if len(years) != len(set(years)):
            v.append(Violation("YEAR_OVERLAP", f"Same-year overlap at {day}-{idx}",
                               slot=TimeSlot(day=day, index=idx),
                               course_ids=[p.atom.course_id for p in placements]))
        # 3rd-year vs electives
        has_y3 = any(courses[p.atom.course_id].year == 3 for p in placements)
        has_elective = any(not courses[p.atom.course_id].required for p in placements)
        if has_y3 and has_elective:
            v.append(Violation("Y3_VS_ELECTIVES", f"3rd-year courses overlap with electives at {day}-{idx}",
                               slot=TimeSlot(day=day, index=idx),
                               course_ids=[p.atom.course_id for p in placements]))
        # CENG vs SENG elective overlap
        elective_programs = {courses[p.atom.course_id].program for p in placements if not courses[p.atom.course_id].required}
        if "CENG" in elective_programs and "SENG" in elective_programs:
            v.append(Violation("PROGRAM_ELECTIVE_OVERLAP", f"CENG and SENG electives overlap at {day}-{idx}",
                               slot=TimeSlot(day=day, index=idx),
                               course_ids=[p.atom.course_id for p in placements]))
    return v

def prefer_consecutive_lab(schedule: Schedule, courses: Dict[str, Course]) -> List[Violation]:
    """
    Soft preference: flag labs that are not consecutive.
    """
    v: List[Violation] = []
    by_course_indices: Dict[str, List[int]] = defaultdict(list)
    for p in schedule.placements:
        if p.atom.session_type == "lab":
            by_course_indices[p.atom.course_id].append(p.slot.index)
    for cid, indices in by_course_indices.items():
        indices.sort()
        # If labs exist and not consecutive pairs (e.g., [3,5]), warn
        if len(indices) >= 2 and not any(indices[i+1] == indices[i] + 1 for i in range(len(indices)-1)):
            course = courses[cid]
            if course.prefer_consecutive_lab:
                v.append(Violation("LAB_NON_CONSECUTIVE", f"Lab hours not consecutive for {cid}",
                                   course_ids=[cid], severity="soft"))
    return v

def collect_violations(schedule: Schedule,
                       courses: Dict[str, Course],
                       instructors: Dict[str, Instructor],
                       rooms: Dict[str, Room],
                       common: CommonSchedule) -> List[Violation]:
    """
    Aggregate violations from all constraints.
    """
    v: List[Violation] = []
    v += no_friday_exam_period(schedule, common)
    v += room_type_and_capacity(schedule, courses, rooms)
    v += instructor_overlap_and_daily_cap(schedule, instructors)
    v += lab_after_theory(schedule)
    v += cohort_and_elective_constraints(schedule, courses)
    v += prefer_consecutive_lab(schedule, courses)
    return v
