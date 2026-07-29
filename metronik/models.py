from django.db import models

from reservations_connect.models import ForeignReservable


class MetronikRoom(ForeignReservable):
    arhitektura = models.CharField(max_length=256, blank=True, null=True)
    tehnologija = models.CharField(max_length=256, blank=True, null=True)
    opis = models.CharField(max_length=256, blank=True, null=True)
    stevilka_sist_kljuca = models.CharField(max_length=256, blank=True, null=True)
    oznake_sist_kljuca = models.CharField(max_length=256, blank=True, null=True)
    oznaka_prostora = models.CharField(max_length=256, blank=True, null=True)
    oznake_na_vratih = models.CharField(max_length=256, blank=True, null=True)
    table_v_objektu = models.CharField(max_length=256, blank=True, null=True)
    etaza = models.CharField(max_length=256, blank=True, null=True)
    zap_st_prostora = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return "{0} ({1})".format(self.reservable.name, self.arhitektura)
