
from datetime import date

from django.http.response import HttpResponse
from django.utils.timezone import datetime

from reservations_connect.metronik.converter import generate_timetable_transfer
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
