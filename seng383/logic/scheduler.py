# logic/scheduler.py
from typing import Dict, List, Optional, Tuple
from models.schedule import Schedule, ScheduledItem
from models.timeslot import TimeSlot, DAYS
from models.course import Course
from models.room import Room
from logic.validators import validate_friday_exam

class Scheduler:
    def __init__(self, courses: Dict[str, Course], rooms: List[Room], instructor_avail: Dict[str, Dict[str, List[Tuple[int,int]]]]):
        self.courses = courses
        self.rooms = rooms
        self.instructor_avail = instructor_avail

    def available_rooms(self, course_part: str) -> List[Room]:
        if course_part == "lab":
            return [r for r in self.rooms if r.room_type == "lab"]
        return [r for r in self.rooms if r.room_type == "classroom"]

    def instructor_free(self, course: Course, ts: TimeSlot) -> bool:
        # Check within declared availability ranges
        day_ranges = self.instructor_avail.get(course.instructor_id, {}).get(ts.day, [])
        return any(start <= ts.hour_index <= end for (start, end) in day_ranges)

    def generate(self, years: List[int]) -> Schedule:
        schedule = Schedule()
        # Heuristic: place theory hours first, then labs; prefer consecutive labs
        for year in years:
            year_courses = [c for c in self.courses.values() if c.year == year]
            # sort by constraints complexity (labs first for room scarcity)
            year_courses.sort(key=lambda c: (c.weekly_lab_hours > 0, -c.weekly_theory_hours), reverse=True)

            for course in year_courses:
                # Place theory blocks
                self._place_blocks(schedule, year, course, "theory", course.weekly_theory_hours)
                # Place lab blocks
                self._place_blocks(schedule, year, course, "lab", course.weekly_lab_hours, prefer_consecutive=True)
        return schedule

    def _place_blocks(self, schedule: Schedule, year: int, course: Course, part: str, hours: int, prefer_consecutive: bool=False):
        placed = 0
        rooms = self.available_rooms(part)
        for day in DAYS:
            # Skip Friday exam window for all parts
            hour_range = list(range(1, 11))
            if prefer_consecutive:
                hour_range = [i for i in hour_range if i+1 <= 10]  # allow 2-hour consecutive
            for h in hour_range:
                ts = TimeSlot(day=day, hour_index=h)
                if validate_friday_exam(ts):  # returns issues list; treat as forbidden
                    continue
                if schedule.occupied(year, ts):
                    continue
                if not self.instructor_free(course, ts):
                    continue
                # find a room
                for room in rooms:
                    # simple lab-after-theory preference: if lab, require existing theory earlier in the week or same day
                    if part == "lab":
                        has_theory_prior = any(
                            it.course_part == "theory"
                            for (_, tslot), it in schedule.grid.items()
                            if it.course_code == course.code and (tslot.day < ts.day or (tslot.day == ts.day and tslot.hour_index < ts.hour_index))
                        )
                        if not has_theory_prior:
                            continue
                    schedule.place(year, ts, ScheduledItem(course_code=course.code, course_part=part, room_id=room.id))
                    placed += 1
                    if prefer_consecutive and placed < hours:
                        # Attempt to place next consecutive hour immediately
                        ts2 = TimeSlot(day=day, hour_index=h+1)
                        if not schedule.occupied(year, ts2) and self.instructor_free(course, ts2):
                            schedule.place(year, ts2, ScheduledItem(course_code=course.code, course_part=part, room_id=room.id))
                            placed += 1
                    if placed >= hours:
                        return
        # If not fully placed, we leave remaining for backtracking improvements
