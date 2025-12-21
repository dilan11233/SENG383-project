# beeplan/core/constraints.py
from typing import Dict, List, Tuple
from collections import defaultdict
from .models import Schedule, Course, Instructor, Room, CommonSchedule, Violation, TimeSlot

def no_friday_exam_period(schedule: Schedule, common: CommonSchedule) -> List[Violation]:
    forb = {(ts.day, ts.index) for ts in common.forbidden_slots}
    out: List[Violation] = []
    for p in schedule.placements:
        if (p.slot.day, p.slot.index) in forb:
            out.append(Violation("FORBIDDEN_SLOT",
                f"{p.atom.course_id} in forbidden Fri slot {p.slot.index}",
                severity="hard", slot=p.slot, course_ids=[p.atom.course_id], room_id=p.room_id))
    return out

def room_type_capacity(schedule: Schedule, courses: Dict[str, Course], rooms: Dict[str, Room]) -> List[Violation]:
    out: List[Violation] = []
    for p in schedule.placements:
        c = courses[p.atom.course_id]; r = rooms[p.room_id]
        if p.atom.session_type == "lab":
            if r.type != "lab":
                out.append(Violation("ROOM_TYPE", f"Lab in non-lab room {r.name}",
                                     severity="hard", slot=p.slot, course_ids=[c.id], room_id=r.id))
            if r.capacity > 40:
                out.append(Violation("LAB_CAPACITY", f"Lab capacity exceeds 40 in {r.name} ({r.capacity})",
                                     severity="hard", slot=p.slot, course_ids=[c.id], room_id=r.id))
        else:
            if r.type != "theory":
                out.append(Violation("ROOM_TYPE", f"Theory in lab room {r.name}",
                                     severity="hard", slot=p.slot, course_ids=[c.id], room_id=r.id))
        # Optional theory capacity vs expected students
        if c.expected_students and r.capacity < c.expected_students and p.atom.session_type == "theory":
            out.append(Violation("ROOM_CAPACITY",
                                 f"Room {r.name} capacity {r.capacity} < expected {c.expected_students}",
                                 severity="hard", slot=p.slot, course_ids=[c.id], room_id=r.id))
    return out

def instructor_overlap_daily_cap(schedule: Schedule, instructors: Dict[str, Instructor]) -> List[Violation]:
    out: List[Violation] = []
    slot_map: Dict[Tuple[str, str, int], List[str]] = defaultdict(list)
    theory_hours: Dict[Tuple[str, str], int] = defaultdict(int)
    for p in schedule.placements:
        slot_map[(p.atom.instructor_id, p.slot.day, p.slot.index)].append(p.atom.course_id)
        if p.atom.session_type == "theory":
            theory_hours[(p.atom.instructor_id, p.slot.day)] += 1
    for (ins, day, idx), cids in slot_map.items():
        if len(cids) > 1:
            out.append(Violation("INSTRUCTOR_OVERLAP",
                                 f"Instructor {ins} overlap at {day}-{idx}",
                                 severity="hard", slot=TimeSlot(day, idx),
                                 instructor_id=ins, course_ids=cids))
    for (ins, day), hours in theory_hours.items():
        cap = instructors[ins].max_daily_theory_hours
        if hours > cap:
            out.append(Violation("INSTRUCTOR_THEORY_CAP",
                                 f"Instructor {ins} exceeds {cap} theory hours on {day} ({hours})",
                                 severity="hard", instructor_id=ins))
    return out

def lab_after_theory(schedule: Schedule) -> List[Violation]:
    out: List[Violation] = []
    earliest_theory: Dict[str, int] = {}
    earliest_lab: Dict[str, int] = {}
    for p in schedule.placements:
        if p.atom.session_type == "theory":
            earliest_theory[p.atom.course_id] = min(earliest_theory.get(p.atom.course_id, p.slot.index), p.slot.index)
        else:
            earliest_lab[p.atom.course_id] = min(earliest_lab.get(p.atom.course_id, p.slot.index), p.slot.index)
    for cid, lidx in earliest_lab.items():
        tidx = earliest_theory.get(cid)
        if tidx is None or lidx <= tidx:
            out.append(Violation("LAB_AFTER_THEORY", f"Lab before theory for {cid}", severity="hard", course_ids=[cid]))
    return out

def cohort_electives(schedule: Schedule, courses: Dict[str, Course]) -> List[Violation]:
    out: List[Violation] = []
    for (day, idx), ps in schedule.by_slot().items():
        years = [courses[p.atom.course_id].year for p in ps]
        if len(years) != len(set(years)):
            out.append(Violation("YEAR_OVERLAP", f"Same-year overlap at {day}-{idx}",
                                 severity="hard", slot=TimeSlot(day, idx),
                                 course_ids=[p.atom.course_id for p in ps]))
        has_y3 = any(courses[p.atom.course_id].year == 3 for p in ps)
        has_elective = any(not courses[p.atom.course_id].required for p in ps)
        if has_y3 and has_elective:
            out.append(Violation("Y3_VS_ELECTIVES",
                                 f"3rd-year courses overlap with electives at {day}-{idx}",
                                 severity="hard", slot=TimeSlot(day, idx),
                                 course_ids=[p.atom.course_id for p in ps]))
        elective_programs = {courses[p.atom.course_id].program for p in ps if not courses[p.atom.course_id].required}
        if "CENG" in elective_programs and "SENG" in elective_programs:
            out.append(Violation("PROGRAM_ELECTIVE_OVERLAP",
                                 f"CENG and SENG electives overlap at {day}-{idx}",
                                 severity="hard", slot=TimeSlot(day, idx),
                                 course_ids=[p.atom.course_id for p in ps]))
    return out

def prefer_consecutive_lab(schedule: Schedule, courses: Dict[str, Course]) -> List[Violation]:
    out: List[Violation] = []
    by_course: Dict[str, List[int]] = defaultdict(list)
    for p in schedule.placements:
        if p.atom.session_type == "lab":
            by_course[p.atom.course_id].append(p.slot.index)
    for cid, idxs in by_course.items():
        idxs.sort()
        if len(idxs) >= 2 and not any(idxs[i+1] == idxs[i] + 1 for i in range(len(idxs) - 1)):
            if courses[cid].prefer_consecutive_lab:
                out.append(Violation("LAB_NON_CONSECUTIVE",
                                     f"Lab hours not consecutive for {cid}",
                                     severity="soft", course_ids=[cid]))
    return out

def collect_violations(schedule: Schedule,
                       courses: Dict[str, Course],
                       instructors: Dict[str, Instructor],
                       rooms: Dict[str, Room],
                       common: CommonSchedule) -> List[Violation]:
    v: List[Violation] = []
    v += no_friday_exam_period(schedule, common)
    v += room_type_capacity(schedule, courses, rooms)
    v += instructor_overlap_daily_cap(schedule, instructors)
    v += lab_after_theory(schedule)
    v += cohort_electives(schedule, courses)
    v += prefer_consecutive_lab(schedule, courses)
    return v
