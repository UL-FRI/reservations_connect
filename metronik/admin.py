from typing import override

from adminsortable2.admin import mark_safe, reverse
from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from reservations_connect.metronik.models import MetronikRoom
from reservations_connect.metronik.resources import MetronikRoomResource


class MetronikRoomAdmin(ImportExportActionModelAdmin):
    model = MetronikRoom
    resource_class = MetronikRoomResource
    search_fields = ('opis', 'arhitektura', 'oznaka_prostora',)
    list_display = ('opis', 'arhitektura', 'oznaka_prostora', '_reservable')
    autocomplete_fields = ('reservable',)

    # TODO: Move this into a ForeignReservable superclass
    @override
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("reservable")

    def _reservable(self, obj):
        return mark_safe(f'<a href="{reverse("admin:reservations_reservable_change", args=(obj.reservable.id,))}">{obj.reservable.name}</a>')

admin.site.register(MetronikRoom, MetronikRoomAdmin)
