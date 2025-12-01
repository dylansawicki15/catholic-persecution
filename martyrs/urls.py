from django.urls import path
from . import views

app_name = 'martyrs'

urlpatterns = [
    path('', views.home, name='home'),
]

