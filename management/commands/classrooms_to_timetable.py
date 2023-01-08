# -*- coding: utf-8 -*-

'''
Created on 2. may. 2014

@author: polz
'''

from django.core.management.base import BaseCommand
from django.db import transaction

import reservations.models
import reservations_connect.models
import timetable.models

class Command(BaseCommand):
    
    args = 'classroomset_slug [reservableset_slug]'
    help = ' Copy classrooms with their resources into timetable.models.ClassroomSet. If reservableset_slug is not given, classroomset_slug is used.'
    
    '''
    Copy classrooms with their resources into timetable.models.ClassroomSet
    '''
    def add_arguments(self, parser):
        # enable this when porting to django 1.8
        #parser.add_argument('classroomset_slug', nargs=1, action='store', dest='classroomset_slug')
        #parser.add_argument('reservableset_slug', nargs='?', action='store', dest='reservableset_slug')
        #parser.add_argument('--update-classroomset', action='store_true', dest='update_classroomset', default=False, 
        #    help='update the classroomset, adding new classrooms if neccessarry.')
        parser.add_argument('classroomset_slug', nargs=1, action='store', dest='classroomset_slug')
        parser.add_argument('reservableset_slug', nargs='?', action='store', dest='reservableset_slug')
        parser.add_option('--update-classroomset', action='store_true', dest='update_classroomset', 
            help='update the classroomset, adding new classrooms if neccessarry.')

    @transaction.atomic
    def update_classroomset(self):
        """create classrooms in timetable, TimetableClassrooms in reservations_connect"""
        for reservable in self.reservableset.reservables.filter(type="classroom"):
            tcs = reservations_connect.models.TimetableClassroom.objects.filter(reservable=reservable)
            if len(tcs) == 0:
                try:
                    tt_classroom = timetable.models.Classroom.objects.get(name=reservable.name)
                except:
                    try:
                        tt_classroom = timetable.models.Classroom.objects.get(short_name=reservable.slug)
                    except:
                        tt_classroom = timetable.models.Classroom(name=reservable.name, short_name=reservable.slug)
                tt_classroom.save()
                tc = reservations_connect.models.TimetableClassroom(reservable=reservable, foreign=tt_classroom)
            elif len(tcs) == 1:
                tc = tcs[0]
                tt_classroom = tc.foreign
            if tt_classroom not in self.classroomset.classrooms.all():
                self.classroomset.classrooms.add(tt_classroom)
                
    def copy_resources(self):
        for reservable in self.reservableset.reservables.filter(type="classroom"):
            tcs = reservations_connect.models.TimetableClassroom.objects.filter(reservable=reservable)
            if len(tcs) != 1:
                print u"More than one (or zero) matching classroom for {0}".format(reservable)
            else:
                classroom = tcs.get().foreign                  
                timetable.models.ClassroomNResources.objects.filter(classroom=classroom).delete()
                for nr in reservations.models.NResources.objects.filter(reservable=reservable):
                    r, created = timetable.models.Resource.objects.get_or_create(name=nr.resource.name)  # @UnusedVariable
                    r.save()
                    timetable_nr = timetable.models.ClassroomNResources(resource=r, classroom=classroom, n=nr.n)
                    timetable_nr.save()
                
    def handle(self, *args, **options):
        #parser = argparse.ArgumentParser(description='Enroll students into subjects for a given timetable.', epilog="Copyright polz")
        #parser.add_argument('--timetable', )
        if 'update_classroomset' not in options:
            options['update_classroomset'] = False
        try:
            options['reservableset_slug'] = args[1]
        except:
            pass
        try:
            options['classroomset_slug'] = args[0]
        except:
            pass
        self.classroomset = timetable.models.ClassroomSet.objects.get(slug=options['classroomset_slug'])
        self.reservableset = reservations.models.ReservableSet.objects.get(slug=options.get('reservableset_slug', options['classroomset_slug']))
        if options['update_classroomset']:
            self.update_classroomset()
        self.copy_resources()
