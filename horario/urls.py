from django.urls import path
from . import views


urlpatterns = [
    path('', views.importar_horarios_desde_archivo, name='importar'),
    path('', views.index, name='index'),

]