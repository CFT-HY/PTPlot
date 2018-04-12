from django.urls import path

from . import views

urlpatterns = [
    path('snr', views.snr_image, name='snr'),
    path('ps', views.ps_image, name='ps'),
    path('', views.ptplot_form, name='index'),
]
