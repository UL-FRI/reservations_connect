import reservations.models
from django.db import models


class ImportBatch(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    source = models.TextField()
    reservations = models.ManyToManyField(reservations.models.Reservation)
    created_reservables = models.ManyToManyField('ForeignReservable', related_name = 'created_by_import')
    updated_reservables = models.ManyToManyField('ForeignReservable', related_name = 'modified_by_import')

    def __str__(self):
        return "{0}:{1} {2} ({3} reservations)".format(self.id, self.time, self.source, len(self.reservations.all()))

class ForeignReservable(models.Model):
    reservable = models.ForeignKey(reservations.models.Reservable, on_delete=models.CASCADE)

class MetronikRoom(models.Model):
    def __unicode__(self):
        return u"{0} -> {1}".format(self.arhitektura, self.reservable)
    reservable = models.ForeignKey(reservations.models.Reservable, null=True, on_delete=models.CASCADE)
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
