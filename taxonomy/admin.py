
from django.contrib import admin

from .models import Espece, Famille, Ordre

admin.site.register(Ordre)
admin.site.register(Famille)
admin.site.register(Espece)
