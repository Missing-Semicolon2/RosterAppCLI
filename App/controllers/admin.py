from App.models import Admin, Shift, Staff, Schedule
from App.database import db
from datetime import datetime
from App.controllers.user import get_user

def create_schedule(admin_id, schedule_name, start_date_str): #Not sure why this was missing # Modified
    admin = get_user(admin_id)
    if not isinstance(admin, Admin):
        raise PermissionError("Only admins can create schedules")

    return admin.create_schedule(schedule_name, start_date_str)

def generate_auto_schedule(admin_id, schedule_id, strategy_type, max_hours = 40.0):
    admin = get_user(admin_id)
    if not isinstance(admin, Admin):
        raise PermissionError("Only admins can generate auto schedules")
    shifts, warnings, schedule = admin.generate_auto_schedule(schedule_id, strategy_type, max_hours)
    # Return for frontend to confirm
    return {
        'shifts': [shift.get_json() for shift in shifts],
        'warnings': warnings,
        'schedule_id': schedule.id
    }

def confirm_auto_schedule(admin_id, schedule_id, confirm: bool, shifts):
    admin = get_user(admin_id)
    if not isinstance(admin, Admin):
        raise PermissionError("Only admins can confirm schedules")
    schedule = db.session.get(Schedule, schedule_id)
    if not schedule:
        raise ValueError("Invalid schedule ID")
    
    if confirm:
        for shift in shifts:
            db.session.add(shift)
        db.session.commit()
        return {'message': 'Schedule confirmed and saved'}
    else:
        db.session.rollback()
        return {'message': 'Schedule generation canceled'}

def schedule_shift(admin_id, staff_id, schedule_id, start_time, end_time):
    admin = get_user(admin_id)
    staff = get_user(staff_id)

    schedule = db.session.get(Schedule, schedule_id)

    if not isinstance(admin, Admin):
        raise PermissionError("Only admins can schedule shifts")
    if not isinstance(staff, Staff):
        raise ValueError("Invalid staff member")
    if not schedule:
        raise ValueError("Invalid schedule ID")

    new_shift = Shift(
        staff_id=staff_id,
        schedule_id=schedule_id,
        start_time=start_time,
        end_time=end_time
    )

    db.session.add(new_shift)
    db.session.commit()

    return new_shift


def get_shift_report(admin_id):
    admin = get_user(admin_id)
    if not isinstance(admin, Admin):
        raise PermissionError("Only admins can view shift reports")

    return admin.get_shift_report()
