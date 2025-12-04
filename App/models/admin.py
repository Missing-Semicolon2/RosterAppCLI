from datetime import datetime
from sqlalchemy import func
from App.database import db
from .user import User
# from App.models import Schedule, Shift, Staff
from App.models.schedule import Schedule
from App.models.shift import Shift
from App.models.staff import Staff
from App.models.strategies import _strategy_registry

class Admin(User):
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "admin")

    def create_schedule(self, name, start_date_str):
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        new_schedule = Schedule(name=name, created_by=self.id, created_at=datetime.now(), start_date=start_date)
        db.session.add(new_schedule)
        db.session.commit()
        return new_schedule

    def generate_auto_schedule(self, schedule_id, strategy_type, max_hours=40.0):
        schedule = db.session.get(Schedule, schedule_id)
        if not schedule:
            raise ValueError("Invalid schedule ID")
        if strategy_type not in _strategy_registry:
            raise ValueError(f"Invalid strategy type: {strategy_type}")
        strategy_cls = _strategy_registry[strategy_type]
        strategy = strategy_cls()
        schedule.strategy_type = strategy_type
        staff_list = Staff.query.all()
        shifts, warnings = strategy.generate_shifts(schedule, staff_list, max_hours)
        # Do not commit yet; return for confirmation
        return shifts, warnings, schedule

    def get_shift_report(self, schedule_id):
        schedule = db.session.get(Schedule, schedule_id)
        if not schedule:
            raise ValueError("Invalid Schedule ID")

        staff_shifts = db.session.query(
            Staff.id,
            Staff.username,
            func.count(Shift.id).label('shift_count'),
            func.sum(
                func.case(
                    [(Shift.clock_out.isnot(None), (func.extract('epoch', Shift.clock_out - Shift.clock_in) / 3600.0))],
                    else_=0.0
                )
            ).label('total_hours')
        ).join(Shift, Shift.staff_id == Staff.id) \
         .filter(Shift.schedule_id == schedule_id) \
         .filter(Shift.clock_in.isnot(None), Shift.clock_out.isnot(None)).group_by(Staff.id, Staff.username) \
         .all()
        
        report = []
        for staff_id, username, shift_count, total_hours in staff_shifts:
            report.append({
                'username': username,
                'total_hours_worked': round(total_hours, 2),  # Rounded because we are human not machines(sort of)
                'number_of_shifts_worked': shift_count
            })
        
        # Include staff with 0 shifts/hours
        all_staff = Staff.query.all()
        reported_usernames = {r['username'] for r in report}
        for staff in all_staff:
            if staff.username not in reported_usernames:
                report.append({
                    'username': staff.username,
                    'total_hours_worked': 0.0,
                    'number_of_shifts_worked': 0
                }) 
        
        return sorted(report, key=lambda x: x['username'])