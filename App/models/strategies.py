from datetime import datetime, timedelta, time
from abc import ABC, abstractmethod
from typing import List, Tuple
from App.models.schedule import Schedule
from App.models.staff import Staff
from App.models.shift import Shift

def is_day(start_time: datetime) ->bool:
    return start_time.hour < 12

class SchedulingStrategy(ABC):
    @abstractmethod
    def generate_shifts(self, schedule: Schedule, staff_list: List['Staff'], max_hours: float = 40.0) -> Tuple[List[Shift], List[str]]: # Max hours default 40 as that is the standard working hours here
        pass

        