# beeplan/core/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Literal
from enum import Enum

Day = Literal["Mon", "Tue", "Wed", "Thu", "Fri"]
SessionType = Literal["theory", "lab"]

class Program(str, Enum):
    CENG = "CENG"
    SENG = "SENG"

@dataclass(frozen=True)
class TimeSlot:
    """
    A discrete weekly slot.

    Args:
        day: Day of week.
        index: Integer slot index within the day (1..N).
    """
    day: Day
    index: int

@dataclass
class Course:
    """
    Course definition and weekly requirements.

    Args:
        id: Unique course ID.
        name: Human-readable course name.
        year: Cohort year (1..4).
        required: True if mandatory for cohort, False if elective.
        weekly_theory_hours: Number of theory hours per week.
        weekly_lab_hours: Number of lab hours per week.
        instructor_id: ID of assigned instructor.
        program: Academic program (CENG/SENG).
        prefer_consecutive_lab: Soft preference to place lab hours consecutively.
        expected_students: Estimated enrollment to validate room capacity (optional).
    """
    id: str
    name: str
    year: int
    required: bool
    weekly_theory_hours: int
    weekly_lab_hours: int
    instructor_id: str
    program: Program
    prefer_consecutive_lab: bool = True
    expected_students: Optional[int] = None

@dataclass
class Instructor:
    """
    Instructor availability and limits.

    Args:
        id: Unique instructor ID.
        name: Full name.
        availability: List of allowed TimeSlots.
        max_daily_theory_hours: Max theory hours per day (default 4).
    """
    id: str
    name: str
    availability: List[TimeSlot]
    max_daily_theory_hours: int = 4

@dataclass
class Room:
    """
    Teaching space.

    Args:
        id: Unique room ID.
        name: Human-readable room name.
        capacity: Seat count.
        type: 'theory' or 'lab'.
    """
    id: str
    name: str
    capacity: int
    type: SessionType

@dataclass
class CommonSchedule:
    """
    Global weekly rules.

    Args:
        days: Allowed days in week (Mon..Fri).
        slots_per_day: Number of discrete slots per day.
        forbidden_slots: TimeSlots that cannot be used (e.g., Friday exam block).
    """
    days: List[Day]
    slots_per_day: int
    forbidden_slots: List[TimeSlot] = field(default_factory=list)

@dataclass(frozen=True)
class SessionAtom:
    """
    A single hour of a course to be scheduled (theory or lab).
    """
    course_id: str
    session_type: SessionType
    year: int
    program: Program
    instructor_id: str

@dataclass
class Placement:
    """
    A scheduled session atom in a room and timeslot.

    Args:
        atom: The session atom.
        slot: The timeslot used.
        room_id: The assigned room.
    """
    atom: SessionAtom
    slot: TimeSlot
    room_id: str

@dataclass
class Schedule:
    """
    Collection of placements with helpers.
    """
    placements: List[Placement] = field(default_factory=list)

    def by_slot(self) -> Dict[Tuple[Day, int], List[Placement]]:
        out: Dict[Tuple[Day, int], List[Placement]] = {}
        for p in self.placements:
            key = (p.slot.day, p.slot.index)
            out.setdefault(key, []).append(p)
        return out

    def by_instructor(self) -> Dict[str, List[Placement]]:
        out: Dict[str, List[Placement]] = {}
        for p in self.placements:
            out.setdefault(p.atom.instructor_id, []).append(p)
        return out

@dataclass
class BeePlanConfig:
    """
    Complete configuration used to generate the schedule.

    Args:
        common: Global time grid and forbidden slots.
        courses: All courses for the term.
        instructors: Instructor definitions and availability.
        rooms: Available rooms.
    """
    common: CommonSchedule
    courses: List[Course]
    instructors: List[Instructor]
    rooms: List[Room]

@dataclass
class Violation:
    """
    Structured violation for reporting.

    Args:
        type: Code identifier (e.g., 'INSTRUCTOR_OVERLAP').
        message: Human-readable description.
        slot: Optional timeslot where violation occurs.
        course_ids: Optional related courses.
        instructor_id: Optional related instructor.
        room_id: Optional related room.
        severity: 'hard' blocks schedule; 'soft' is a preference break.
    """
    type: str
    message: str
    severity: Literal["hard", "soft"] = "hard"
    slot: Optional[TimeSlot] = None
    course_ids: Optional[List[str]] = None
    instructor_id: Optional[str] = None
    room_id: Optional[str] = None

@dataclass
class ScheduleResult:
    """
    Result of scheduling attempt.

    Args:
        schedule: Final or partial schedule.
        violations: List of detected violations.
        warnings: Non-blocking notes (e.g., soft constraints).
        attempts: Backtracking steps attempted (for logging/metrics).
        complete: True if no hard violations and all atoms placed.
    """
    schedule: Schedule
    violations: List[Violation]
    warnings: List[str]
    attempts: int
    complete: bool
