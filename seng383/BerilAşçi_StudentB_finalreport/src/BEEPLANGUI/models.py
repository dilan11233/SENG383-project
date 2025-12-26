"""Data models for BeePlan scheduling system."""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class CourseType(Enum):
    """Course type enumeration."""
    MANDATORY = "mandatory"
    DEPARTMENTAL_ELECTIVE = "departmental_elective"
    CENG_ELECTIVE = "ceng_elective"
    SENG_ELECTIVE = "seng_elective"


@dataclass
class Instructor:
    """Represents an instructor."""
    name: str
    max_theory_daily: int = 4
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if not isinstance(other, Instructor):
            return False
        return self.name == other.name


@dataclass
class Room:
    """Represents a room."""
    id: str
    type: str  # "lab" or "classroom"
    capacity: int
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Room):
            return False
        return self.id == other.id


@dataclass
class TimeSlot:
    """Represents a time slot."""
    day: str  # "Monday", "Tuesday", etc.
    hour: int  # Starting hour (e.g., 9 for 09:20)
    minute: int = 20  # Starting minute
    
    def __hash__(self):
        return hash((self.day, self.hour, self.minute))
    
    def __eq__(self, other):
        if not isinstance(other, TimeSlot):
            return False
        return (self.day == other.day and 
                self.hour == other.hour and 
                self.minute == other.minute)
    
    def to_string(self) -> str:
        """Convert time slot to human-readable string."""
        hour_str = str(self.hour).zfill(2)
        minute_str = str(self.minute).zfill(2)
        return f"{hour_str}:{minute_str}"
    
    def get_end_time(self, duration_hours: int = 1) -> tuple:
        """Get end time as (hour, minute) tuple."""
        total_minutes = (self.hour * 60 + self.minute) + (duration_hours * 60)
        end_hour = total_minutes // 60
        end_minute = total_minutes % 60
        return (end_hour, end_minute)


@dataclass
class Course:
    """Represents a course."""
    code: str
    name: str
    instructor: str
    theory_hours: int
    lab_hours: int
    year: int
    students: int
    type: str  # "mandatory", "departmental_elective", "ceng_elective", "seng_elective"
    
    # Scheduling assignments (set by algorithm)
    theory_slot: Optional[TimeSlot] = None
    theory_room: Optional[Room] = None
    lab_slot: Optional[TimeSlot] = None
    lab_room: Optional[Room] = None
    
    def __hash__(self):
        return hash(self.code)
    
    def __eq__(self, other):
        if not isinstance(other, Course):
            return False
        return self.code == other.code
    
    def get_course_type_enum(self) -> CourseType:
        """Convert string type to CourseType enum."""
        type_map = {
            "mandatory": CourseType.MANDATORY,
            "departmental_elective": CourseType.DEPARTMENTAL_ELECTIVE,
            "ceng_elective": CourseType.CENG_ELECTIVE,
            "seng_elective": CourseType.SENG_ELECTIVE
        }
        return type_map.get(self.type, CourseType.MANDATORY)
    
    def is_scheduled(self) -> bool:
        """Check if course is fully scheduled."""
        # If course has theory hours, theory must be scheduled
        if self.theory_hours > 0:
            theory_scheduled = self.theory_slot is not None and self.theory_room is not None
            if not theory_scheduled:
                return False
        else:
            theory_scheduled = True  # No theory needed
        
        # If course has lab hours, lab must be scheduled
        if self.lab_hours > 0:
            lab_scheduled = self.lab_slot is not None and self.lab_room is not None
            return theory_scheduled and lab_scheduled
        
        return theory_scheduled


@dataclass
class ScheduleEntry:
    """Represents a single entry in the schedule grid."""
    course: Course
    room: Room
    time_slot: TimeSlot
    is_lab: bool  # True for lab sessions, False for theory
    duration_hours: int  # Duration in hours (typically 1 for theory, 2 for lab)


@dataclass
class Conflict:
    """Represents a scheduling conflict."""
    message: str
    entry1: Optional[ScheduleEntry] = None
    entry2: Optional[ScheduleEntry] = None
