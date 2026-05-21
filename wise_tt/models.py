
from django.db import models
from reservations_connect.models import ForeignReservable


class WiseIzvajalec(ForeignReservable):
    type = "teacher"
    name = models.CharField(max_length = 255)

class WiseSkupina(ForeignReservable):
    type = "group"
    name = models.CharField(max_length = 255)

class WiseProstor(ForeignReservable):
    type = "classroom"
    name = models.CharField(max_length = 255)

class WiseActivity(ForeignReservable):
    type = "activity"
    name = models.CharField(max_length = 255)
    vrsta = models.CharField(max_length = 255)

wise_classes = [WiseIzvajalec, WiseSkupina, WiseProstor, WiseActivity]