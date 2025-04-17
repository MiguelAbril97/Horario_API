from django.urls import path
from . import views

urlpatterns = [
    path('api/importar/', views.importar_horarios_desde_archivo),
    path('api/horarios/', views.obtener_horario, name='api_obtener_horario'),
    path('api/horarios/tarde/', views.horarios_tarde, name='api_horarios_tarde'),
    path('api/horarios/profesor/<int:id_usuario>/', views.horario_profe, name='api_horario_profe'),
    path('api/profesores/', views.obtener_profesores, name='api_hobtener_profesores'),
    path('api/profesor/<int:id_usuario>/', views.obtener_profesor, name='api_obtener_profesor'),
    path('usuario/token/<str:token>',views.obtener_usuario_token),
]