from rest_framework import serializers
from .models import *
from datetime import datetime


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


class AusenciaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ausencia
        fields = ['profesor', 'fecha', 'motivo', 'horario']

    def validate_motivo(self, motivo):
        if len(motivo) > 200:
            raise serializers.ValidationError("El motivo no puede superar los 200 caracteres.")
        return motivo

    def validate_fecha(self, fecha):
        if(fecha < datetime.now().date()):
            raise serializers.ValidationError("La fecha no puede ser anterior a la fecha actual.")
        return fecha
    
    def validate_horario_fecha(self, horario,fecha):
        ausencia = Ausencia.objects.filter(horario=horario, fecha=fecha).first()
        if(not ausencia is None):
            if(not self.instance is None and ausencia.id == self.instance,id):
                pass
            else:
                raise serializers.ValidationError("Ya existe una ausencia registrada para este horario y fecha.")
        return horario
    
    def create(self, validated_data):

        ausencia = Ausencia.objects.create(
            profesor=validated_data["profesor"],
            fecha=validated_data["fecha"],
            motivo=validated_data["motivo"],
            horario=validated_data["horario"]
        )
        return ausencia
    
    def update(self, instance, validated_data):
        fecha = validated_data.get('fecha')
        try:
            validated_data['fecha'] = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            raise serializers.ValidationError({"fecha": "Formato de fecha inválido. Usa YYYY-MM-DD."})


        instance.profesor=validated_data["profesor"],
        instance.fecha=validated_data["fecha"],
        instance.motivo=validated_data["motivo"],
        instance.horario=validated_data["horario"]
        
        return instance
    
class AusenciaSerializer(serializers.ModelSerializer):
    profesor = UsuarioSerializer(read_only=True)
    horario = HorarioSerializer(read_only=True)

    class Meta:
        model = Ausencia
        fields = '__all__'