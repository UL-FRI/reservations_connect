
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from reservations_connect.metronik.generated.metronik import (
    ArrayOfTimeDescriptor,
    RoomDescriptor,
    TimeDescriptor,
    TimetableTransfer,
    WebServiceSoapTimetableTransferInput,
)
from reservations_connect.metronik.models import MetronikRoom

HOUR_FORMAT = "%H:%M:%S"
DAY_FORMAT = "%Y-%m-%d"

# From the WSDL: soap:operation soapAction and soap:address location.
METRONIK_SOAP_ACTION = "http://www.metronik.si/TimetableTransfer"
METRONIK_SOAP_ENDPOINT = "http://192.168.190.81/Fri.Webservice/webservice.asmx"

# Metronik is a physical box in Ljubljana - always use its local time for the
# schedule, regardless of the server's or Django's configured timezone.
METRONIK_TZ = ZoneInfo("Europe/Ljubljana")


def generate_timetable_transfer(metronik_room: MetronikRoom, day: date) -> TimetableTransfer:
    # Day boundaries in Europe/Ljubljana (metronik's local time), not whatever
    # zone the server or Django happens to be configured with.
    date_from = datetime.combine(day, datetime.min.time(), tzinfo=METRONIK_TZ)
    date_to_boundary = datetime.combine(day, datetime.max.time(), tzinfo=METRONIK_TZ)

    # All reservations on this day in this room
    reservations = metronik_room.reservable.reservations.filter(
        start__gte=date_from,
        end__lte=date_to_boundary,
    )

    # Veljavnost je po prosnji metronic ne 1, ampak 10 dni.
    date_to = date_to_boundary + timedelta(days=10)

    times = []
    for reservation in reservations:
        start = reservation.start.astimezone(METRONIK_TZ)
        end = reservation.end.astimezone(METRONIK_TZ)
        time_start = start.time()
        time_end = end.time()
        # Handle overnight reservations
        if start.date() < end.date():
            time_end = datetime.max.time()
        if start.date() > end.date():
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


def generate_soap_envelope(metronik_room: MetronikRoom, day: date) -> WebServiceSoapTimetableTransferInput:
    """Wrap a TimetableTransfer in the SOAP envelope metronik's webservice.asmx expects."""
    transfer = generate_timetable_transfer(metronik_room, day)
    return WebServiceSoapTimetableTransferInput(
        body=WebServiceSoapTimetableTransferInput.Body(timetable_transfer=transfer)
    )


def faculty_for_room(metronik_room: MetronikRoom) -> str:
    if metronik_room.arhitektura.startswith("R"):
        return "FRI"
    elif metronik_room.arhitektura.startswith("K"):
        return "FKKT"
    return "X"
