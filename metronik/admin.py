from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from reservations_connect.metronik.models import MetronikRoom
from reservations_connect.metronik.resources import MetronikRoomResource


class MetronikRoomAdmin(ImportExportActionModelAdmin):
    model = MetronikRoom
    resource_class = MetronikRoomResource
    search_fields = ('opis', 'arhitektura', 'oznaka_prostora',)
    list_display = ('opis', 'arhitektura', 'oznaka_prostora',)
    autocomplete_fields = ('reservable',)

admin.site.register(MetronikRoom, MetronikRoomAdmin)
