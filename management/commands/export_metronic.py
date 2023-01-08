# -*- coding: utf-8 -*-
import sys
import logging

from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.conf import settings

from collections import namedtuple
from reservations_connect.models import MetronikRoom
from datetime import timedelta, datetime, time

import suds


logging.basicConfig(level=logging.INFO)

# Once the console handler is configured, the user can enable module specific
# debugging doing the following:
# logging.getLogger(<desired package>).setLevel(logging.<desired-level>)
# A common example (show sent/received soap messages):
# logging.getLogger('suds.transport').setLevel(logging.DEBUG)

HOUR_FORMAT = "%H:%M:%S"
DAY_FORMAT = "%Y-%m-%d"


class Command(BaseCommand):
    '''
    Export the busy times for all classrooms which have
    a known air conditioning system ID
    '''

    def split_by_days(self, r_start, r_end):
        "returns a dictionary of (date, times) for this reservation"
        Interval = namedtuple('Interval', ['start', 'end'])
        res_dict = dict()
        d_start = r_start.date()
        h_start = r_start.time()
        d_end = r_end.date()
        while d_start <= d_end:
            next_d_start = d_start + timedelta(days=1)
            if next_d_start >= d_end:
                h_end = r_end.time()
            else:
                h_end = time().max
                # h_end = time(23, 59)
            res_dict[d_start] = set([
                # workaround buga - trajanje mora biti do 1min pred polnocjo
                Interval(
                    start=datetime.combine(d_start, h_start),
                    end=datetime.combine(d_start, h_end) - timedelta(minutes=1)
                )
            ])
            h_start = time().min
            d_start = next_d_start
        return res_dict

    def handle(self, *args, **options):
        wsdl_url = settings.METRONIK_URL
        if len(args) > 1:
            print ("Usage: export_metronik [wsdl_url]")
            sys.exit(1)
        elif len(args) == 1:
            wsdl_url = args[0]
        client = suds.client.Client(wsdl_url)
        room_table = []
        for metronik_room in MetronikRoom.objects.all():
            room = metronik_room.reservable
            if room is not None:
                all_times = dict()
                today = now()
                tomorrow = datetime.combine(today.date() + timedelta(days=1),
                                            time())
                filtered = room.reservation_set.filter(start__gte=tomorrow)
                filtered = filtered.filter(start__lt=tomorrow + timedelta(days=7))
                for reservation in filtered.order_by('start'):
                    times_dict = self.split_by_days(reservation.start,
                                                    reservation.end)
                    for k, v in times_dict.iteritems():
                        busy_set = all_times.get(k, set())
                        busy_set = busy_set.union(v)
                        all_times[k] = busy_set
                for day in sorted(all_times.keys()):
                    times_list = list()
                    for hours in sorted(all_times[day]):
                        td = client.factory.create('TimeDescriptor')
                        td.Occupied = True
                        td.From = hours.start.strftime(HOUR_FORMAT)
                        td.To = hours.end.strftime(HOUR_FORMAT)
                        times_list.append(td)
                    times = client.factory.create('ArrayOfTimeDescriptor')
                    times.TimeDescriptor = times_list
                    room_descriptor = client.factory.create('RoomDescriptor')
                    room_descriptor.Faculty = 'FRI'
                    room_descriptor.Room = metronik_room.arhitektura
                    room_descriptor.ValidFrom = day.strftime(DAY_FORMAT)
                    # Veljavnost je po prosnji metronic ne 1, ampak 10 dni.
                    valid_to = (day+timedelta(days=10)).strftime(DAY_FORMAT)
                    room_descriptor.ValidTo = valid_to
                    room_descriptor.WeekDay = day.isoweekday()
                    room_table.append((room_descriptor, times))
        for room_day, times in room_table:
            #print room_day, times
            try:
                client.service.TimetableTransfer(room_day, times)
                # print(client.last_sent())
            except Exception, e:
                pass
                #print unicode((e,))
