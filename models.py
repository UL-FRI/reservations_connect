from django.db import models
import reservations.models
import friprosveta.models
import timetable.models

class ImportBatch(models.Model):
    def __unicode__(self):
        return u"{0}:{1} {2} ({3} reservations)".format(self.id, self.time, self.source, len(self.reservations.all()))
    time = models.DateTimeField(auto_now_add=True)
    source = models.TextField()
    reservations = models.ManyToManyField(reservations.models.Reservation)
    created_reservables = models.ManyToManyField('ForeignReservable', related_name = 'created_by_import')
    updated_reservables = models.ManyToManyField('ForeignReservable', related_name = 'modified_by_import')

class ForeignReservable(models.Model):
    def __unicode__(self):
        return unicode(self.reservable)
    reservable = models.ForeignKey(reservations.models.Reservable)

class FriprosvetaActivity(ForeignReservable):
    type = "activity"
    # foreign = models.ForeignKey(timetable.models.Activity, null=True)
    foreign_id = models.IntegerField()
    @classmethod
    def by_timetable(cls, tt):
        return tt.activities.distinct()
#        return cls.objects.filter(foreign__activityset__timetable = tt).distinct()

class FriprosvetaTeacher(ForeignReservable):
    type = "teacher"
    # foreign = models.ForeignKey(friprosveta.models.Teacher, null=True)
    foreign_id = models.IntegerField()
    @classmethod
    def by_timetable(cls, tt):
        return tt.teachers.distinct()
#        return cls.objects.filter(foreign__activity__activityset__timetable = tt).distinct()

class TimetableClassroom(ForeignReservable):
    type = "classroom"
    # foreign = models.ForeignKey(timetable.models.Classroom, null=True)
    foreign_id = models.IntegerField()
    @classmethod
    def by_timetable(cls, tt):
        return tt.classrooms.all()
#        return cls.objects.filter(foreign__classroomset__timetables = tt).distinct()

class TimetableGroup(ForeignReservable):
    type = "group"
    # foreign = models.ForeignKey(timetable.models.Group, null=True)
    foreign_id = models.IntegerField()
    @classmethod
    def by_timetable(cls, tt):
        return tt.groups.all()
        # return cls.objects.filter(foreign__groupset__timetables = tt).distinct()

friprosveta_classes = [TimetableClassroom, FriprosvetaTeacher]
#friprosveta_classes = [FriprosvetaActivity, FriprosvetaTeacher, TimetableClassroom, TimetableGroup]

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

class MetronikRoom(models.Model):
    def __unicode__(self):
        return u"{0} -> {1}".format(self.arhitektura, self.reservable)
    reservable = models.ForeignKey(reservations.models.Reservable, null=True)
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
