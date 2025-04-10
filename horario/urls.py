from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('horario',views.obtener_horario,name='obtener_horario'),
    path('horario_profe/<int:id_usuario>/',views.horario_profe,name='horario_profe'),
    path('horarios_tarde/',views.horarios_tarde,name='horarios_tarde'),
    path('importar', views.importar_horarios_desde_archivo, name='importar'),

]