from rest_framework import serializers
from .models import Horario, Asignatura, Aula, Grupo, Usuario


class AsignaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asignatura
        fields = '__all__'

class AulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aula
        fields = '__all__'

class GrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grupo
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class HorarioSerializer(serializers.ModelSerializer):
    asignatura = AsignaturaSerializer(read_only=True)
    aula = AulaSerializer(read_only=True)
    grupo = GrupoSerializer(read_only=True)
    profesor = UsuarioSerializer(read_only=True)

    class Meta:
        model = Horario
        fields = '__all__'

class HorarioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = ['dia', 'asignatura', 'aula', 'grupo', 'hora', 'profesor']
