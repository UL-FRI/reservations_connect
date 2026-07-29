from django.utils.text import slugify
from import_export.resources import ModelResource

from reservations.models import Reservable
from reservations_connect.metronik.models import MetronikRoom


class MetronikRoomResource(ModelResource):
    class Meta:
        model = MetronikRoom
        exclude = ("reservable",)

    def do_instance_save(self, instance: MetronikRoom, is_create):
        base_slug = f"metronik-{slugify(instance.arhitektura)}"

        if instance.reservable_id is None:
            reservable, _ = Reservable.objects.update_or_create(
                slug=base_slug,
                defaults={
                    "name": instance.opis or instance.oznaka_prostora or "?",
                    "type": "classroom",
                },
            )
            instance.reservable = reservable

        instance.save()
