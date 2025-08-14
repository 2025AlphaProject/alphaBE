from django.contrib import admin

from usr.models import User, FCMToken

# Register your models here.
admin.site.register(User)
admin.site.register(FCMToken)