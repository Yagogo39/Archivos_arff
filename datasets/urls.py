from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('descargar/<str:tipo>/', views.descargar_csv, name='descargar_csv'),
]
