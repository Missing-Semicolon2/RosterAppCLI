from datetime import datetime, timedelta, time
from abc import ABC, abstractmethod
from typing import List, Tuple
from App.models.staff import Staff
from App.models.shift import Shift
from App.models.schedule import Schedule

def is_day(start_time: datetime):
    return start_time.hour < 12

_strategy_registry = {}

# Note Decorator Design Pattern implemented cause I wanted to try and make it more extensible(...sigh)
def register_strategy(strategy_type: str):
    def decorator(cls):
        _strategy_registry[strategy_type] = cls
        return cls
    return decorator

class SchedulingStrategy(ABC):
    @abstractmethod
    def generate_shifts(self, schedule: Schedule, staff_list: List[Staff], max_hours: float = 40.0): # Max hours default 40 as that is the standard working hours here
        pass

class EvenDistributionStrategy(SchedulingStrategy):
    def generate_shifts(self, schedule, staff_list, max_hours = 40):
        return self()._generate_shifts(schedule, staff_list, strategy_type='even_distribution', max_hours = max_hours)
    
    def _generate_shifts(self, schedule: Schedule, staff_list: List[Staff], strategy_type: str, max_hours: float, shift_starts: List[time], shift_hours: int):
        if not staff_list:
            return [], ["No Staff Available for Roster, Boss :("]
        
        shifts: List[Shift] = []
        warnings: List[str] = []
        start_date = schedule.start_date
        assigned_shifts: List[Shift] = []
        shift_len = timedelta(hours = shift_hours)
        slots = []

        for d in range(7):
            day = start_date + timedelta(days = d)
            for st in shift_starts:
                start_time = datetime.combine(day, st)
                end_time = start_time + shift_len
                slot_type = 'day' if is_day(start_time) else 'night'
                slots.append((start_time, end_time, slot_type))
            
        for slot in slots:
            start, end, slot_type = slot
            staff = self._assign_shift_to_staff(start, end, slot_type, staff_list, assigned_shifts, strategy_type)
            if staff:
                shift = Shift(staff_id=staff.id, schedule_id=schedule.id, start_time=start, end_time=end)
                assigned_shifts.append(shift)
                shifts.append(shift)
            else:
                warnings.append(f"Could not assign staff to slot {start} - {end}")

        # Post assignment checks; honestly, just extra complexity I am adding...sigh
        warnings.extend(self._post_assignment_checks(schedule, staff_list, assigned_shifts, max_hours))
        return shifts, warnings

    def _assign_shift_to_staff(self, start: datetime, end: datetime, slot_type: str, staff_list: List[Staff], assigned_shifts: List[Shift], strategy_type: str):
        shift_hours = (end - start).total_seconds() / 3600
        candidates = []

        for staff in staff_list:
            staff_assigned = [s for s in assigned_shifts if s.staff_id == staff.id]
            # Checking if each staff member has one shift per day
            if any(s.start_time.date() == start.date() for s in staff_assigned):
                continue
            # 
            num_shifts = len(staff_assigned)
            current_hours = sum((s.end_time - s.start_time).total_seconds() / 3600 for s in staff_assigned)
            num_days = len(set(s.start_time.date() for s in staff_assigned))
            base_key = (num_shifts, current_hours) if strategy_type != 'minimize_day' else (num_days, current_hours)
            if strategy_type == 'balance_day_night':
                day_count = sum(1 for s in staff_assigned if is_day(s.start_time))
                night_count = num_shifts - day_count
                balance_diff = day_count - night_count if slot_type == 'night' else night_count - day_count
                key = (balance_diff, *base_key)
            else:
                key = base_key
            candidates.append((staff, key))

        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
    
    def _post_assignment_checks(self, schedule: Schedule, staff_list: List[Staff], assigned_shifts: List[Shift], max_hours: float):
        warnings = []
        all_days = [schedule.start_date + timedelta(days=d) for d in range(7)]
        
        for staff in staff_list:
            staff_assigned = [s for s in assigned_shifts if s.staff_id == staff.id]
            current_hours = sum((s.end_time - s.start_time).total_seconds() / 3600 for s in staff_assigned)
            
            if current_hours > max_hours:
                warnings.append(f"Staff {staff.username} exceeds max weekly hours: {current_hours} > {max_hours}")
            work_days = set(s.start_time.date() for s in staff_assigned)
            off_days = sorted([d for d in all_days if d not in work_days])
            
            if len(off_days) < 2:
                warnings.append(f"Staff {staff.username} has fewer than 2 off days")
                continue
            has_consec = any((off_days[i+1] - off_days[i]).days == 1 for i in range(len(off_days)-1))
            if not has_consec:
                warnings.append(f"Staff {staff.username} does not have two consecutive off days")
        return warnings

@register_strategy('even_distribution')
class EvenDistributionStrategy(SchedulingStrategy):
    def generate_shifts(self, schedule: Schedule, staff_list: List[Staff], max_hours: float = 40.0) -> Tuple[List[Shift], List[str]]:
        shift_starts = [time(0, 0), time(8, 0), time(16, 0)]
        shift_hours = 8
        return self._generate_shifts(schedule, staff_list, 'even_distribution', max_hours, shift_starts, shift_hours)

@register_strategy('minimize_day')
class MinimizeDayStrategy(SchedulingStrategy):
    def generate_shifts(self, schedule: Schedule, staff_list: List[Staff], max_hours: float = 40.0) -> Tuple[List[Shift], List[str]]:
        shift_starts = [time(6, 0), time(18, 0)]
        shift_hours = 12
        return self._generate_shifts(schedule, staff_list, 'minimize_day', max_hours, shift_starts, shift_hours)

@register_strategy('balance_day_night')
class BalanceDayNightStrategy(SchedulingStrategy):
    def generate_shifts(self, schedule: Schedule, staff_list: List[Staff], max_hours: float = 40.0) -> Tuple[List[Shift], List[str]]:
        shift_starts = [time(6, 0), time(18, 0)]
        shift_hours = 12
        return self._generate_shifts(schedule, staff_list, 'balance_day_night', max_hours, shift_starts, shift_hours)