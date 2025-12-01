from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Martyr, PrayerIntention


def home(request):
    martyrs_list = Martyr.objects.all()
    paginator = Paginator(martyrs_list, 3)
    page_number = request.GET.get('page')
    martyrs = paginator.get_page(page_number)
    
    prayer_intentions_list = PrayerIntention.objects.all()
    prayer_paginator = Paginator(prayer_intentions_list, 3)
    prayer_page_number = request.GET.get('prayer_page')
    prayer_intentions = prayer_paginator.get_page(prayer_page_number)
    
    context = {
        'martyrs': martyrs,
        'prayer_intentions': prayer_intentions,
    }
    
    return render(request, 'martyrs/home.html', context)
