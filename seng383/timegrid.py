# beeplan/core/timegrid.py
from typing import List, Dict, Tuple
from .models import CommonSchedule, TimeSlot

# Çankaya slot times (index 1..8)
SLOT_TIMES: Dict[int, Tuple[str, str]] = {
    1: ("09:30", "10:20"),
    2: ("10:30", "11:20"),
    3: ("11:30", "12:20"),
    4: ("12:30", "13:20"),
    5: ("13:30", "14:20"),
    6: ("14:30", "15:20"),
    7: ("15:30", "16:20"),
    8: ("16:30", "17:20"),
}

def common_schedule_cankaya(slots_per_day: int = 8) -> CommonSchedule:
    """
    Çankaya: Mon..Fri grid; Friday exam block 13:20–15:10 overlaps slots 5 and 6.
    """
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    forbidden = [TimeSlot(day="Fri", index=5), TimeSlot(day="Fri", index=6)]
    return CommonSchedule(days=days, slots_per_day=slots_per_day, forbidden_slots=forbidden)

def enumerate_all_slots(common: CommonSchedule) -> List[TimeSlot]:
    forb = {(ts.day, ts.index) for ts in common.forbidden_slots}
    return [TimeSlot(d, i)
            for d in common.days
            for i in range(1, common.slots_per_day + 1)
            if (d, i) not in forb]
