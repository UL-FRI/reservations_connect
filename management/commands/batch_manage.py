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
from django.utils import timezone

class Command(BaseCommand):
    '''
    Manage batches of imported reservations
    '''
    def remove_reservations(self):
        self.batch.reservations.all().delete()
    def remove_future_reservations(self):
        self.batch.reservations.filter(end__gte = timezone.now()).delete()
    def remove_batch(self):
        self.batch.delete()
    
    def show(self):
        print(self.batch)
        print("reservations:")
        for i in self.batch.reservations.all():
            print("    {0} ({1} - {2})".format(i, i.start, i.end))
            for j in i.reservables.all():
                print("        {0}".format(j))
        print("updated reservables:")
        for i in self.batch.updated_reservables.all():
            print("    {0}".format(i))
        print("created reservables:")
        for i in self.batch.created_reservables.all():
            print("    {0}".format(i))
    def list_batches(self):
        for i in ImportBatch.objects.all():
            print(i)
    def handle(self, *args, **options):
        #parser = argparse.ArgumentParser(description='Enroll students into subjects for a given timetable.', epilog="Copyright polz")
        #parser.add_argument('--timetable', )
        d = {
            'remove_reservations': self.remove_reservations,
            'remove_future_reservations': self.remove_future_reservations,
            'remove_batch': self.remove_batch,
            'show': self.show,
            # 'list_batches': list_batches,
        }
        if len(args) > 2 or len(args) >= 1 and args[0] not in d:
            print("Usage: batch_import {0} batch_id".format(str(d.keys())))
            return
        if len(args) <= 1:
            self.list_batches()
        else:
            self.batch = ImportBatch.objects.get(id=int(args[1]))
            d[args[0]]()
