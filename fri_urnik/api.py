import logging
import re
from dataclasses import dataclass
from datetime import time
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
    name: str
    tag: str
    classroom_name: str
    duration_h: int
    start: time
    type: str
    teacher_names: list[str]
    day_of_week: DayOfWeek


def get_allocations(urnik_url: str, urnik_slug: str) -> Iterable[FRIUrnikAllocation]:
    url = f"{urnik_url}/timetable/{urnik_slug}/allocations.json?mode=ext"
    resp = session.get(url)
    resp.raise_for_status()
    data = resp.json()

    for dow, allocs in data.items():
        day_of_week = getattr(DayOfWeek, dow)
        for al in allocs:
            try:
                h, m = al["start"].split(":")
                yield FRIUrnikAllocation(
                    day_of_week=day_of_week,
                    name=al["name"],
                    classroom_name=al["classroom"],
                    duration_h=al["durration"],
                    start=time(int(h), int(m)),
                    type=al["type"],
                    teacher_names=al["teachers"],
                    tag=al["tag"],
                )
            except Exception as e:
                logging.warning("Failed to parse allocation: %s", al)
                logging.exception(e)


def get_current_timetable_slug(urnik_url: str) -> str | None:
    resp = session.head(urnik_url)
    redirected_url = resp.headers.get("Location", "")
    match = re.search(r"/timetable/([^/]+)/", redirected_url)
    if match:
        return match.group(1)
