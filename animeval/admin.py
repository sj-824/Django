from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ProfileModel, ReviewModel, Counter, AccessReview, AnimeModel
# Register your models here.

admin.site.register(User,UserAdmin)
admin.site.register(ProfileModel)
admin.site.register(ReviewModel)
admin.site.register(Counter)
admin.site.register(AccessReview)
admin.site.register(AnimeModel)

