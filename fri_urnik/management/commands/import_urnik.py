# -*- coding: utf-8 -*-

"""
Created on 2. may. 2014

@author: polz
"""

import logging
import re
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from reservations.models import Reservable, ReservableSet, ReservableType, Reservation

from reservations_connect.fri_urnik.api import (
    FRIUrnikAllocation,
    get_allocations,
    get_current_timetable_slug,
)
from reservations_connect.fri_urnik.models import UrnikClassroom, UrnikTeacher
from reservations_connect.models import ImportBatch


class Command(BaseCommand):
    base_url = "https://urnik.fri.uni-lj.si"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timetable",
            dest="timetable_slug",
            help="Which timetable to import from (defaults to active timetable)",
        )
        parser.add_argument(
            "--reservableset",
            dest="reservableset_slug",
            help="Which ReservableSet to import into",
            default="rezervacije_fri",
        )
        parser.add_argument(
            "--start-date",
            dest="start_date_str",
            default=None,
        )
        parser.add_argument(
            "--end-date",
            dest="end_date_str",
            default=None,
        )
        parser.add_argument(
            "--no-confirm",
            dest="no_confirm",
            action="store_true",
            help="Don't ask for confirmation before deleting old reservations",
        )

    @transaction.atomic
    def handle(
        self,
        timetable_slug,
        reservableset_slug,
        start_date_str,
        end_date_str,
        no_confirm,
        *args,
        **options,
    ):
        self.no_confirm = no_confirm
        self.timetable_slug = timetable_slug or get_current_timetable_slug(
            self.base_url
        )
        if not self.timetable_slug:
            logging.error(
                "Could not auto-detect active timetable. Please specify one with --timetable."
            )
            return
        self.reservableset = ReservableSet.objects.get(slug=reservableset_slug)

        if start_date_str is not None:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = date.today()

        if end_date_str is not None:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        else:
            end_date = start_date + timedelta(days=7)

        batch_identifier = f"{self.base_url}/timetable/{self.timetable_slug}"

        self.batch = ImportBatch.objects.create(
            source=batch_identifier,
        )

        # Delete the previous batch
        self.delete_after(batch_identifier, start_date)

        allocations = get_allocations(self.base_url, self.timetable_slug)
        self.import_allocations(allocations, start_date, end_date)

    def delete_after(self, batch_identifier, datetime_from: date):
        """Delete all reservations, imported from the same source, after the currently imported weeek"""
        to_delete = Reservation.objects.filter(
            importbatch__source=batch_identifier,
            end__gte=datetime_from,
        )
        self.confirm(
            f"About to delete {to_delete.count()} reservations imported from {batch_identifier} after {datetime_from}. Are you sure?"
        )
        to_delete.delete()

    def import_allocations(
        self,
        allocations: Iterable[FRIUrnikAllocation],
        start_date: date,
        end_date: date,
    ):
        allocs_by_day: Mapping[int, list[FRIUrnikAllocation]] = {
            d: [] for d in range(7)
        }
        for alloc in allocations:
            allocs_by_day[alloc.day_of_week].append(alloc)

        # Iterate over every day from start to end
        for day in daterange(start_date, end_date):
            allocs = allocs_by_day[day.weekday()]
            logging.info("Importing %d allocations for %s", len(allocs), day)

            for alloc in allocs:
                # Timezone: Europe/Ljubljana
                start_dt = datetime.combine(
                    day, alloc.start, tzinfo=ZoneInfo("Europe/Ljubljana")
                )
                end_dt = start_dt + timedelta(hours=alloc.duration_h)

                reservation = Reservation.objects.create(
                    reason=alloc.name,
                    start=start_dt,
                    end=end_dt,
                )
                self.batch.reservations.add(reservation)

                # Import classroom reservation
                classroom = lookup_classroom(alloc.classroom_name, self.reservableset)
                reservation.reservables.add(classroom)

                # Import teacher "reservations"
                for teacher_name in alloc.teacher_names:
                    teacher = lookup_teacher(teacher_name, self.reservableset)
                    reservation.reservables.add(teacher)

    def confirm(self, message):
        if self.no_confirm:
            return
        answer = input(f"{message} [y/N] ")
        if answer.lower() != "y":
            print("Aborting.")
            exit(0)


@lru_cache(maxsize=None)
def lookup_teacher(teacher_str: str, reservableset: ReservableSet) -> Reservable | None:
    # TODO: handle this better when we have IDs available
    try:
        fr = UrnikTeacher.objects.get(name=teacher_str)
        return fr.reservable
    except UrnikTeacher.DoesNotExist:
        teacher_type, _ = ReservableType.objects.get_or_create(slug="teacher", defaults={"display_name": "Teacher"})
        teacher, _ = Reservable.objects.get_or_create(
            type=teacher_type,
            slug=f"urnik-teacher-{slugify(teacher_str)}",
            defaults=dict(
                name=teacher_str,
            )
        )
        UrnikTeacher.objects.create(reservable=teacher, name=teacher_str)
        reservableset.reservables.add(teacher)
        return teacher

@lru_cache(maxsize=None)
def lookup_classroom(classroom_name: str, reservableset: ReservableSet) -> Reservable | None:
    # TODO: handle this better when we have IDs available
    try:
        return UrnikClassroom.objects.get(name=classroom_name).reservable
    except UrnikClassroom.DoesNotExist:
        classroom_type, _ = ReservableType.objects.get_or_create(slug="classroom", defaults={"display_name": "Classroom"})
        r = Reservable.objects.create(
            type=classroom_type,
            slug=f"urnik-classroom-{slugify(classroom_name)}",
            name=classroom_name,
        )
        UrnikClassroom.objects.create(reservable=r, name=classroom_name)
        reservableset.reservables.add(r)
        return r


def daterange(start_date: date, end_date: date) -> Iterable[date]:
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)
