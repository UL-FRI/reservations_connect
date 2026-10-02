import logging
from dataclasses import dataclass
from datetime import date, time
from enum import IntEnum
from typing import Iterable

import requests

session = requests.Session()
session.headers["User-agent"] = "reservations_connect"


class DayOfWeek(IntEnum):
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


@dataclass
class FRIUrnikAllocation:
    id: int
    name: str
    tag: str
    type: str
    duration_h: int
    start: time
    day_of_week: DayOfWeek
    classroom_id: int
    classroom_name: str
    teacher_ids: list[int]


@dataclass
class FRIUrnikTimetable:
    id: int
    slug: str
    name: str
    start: date
    end: date
    public: bool
    activityset_id: int


@dataclass
class FRIUrnikTeacher:
    id: int
    name: str


def _find_by_id(items: Iterable[dict], item_id: int) -> dict | None:
    return next((item for item in items if item["id"] == item_id), None)


def _parse_timetable(t: dict) -> FRIUrnikTimetable:
    return FRIUrnikTimetable(
        id=t["id"],
        slug=t["slug"],
        name=t["name"],
        start=date.fromisoformat(t["start"]),
        end=date.fromisoformat(t["end"]),
        public=t["public"],
        activityset_id=t["activityset"],
    )


def get_timetable(urnik_url: str, timetable_id: int) -> FRIUrnikTimetable | None:
    """Look up a timetable by id via the /api/timetable/ endpoint."""
    resp = session.get(f"{urnik_url}/api/timetable/")
    resp.raise_for_status()
    t = _find_by_id(resp.json(), timetable_id)
    return _parse_timetable(t) if t else None


def get_timetable_by_slug(urnik_url: str, slug: str) -> FRIUrnikTimetable | None:
    """Look up a timetable by slug via the /api/timetable/<slug>/ endpoint."""
    resp = session.get(f"{urnik_url}/api/timetable/{slug}/")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return _parse_timetable(resp.json())


def get_default_timetable(urnik_url: str) -> FRIUrnikTimetable | None:
    """Look up the timetable marked as default for this urnik site via /api/site/."""
    resp = session.get(f"{urnik_url}/api/site/")
    resp.raise_for_status()
    sites = resp.json()
    default_site = next((s for s in sites if s.get("default")), None)
    if default_site is None:
        return None
    return get_timetable(urnik_url, default_site["timetable"])


def get_activities(urnik_url: str, activityset_id: int) -> dict[int, dict]:
    """Fetch all activities (id -> {name, short_name, type, duration}) for a timetable's activityset."""
    resp = session.get(f"{urnik_url}/api/activityset/")
    resp.raise_for_status()
    activityset = _find_by_id(resp.json(), activityset_id)
    if activityset is None:
        return {}

    resp = session.get(f"{urnik_url}/api/activityset/{activityset['slug']}/activity/")
    resp.raise_for_status()
    return {a["id"]: a for a in resp.json()}


def get_classrooms(urnik_url: str) -> dict[int, dict]:
    """Fetch all classrooms (id -> {name, ...}), across all locations."""
    resp = session.get(f"{urnik_url}/api/location/")
    resp.raise_for_status()
    classrooms: dict[int, dict] = {}
    for location in resp.json():
        resp = session.get(f"{urnik_url}/api/location/{location['id']}/classroom/")
        resp.raise_for_status()
        for classroom in resp.json():
            classrooms[classroom["id"]] = classroom
    return classrooms


def get_teachers(urnik_url: str) -> dict[int, FRIUrnikTeacher]:
    """Fetch all teachers (id -> FRIUrnikTeacher)."""
    resp = session.get(f"{urnik_url}/api/teacher/")
    resp.raise_for_status()
    teachers = {}
    for t in resp.json():
        user = t.get("user") or {}
        name = f"{user.get('last_name', '')}, {user.get('first_name', '')}".strip(", ")
        teachers[t["id"]] = FRIUrnikTeacher(id=t["id"], name=name)
    return teachers


def get_allocations(
    urnik_url: str, timetable: FRIUrnikTimetable
) -> Iterable[FRIUrnikAllocation]:
    activities = get_activities(urnik_url, timetable.activityset_id)
    classrooms = get_classrooms(urnik_url)

    resp = session.get(f"{urnik_url}/api/timetable/{timetable.slug}/allocation/")
    resp.raise_for_status()

    for al in resp.json():
        try:
            activity = activities[al["activityRealization"]["activity"]]
            classroom = classrooms[al["classroom"]]
            h, m = al["start"].split(":")
            yield FRIUrnikAllocation(
                id=al["id"],
                name=activity["name"],
                tag=activity["short_name"],
                type=activity["type"],
                duration_h=activity["duration"],
                start=time(int(h), int(m)),
                day_of_week=getattr(DayOfWeek, al["day"]),
                classroom_id=al["classroom"],
                classroom_name=classroom["name"],
                teacher_ids=al["activityRealization"]["teachers"],
            )
        except Exception as e:
            logging.warning("Failed to parse allocation: %s", al)
            logging.exception(e)
