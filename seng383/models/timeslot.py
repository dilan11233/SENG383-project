# models/timeslot.py
from dataclasses import dataclass

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

@dataclass(frozen=True)
class TimeSlot:
    day: str           # "Mon".."Fri"
    hour_index: int    # integer index for hour block (e.g., 1..10)

# Example mapping: hour_index -> clock times defined centrally for GUI and rules
TIME_BLOCKS = {
    1: "08:30–09:20",
    2: "09:30–10:20",
    3: "10:30–11:20",
    4: "11:30–12:20",
    5: "12:30–13:20",
    6: "13:30–14:20",
    7: "14:30–15:20",
    8: "15:30–16:20",
    9: "16:30–17:20",
    10: "17:30–18:20",
}
