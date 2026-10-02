from django.db import models
from reservations_connect.models import ForeignReservable


class UrnikTeacher(ForeignReservable):
    type = "teacher"
    foreign_id = models.PositiveBigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)

class UrnikClassroom(ForeignReservable):
    type = "classroom"
    foreign_id = models.PositiveBigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
