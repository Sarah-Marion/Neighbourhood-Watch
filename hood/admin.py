from django.contrib import admin
from .models import Profile, Hood, Location, Business, News

# Register your models here.
admin.site.register(Profile)
admin.site.register(Hood)
admin.site.register(Location)
admin.site.register(Business)
admin.site.register(News)