# models/curriculum.py
from dataclasses import dataclass
from typing import List
from .course import Course

@dataclass
class Curriculum:
    department: str
    courses: List[Course]

    def courses_by_year(self, year: int) -> List[Course]:
        return [c for c in self.courses if c.year == year]
