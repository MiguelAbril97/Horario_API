from rest_framework import serializers
from .models import *
from datetime import datetime
from django.contrib.auth.models import Group



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
        
class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = Usuario
        fields = ['username', 'password', 'email', 'first_name', 'last_name', 'rol']
    def create(self, validated_data):
        usuario = Usuario(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            rol=validated_data['rol']
        )
        usuario.set_password(validated_data['password'])
        usuario.save()
        return usuario
    def update(self, instance, validated_data):
        instance.username = validated_data['username']
        instance.email = validated_data['email']
        instance.first_name = validated_data['first_name']
        instance.last_name = validated_data['last_name']
        instance.rol = validated_data['rol']
        instance.save()
        return instance

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

    def validate(self, data):
        profesor = data.get('profesor')
        fecha = data.get('fecha')
        horario = data.get('horario')
        
        control = Ausencia.objects.filter(profesor=profesor, fecha=fecha, horario=horario).first()
        if not control is None:
            if (not self.instance is None and control.id == self.instance.id):
                pass
            else:
                raise serializers.ValidationError("Ya existe una ausencia registrada para este profesor, fecha y horario.")
        return data
        
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
        if not ausencia is None:
            if not self.instance is None and ausencia.id == self.instance.id:
                pass
            else:
                raise serializers.ValidationError(
                    "Ya existe una ausencia registrada para este horario y fecha."
                )
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


        instance.profesor = validated_data["profesor"]
        instance.fecha = validated_data["fecha"]
        instance.motivo = validated_data["motivo"]
        instance.horario = validated_data["horario"]
        instance.save()
        return instance
    
class AusenciaSerializer(serializers.ModelSerializer):
    profesor = UsuarioSerializer(read_only=True)
    horario = HorarioSerializer(read_only=True)

    class Meta:
        model = Ausencia
        fields = '__all__'
