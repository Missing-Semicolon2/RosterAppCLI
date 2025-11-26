from datetime import datetime
from App.database import db
from .user import User
from App.models import Shift

class Staff(User):
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "staff",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "staff")

    def get_combined_roster(self):
        return [shift.get_json() for shift in self.shifts]

    def clock_in(self, shift_id):
        shift = db.session.get(Shift, shift_id)
        if not shift or shift.staff_id != self.id:
            raise ValueError("Invalid shift for staff")
        shift.clock_in = datetime.now()
        db.session.commit()
        return shift

    def clock_out_shift(self, shift_id):
        shift = db.session.get(Shift, shift_id)
        if not shift or shift.staff_id != self.id:
            raise ValueError("Invalid shift for staff")
        shift.clock_out = datetime.now()
        db.session.commit()
        return shift