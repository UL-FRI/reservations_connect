from django.db import models
from reservations_connect.models import ForeignReservable


# TODO: replace name with foreign_id when IDs are added to the API
#   make sure to add a migration step when you do that

class UrnikTeacher(ForeignReservable):
    type = "teacher"
    name = models.CharField(max_length=255)

class UrnikClassroom(ForeignReservable):
    type = "classroom"
    name = models.CharField(max_length=100)    