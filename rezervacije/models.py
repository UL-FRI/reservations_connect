from django.db import models
from reservations_connect.models import ForeignReservable

class ExternalReservable(ForeignReservable):
    """Reservable, synced from a different reservations instance"""
    foreign_id = models.PositiveBigIntegerField()
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
