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
