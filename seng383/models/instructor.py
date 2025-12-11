# models/instructor.py
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class Instructor:
    id: str
    name: str
    departments: List[str]
    availability: Dict[str, List[Tuple[int, int]]]  
    # e.g., {"Mon": [(1,5)], "Tue": [(1,8)]} timeslot indices per day
