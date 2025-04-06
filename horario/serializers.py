from rest_framework import serializers
from .models import Horario, Asignatura, Aula, Grupo, Usuario

class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = ('dia', 'asignatura', 'aula', 'grupo', 'hora', 'profesor')
