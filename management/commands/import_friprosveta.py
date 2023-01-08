# -*- coding: utf-8 -*-

'''
Created on 2. may. 2014

@author: polz
'''

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils.timezone import get_default_timezone

import friprosveta.models
import reservations.models
from reservations_connect.models import *
from django.db import transaction
from datetime import timedelta, datetime, time

class Command(BaseCommand):
    '''
    Copy all teachers, classrooms, groups, activities 
    '''

    def _get_name_and_slug(self, i):
        name = None
        for name_fn in [
                lambda x: unicode(x.name),
                lambda x: unicode(x.user.first_name + " " + x.user.last_name),
                lambda x: unicode(x)]:
            try:
                name = name_fn(i)
                break
            except:
                pass
        getOut = False
        for append_property in [None, "code", 'id']:
            for slug_property in ['slug', 'username', 'short_name', 'name', 'user.username', 'user']:
                try:
                    if append_property is None:
                        slug = slugify(unicode(getattr(i, slug_property)))[:50]
                    else:
                        a = unicode(getattr(i, append_property))
                        slug = slugify(unicode(getattr(i, slug_property)) + '-' + a)[:(50-1-len(a))]
                    if len(reservations.models.Reservable.objects.filter(slug=slug)) > 0:
                        raise Exception
                    getOut = True
                    break;
                except Exception, e:
                    pass
            if getOut:
                break
        return name, slug


    @transaction.atomic
    def update_reservables(self):
        for C in friprosveta_classes:
            collection = C.by_timetable(self.timetable)
            for i in collection:
                f = None
                created = False
                updated = False
                try:
                    f = C.objects.get(foreign_id = i.id)
                    r = f.reservable
                    name, slug = r.name, r.slug
                except Exception, e:
                    print (i, ":", e)
                    name, slug = self._get_name_and_slug(i)
                    # print("Name, slug:", name, slug)
                    r1 = reservations.models.Reservable.objects.filter(slug=slug, type=C.type)
                    # if len(r1) < 1:
                    #     slug = slug.upper()
                    #     r1 = reservations.models.Reservable.objects.filter(slug=slug, type=C.type)
                    if len(r1) < 1:
                        r1 = reservations.models.Reservable.objects.filter(name=name, type=C.type)
                    if len(r1) > 1:
                        r1 = reservations.models.Reservable.objects.filter(slug=slug, name=name, type=C.type)
                    if len(r1) > 0:
                        updated = True
                        r = r1[0]
                        if len(r1) > 1:
                            print(u"Multiple matches for {0}, {1}".format(slug, name))
                            print(u"    {}".format(r1.all()))
                    else:
                        r = reservations.models.Reservable(name = name, slug=slug, type=C.type)
                        created = True
                        r.save()
                    print(r.slug, r.name)
                    print(C, r, i)
                    # f = C(reservable = r, foreign = i)
                    f = C(reservable = r, foreign_id = i.id)
                f.save()
                if len(r.reservableset_set.filter(id = self.reservableset.id)) == 0:
                    self.reservableset.reservables.add(r)
                    updated = True
                if created:
                    self.batch.created_reservables.add(f)
                elif updated:
                    self.batch.updated_reservables.add(f)

    @transaction.atomic
    def update_reservations(self):
        reservations.models.Reservation.objects.prune()
        print("FINDING ALLOCATIONS")
        d = dict()
        for allocation in self.timetable.allocations.all():
            day_reservations = d.get(allocation.day, list())
            r = allocation.activityRealization
            reservables = []
            for CL, l in [ (FriprosvetaTeacher, r.teachers.all()), 
                (TimetableClassroom, [allocation.classroom]),
                (TimetableGroup, r.groups.all()),
                (FriprosvetaActivity, [r.activity]) ]:
                for i in l:
                    for k in CL.objects.filter(foreign_id=i.id, reservable__reservableset_set=self.reservableset):
                    #for k in CL.objects.filter(foreign=i):
                        reservables.append(k.reservable)
            day_reservations.append((r.activity.name, allocation.start, r.activity.duration, reservables))
            d[allocation.day] = day_reservations
        tzinfo = get_default_timezone()
        day = datetime.combine(self.timetable.start, time(0, 0))
        end = datetime.combine(self.timetable.end, time(0, 0))
        day = day.replace(tzinfo = tzinfo)
        end = end.replace(tzinfo = tzinfo)
        print("CREATING RESERVATIONS")
        while day <= end:
            try:
                weekday = timetable.models.WEEKDAYS[day.weekday()][0]
            except:
                weekday = str(day.weekday())
            for (reason, start, duration, reservables) in d.get(weekday, []):
                start_t = day + int(start[:2]) * timedelta(hours = 1) # int(07:00[:2]) = 7
                end_t = start_t + duration * timedelta(hours = 1)
                r = reservations.models.Reservation(reason=reason, start = start_t, end = end_t)
                r.save()
                # print r.reason, r.start
                for reservable in reservables:
                    # print "    ", reservable
                    r.reservables.add(reservable)
                self.batch.reservations.add(r)
            day += timedelta(days=1) 

    @transaction.atomic
    def classroom_resources_from_urnik(self):
        multi_resources = {u"Fizični računalnik":1, 'Delovno mesto':1,
            'Chair': 1, 'Računalnik': 1, 'Tanki odjemalec': 1}
        t = self.timetable
        classrooms = TimetableClassroom.objects.filter(foreign__classroomset__timetables = self.timetable).distinct()
        for c in classrooms:
            f = c.foreign
            print (f, f.capacity)
            modified = False
            for r in f.resources.all():
                if r.name in multi_resources:
                    n = f.capacity * multi_resources[r.name]
                else:
                    n = 1
                slug = slugify(r.name)
                resource, created = reservations.models.Resource.objects.get_or_create(slug = slug)
                if created:
                    resource.type = slug
                    resource.name = r.name
                    resource.save()
                nresources_list = reservations.models.NResources.objects.filter(resource = resource, reservable=c.reservable)
                if len(nresources_list) > 0:
                    print ("Multiple NResources between {0} and {1}".format(resource, c.reservable))
                    nresources_list.delete()
                if len(nresources_list) == 1:
                    nresources = nresources_list[0]
                    if nresources.n != n:
                        nresources.n = n
                        modified = True
                elif len(nresources_list) == 0:
                    modified = True
                    nresources = reservations.models.NResources(resource = resource, reservable=c.reservable, n = n)
                nresources.save()
                print (u"    {0}x{1}".format(n, r.name)) 
            if modified:
                self.batch.updated_reservables.add(c)

    def import_urnik(self):
        self.update_reservables()
        self.update_reservations()
        # self.classroom_resources_from_urnik()

    def handle(self, *args, **options):
        #parser = argparse.ArgumentParser(description='Enroll students into subjects for a given timetable.', epilog="Copyright polz")
        #parser.add_argument('--timetable', )
        d = {
            'all': self.import_urnik,
            'reservables': self.update_reservables,
            'reservations': self.update_reservations,
            'resources': self.classroom_resources_from_urnik,
        }
        if len(args) != 3:
            print("Usage: import_friprosveta {0} reservableset_slug timetable_slug".format(str(d.keys())))
            if len(args) > 0 and args[0] in d:
                if len(args) == 1:
                    for rs in reservations.models.ReservableSet.objects.all():
                        print rs.slug, ": ", rs.name
                elif len(args) == 2:
                    for t in friprosveta.models.Timetable.objects.all():
                        print t.slug, ": ", t.name
            return
        self.reservableset = reservations.models.ReservableSet.objects.get(slug=args[1])
        self.timetable = friprosveta.models.Timetable.objects.get(slug=args[2])
        self.batch = ImportBatch()
        self.batch.source = 'timetable://{0}'.format(self.timetable)
        self.batch.save()
        d[args[0]]()
