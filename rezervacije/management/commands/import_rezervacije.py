import logging
import re
from tqdm import tqdm
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
import requests
from reservations.models import Reservable, ReservableType, Reservation


import json

from reservations_connect.models import ImportBatch
from reservations_connect.rezervacije.models import ExternalReservable

URNIK_REASON_RE = re.compile(r".+\(\d+\)_.+")

class Command(BaseCommand):
    base_url = "https://rezervacije.fri.uni-lj.si"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            type=str,
            default=self.base_url,
            help="Base URL of the API to fetch reservables and reservations from.",
        )
        parser.add_argument(
            "--save-json",
            action="store_true",
            help="Save downloaded data to JSON",
        )
        parser.add_argument(
            "--load-json",
            action="store_true",
            help="Load data from JSON",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            help="Start date filter for reservations (YYYY-MM-DD) - defaults to 30 days ago",
        )
        parser.add_argument(
            "--no-confirm",
            dest="no_confirm",
            action="store_true",
            help="Don't ask for confirmation before deleting old reservations",
        )


    @transaction.atomic
    def handle(self, *args, **options):
        self.opt = options
        self.no_confirm = options["no_confirm"]
        
        start_date = datetime.fromisoformat(options["start_date"]) if options["start_date"] else datetime.now() - timedelta(days=30)
        start_date = start_date.astimezone(ZoneInfo("Europe/Ljubljana"))
        
        batch_identifier = self.base_url
        self.batch = ImportBatch.objects.create(
            source=batch_identifier,
        )
        # Delete the previous batch
        self.delete_after(batch_identifier, start_date)
        
        
        api_reservables = self._load_or_download("reservables", f"{self.base_url}/reservables/?page_size=100")
        api_reservations = self._load_or_download("reservations", f"{self.base_url}/reservations/?page_size=100&start={options['start_date']}")
        api_reservations = dedupe_reservations(api_reservations)
        reservables_by_id: dict[str, dict] = {r["id"]: r for r in api_reservables}

        for api_reservation in tqdm(api_reservations, desc="Importing reservations"):
            # Filter reservations here because the API refuses to filter by start date
            start_time = datetime.fromisoformat(api_reservation["start"]).astimezone(ZoneInfo("Europe/Ljubljana"))
            if start_time < start_date:
                continue
            end_time = datetime.fromisoformat(api_reservation["end"]).astimezone(ZoneInfo("Europe/Ljubljana"))

            # Skip urnik reservations
            if URNIK_REASON_RE.match(api_reservation["reason"]):
                continue
            
            reservation = Reservation.objects.create(
                # external_id=f'{self.base_url}/reservations/{api_reservation["id"]}',
                reason=api_reservation["reason"],
                start=start_time,
                end=end_time,
            )
            for reservable_id in api_reservation["reservables"]:
                reservable = get_reservable(reservables_by_id[reservable_id])
                if reservable:
                    reservation.reservables.add(reservable)
            self.batch.reservations.add(reservation)
        

    def _load_or_download(self, name: str, url: str) -> list[dict]:
        filename = f"api_{name}.json"
        if self.opt["load_json"]:
            with open(filename, "r") as f:
                return json.load(f)
        data = list(get_drf_paginated(url))
        if self.opt["save_json"]:
            with open(filename, "w") as f:
                json.dump(data, f, indent="\t")
        return data

    
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

    def confirm(self, message):
        if self.no_confirm:
            return
        answer = input(f"{message} [y/N] ")
        if answer.lower() != "y":
            print("Aborting.")
            exit(0)

_reservable_cache = {}
def get_reservable(data) -> Reservable | None:
    if data["type"] not in ("classroom", "teacher"):
        return
    if data["id"] in _reservable_cache:
        return _reservable_cache[data["id"]]

    name = data["name"]
    # Classrooms have bad names
    if data["type"] == "classroom":
        name = data["slug"]

    try:
        r = ExternalReservable.objects.get(foreign_id=data["id"], type=data["type"]).reservable
    except ExternalReservable.DoesNotExist:
        reservable_type, _ = ReservableType.objects.get_or_create(
            slug=data["type"], defaults={"display_name": data["type"].title()}
        )
        r = Reservable.objects.create(name=name, slug=data["slug"], type=reservable_type)
        ExternalReservable.objects.create(foreign_id=data["id"], type=data["type"], reservable=r)
    
    _reservable_cache[data["id"]] = r
    return r

def dedupe_reservations(reservations: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for r in reservations:
        # key = (r["reason"], r["start"], r["end"], tuple(sorted(r["reservables"])))
        key = r["id"]
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    print(f"Deduped reservations: {len(reservations)} -> {len(deduped)}")
    return deduped    


def get_drf_paginated(url):
    pbar = tqdm(total=0, unit=" items")
    while url:
        response = requests.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()
        pbar.total = data["count"]
        pbar.update(len(data["results"]))
        yield from data["results"]
        url = data["next"]
