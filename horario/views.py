from django.shortcuts import redirect
from .models import *
from rest_framework.decorators import api_view, permission_classes, parser_classes
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
import unicodedata
from django.contrib.auth.models import Group
from oauth2_provider.models import AccessToken     

from rest_framework.parsers import MultiPartParser, FormParser
from django.core.mail import EmailMessage


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
            apellidos = quitar_tildes(apellidos)
            nombre = quitar_tildes(nombre)
            
            primer_apellido = apellidos.split()[0].lower()
            username = (nombre + apellidos).replace(" ", "")

            email = nombre.lower().replace(" ", "")+"."+primer_apellido+"@iespoligonosur.org"
        except ValueError:
            print(f"Error en {i}")
            nombre = profesor_nombre_apellidos
            apellidos = profesor_nombre_apellidos
            username = profesor_nombre_apellidos
            email = nombre.lower()+"."+primer_apellido+"@iespoligonosur.org"
        
        usuario = Usuario.objects.filter(username=username).first()
        
        if asignatura_nombre.find("Equipo Directivo") != -1 :
                rol = Usuario.DIRECTOR
        else:
                rol = Usuario.PROFESOR
        
        if not usuario:
            try:
                usuario = Usuario(
                    username=username,
                    first_name=nombre,
                    last_name=apellidos,
                    email=email,
                    rol=rol
                )
                usuario.set_password("changeme123")
                usuario.save()
                
                if rol == Usuario.DIRECTOR:
                    group = Group.objects.get(name="Directores")
                    group.user_set.add(usuario)
                    director = Director.objects.create(usuario=usuario)
                    director.save()
                    print("Director: "+nombre+" creado")
                else:
                    group = Group.objects.get(name="Profesores")
                    group.user_set.add(usuario)
                    profesorado = Profesor.objects.create(usuario=usuario)
                    profesorado.save()
                    print("Profesor: "+nombre+" creado")

            except Exception as e:
                print(f"Error al crear el usuario: {e}")
        
        #Si ya se habia creado el usuario como profesor se elimina del grupo profesores y se añade al directores
        elif rol == Usuario.DIRECTOR and usuario.rol != rol:
            try:
                profesor = Profesor.objects.select_related("usuario").get(usuario=usuario.id)
                profesor.delete()
                group = Group.objects.get(name="Directores")
                group.user_set.add(usuario)
                usuario.rol = rol
                usuario.save()
                director = Director.objects.create(usuario=usuario)
                director.save()
                print("Director: "+nombre+" creado")
            except Exception as e:
                print(f"Error al actualizar el rol del usuario {usuario.username}: {e}")
        
        
        asignatura = Asignatura.objects.filter(nombre=asignatura_nombre).first()
        if not asignatura:
            asignatura = Asignatura.objects.create(nombre=asignatura_nombre)

        aula = Aula.objects.filter(numero=codigo).first()
        if not aula:
            aula = Aula.objects.create(numero=codigo)

        grupo = Grupo.objects.filter(nombre=curso).first()
        if not grupo:
            grupo = Grupo.objects.create(nombre=curso)

        dia_filter = Horario.objects.select_related(
            'asignatura','aula','grupo','profesor').filter(
            dia=dia,asignatura=asignatura.id,aula=aula.id,grupo=grupo.id,hora=hora,profesor=usuario.id)
            
        if(not dia_filter):
            data = {
                "dia": dia,
                "asignatura": asignatura.id,
                "aula": aula.id,
                "grupo": grupo.id,
                "hora": hora,
                "profesor": usuario.id,
            }
            serializer = HorarioCreateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                print(f"Horario creado")
            else:
                print(f"Fila {i}: {serializer.errors}")
    
    horarios = Horario.objects.select_related('profesor','grupo','aula','asignatura').all()
    serializer = HorarioSerializer(horarios, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subir_horario(request):
    if request.user.has_perm('horario.add_horario'):
        if request.method == "POST":
            try:
                Horario.objects.all().delete()
                Profesor.objects.all().delete()
                Director.objects.all().delete()
                Usuario.objects.all().exclude(username=env("SUPERUSER_USERNAME")).delete()
                Asignatura.objects.all().delete()
                Aula.objects.all().delete()
                Grupo.objects.all().delete()
                Ausencia.objects.all().delete()
            except Exception as e:
                print(f"Error al eliminar datos: {e}")
            archivo = request.FILES['file']
            contenido = archivo.read().decode('latin-1')
            lineas = io.StringIO(contenido)
            lector = csv.reader(lineas, delimiter="\t")
            try:
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
                        apellidos = quitar_tildes(apellidos)
                        nombre = quitar_tildes(nombre)
                        
                        primer_apellido = apellidos.split()[0].lower()
                        username = (nombre + apellidos).replace(" ", "")

                        email = nombre.lower().replace(" ", "")+"."+primer_apellido+"@iespoligonosur.org"
                    except ValueError:
                        print(f"Error en {i}")
                        nombre = profesor_nombre_apellidos
                        apellidos = profesor_nombre_apellidos
                        username = profesor_nombre_apellidos
                        email = nombre.lower()+"."+primer_apellido+"@iespoligonosur.org"
                    
                    usuario = Usuario.objects.filter(username=username).first()
                    
                    if asignatura_nombre.find("Equipo Directivo") != -1 :
                            rol = Usuario.DIRECTOR
                    else:
                            rol = Usuario.PROFESOR
                    
                    if not usuario:
                        try:
                            usuario = Usuario(
                                username=username,
                                first_name=nombre,
                                last_name=apellidos,
                                email=email,
                                rol=rol
                            )
                            usuario.set_password("changeme123")
                            usuario.save()
                            
                            if rol == Usuario.DIRECTOR:
                                group = Group.objects.get(name="Directores")
                                group.user_set.add(usuario)
                                director = Director.objects.create(usuario=usuario)
                                director.save()
                                print("Director: "+nombre+" creado")
                            else:
                                group = Group.objects.get(name="Profesores")
                                group.user_set.add(usuario)
                                profesorado = Profesor.objects.create(usuario=usuario)
                                profesorado.save()
                                print("Profesor: "+nombre+" creado")

                        except Exception as e:
                            print(f"Error al crear el usuario: {e}")
                    
                    #Si ya se habia creado el usuario como profesor se elimina del grupo profesores y se añade al directores
                    elif rol == Usuario.DIRECTOR and usuario.rol != rol:
                        try:
                            profesor = Profesor.objects.select_related("usuario").get(usuario=usuario.id)
                            profesor.delete()
                            group = Group.objects.get(name="Directores")
                            group.user_set.add(usuario)
                            usuario.rol = rol
                            usuario.save()
                            director = Director.objects.create(usuario=usuario)
                            director.save()
                            print("Director: "+nombre+" creado")
                        except Exception as e:
                            print(f"Error al actualizar el rol del usuario {usuario.username}: {e}")
                    
                    
                    asignatura = Asignatura.objects.filter(nombre=asignatura_nombre).first()
                    if not asignatura:
                        asignatura = Asignatura.objects.create(nombre=asignatura_nombre)

                    aula = Aula.objects.filter(numero=codigo).first()
                    if not aula:
                        aula = Aula.objects.create(numero=codigo)

                    grupo = Grupo.objects.filter(nombre=curso).first()
                    if not grupo:
                        grupo = Grupo.objects.create(nombre=curso)

                    dia_filter = Horario.objects.select_related(
                        'asignatura','aula','grupo','profesor').filter(
                        dia=dia,asignatura=asignatura.id,aula=aula.id,grupo=grupo.id,hora=hora,profesor=usuario.id)
                        
                    if(not dia_filter):
                        data = {
                            "dia": dia,
                            "asignatura": asignatura.id,
                            "aula": aula.id,
                            "grupo": grupo.id,
                            "hora": hora,
                            "profesor": usuario.id,
                        }
                        serializer = HorarioCreateSerializer(data=data)
                        if serializer.is_valid():
                            serializer.save()
                            print(f"Horario creado")
                        else:
                            print(f"Fila {i}: {serializer.errors}")
                return Response(status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response(repr(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_usuario(request):
    if request.user.has_perm('horario.add_usuario'):
        serializer = UsuarioCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                usuario = serializer.save()
                rol = serializer.validated_data['rol']
                if rol == Usuario.DIRECTOR:
                    group = Group.objects.get(name="Directores")
                    group.user_set.add(usuario)
                    director = Director.objects.create(usuario=usuario)
                    director.save()
                elif rol == Usuario.PROFESOR:
                    group = Group.objects.get(name="Profesores")
                    group.user_set.add(usuario)
                    profesor = Profesor.objects.create(usuario=usuario)
                    profesor.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(repr(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)    
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def editar_usuario(request, id_usuario):
    if request.user.has_perm('horario.change_usuario'):
        usuario = Usuario.objects.get(id=id_usuario)
        rolUsuario = usuario.rol
        serializer = UsuarioCreateSerializer(data=request.data, instance=usuario)
        if serializer.is_valid():
            try:
                rolEditado = serializer.validated_data['rol']
                serializer.save()
                if rolEditado != rolUsuario:
                    if rolEditado == Usuario.DIRECTOR:
                        profesor = Profesor.objects.select_related("usuario").get(usuario=id_usuario)
                        profesor.delete()
                        group = Group.objects.get(name="Directores")
                        group.user_set.add(rolEditado)
                        director = Director.objects.create(usuario=usuario)
                        director.save()
                    elif rolEditado == Usuario.PROFESOR:
                        director = Director.objects.select_related("usuario").get(usuario=id_usuario)
                        director.delete()
                        group = Group.objects.get(name="Profesores")
                        group.user_set.add(rolEditado)
                        profesor = Profesor.objects.create(usuario=usuario)
                        profesor.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(repr(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_usuario(request, id_usuario):
    if request.user.has_perm('horario.delete_usuario'):
        usuario = Usuario.objects.get(id=id_usuario)
        try:
            if usuario.rol == Usuario.DIRECTOR:
                director = Director.objects.select_related("usuario").get(usuario=id_usuario)
                director.delete()
                group = Group.objects.get(name="Directores")
                group.user_set.remove(usuario)
            elif usuario.rol == Usuario.PROFESOR:
                profesor = Profesor.objects.select_related("usuario").get(usuario=id_usuario)
                profesor.delete()
                group = Group.objects.get(name="Profesores")
                group.user_set.remove(usuario)
            usuario.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_horario(request):
    if request.user.has_perm('horario.view_horario'):
        horarios = Horario.objects.select_related('profesor','grupo','aula','asignatura').all()
        serializer = HorarioSerializer(horarios, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_horario_aula(request, aula):
    if request.user.has_perm('horario.view_horario'):
        id_aula = Aula.objects.filter(numero__icontains=aula).first()
        if id_aula:
            horarios = Horario.objects.select_related('profesor','grupo','aula','asignatura').filter(aula=id_aula.id).all()
            serializer = HorarioSerializer(horarios, many=True)
            return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_horario_grupo(request, grupo):
    if request.user.has_perm('horario.view_horario'):
        id_grupo = Grupo.objects.filter(nombre__icontains=grupo).first()
        if id_grupo:
            horarios = Horario.objects.select_related('profesor','grupo','aula','asignatura').filter(grupo=id_grupo.id).all()
            serializer = HorarioSerializer(horarios, many=True)
            return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def horario_profe(request, id_usuario):
    if request.user.has_perm('horario.view_horario'):
        horarios = Horario.objects.select_related('profesor','grupo','aula','asignatura').filter(profesor=id_usuario).all()
        serializer = HorarioSerializer(horarios, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def horario_profe_dia(request, id_usuario, dia):
    if request.user.has_perm('horario.view_horario'):
        horarios = Horario.objects.select_related('profesor','grupo','aula','asignatura'
                                                  ).filter(profesor=id_usuario, dia=dia).all()
        serializer = HorarioSerializer(horarios, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def horarios_mañana(request):
    if request.user.has_perm('horario.view_horario'):
        horarios = Horario.objects.filter(hora__lte=7)
        serializer = HorarioSerializer(horarios, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def horarios_tarde(request):
    if request.user.has_perm('horario.view_horario'):
        horarios = Horario.objects.filter(hora__gt=7)
        serializer = HorarioSerializer(horarios, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_profesores(request):
    if request.user.has_perm('horario.view_usuario'):
        usuarios = Usuario.objects.all().order_by('last_name')
        serializer = UsuarioSerializer(usuarios, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def obtener_guardias(request, dia):
    if request.user.has_perm('horario.view_horario'):
        horarios = Horario.objects.select_related('profesor', 'grupo', 'aula', 'asignatura'
                            ).filter(asignatura__nombre__icontains="Guardia", dia=dia).all()
        serializer = HorarioSerializer(horarios, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_horario_dia(request, dia):
    if request.user.has_perm('horario.view_horario'):
        usuarios = Horario.objects.filter(dia=dia).all()
        serializer = HorarioSerializer(usuarios, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_profesor(request, id_usuario):
    if request.user.has_perm('horario.view_usuario'):
        usuario = Usuario.objects.get(id=id_usuario)
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_ausencia(request):
    if request.user.has_perm('horario.add_ausencia'):
        serializer = AusenciaCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(repr(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
       
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_ausencias(request):
    if request.user.has_perm('horario.view_ausencia'):
        ausencias = Ausencia.objects.select_related('profesor','horario').all()
        serializer = AusenciaSerializer(ausencias, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_ausencias_profesor(request, id_profesor):
    if request.user.has_perm('horario.view_ausencia'):
        if request.user.groups.filter(name="Directores").exists() or request.user.id == id_profesor:
            ausencias = Ausencia.objects.select_related('profesor', 'horario').filter(profesor=id_profesor).all()
            serializer = AusenciaSerializer(ausencias, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_ausencias_fecha(request, fecha):
    if request.user.has_perm('horario.view_ausencia'):
        ausencias = Ausencia.objects.select_related('profesor','horario').filter(fecha=fecha).all()
        serializer = AusenciaSerializer(ausencias, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_ausencia(request, id_ausencia):
    if request.user.has_perm('horario.view_horario'):
        ausencia = Ausencia.objects.select_related('profesor','horario').get(id=id_ausencia)
        serializer = AusenciaSerializer(ausencia)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def editar_ausencia(request, id_ausencia):
    ausencia = Ausencia.objects.get(id=id_ausencia)
    serializer = AusenciaCreateSerializer(data=request.data, instance=ausencia)
    if serializer.is_valid():
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(repr(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(serializer.errors)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_ausencia(request, id_ausencia):
    if request.user.has_perm('horario.delete_ausencia'):
        try:
            ausencia = Ausencia.objects.get(id=id_ausencia)
            ausencia.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Ausencia.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(repr(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def enviar_pdf_por_correo(request):
    if request.user.is_superuser or request.user.groups.filter(name="Directores").exists():
        pdf_file = request.FILES.get('pdf')
        destinatario = env('EMAIL_USER') 
        #request.data.get('email')

        if not pdf_file or not destinatario:
            return Response({'error': 'Falta el archivo PDF o el email de destino.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            email = EmailMessage(
                subject='Envío de PDF',
                body='Adjunto el PDF solicitado.',
                from_email=None,  # Usará DEFAULT_FROM_EMAIL
                to=[destinatario]
            )
            email.attach(pdf_file.name, pdf_file.read(), 'application/pdf')
            email.send()
            return Response({'mensaje': 'Correo enviado correctamente.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def obtener_usuario_token(request, token):
    ModeloToken = AccessToken.objects.get(token=token)
    usuario = Usuario.objects.get(id=ModeloToken.user_id)
    serializer = UsuarioSerializer(usuario)
    return Response(serializer.data)
