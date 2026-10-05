
from datetime import date, timedelta

from django.http.response import HttpResponse, JsonResponse
from django.utils.timezone import datetime

from reservations_connect.metronik.converter import (
    METRONIK_SOAP_ACTION,
    METRONIK_SOAP_ENDPOINT,
    generate_soap_envelope,
    generate_timetable_transfer,
)
from reservations_connect.metronik.models import MetronikRoom

from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

# /api/metronik/debug?room={room_id}&date={date}
def metronik_debug(request):
    room = MetronikRoom.objects.get(pk=request.GET['room'])
    date_str = request.GET.get('date')
    day = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()

    transfer = generate_timetable_transfer(room, day)

    config = SerializerConfig(indent="\t")
    context = XmlContext()
    serializer = XmlSerializer(context=context, config=config)

    return HttpResponse(serializer.render(transfer), content_type="application/xml")


DAYS_AHEAD = 7

# /api/metronik/payloads?date={date}
# For every room that has a mapped reservable, returns the ready-to-send SOAP
# envelopes for the relay script to forward to the Metronik service - one per
# room for each of the next DAYS_AHEAD days, starting tomorrow relative to
# `date` (today by default).
def metronik_payloads(request):
    date_str = request.GET.get('date')
    base_day = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    days = [base_day + timedelta(days=offset) for offset in range(1, DAYS_AHEAD + 1)]

    context = XmlContext()
    serializer = XmlSerializer(context=context, config=SerializerConfig(xml_declaration=True))

    payloads = []
    for room in MetronikRoom.objects.select_related("reservable"):
        for day in days:
            envelope = generate_soap_envelope(room, day)
            payloads.append({
                "room": room.arhitektura,
                "date": day.strftime("%Y-%m-%d"),
                "endpoint": METRONIK_SOAP_ENDPOINT,
                "soap_action": METRONIK_SOAP_ACTION,
                "payload": serializer.render(envelope),
            })

    return JsonResponse({"payloads": payloads})
