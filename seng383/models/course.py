# models/course.py
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Course:
    code: str
    name: str
    year: int  # 1..4
    instructor_id: str
    weekly_theory_hours: int  # e.g., 3 for 3+0, or 2 for 2+1
    weekly_lab_hours: int     # e.g., 1 for 2+1, or 0 for 3+0
    department: str           # e.g., "CENG", "SENG"
    is_elective: bool = False
    capacity: Optional[int] = None  # for labs, default None

    def total_hours(self) -> int:
        return self.weekly_theory_hours + self.weekly_lab_hours
