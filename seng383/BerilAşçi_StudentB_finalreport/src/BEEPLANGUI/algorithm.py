"""Core scheduling algorithm with constraint satisfaction."""

from typing import List, Dict, Set, Optional, Tuple
from models import (
    Course, Instructor, Room, TimeSlot, ScheduleEntry, Conflict,
    CourseType
)
from collections import defaultdict


class ScheduleAlgorithm:
    """CSP-based scheduling algorithm for course timetabling."""
    
    # Time slots: Monday-Friday, 09:20-17:20 (8 hours)
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    HOURS = [9, 10, 11, 12, 13, 14, 15, 16]  # Starting hours
    MINUTE = 20
    
    # Friday ban: 13:20-15:10 (1:20 PM - 3:10 PM)
    FRIDAY_BAN_START = (13, 20)
    FRIDAY_BAN_END = (15, 10)
    
    def __init__(self, courses: List[Course], instructors: List[Instructor], rooms: List[Room]):
        """Initialize the scheduling algorithm."""
        self.courses = courses
        self.instructors = {inst.name: inst for inst in instructors}
        self.rooms = {room.id: room for room in rooms}
        
        # Track assignments
        self.schedule_entries: List[ScheduleEntry] = []
        self.instructor_schedule: Dict[str, List[ScheduleEntry]] = defaultdict(list)
        self.room_schedule: Dict[str, List[ScheduleEntry]] = defaultdict(list)
        
        # Track daily theory hours per instructor
        self.instructor_daily_theory: Dict[Tuple[str, str], int] = defaultdict(int)
    
    def is_friday_ban_violated(self, time_slot: TimeSlot, duration_hours: int) -> bool:
        """Check if time slot violates Friday ban (13:20-15:10)."""
        if time_slot.day != "Friday":
            return False
        
        start_minutes = time_slot.hour * 60 + time_slot.minute
        end_minutes = start_minutes + (duration_hours * 60)
        
        ban_start = self.FRIDAY_BAN_START[0] * 60 + self.FRIDAY_BAN_START[1]
        ban_end = self.FRIDAY_BAN_END[0] * 60 + self.FRIDAY_BAN_END[1]
        
        # Check if time slot overlaps with ban period
        return not (end_minutes <= ban_start or start_minutes >= ban_end)
    
    def time_slots_overlap(self, slot1: TimeSlot, duration1: int, 
                          slot2: TimeSlot, duration2: int) -> bool:
        """Check if two time slots overlap."""
        if slot1.day != slot2.day:
            return False
        
        start1 = slot1.hour * 60 + slot1.minute
        end1 = start1 + (duration1 * 60)
        start2 = slot2.hour * 60 + slot2.minute
        end2 = start2 + (duration2 * 60)
        
        return not (end1 <= start2 or end2 <= start1)
    
    def check_instructor_conflict(self, course: Course, time_slot: TimeSlot, 
                                  duration_hours: int) -> bool:
        """Check if instructor is already scheduled at this time."""
        instructor_name = course.instructor
        if instructor_name not in self.instructor_schedule:
            return False
        
        for entry in self.instructor_schedule[instructor_name]:
            if self.time_slots_overlap(time_slot, duration_hours, 
                                      entry.time_slot, entry.duration_hours):
                return True
        return False
    
    def check_room_conflict(self, room: Room, time_slot: TimeSlot, 
                           duration_hours: int) -> bool:
        """Check if room is already scheduled at this time."""
        if room.id not in self.room_schedule:
            return False
        
        for entry in self.room_schedule[room.id]:
            if self.time_slots_overlap(time_slot, duration_hours,
                                      entry.time_slot, entry.duration_hours):
                return True
        return False
    
    def check_instructor_daily_load(self, course: Course, time_slot: TimeSlot) -> bool:
        """Check if instructor exceeds daily theory hours limit."""
        instructor_name = course.instructor
        if instructor_name not in self.instructors:
            return False
        
        max_theory = self.instructors[instructor_name].max_theory_daily
        daily_key = (instructor_name, time_slot.day)
        current_load = self.instructor_daily_theory[daily_key]
        
        return (current_load + course.theory_hours) <= max_theory
    
    def check_lab_sequence(self, course: Course) -> bool:
        """Check if lab session is after theory session in the week."""
        if course.lab_hours == 0 or course.lab_slot is None or course.theory_slot is None:
            return True
        
        # Convert day to index for comparison
        day_order = {day: idx for idx, day in enumerate(self.DAYS)}
        theory_day_idx = day_order.get(course.theory_slot.day, -1)
        lab_day_idx = day_order.get(course.lab_slot.day, -1)
        
        if theory_day_idx == -1 or lab_day_idx == -1:
            return False
        
        # Lab must be on same day or later day
        if lab_day_idx < theory_day_idx:
            return False
        
        # If same day, lab must be after theory time
        if lab_day_idx == theory_day_idx:
            theory_start = course.theory_slot.hour * 60 + course.theory_slot.minute
            lab_start = course.lab_slot.hour * 60 + course.lab_slot.minute
            return lab_start > theory_start
        
        return True
    
    def check_elective_conflicts(self, course: Course, time_slot: TimeSlot, 
                                 duration_hours: int) -> bool:
        """Check conflicts between 3rd-year courses and departmental electives,
        and between CENG and SENG electives."""
        course_type = course.get_course_type_enum()
        
        for entry in self.schedule_entries:
            entry_course = entry.course
            entry_type = entry_course.get_course_type_enum()
            
            # Check if time slots overlap
            if not self.time_slots_overlap(time_slot, duration_hours,
                                          entry.time_slot, entry.duration_hours):
                continue
            
            # Rule: 3rd-year courses must not overlap with departmental electives
            if (course.year == 3 and course_type == CourseType.MANDATORY and
                entry_type == CourseType.DEPARTMENTAL_ELECTIVE):
                return True
            if (entry_course.year == 3 and entry_type == CourseType.MANDATORY and
                course_type == CourseType.DEPARTMENTAL_ELECTIVE):
                return True
            
            # Rule: CENG and SENG electives must not overlap
            if (course_type == CourseType.CENG_ELECTIVE and 
                entry_type == CourseType.SENG_ELECTIVE):
                return True
            if (course_type == CourseType.SENG_ELECTIVE and
                entry_type == CourseType.CENG_ELECTIVE):
                return True
        
        return False
    
    def check_room_capacity(self, course: Course, room: Room, is_lab: bool) -> bool:
        """Check if room capacity is sufficient."""
        if is_lab and course.lab_hours > 0:
            # Lab sessions strictly limited to 40 students per section
            # For courses with more students, we assume multiple sections
            # but schedule only one section at a time
            if room.type != "lab":
                return False
            # Lab room must have capacity <= 40 (strict limit)
            if room.capacity > 40:
                return False
            # For practical purposes, we allow scheduling if room capacity >= 40
            # (assuming the course will be split into multiple sections)
            return room.capacity >= 40
        
        # Theory sessions need sufficient capacity
        return room.capacity >= course.students
    
    def can_assign_theory(self, course: Course, time_slot: TimeSlot, room: Room) -> bool:
        """Check if theory session can be assigned."""
        # Check if course fits within time window (ends before 17:20)
        end_hour, end_minute = time_slot.get_end_time(course.theory_hours)
        if end_hour > 17 or (end_hour == 17 and end_minute > 20):
            return False
        
        # Check Friday ban
        if self.is_friday_ban_violated(time_slot, course.theory_hours):
            return False
        
        # Check instructor conflict
        if self.check_instructor_conflict(course, time_slot, course.theory_hours):
            return False
        
        # Check room conflict
        if self.check_room_conflict(room, time_slot, course.theory_hours):
            return False
        
        # Check room capacity
        if not self.check_room_capacity(course, room, False):
            return False
        
        # Check instructor daily load
        if not self.check_instructor_daily_load(course, time_slot):
            return False
        
        # Check elective conflicts
        if self.check_elective_conflicts(course, time_slot, course.theory_hours):
            return False
        
        return True
    
    def can_assign_lab(self, course: Course, time_slot: TimeSlot, room: Room) -> bool:
        """Check if lab session can be assigned."""
        # If course has theory hours, theory must be scheduled first
        # If course has 0 theory hours, lab can be scheduled independently
        if course.theory_hours > 0 and course.theory_slot is None:
            return False
        
        # Check if course fits within time window (ends before 17:20)
        end_hour, end_minute = time_slot.get_end_time(course.lab_hours)
        if end_hour > 17 or (end_hour == 17 and end_minute > 20):
            return False
        
        # Check Friday ban
        if self.is_friday_ban_violated(time_slot, course.lab_hours):
            return False
                # Validate that theory session is scheduled before lab (if course has theory)
        if course.theory_hours > 0 and course.theory_slot:
            day_order = {day: idx for idx, day in enumerate(self.DAYS)}
            theory_day_idx = day_order.get(course.theory_slot.day, -1)
            lab_day_idx = day_order.get(time_slot.day, -1)
            
            # Lab must be on same day or later than theory
            if lab_day_idx < theory_day_idx:
                return False
            
            # If same day, lab must be after theory
            if lab_day_idx == theory_day_idx:
                theory_start = course.theory_slot.hour * 60 + course.theory_slot.minute
                lab_start = time_slot.hour * 60 + time_slot.minute
                if lab_start <= theory_start:
                    return False
        
        # Check instructor conflict
        if self.check_instructor_conflict(course, time_slot, course.lab_hours):
            return False
        
        # Check room conflict
        if self.check_room_conflict(room, time_slot, course.lab_hours):
            return False
        
        # Check room capacity (strict 40 limit for labs)
        if not self.check_room_capacity(course, room, True):
            return False
        
        # Check elective conflicts
        if self.check_elective_conflicts(course, time_slot, course.lab_hours):
            return False
        
        return True
    
    def add_schedule_entry(self, course: Course, room: Room, time_slot: TimeSlot,
                          is_lab: bool, duration_hours: int) -> None:
        """Add a schedule entry and update tracking structures."""
        entry = ScheduleEntry(course, room, time_slot, is_lab, duration_hours)
        self.schedule_entries.append(entry)
        self.instructor_schedule[course.instructor].append(entry)
        self.room_schedule[room.id].append(entry)
        
        if not is_lab:
            daily_key = (course.instructor, time_slot.day)
            self.instructor_daily_theory[daily_key] += duration_hours
    
    def remove_schedule_entry(self, entry: ScheduleEntry) -> None:
        """Remove a schedule entry and update tracking structures."""
        if entry in self.schedule_entries:
            self.schedule_entries.remove(entry)
            if entry in self.instructor_schedule[entry.course.instructor]:
                self.instructor_schedule[entry.course.instructor].remove(entry)
            if entry in self.room_schedule[entry.room.id]:
                self.room_schedule[entry.room.id].remove(entry)
            
            if not entry.is_lab:
                daily_key = (entry.course.instructor, entry.time_slot.day)
                self.instructor_daily_theory[daily_key] -= entry.duration_hours
    
    def get_available_rooms(self, course: Course, is_lab: bool) -> List[Room]:
        """Get list of available rooms for a course."""
        available = []
        for room in self.rooms.values():
            if is_lab and room.type != "lab":
                continue
            if not is_lab and room.type == "lab":
                continue  # Theory should be in classrooms
            if self.check_room_capacity(course, room, is_lab):
                available.append(room)
        return available
    
    def generate_schedule(self) -> Tuple[bool, List[str]]:
        self.courses.sort(key=lambda c: (c.year, c.code, 1 if getattr(c, 'type', '') == 'lab' else 0)) 
        
        """Generate schedule using backtracking algorithm.
        
        Returns:
            Tuple of (success: bool, messages: List[str])
        """
        # Reset previous schedule
        self.schedule_entries = []
        self.instructor_schedule = defaultdict(list)
        self.room_schedule = defaultdict(list)
        self.instructor_daily_theory = defaultdict(int)
        
        # Sort courses for better backtracking efficiency:
        # 1. Mandatory before elective
        # 2. Lower year before higher year
        # 3. Courses with fewer constraints first (theory-only before lab, smaller duration)
        # 4. Within electives: CENG before SENG before departmental (to minimize conflicts)
        def course_priority(c):
            type_priority = {
                "mandatory": 0,
                "ceng_elective": 1,
                "seng_elective": 2,
                "departmental_elective": 3
            }
            return (
                type_priority.get(c.type, 99),  # Mandatory first
                c.year,  # Lower years first
                c.lab_hours > 0,  # Theory-only before lab courses
                -(c.theory_hours + c.lab_hours),  # Shorter courses first (negative for descending)
                c.code  # Alphabetical as tie-breaker
            )
        
        courses_to_schedule = sorted(self.courses, key=course_priority)
        
        messages = []
        success = self._backtrack(courses_to_schedule, 0, messages)
        
        return success, messages
    
    def _backtrack(self, courses: List[Course], index: int, messages: List[str]) -> bool:
        """Backtracking algorithm to assign courses."""
        if index >= len(courses):
            return True
        
        course = courses[index]
        
        # Try to schedule theory first (only if course has theory hours)
        if course.theory_hours > 0 and course.theory_slot is None:
            theory_assigned = self._try_assign_theory(course)
            if not theory_assigned:
                messages.append(f"Could not schedule theory for {course.code}")
                return False
        
        # Try to schedule lab if needed
        if course.lab_hours > 0 and course.lab_slot is None:
            lab_assigned = self._try_assign_lab(course)
            if not lab_assigned:
                # Unassign theory to try different combination
                if course.theory_slot:
                    self._unassign_theory(course)
                messages.append(f"Could not schedule lab for {course.code}")
                return False
        
        # Verify lab sequence constraint (only if both theory and lab exist)
        if course.lab_hours > 0 and course.theory_hours > 0 and not self.check_lab_sequence(course):
            self._unassign_course(course)
            messages.append(f"Lab sequence violation for {course.code}")
            return False
        
        # Recursively schedule next course
        if self._backtrack(courses, index + 1, messages):
            return True
        
        # Backtrack: unassign current course
        self._unassign_course(course)
        return False
    
    def _try_assign_theory(self, course: Course) -> bool:
        """Try to assign theory session to course."""
        available_rooms = self.get_available_rooms(course, False)
        
        for day in self.DAYS:
            for hour in self.HOURS:
                time_slot = TimeSlot(day, hour, self.MINUTE)
                
                for room in available_rooms:
                    if self.can_assign_theory(course, time_slot, room):
                        course.theory_slot = time_slot
                        course.theory_room = room
                        self.add_schedule_entry(course, room, time_slot, False, course.theory_hours)
                        return True
        
        return False
    
    def _try_assign_lab(self, course: Course) -> bool:
        """Try to assign lab session to course."""
        # If course has theory hours, theory must be scheduled first
        # If course has 0 theory hours, lab can be scheduled independently
        if course.theory_hours > 0 and course.theory_slot is None:
            return False
        
        available_rooms = self.get_available_rooms(course, True)
        day_order = {day: idx for idx, day in enumerate(self.DAYS)}
        
        # If theory exists, lab must be on same day or later
        # If no theory (theory_hours = 0), lab can be scheduled on any day
        if course.theory_slot:
            theory_day_idx = day_order.get(course.theory_slot.day, 0)
            start_day_idx = theory_day_idx
        else:
            start_day_idx = 0
        
        # Lab must be on same day or later (if theory exists)
        for day_idx in range(start_day_idx, len(self.DAYS)):
            day = self.DAYS[day_idx]
            
            for hour in self.HOURS:
                time_slot = TimeSlot(day, hour, self.MINUTE)
                
                # If same day and theory exists, lab must be after theory
                if course.theory_slot and day_idx == day_order.get(course.theory_slot.day, 0):
                    theory_start = course.theory_slot.hour * 60 + course.theory_slot.minute
                    lab_start = time_slot.hour * 60 + time_slot.minute
                    if lab_start <= theory_start:
                        continue
                
                for room in available_rooms:
                    if self.can_assign_lab(course, time_slot, room):
                        course.lab_slot = time_slot
                        course.lab_room = room
                        self.add_schedule_entry(course, room, time_slot, True, course.lab_hours)
                        return True
        
        return False
    
    def _unassign_theory(self, course: Course) -> None:
        """Unassign theory session from course."""
        if course.theory_slot and course.theory_room:
            # Find and remove entry
            for entry in self.schedule_entries[:]:
                if (entry.course == course and not entry.is_lab):
                    self.remove_schedule_entry(entry)
                    break
            course.theory_slot = None
            course.theory_room = None
    
    def _unassign_lab(self, course: Course) -> None:
        """Unassign lab session from course."""
        if course.lab_slot and course.lab_room:
            # Find and remove entry
            for entry in self.schedule_entries[:]:
                if (entry.course == course and entry.is_lab):
                    self.remove_schedule_entry(entry)
                    break
            course.lab_slot = None
            course.lab_room = None
    
    def _unassign_course(self, course: Course) -> None:
        """Unassign both theory and lab from course."""
        self._unassign_theory(course)
        self._unassign_lab(course)
    
    def validate_schedule(self) -> List[Conflict]:
        """Validate the current schedule and return list of conflicts."""
        conflicts = []
        
        for course in self.courses:
            # Check if course is scheduled
            if not course.is_scheduled():
                conflicts.append(Conflict(f"Course {course.code} is not fully scheduled"))
                continue
            
            # Check Friday ban for theory
            if course.theory_slot and course.theory_room:
                if self.is_friday_ban_violated(course.theory_slot, course.theory_hours):
                    entry = ScheduleEntry(course, course.theory_room, course.theory_slot, False, course.theory_hours)
                    conflicts.append(Conflict(
                        f"Friday ban violation: {course.code} theory scheduled during exam period (13:20-15:10)",
                        entry, None
                    ))
            
            # Check Friday ban for lab
            if course.lab_slot and course.lab_room:
                if self.is_friday_ban_violated(course.lab_slot, course.lab_hours):
                    entry = ScheduleEntry(course, course.lab_room, course.lab_slot, True, course.lab_hours)
                    conflicts.append(Conflict(
                        f"Friday ban violation: {course.code} lab scheduled during exam period (13:20-15:10)",
                        entry, None
                    ))
            
            # Check lab sequence (only if both theory and lab exist)
            if course.lab_hours > 0 and course.theory_hours > 0 and not self.check_lab_sequence(course):
                conflicts.append(Conflict(f"Lab sequence violation for {course.code}"))
        
        # Check for overlaps
        for i, entry1 in enumerate(self.schedule_entries):
            for entry2 in self.schedule_entries[i+1:]:
                if entry1.time_slot.day == entry2.time_slot.day:
                    if self.time_slots_overlap(entry1.time_slot, entry1.duration_hours,
                                              entry2.time_slot, entry2.duration_hours):
                        # Check instructor conflict
                        if entry1.course.instructor == entry2.course.instructor:
                            conflicts.append(Conflict(
                                f"Instructor {entry1.course.instructor} double-booking: {entry1.course.code} and {entry2.course.code} at same time",
                                entry1, entry2
                            ))
                        # Check room conflict
                        if entry1.room == entry2.room:
                            conflicts.append(Conflict(
                                f"Room {entry1.room.id} double-booking: {entry1.course.code} and {entry2.course.code} at same time",
                                entry1, entry2
                            ))
        
        return conflicts
