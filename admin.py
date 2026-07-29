from typing import override

from django.contrib import admin
from django.db.models.aggregates import Count
from django.urls import reverse
from django.utils.safestring import mark_safe

from reservations_connect.models import ImportBatch

# Register your models here.

@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "time", "source", "_reservations")

    def _reservations(self, obj):
        return mark_safe(f'<a href="{reverse("admin:reservations_reservation_changelist")}?importbatch__id__exact={obj.id}">{obj.reservations_count}</a>')

    @override
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            reservations_count=Count("reservations")
        )
