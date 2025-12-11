# models/room.py
from dataclasses import dataclass

@dataclass
class Room:
    id: str
    name: str
    capacity: int
    room_type: str  # "lab" or "classroom"
    department: str # optional, if room primarily belongs to a dept
