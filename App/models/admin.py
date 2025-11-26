from datetime import datetime
from App.database import db
from .user import User
from App.models import Schedule, Shift, Staff
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
        new_schedule = Schedule(name=name, created_by=self.id, created_at=datetime.utcnow(), start_date=start_date)
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

    def get_shift_report(self):
        return [shift.get_json() for shift in Shift.query.order_by(Shift.start_time).all()]