
from datetime import date, datetime

from reservations_connect.metronik.generated.metronik import RoomDescriptor, TimeDescriptor, TimetableTransfer
from reservations_connect.metronik.models import MetronikRoom



def generate_timetable_transfer(metronik_room: MetronikRoom, day: date) -> TimetableTransfer:
    # All reservations on this day in this room
    reservations = metronik_room.reservable.reservation_set.filter(
        start__gte=datetime.combine(day, datetime.min.time()), 
        end__lte=datetime.combine(day, datetime.max.time()), 
    )
    times = []
    for reservation in reservations:
        time_start = reservation.start.time()
        time_end = reservation.end.time()
        # Handle overnight reservations
        if reservation.start.date() < reservation.end.date():
            time_end = datetime.max.time()
        if reservation.start.date() > reservation.end.date():
            time_start = datetime.min.time()
        
        times.append(TimeDescriptor(
            occupied=True,
            from_value=time_start,
            to=time_end,
        ))
        
    return TimetableTransfer(
        room=RoomDescriptor(
            faculty=faculty_for_room(metronik_room),
            valid_from=date_from.strftime("%Y-%m-%d"),
            valid_to=date_to.strftime("%Y-%m-%d"), room=metronik_room.arhitektura,
            week_day=date_from.isoweekday(),
        ),
        times=times
    )


def faculty_for_room(metronik_room: MetronikRoom) -> str:
    if metronik_room.arhitetektura.startswith("R"):
        return "FRI"
    elif metronik_room.arhitetektura.startswith("K"):
        return "FKKT"
    return "X"
