from django.shortcuts import redirect
from .models import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
import csv
import io
import environ
import os
from pathlib import Path
from django.contrib.auth.hashers import make_password
import unicodedata
from rest_framework import generics
from django.contrib.auth.models import Group
from oauth2_provider.models import AccessToken     



BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'), True)
env = environ.Env()

# Create your views here.
def index(request):
    return redirect('obtener_horario')

def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def importar_horarios_desde_archivo(request):
    ruta = env('RUTA_TXT')

    with open(ruta, encoding='latin-1') as archivo:
        contenido = archivo.read()
    
    lineas = io.StringIO(contenido)
    lector = csv.reader(lineas, delimiter="\t")

    for i, fila in enumerate(lector, start=1):
        if len(fila) < 6:
            print(f"Fila {i}: estructura de datos inválida.")
            continue
        
        asignatura_nombre = fila[0].strip()
        curso = fila[1].strip()
        codigo = fila[2].strip()
        profesor_nombre_apellidos = fila[3].strip()
        dia = fila[4].strip()
        hora = int(fila[5].strip())
        try:
            apellidos, nombre = [parte.strip() for parte in profesor_nombre_apellidos.split(",", 1)]
        except ValueError:
            print(f"Fila {i}: nombre y apellidos no válidos.")

        apellidos = quitar_tildes(apellidos)
        nombre = quitar_tildes(nombre)
        
        primer_apellido = apellidos.split()[0].lower()
        username = username = (nombre + apellidos).replace(" ", "")

        email = nombre.lower().replace(" ", "")+"."+primer_apellido+"@iespoligonosur.org"
        
        profesor = Usuario.objects.filter(username=username).first()
        
        if asignatura_nombre == "Equipo Directivo":
                rol = Usuario.DIRECTOR
        else:
                rol = Usuario.PROFESOR
        
        if not profesor:
            try:
                profesor = Usuario.objects.create(
                username=username,
                password = "changeme123",
                first_name=nombre,
                last_name=apellidos,
                email=email,
                rol=rol
                )
                
                if rol == Usuario.DIRECTOR:
                    group = Group.objects.get(name="Directores")
                    group.user_set.add(profesor)
                    director = Director.objects.create(usuario=profesor)
                    director.save()
                    print("Director: "+nombre+" creado")
                else:
                    group = Group.objects.get(name="Profesores")
                    group.user_set.add(profesor)
                    profesorado = Profesor.objects.create(usuario=profesor)
                    profesorado.save()
                    print("Profesor: "+nombre+" creado")

            except Exception as e:
                print(f"Error al crear el usuario: {e}")
        
        elif rol == Usuario.DIRECTOR and profesor.rol != rol:
            profesor.rol = rol
            profesor.save()
            print("Rol de profesor actualizado: "+nombre)
        
        
        asignatura = Asignatura.objects.filter(nombre=asignatura_nombre).first()
        if not asignatura:
            asignatura = Asignatura.objects.create(nombre=asignatura_nombre)

        aula = Aula.objects.filter(numero=codigo).first()
        if not aula:
            aula = Aula.objects.create(numero=codigo)

        grupo = Grupo.objects.filter(nombre=curso).first()
        if not grupo:
            grupo = Grupo.objects.create(nombre=curso)

        data = {
            "dia": dia,
            "asignatura": asignatura.id,
            "aula": aula.id,
            "grupo": grupo.id,
            "hora": hora,
            "profesor": profesor.id,
        }
        serializer = HorarioCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
        else:
            print(f"Fila {i}: {serializer.errors}")
    return redirect('obtener_horario')

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_horario(request):
    horarios = Horario.objects.select_related('profesor','grupo','aula','asignatura').all()
    serializer = HorarioSerializer(horarios, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def horario_profe(request, id_usuario):
    horarios = Horario.objects.select_related('profesor','grupo','aula','asignatura').filter(profesor=id_usuario).all()
    serializer = HorarioSerializer(horarios, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def horario_profe_dia(request, id_usuario,dia):
    horarios = Horario.objects.select_related('profesor','grupo','aula','asignatura'
                                              ).filter(profesor=id_usuario,dia=dia).all()
    serializer = HorarioSerializer(horarios, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def horarios_tarde(request):
    horarios = Horario.objects.filter(hora__gt=7)
    serializer = HorarioSerializer(horarios, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_profesores(request):
    usuarios = Usuario.objects.all()
    serializer = UsuarioSerializer(usuarios, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_horario_dia(request,dia):
    usuarios = Horario.objects.filter(dia=dia).all()
    serializer = HorarioSerializer(usuarios, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_profesor(request,id_usuario):
    usuario = Usuario.objects.get(id=id_usuario)
    serializer = UsuarioSerializer(usuario)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def crear_ausencia(request):
    serializer = AusenciaCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(repr(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_ausencias(request):
    ausencias = Ausencia.objects.select_related('profesor','horario').all()
    serializer = AusenciaSerializer(ausencias, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_ausencias_profesor(request,id_profesor):
    ausencias = Ausencia.objects.select_related('profesor','horario').filter(profesor=id_profesor).all()
    serializer = AusenciaSerializer(ausencias, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_ausencias_fecha(request,fecha):
    print(fecha)
    ausencias = Ausencia.objects.select_related('profesor','horario').filter(fecha=fecha).all()
    serializer = AusenciaSerializer(ausencias, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_ausencia(request,id_ausencia):
    ausencia = Ausencia.objects.select_related('profesor','horario').get(id=id_ausencia)
    serializer = AusenciaSerializer(ausencia)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([AllowAny])
def editar_ausencia(request, id_ausencia):
    ausencia = Ausencia.objects.get(id=id_ausencia)
    serializer = AusenciaCreateSerializer(ausencia, data=request.data)
    if serializer.is_valid():
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(repr(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def eliminar_ausencia(request, id_ausencia):
    try:
        ausencia = Ausencia.objects.get(id=id_ausencia)
        ausencia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Ausencia.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(repr(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_usuario_token(request,token):
    ModeloToken = AccessToken.objects.get(token=token)
    usuario = Usuario.objects.get(id=ModeloToken.user_id)
    serializer = UsuarioSerializer(usuario)
    return Response(serializer.data)