# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0001_initial'),
        ('friprosveta', '0001_initial'),
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForeignReservable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FriprosvetaActivity',
            fields=[
                ('foreignreservable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reservations_connect.ForeignReservable')),
                ('foreign', models.ForeignKey(to='timetable.Activity')),
            ],
            options={
            },
            bases=('reservations_connect.foreignreservable',),
        ),
        migrations.CreateModel(
            name='FriprosvetaTeacher',
            fields=[
                ('foreignreservable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reservations_connect.ForeignReservable')),
                ('foreign', models.ForeignKey(to='friprosveta.Teacher')),
            ],
            options={
            },
            bases=('reservations_connect.foreignreservable',),
        ),
        migrations.CreateModel(
            name='ImportBatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('source', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MetronikRoom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('arhitektura', models.CharField(max_length=256, null=True, blank=True)),
                ('tehnologija', models.CharField(max_length=256, null=True, blank=True)),
                ('opis', models.CharField(max_length=256, null=True, blank=True)),
                ('stevilka_sist_kljuca', models.CharField(max_length=256, null=True, blank=True)),
                ('oznake_sist_kljuca', models.CharField(max_length=256, null=True, blank=True)),
                ('oznaka_prostora', models.CharField(max_length=256, null=True, blank=True)),
                ('oznake_na_vratih', models.CharField(max_length=256, null=True, blank=True)),
                ('table_v_objektu', models.CharField(max_length=256, null=True, blank=True)),
                ('etaza', models.CharField(max_length=256, null=True, blank=True)),
                ('zap_st_prostora', models.CharField(max_length=256, null=True, blank=True)),
                ('reservable', models.ForeignKey(to='reservations.Reservable', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TimetableClassroom',
            fields=[
                ('foreignreservable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reservations_connect.ForeignReservable')),
                ('foreign', models.ForeignKey(to='timetable.Classroom')),
            ],
            options={
            },
            bases=('reservations_connect.foreignreservable',),
        ),
        migrations.CreateModel(
            name='TimetableGroup',
            fields=[
                ('foreignreservable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reservations_connect.ForeignReservable')),
                ('foreign', models.ForeignKey(to='timetable.Group')),
            ],
            options={
            },
            bases=('reservations_connect.foreignreservable',),
        ),
        migrations.CreateModel(
            name='WiseActivity',
            fields=[
                ('foreignreservable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reservations_connect.ForeignReservable')),
                ('name', models.CharField(max_length=255)),
                ('vrsta', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=('reservations_connect.foreignreservable',),
        ),
        migrations.CreateModel(
            name='WiseIzvajalec',
            fields=[
                ('foreignreservable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reservations_connect.ForeignReservable')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=('reservations_connect.foreignreservable',),
        ),
        migrations.CreateModel(
            name='WiseProstor',
            fields=[
                ('foreignreservable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reservations_connect.ForeignReservable')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=('reservations_connect.foreignreservable',),
        ),
        migrations.CreateModel(
            name='WiseSkupina',
            fields=[
                ('foreignreservable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reservations_connect.ForeignReservable')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=('reservations_connect.foreignreservable',),
        ),
        migrations.AddField(
            model_name='importbatch',
            name='created_reservables',
            field=models.ManyToManyField(related_name=b'created_by_import', to='reservations_connect.ForeignReservable'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='importbatch',
            name='reservations',
            field=models.ManyToManyField(to='reservations.Reservation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='importbatch',
            name='updated_reservables',
            field=models.ManyToManyField(related_name=b'modified_by_import', to='reservations_connect.ForeignReservable'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='foreignreservable',
            name='reservable',
            field=models.ForeignKey(to='reservations.Reservable'),
            preserve_default=True,
        ),
    ]
