# beeplan/core/timegrid.py
from typing import List
from .models import CommonSchedule, TimeSlot

def default_common_schedule(slots_per_day: int = 8) -> CommonSchedule:
    """
    Create a default Mon..Fri grid with Friday exam block (13:20–15:10)
    mapped to slots 6 and 7 by convention.
    """
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    forbidden = [TimeSlot(day="Fri", index=6), TimeSlot(day="Fri", index=7)]
    return CommonSchedule(days=days, slots_per_day=slots_per_day, forbidden_slots=forbidden)

def enumerate_all_slots(common: CommonSchedule) -> List[TimeSlot]:
    """Return all valid slots excluding forbidden ones."""
    forb = {(ts.day, ts.index) for ts in common.forbidden_slots}
    slots: List[TimeSlot] = []
    for d in common.days:
        for i in range(1, common.slots_per_day + 1):
            if (d, i) not in forb:
                slots.append(TimeSlot(day=d, index=i))
    return slots
