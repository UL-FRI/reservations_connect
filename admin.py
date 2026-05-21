from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from reservations_connect.models import *

# Register your models here.

class MetronikRoomAdmin(ImportExportActionModelAdmin):
    model = MetronikRoom

admin.site.register(ImportBatch)

admin.site.register(MetronikRoom, MetronikRoomAdmin)
