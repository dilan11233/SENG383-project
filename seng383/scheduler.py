# beeplan/core/scheduler.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging

from .models import (
    BeePlanConfig, Schedule, ScheduleResult, Violation, Course, Instructor, Room,
    SessionAtom, Placement, TimeSlot
)
from .validate import validate_config
from .constraints import collect_violations
from .errors import InvalidInputError, SchedulingError

logger = logging.getLogger(__name__)

@dataclass
class Domain:
    """
    Allowed (slot, room_id) pairs for a session atom.
    """
    pairs: List[Tuple[TimeSlot, str]]

def build_atoms(courses: List[Course]) -> List[SessionAtom]:
    atoms: List[SessionAtom] = []
    for c in courses:
        atoms.extend(SessionAtom(c.id, "theory", c.year, c.program, c.instructor_id)
                     for _ in range(c.weekly_theory_hours))
        atoms.extend(SessionAtom(c.id, "lab", c.year, c.program, c.instructor_id)
                     for _ in range(c.weekly_lab_hours))
    return atoms

def compute_initial_domains(config: BeePlanConfig) -> Dict[SessionAtom, Domain]:
    """
    For each atom, enumerate all (slot, room) pairs that satisfy:
    - Not in forbidden slots
    - Room type matches session type
    - Instructor is available in the slot
    """
    rooms_by_type: Dict[str, List[Room]] = {"theory": [], "lab": []}
    for r in config.rooms:
        rooms_by_type[r.type].append(r)

    availability_set: Dict[str, set[Tuple[str, int]]] = {
        ins.id: {(ts.day, ts.index) for ts in ins.availability}
        for ins in config.instructors
    }
    forbidden = {(ts.day, ts.index) for ts in config.common.forbidden_slots}
    days = config.common.days
    slots_per_day = config.common.slots_per_day

    domains: Dict[SessionAtom, Domain] = {}
    for atom in build_atoms(config.courses):
        pairs: List[Tuple[TimeSlot, str]] = []
        for d in days:
            for i in range(1, slots_per_day + 1):
                if (d, i) in forbidden:
                    continue
                if (d, i) not in availability_set.get(atom.instructor_id, set()):
                    continue
                for room in rooms_by_type[atom.session_type]:
                    pairs.append((TimeSlot(day=d, index=i), room.id))
        domains[atom] = Domain(pairs=pairs)
    return domains

def sort_atoms_mrv(atoms: List[SessionAtom], domains: Dict[SessionAtom, Domain], courses: Dict[str, Course]) -> List[SessionAtom]:
    """
    MRV with tie-breaking:
      1) Required before elective
      2) Higher total weekly hours courses first
      3) Labs before theory (so labs don't starve on room type)
      4) Fewer domain options first (MRV)
      5) Higher year first (to protect constraints like Y3 vs electives)
    """
    def k(a: SessionAtom):
        c = courses[a.course_id]
        return (
            0 if c.required else 1,
            - (c.weekly_theory_hours + c.weekly_lab_hours),
            0 if a.session_type == "lab" else 1,
            len(domains[a].pairs),
            - c.year,
        )
    return sorted(atoms, key=k)

def incremental_hard_violation(schedule: Schedule,
                               courses: Dict[str, Course],
                               instructors: Dict[str, Instructor],
                               rooms: Dict[str, Room],
                               common) -> bool:
    """
    Fast checks to prune during search:
    - Instructor overlapping in same slot
    - Room double-booking in same slot
    - Forbidden slot usage
    - Daily theory cap exceeded (approximate)
    - Year overlap within slot
    """
    by_slot = schedule.by_slot()
    # Room and instructor overlap in same slot
    for (_, _), placements in by_slot.items():
        seen_rooms: set[str] = set()
        seen_instructors: set[str] = set()
        years: List[int] = []
        for p in placements:
            if p.room_id in seen_rooms:
                return True
            seen_rooms.add(p.room_id)
            key = (p.atom.instructor_id)
            if key in seen_instructors:
                return True
            seen_instructors.add(key)
            years.append(courses[p.atom.course_id].year)
        if len(years) != len(set(years)):
            return True

    # Forbidden slots quick check
    forb = {(ts.day, ts.index) for ts in common.forbidden_slots}
    for p in schedule.placements:
        if (p.slot.day, p.slot.index) in forb:
            return True

    # Daily theory cap quick check
    per_day: Dict[Tuple[str, str], int] = {}
    for p in schedule.placements:
        if p.atom.session_type == "theory":
            key = (p.atom.instructor_id, p.slot.day)
            per_day[key] = per_day.get(key, 0) + 1
    for (ins, day), count in per_day.items():
        if count > instructors[ins].max_daily_theory_hours:
            return True

    # Lab-after-theory quick check (optimistic: allow partial)
    # If any lab exists and no theory scheduled yet for the same course earlier in the week, block only if lab index <= any theory index or none theory
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
            return True

    return False

def generate(config: BeePlanConfig, step_limit: int = 300000) -> ScheduleResult:
    """
    Core scheduling function (backtracking + MRV + forward checking).

    Args:
        config: Full BeePlanConfig.
        step_limit: Upper bound on backtracking steps to avoid runaway search.

    Returns:
        ScheduleResult with complete flag if fully satisfiable, otherwise partial + violations.

    Raises:
        InvalidInputError: when config invalid.
        SchedulingError: on unexpected errors.
    """
    try:
        validate_config(config)
    except InvalidInputError:
        raise
    except Exception as e:
        raise SchedulingError(f"Validation failed unexpectedly: {e}") from e

    courses_map: Dict[str, Course] = {c.id: c for c in config.courses}
    rooms_map: Dict[str, Room] = {r.id: r for r in config.rooms}
    instructors_map: Dict[str, Instructor] = {i.id: i for i in config.instructors}

    schedule = Schedule()
    attempts = 0

    try:
        domains = compute_initial_domains(config)
        atoms = list(domains.keys())
        atoms = sort_atoms_mrv(atoms, domains, courses_map)

        used_room_slot: set[Tuple[str, str, int]] = set()
        used_instructor_slot: set[Tuple[str, str, int]] = set()

        def place(idx: int) -> bool:
            nonlocal attempts
            attempts += 1
            if attempts > step_limit:
                return False
            if idx == len(atoms):
                return True

            atom = atoms[idx]
            # MRV within atom: sort domain pairs by room balance and slot index
            candidates = sorted(domains[atom].pairs, key=lambda pr: (pr[0].index, pr[0].day, pr[1]))
            for slot, room_id in candidates:
                # Fast occupancy checks
                if (room_id, slot.day, slot.index) in used_room_slot:
                    continue
                if (atom.instructor_id, slot.day, slot.index) in used_instructor_slot:
                    continue

                schedule.placements.append(Placement(atom=atom, slot=slot, room_id=room_id))
                used_room_slot.add((room_id, slot.day, slot.index))
                used_instructor_slot.add((atom.instructor_id, slot.day, slot.index))

                # Incremental prune: early hard violation check
                if not incremental_hard_violation(schedule, courses_map, instructors_map, rooms_map, config.common):
                    if place(idx + 1):
                        return True

                # Revert
                schedule.placements.pop()
                used_room_slot.remove((room_id, slot.day, slot.index))
                used_instructor_slot.remove((atom.instructor_id, slot.day, slot.index))

            return False

        complete = place(0)

        # Final violations collection (hard + soft)
        violations = collect_violations(schedule, courses_map, instructors_map, rooms_map, config.common)
        # If not complete or any hard violations exist, mark incomplete
        hard_exists = any(v.severity == "hard" for v in violations)
        complete = complete and not hard_exists

        return ScheduleResult(
            schedule=schedule,
            violations=violations,
            warnings=[v.message for v in violations if v.severity == "soft"],
            attempts=attempts,
            complete=complete,
        )

    except InvalidInputError:
        raise
    except Exception as e:
        logger.exception("Unexpected scheduling failure.")
        raise SchedulingError(f"Unexpected failure: {e}") from e
