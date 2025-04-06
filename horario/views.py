from django.shortcuts import render,redirect
from .models import *
from django.contrib import messages
from .serializers import HorarioSerializer
import csv
import io
import environ
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'), True)
env = environ.Env()

# Create your views here.
def index(request):
    return render(request, 'horario/index.html')

def importar_horarios_desde_archivo():
    ruta = env('RUTA_TXT')

    with open(ruta, encoding='utf-8') as archivo:
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
        profesor_nombre = fila[3].strip()
        dia = fila[4].strip()
        hora = fila[5].strip()

        asignatura, _ = Asignatura.objects.get_or_create(nombre=asignatura_nombre)
        aula, _ = Aula.objects.get_or_create(numero=codigo)
        grupo, _ = Grupo.objects.get_or_create(nombre=curso)

        try:
            profesor = Usuario.objects.get(username=profesor_nombre)
        except Usuario.DoesNotExist:
            errores.append(f"Fila {i}: Profesor '{profesor_nombre}' no encontrado.")
            continue

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