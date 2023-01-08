# -*- coding: utf-8 -*-

'''
Created on 2. may. 2014

@author: polz
'''

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils.timezone import get_default_timezone
from django.conf import settings

import friprosveta.models
import reservations.models
from reservations_connect.management._wise_scrape import get_wise_reservations
from reservations_connect.models import *
from django.db import transaction
from datetime import timedelta, datetime, time

class Command(BaseCommand):
    '''
    Copy all teachers, classrooms, groups, activities 
    '''
    @transaction.atomic
    def update_reservables(self):
        multi_items = {'teachers': 'teacher', 'groups': 'group', 'classrooms': 'classroom'}
        d = {'teachers': WiseIzvajalec, 'groups': WiseSkupina, 'classrooms': WiseProstor, 'reason': WiseActivity}
        sets = dict([(i, set()) for i in ['teachers', 'groups', 'classrooms', 'reason']])
        for i in self.data:
            for k in d:
                if k in multi_items:
                    for j in i[k]:
                        sets[k].add(j)
                else:
                    sets[k].add(i[k])
        for k, s in sets.iteritems():
            for i in s:
                C = d[k]
                try:
                    o = C.objects.get(name = i)
                except:
                    try:
                        reservables = reservations.models.Reservable.objects.filter(slug = slugify(i[:50]))
                        if len(reservables) == 0:
                            reservable = reservations.models.Reservable(name = i, type = C.type, slug = slugify(i[:50]))
                            reservable.save()
                        elif len(reservables) == 1:
                            reservable = reservables[0]
                        else:
                            print u"Multiple reservables for " + slugify(i[:50]) + "(" + i + ")"
                            reservable = reservables[0]
                        if reservable.name != i:
                            print reservable.slug + ": '" + i + "' != '" + reservable.name + "'" 
                        o = C(name = i, reservable = reservable)
                        o.save()
                        self.batch.created_reservables.add(o)
                    except Exception, e:
                        print e
                        pass
                if len(self.reservable_set.reservables.filter(id=o.reservable.id)) == 0:
                    self.reservable_set.reservables.add(o.reservable)
             
    def update_reservations(self):
        multi_items = {'teachers': 'teacher', 'groups': 'group', 'classrooms': 'classroom'}
        d = {'teachers': WiseIzvajalec, 'groups': WiseSkupina, 'classrooms': WiseProstor, 'reason': WiseActivity}
        for i in self.data:
            reservables = []
            for k, C in d.iteritems():
                try:
                    if k in multi_items:
                        for j in i[k]:
                            reservable = C.objects.get(name = j).reservable
                            reservables.append(reservable)
                    else:
                        reservable = C.objects.get(name = i[k]).reservable
                        reservables.append(reservable)
                except Exception, e:
                    print "E:", k, e
            reservation = reservations.models.Reservation(start = i['start'], end = i['end'], reason = i['reason'])
            reservation.save()
            self.batch.reservations.add(reservation)
            for r in reservables:
                reservation.reservables.add(r)
 
    def import_wise(self):
        self.update_reservables()
        self.update_reservations()

    def handle(self, *args, **options):
        #parser = argparse.ArgumentParser(description='Enroll students into subjects for a given timetable.', epilog="Copyright polz")
        #parser.add_argument('--timetable', )
        d = {
            'all': self.import_wise,
            'reservables': self.update_reservables,
            'reservations': self.update_reservations,
        }
        if len(args) < 2:
            print("Usage: import_wise {0} reservableset_slug [base_url]".format(str(d.keys())))
            for rs in reservations.models.ReservableSet.objects.all():
                print rs.slug, ": ", rs.name

            return
        elif len(args) == 3:
            base_url = args[2]
        else:
            base_url = settings.WISE_URL
        self.reservable_set = reservations.models.ReservableSet.objects.get(slug=args[1])
        self.data = get_wise_reservations(base_url)
        self.batch = ImportBatch()
        self.batch.source = base_url
        self.batch.save()
        print "creating batch, id={}".format(self.batch.id)
        d[args[0]]()
        print self.batch.id
