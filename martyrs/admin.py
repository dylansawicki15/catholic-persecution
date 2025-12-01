from django.contrib import admin
from .models import Martyr, PrayerIntention


@admin.register(Martyr)
class MartyrAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'date', 'created_at']
    search_fields = ['name', 'country', 'description']
    list_filter = ['country', 'date']
    date_hierarchy = 'date'


@admin.register(PrayerIntention)
class PrayerIntentionAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    search_fields = ['title', 'details']
    date_hierarchy = 'created_at'
