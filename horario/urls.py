from django.urls import path
from . import views

urlpatterns = [
    #Horarios
    path('api/horarios/subir/', views.subir_horario),
    path('api/importar/', views.importar_horarios_desde_archivo),
    path('api/horarios/', views.obtener_horario, name='api_obtener_horario'),
    path('api/horarios/dia/<str:dia>/',views.obtener_horario_dia),
    path('api/horarios/tarde/', views.horarios_tarde, name='api_horarios_tarde'),
    path('api/horarios/profesor/<int:id_usuario>/', views.horario_profe, name='api_horario_profe'),
    path('api/horarios/profesor/<int:id_usuario>/<str:dia>/', views.horario_profe_dia),
    path('api/horarios/guardias/<str:dia>/', views.obtener_guardias),
    path('api/horarios/aula/<str:aula>/', views.obtener_horario_aula),
    path('api/horarios/grupo/<str:grupo>/', views.obtener_horario_grupo),

    path('api/aulas/lista/', views.lista_aulas, name='lista_aulas'),
    path('api/grupos/lista/', views.lista_grupos, name='lista_grupos'),
    
    #Profesores
    path('api/profesores/', views.obtener_profesores, name='api_hobtener_profesores'),
    path('api/profesor/<int:id_usuario>/', views.obtener_profesor, name='api_obtener_profesor'),
    
    #Usuario
    path('api/usuario/token/<str:token>/',views.obtener_usuario_token),
    
    #Ausencias
    path('api/ausencias/', views.obtener_ausencias, name='api_obtener_ausencias'),
    path('api/ausencias/profesor/<int:id_profesor>/', views.obtener_ausencias_profesor, name='api_obtener_ausencias_profesor'),
    path('api/ausencia/<int:id_ausencia>/', views.obtener_ausencia, name='api_obtener_ausencia'),
    path('api/ausencias/fecha/<str:fecha>/', views.obtener_ausencias_fecha, name='api_obtener_ausencias_fecha'),
    path('api/ausencias/crear/', views.crear_ausencia, name='api_crear_ausencia'),
    path('api/ausencias/editar/<int:id_ausencia>/', views.editar_ausencia, name='api_editar_ausencia'),
    path('api/ausencias/justificar/<int:id_ausencia>/', views.justificar_ausencia, name='api_justificar_ausencia'),
    path('api/ausencias/eliminar/<int:id_ausencia>/', views.eliminar_ausencia, name='api_eliminar_ausencia'),
    #Enviar parte de ausencias
    path('api/ausencias/enviar-parte/', views.enviar_pdf_por_correo),
    
    #CRUD USUARIO
    path('api/usuario/crear/', views.crear_usuario, name='api_crear_usuario'),
    path('api/usuario/editar/<int:id_usuario>/', views.editar_usuario, name='api_editar_usuario'),
    path('api/usuario/eliminar/<int:id_usuario>/', views.eliminar_usuario, name='api_eliminar_usuario'),
]
