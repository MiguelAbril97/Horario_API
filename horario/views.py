from django.shortcuts import render,redirect
from .models import *
from django.contrib import messages
from .serializers import HorarioSerializer
import csv
import io
import environ
import os
from pathlib import Path
from django.contrib.auth.hashers import make_password
import unicodedata


BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'), True)
env = environ.Env()

# Create your views here.
def index(request):
    return render(request, 'horario/index.html')

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

    errores = []
    for i, fila in enumerate(lector, start=1):
        if len(fila) < 6:
            errores.append(f"Fila {i}: estructura de datos inválida.")
            continue
        
        asignatura_nombre = fila[0].strip()
        curso = fila[1].strip()
        codigo = fila[2].strip()
        profesor_nombre_apellidos = fila[3].strip()
        dia = fila[4].strip()
        hora = fila[5].strip()
        
        apellidos, nombre = [parte.strip() for parte in profesor_nombre_apellidos.split(",", 1)]
        apellidos = quitar_tildes(apellidos)
        nombre = quitar_tildes(nombre)
        
        primer_apellido = apellidos.split()[0].lower()
        username = username = (nombre + apellidos).replace(" ", "")

        email = nombre.lower().replace(" ", "")+"."+primer_apellido+"@iespoligonosur.org"
        
        profesor = Usuario.objects.filter(username=username).first()
        
        if not profesor:
            try:
                profesor = Usuario.objects.create(
                username=username,
                password = make_password("changeme123"),
                first_name=nombre,
                last_name=apellidos,
                email=email,
                rol=2
                )
            except Exception as e:
                print(f"Error al crear el usuario: {e}")
        
        
        asignatura = Asignatura.objects.filter(nombre=asignatura_nombre).first()
        if not asignatura:
            asignatura = Asignatura.objects.create(nombre=asignatura_nombre)

        aula = Aula.objects.filter(numero=codigo).first()
        if not aula:
            aula = Aula.objects.create(numero=codigo)

        grupo = Grupo.objects.filter(nombre=curso).first()
        if not grupo:
            grupo = Grupo.objects.create(nombre=curso)

        """try:
            profesor = Usuario.objects.get(username=profesor_nombre)
        except Usuario.DoesNotExist:
            errores.append(f"Fila {i}: Profesor '{profesor_nombre}' no encontrado.")
            continue"""

        data = {
            "dia": dia,
            "asignatura": asignatura.id,
            "aula": aula.id,
            "grupo": grupo.id,
            "hora": hora,
            "profesor": profesor.id,
        }
        serializer = HorarioSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
        else:
            errores.append(f"Fila {i}: {serializer.errors}")

    if errores:
        return print("Errores:\n" + "\n".join(errores), content_type="text/plain")
    return print("Importación exitosa", content_type="text/plain")