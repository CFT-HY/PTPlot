from django.urls import path

from . import views

urlpatterns = [
    path('', views.ptplot_form, name='index'),
]
