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
    def generate_shifts(self, schedule: Schedule, staff_list: List['Staff'], max_hours: float = 40.0): # Max hours default 40 as that is the standard working hours here
        pass

class EvenDistributionStrategy(SchedulingStrategy):
    def generate_shifts(self, schedule, staff_list, max_hours = 40):
        return self()._generate_shifts(schedule, staff_list, strategy_type='even_distribution', max_hours = max_hours)
    
    def _generate_shifts(self, schedule: Schedule, staff_list: List['Staff'], strategy_type: str, max_hour: float):
        if not staff_list:
            return [], ["No Staff Available for Roster, Boss :("]
        shifts: List[Shift] = []
        warnings: List[str] = []
        start_date = schedule.start_date