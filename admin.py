from django.contrib import admin
from reservations_connect.models import *
# Register your models here.
admin.site.register(ImportBatch)
admin.site.register(FriprosvetaActivity)
admin.site.register(FriprosvetaTeacher)
admin.site.register(TimetableClassroom)
admin.site.register(TimetableGroup)

admin.site.register(WiseIzvajalec)
admin.site.register(WiseSkupina)
admin.site.register(WiseProstor)
admin.site.register(WiseActivity)

admin.site.register(MetronikRoom)
