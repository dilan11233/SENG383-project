# beeplan/core/scheduler.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import logging

from .models import (BeePlanConfig, Schedule, ScheduleResult, Violation, Course, Instructor, Room,
                     SessionAtom, Placement, TimeSlot)
from .validate import validate_config
from .constraints import collect_violations
from .errors import InvalidInputError, SchedulingError

logger = logging.getLogger(__name__)

@dataclass
class Domain:
    pairs: List[Tuple[TimeSlot, str]]

def build_atoms(courses: List[Course]) -> List[SessionAtom]:
    atoms: List[SessionAtom] = []
    for c in courses:
        atoms += [SessionAtom(c.id, "theory", c.year, c.program, c.instructor_id)
                  for _ in range(c.weekly_theory_hours)]
        atoms += [SessionAtom(c.id, "lab", c.year, c.program, c.instructor_id)
                  for _ in range(c.weekly_lab_hours)]
    return atoms

def compute_domains(config: BeePlanConfig) -> Dict[SessionAtom, Domain]:
    rooms_by_type = {"theory": [r for r in config.rooms if r.type == "theory"],
                     "lab": [r for r in config.rooms if r.type == "lab"]}
    availability = {ins.id: {(ts.day, ts.index) for ts in ins.availability} for ins in config.instructors}
    forbidden = {(ts.day, ts.index) for ts in config.common.forbidden_slots}
    domains: Dict[SessionAtom, Domain] = {}
    for atom in build_atoms(config.courses):
        pairs: List[Tuple[TimeSlot, str]] = []
        for d in config.common.days:
            for i in range(1, config.common.slots_per_day + 1):
                if (d, i) in forbidden:
                    continue
                if (d, i) not in availability.get(atom.instructor_id, set()):
                    continue
                for r in rooms_by_type[atom.session_type]:
                    pairs.append((TimeSlot(d, i), r.id))
        domains[atom] = Domain(pairs=pairs)
    return domains

def sort_atoms(atoms: List[SessionAtom], domains: Dict[SessionAtom, Domain], courses: Dict[str, Course]) -> List[SessionAtom]:
    def k(a: SessionAtom):
        c = courses[a.course_id]
        return (
            0 if c.required else 1,                       # required before electives
            - (c.weekly_theory_hours + c.weekly_lab_hours), # heavier first
            0 if a.session_type == "lab" else 1,           # labs earlier (scarce rooms)
            len(domains[a].pairs),                         # MRV
            - c.year,                                      # higher year priority
        )
    return sorted(atoms, key=k)

def incremental_prune(schedule: Schedule,
                      courses: Dict[str, Course],
                      instructors: Dict[str, Instructor],
                      rooms: Dict[str, Room],
                      common: BeePlanConfig.common.__class__) -> bool:
    """
    Early hard-pruning: room/instructor double-booking, forbidden slots,
    daily theory cap, year overlap, lab-before-theory.
    """
    by_slot = schedule.by_slot()
    forb = {(ts.day, ts.index) for ts in common.forbidden_slots}

    for (day, idx), ps in by_slot.items():
        seen_rooms = set(); seen_instr = set(); years = []
        for p in ps:
            if (day, idx) in forb: return True
            if p.room_id in seen_rooms: return True
            seen_rooms.add(p.room_id)
            if p.atom.instructor_id in seen_instr: return True
            seen_instr.add(p.atom.instructor_id)
            years.append(courses[p.atom.course_id].year)
        if len(years) != len(set(years)): return True

    theory_per_day: Dict[Tuple[str, str], int] = {}
    earliest_t: Dict[str, int] = {}; earliest_l: Dict[str, int] = {}
    for p in schedule.placements:
        if p.atom.session_type == "theory":
            theory_per_day[(p.atom.instructor_id, p.slot.day)] = theory_per_day.get((p.atom.instructor_id, p.slot.day), 0) + 1
            earliest_t[p.atom.course_id] = min(earliest_t.get(p.atom.course_id, p.slot.index), p.slot.index)
        else:
            earliest_l[p.atom.course_id] = min(earliest_l.get(p.atom.course_id, p.slot.index), p.slot.index)
    for (ins, day), count in theory_per_day.items():
        if count > instructors[ins].max_daily_theory_hours: return True
    for cid, lidx in earliest_l.items():
        tidx = earliest_t.get(cid)
        if tidx is None or lidx <= tidx: return True

    return False

def generate(config: BeePlanConfig, step_limit: int = 400000) -> ScheduleResult:
    try:
        validate_config(config)
    except InvalidInputError:
        raise
    except Exception as e:
        raise SchedulingError(f"Unexpected during validation: {e}") from e

    courses = {c.id: c for c in config.courses}
    rooms = {r.id: r for r in config.rooms}
    instructors = {i.id: i for i in config.instructors}

    schedule = Schedule()
    attempts = 0

    try:
        domains = compute_domains(config)
        atoms = sort_atoms(list(domains.keys()), domains, courses)
        used_room_slot: set[Tuple[str, str, int]] = set()
        used_instr_slot: set[Tuple[str, str, int]] = set()

        def place(i: int) -> bool:
            nonlocal attempts
            attempts += 1
            if attempts > step_limit:
                return False
            if i == len(atoms):
                return True
            a = atoms[i]
            # slight bias: earlier slots, balanced room usage
            candidates = sorted(domains[a].pairs, key=lambda pr: (pr[0].day, pr[0].index, pr[1]))
            for slot, room_id in candidates:
                if (room_id, slot.day, slot.index) in used_room_slot:
                    continue
                if (a.instructor_id, slot.day, slot.index) in used_instr_slot:
                    continue
                schedule.placements.append(Placement(a, slot, room_id))
                used_room_slot.add((room_id, slot.day, slot.index))
                used_instr_slot.add((a.instructor_id, slot.day, slot.index))

                if not incremental_prune(schedule, courses, instructors, rooms, config.common):
                    if place(i + 1):
                        return True

                schedule.placements.pop()
                used_room_slot.remove((room_id, slot.day, slot.index))
                used_instr_slot.remove((a.instructor_id, slot.day, slot.index))
            return False

        complete = place(0)
        violations = collect_violations(schedule, courses, instructors, rooms, config.common)
        hard = any(v.severity == "hard" for v in violations)
        complete = complete and not hard

        return ScheduleResult(schedule=schedule, violations=violations, warnings=[v.message for v in violations if v.severity == "soft"],
                              attempts=attempts, complete=complete)
    except Exception as e:
        logger.exception("Scheduling failed")
        raise SchedulingError(f"Scheduling failed: {e}") from e
