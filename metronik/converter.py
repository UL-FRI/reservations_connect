
from datetime import date, datetime, timedelta

from reservations_connect.metronik.generated.metronik import ArrayOfTimeDescriptor, RoomDescriptor, TimeDescriptor, TimetableTransfer
from reservations_connect.metronik.models import MetronikRoom

HOUR_FORMAT = "%H:%M:%S"
DAY_FORMAT = "%Y-%m-%d"


def generate_timetable_transfer(metronik_room: MetronikRoom, day: date) -> TimetableTransfer:
    # All reservations on this day in this room
    reservations = metronik_room.reservable.reservations.filter(
        start__gte=datetime.combine(day, datetime.min.time()), 
        end__lte=datetime.combine(day, datetime.max.time()), 
    )

    date_from = datetime.combine(day, datetime.min.time())
    # Veljavnost je po prosnji metronic ne 1, ampak 10 dni.
    date_to = datetime.combine(day, datetime.max.time()) + timedelta(days=10)
    
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
            from_value=time_start.strftime(HOUR_FORMAT),
            to=time_end.strftime(HOUR_FORMAT),
        ))
        
    return TimetableTransfer(
        room=RoomDescriptor(
            faculty=faculty_for_room(metronik_room),
            valid_from=date_from.strftime(DAY_FORMAT),
            valid_to=date_to.strftime(DAY_FORMAT), 
            room=metronik_room.arhitektura,
            week_day=date_from.isoweekday(),
        ),
        times=ArrayOfTimeDescriptor(
            time_descriptor=times,
        )
    )


def faculty_for_room(metronik_room: MetronikRoom) -> str:
    if metronik_room.arhitektura.startswith("R"):
        return "FRI"
    elif metronik_room.arhitektura.startswith("K"):
        return "FKKT"
    return "X"
