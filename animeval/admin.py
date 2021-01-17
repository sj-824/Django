from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.contrib.auth.admin import UserAdmin
from .models import User, ProfileModel, ReviewModel, Counter, AccessReview, AnimeModel
from django.shortcuts import render, redirect, get_list_or_404
from .forms import CSVUpload
import io
import csv
# Register your models here.

admin.site.register(User,UserAdmin)
admin.site.register(ProfileModel)
admin.site.register(ReviewModel)
admin.site.register(Counter)
admin.site.register(AccessReview)

@admin.register(AnimeModel)
class AnimeModelAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        add_urls = [
            path('add_page/', self.admin_site.admin_view(self.add_view), name="add_page"),
            path('import/', self.admin_site.admin_view(self.import_view), name = 'import'),

        ]
        return add_urls + urls

    def add_view(self, request):
        return TemplateResponse(request, 'admin/animeval/animemodel/add_page.html')
    
    def import_view(self, request):
        if request.method == 'POST':
            form = CSVUpload(request.POST, request.FILES)
            if form.is_valid():
                csvfile = io.TextIOWrapper(form.cleaned_data['file'], encoding = 'utf-8')
                reader = csv.reader(csvfile)

                animes = []
                for row_data in reader:
                    title = row_data[0]
                    started = row_data[1]
                    genre = row_data[2]
                    corp = row_data[3]
                    cv = row_data[4]
                    anime = AnimeModel(
                        title = title,
                        started = started,
                        genre = genre,
                        corporation = corp,
                        character_voice = cv
                    )
                    animes.append(anime)
                AnimeModel.objects.bulk_create(animes)

                return redirect('admin:add_page')
            
        else:
            form = CSVUpload()
        return TemplateResponse(request, 'admin/animeval/animemodel/import.html', {'form' : form})