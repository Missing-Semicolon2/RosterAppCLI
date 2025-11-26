from App.models import Staff, Shift
from App.database import db
from datetime import datetime
from App.controllers.user import get_user

def get_combined_roster(staff_id):
    staff = get_user(staff_id)
    if not isinstance(staff, Staff):
        raise PermissionError("Only staff can view roster")
    return staff.get_combined_roster()


def clock_in(staff_id, shift_id):
    staff = get_user(staff_id)
    if not isinstance(staff, Staff):
        raise PermissionError("Only staff can clock in")
    return staff.clock_in(shift_id)


def clock_out(staff_id, shift_id):
    staff = get_user(staff_id)
    if not isinstance(staff, Staff):
        raise PermissionError("Only staff can clock out")
    return staff.clock_out_shift(shift_id)

def get_shift(shift_id):
    return db.session.get(Shift, shift_id)