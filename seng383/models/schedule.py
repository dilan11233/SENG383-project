# models/schedule.py
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, List
from .timeslot import TimeSlot
from .course import Course
from .room import Room

@dataclass
class ScheduledItem:
    course_code: str
    course_part: str   # "theory" or "lab"
    room_id: str

@dataclass
class Schedule:
    # Key: (year, TimeSlot) -> ScheduledItem
    grid: Dict[Tuple[int, TimeSlot], ScheduledItem] = field(default_factory=dict)

    def place(self, year: int, ts: TimeSlot, item: ScheduledItem) -> None:
        self.grid[(year, ts)] = item

    def get(self, year: int, ts: TimeSlot) -> Optional[ScheduledItem]:
        return self.grid.get((year, ts))

    def occupied(self, year: int, ts: TimeSlot) -> bool:
        return (year, ts) in self.grid

    def items_for_course(self, course_code: str) -> List[Tuple[int, TimeSlot, ScheduledItem]]:
        return [(yr, ts, si) for (yr, ts), si in self.grid.items() if si.course_code == course_code]
