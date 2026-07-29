from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MetronikConfig(AppConfig):
    name = "reservations_connect.metronik"
    verbose_name = _("Reservations Connect: Metronik")
