import logging
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from reservations.models import Reservable, ReservableSet, ReservableType, Reservation

from reservations_connect.fri_urnik.api import (
    FRIUrnikAllocation,
    FRIUrnikTeacher,
    get_allocations,
    get_default_timetable,
    get_teachers,
    get_timetable_by_slug,
)
from reservations_connect.fri_urnik.models import UrnikClassroom, UrnikTeacher
from reservations_connect.models import ImportBatch

TZ = ZoneInfo("Europe/Ljubljana")

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    base_url = "https://urnik.fri.uni-lj.si"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timetable",
            dest="timetable_slug",
            help="Which timetable to import from (defaults to the site's default timetable)",
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
            help="Override the sync range start (YYYY-MM-DD). Defaults to today.",
        )
        parser.add_argument(
            "--end-date",
            dest="end_date_str",
            default=None,
            help="Override the sync range end, inclusive (YYYY-MM-DD). Defaults to the timetable's end date.",
        )
        parser.add_argument(
            "--no-confirm",
            dest="no_confirm",
            action="store_true",
            help="Don't ask for confirmation before deleting removed reservations",
        )

    @transaction.atomic
    def handle(
        self,
        timetable_slug,
        reservableset_slug,
        start_date_str,
        end_date_str,
        no_confirm,
        verbosity,
        *args,
        **options,
    ):
        self.setup_logging(verbosity)

        self.no_confirm = no_confirm
        self.reservableset = ReservableSet.objects.get(slug=reservableset_slug)

        logger.info("Resolving timetable (base_url=%s, requested slug=%r)", self.base_url, timetable_slug)
        timetable = (
            get_timetable_by_slug(self.base_url, timetable_slug)
            if timetable_slug
            else get_default_timetable(self.base_url)
        )
        if timetable is None:
            logger.error(
                "Could not find timetable%s.",
                f" '{timetable_slug}'" if timetable_slug else " (no default timetable set)",
            )
            return
        logger.info(
            "Using timetable '%s' (%s), timetable date range %s - %s",
            timetable.slug,
            timetable.name,
            timetable.start,
            timetable.end,
        )

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_str
            else max(date.today(), timetable.start)
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if end_date_str
            else timetable.end
        )
        logger.info("Computed sync range: %s - %s (today is %s)", start_date, end_date, date.today())

        if start_date > end_date:
            logger.warning(
                "Nothing to sync: computed range %s - %s is empty/inverted. "
                "This usually means the timetable's 'end' date (%s) on %s is in the past "
                "(or before its own 'start' date, %s) - check the timetable data upstream, "
                "or pass --start-date/--end-date explicitly to override.",
                start_date,
                end_date,
                timetable.end,
                self.base_url,
                timetable.start,
            )
            return

        self.external_id_prefix = f"urnik:{timetable.slug}:"
        self.batch = ImportBatch.objects.create(
            source=f"{self.base_url}/timetable/{timetable.slug}",
        )
        self._classroom_cache: dict[int, Reservable] = {}
        self._teacher_cache: dict[int, Reservable] = {}

        logger.info("Fetching allocations and teachers from %s", self.base_url)
        allocations = list(get_allocations(self.base_url, timetable))
        teachers = get_teachers(self.base_url)
        logger.info("Fetched %d allocations and %d teachers", len(allocations), len(teachers))

        self.sync_allocations(allocations, teachers, start_date, end_date)

    def setup_logging(self, verbosity: int):
        """Make sure our info logging actually reaches the console.

        Django's default logging config only attaches a handler to the
        'django' logger tree, so plain logger.info() calls here would
        otherwise be silently dropped.
        """
        level = {0: logging.WARNING, 1: logging.INFO}.get(verbosity, logging.DEBUG)
        logger.setLevel(level)
        if not logger.handlers:
            handler = logging.StreamHandler(self.stdout)
            handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
            logger.addHandler(handler)
        logger.propagate = False

    def sync_allocations(
        self,
        allocations: Iterable[FRIUrnikAllocation],
        teachers: dict[int, FRIUrnikTeacher],
        start_date: date,
        end_date: date,
    ):
        allocs_by_day: Mapping[int, list[FRIUrnikAllocation]] = {
            d: [] for d in range(7)
        }
        for alloc in allocations:
            allocs_by_day[alloc.day_of_week].append(alloc)

        synced_external_ids: set[str] = set()

        for day in daterange(start_date, end_date + timedelta(days=1)):
            allocs = allocs_by_day[day.weekday()]
            logger.info("Syncing %d allocations for %s", len(allocs), day)

            for alloc in allocs:
                external_id = self.external_id_for(alloc, day)
                synced_external_ids.add(external_id)

                start_dt = datetime.combine(day, alloc.start, tzinfo=TZ)
                end_dt = start_dt + timedelta(hours=alloc.duration_h)

                reservation, created = Reservation.objects.update_or_create(
                    external_id=external_id,
                    defaults={
                        "reason": alloc.name,
                        "start": start_dt,
                        "end": end_dt,
                    },
                )

                classroom = self.lookup_classroom(alloc.classroom_id, alloc.classroom_name)
                teacher_reservables = [
                    self.lookup_teacher(teacher_id, teachers[teacher_id].name)
                    for teacher_id in alloc.teacher_ids
                    if teacher_id in teachers
                ]
                reservation.reservables.set([classroom, *teacher_reservables])

                self.batch.reservations.add(reservation)

        logger.info("Synced %d reservation occurrences", len(synced_external_ids))
        self.remove_stale(start_date, end_date, synced_external_ids)

    def remove_stale(self, start_date: date, end_date: date, synced_external_ids: set[str]):
        """Delete reservations, previously synced from this timetable into this date
        range, whose allocation is no longer present on the timetable."""
        range_start = datetime.combine(start_date, datetime.min.time(), tzinfo=TZ)
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=TZ)

        to_delete = Reservation.objects.filter(
            external_id__startswith=self.external_id_prefix,
            start__gte=range_start,
            start__lt=range_end,
        ).exclude(external_id__in=synced_external_ids)

        logger.info(
            "Found %d stale reservations to remove (no longer on the timetable) for %s - %s",
            to_delete.count(),
            start_date,
            end_date,
        )
        self.confirm(
            f"About to delete {to_delete.count()} reservations removed from the timetable "
            f"between {start_date} and {end_date}. Are you sure?"
        )
        to_delete.delete()

    def external_id_for(self, alloc: FRIUrnikAllocation, day: date) -> str:
        return f"{self.external_id_prefix}{alloc.id}:{day.isoformat()}"

    def lookup_classroom(self, classroom_id: int, classroom_name: str) -> Reservable:
        if classroom_id in self._classroom_cache:
            return self._classroom_cache[classroom_id]

        try:
            urnik_classroom = UrnikClassroom.objects.get(foreign_id=classroom_id)
            reservable = urnik_classroom.reservable
            if urnik_classroom.name != classroom_name:
                urnik_classroom.name = classroom_name
                urnik_classroom.save(update_fields=["name"])
                reservable.name = classroom_name
                reservable.save(update_fields=["name"])
                self.batch.updated_reservables.add(urnik_classroom)
        except UrnikClassroom.DoesNotExist:
            classroom_type, _ = ReservableType.objects.get_or_create(
                slug="classroom", defaults={"display_name": "Classroom"}
            )
            reservable = Reservable.objects.create(
                type=classroom_type,
                slug=f"urnik-classroom-{classroom_id}",
                name=classroom_name,
            )
            urnik_classroom = UrnikClassroom.objects.create(
                reservable=reservable, foreign_id=classroom_id, name=classroom_name
            )
            self.reservableset.reservables.add(reservable)
            self.batch.created_reservables.add(urnik_classroom)

        self._classroom_cache[classroom_id] = reservable
        return reservable

    def lookup_teacher(self, teacher_id: int, teacher_name: str) -> Reservable:
        if teacher_id in self._teacher_cache:
            return self._teacher_cache[teacher_id]

        try:
            urnik_teacher = UrnikTeacher.objects.get(foreign_id=teacher_id)
            reservable = urnik_teacher.reservable
            if urnik_teacher.name != teacher_name:
                urnik_teacher.name = teacher_name
                urnik_teacher.save(update_fields=["name"])
                reservable.name = teacher_name
                reservable.save(update_fields=["name"])
                self.batch.updated_reservables.add(urnik_teacher)
        except UrnikTeacher.DoesNotExist:
            teacher_type, _ = ReservableType.objects.get_or_create(
                slug="teacher", defaults={"display_name": "Teacher"}
            )
            reservable = Reservable.objects.create(
                type=teacher_type,
                slug=f"urnik-teacher-{teacher_id}",
                name=teacher_name,
            )
            urnik_teacher = UrnikTeacher.objects.create(
                reservable=reservable, foreign_id=teacher_id, name=teacher_name
            )
            self.reservableset.reservables.add(reservable)
            self.batch.created_reservables.add(urnik_teacher)

        self._teacher_cache[teacher_id] = reservable
        return reservable

    def confirm(self, message):
        if self.no_confirm:
            return
        answer = input(f"{message} [y/N] ")
        if answer.lower() != "y":
            print("Aborting.")
            exit(0)


def daterange(start_date: date, end_date: date) -> Iterable[date]:
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)
