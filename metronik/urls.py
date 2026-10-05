
from django.urls import path

from reservations_connect.metronik.views import metronik_debug, metronik_payloads


urlpatterns = [
    path("api/metronik/debug", metronik_debug, name="metronik_debug"),
    path("api/metronik/payloads", metronik_payloads, name="metronik_payloads"),
]