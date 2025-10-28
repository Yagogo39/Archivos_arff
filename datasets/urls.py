from django.urls import path
from . import views

urlpatterns = [
    path('', views.cargar_arff, name='cargar_arff'),
]
