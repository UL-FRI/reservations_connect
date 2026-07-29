
from django.urls import path

from reservations_connect.metronik.views import metronik_debug


urlpatterns = [
    path("api/metronik/debug", metronik_debug, name="metronik_debug")
]