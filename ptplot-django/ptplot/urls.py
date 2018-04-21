
from django.urls import path

from . import views

urlpatterns = [
    path(r'snr', views.snr_image, name='snr'),
    path(r'ps', views.ps_image, name='ps'),
    path(r'theories', views.theory, name='theory'),
    path(r'theories/<int:theory_id>', views.theory_detail, name='theory_detail'),
    path(r'parameterchoice', views.parameterchoice_form, name='parameterchoice'),
    path(r'single', views.single, name='single'),
    path(r'', views.index, name='index'),
]


