from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import Group
from pathlib import Path
import csv
import io
import os
import unicodedata
import environ

from horario.models import Usuario, Director, Profesor, Asignatura, Aula, Grupo, Horario
from horario.serializers import HorarioCreateSerializer

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Ruta personalizada del fichero a importar')

    def _quitar_tildes(self, texto: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def handle(self, *args, **options):
        env = environ.Env()
        environ.Env.read_env(os.path.join(settings.BASE_DIR, '.env'), True)
        file_path = options.get('path') or env('RUTA_TXT', default=None)
        if not file_path:
            file_path = Path(settings.BASE_DIR) / 'Datos_horarios.txt'
        else:
            file_path = Path(file_path)

        if not file_path.exists():
            self.stderr.write(f'Archivo no encontrado: {file_path}')
            return

        self.stdout.write(f'Importando horarios desde {file_path}')
        with open(file_path, encoding='latin-1') as archivo:
            contenido = archivo.read()

        lineas = io.StringIO(contenido)
        lector = csv.reader(lineas, delimiter='\t')

        for i, fila in enumerate(lector, start=1):
            if len(fila) < 6:
                self.stderr.write(f'Fila {i}: estructura de datos inválida.')
                continue

            asignatura_nombre = fila[0].strip()
            curso = fila[1].strip()
            codigo = fila[2].strip()
            profesor_nombre_apellidos = fila[3].strip()
            dia = fila[4].strip()
            hora = int(fila[5].strip())

            try:
                apellidos, nombre = [parte.strip() for parte in profesor_nombre_apellidos.split(',', 1)]
                apellidos = self._quitar_tildes(apellidos)
                nombre = self._quitar_tildes(nombre)

                primer_apellido = apellidos.split()[0].lower()
                username = (nombre + apellidos).replace(' ', '')
                email = nombre.lower().replace(' ', '') + '.' + primer_apellido + '@iespoligonosur.org'
            except ValueError:
                self.stderr.write(f'Error procesando profesor en fila {i}')
                nombre = profesor_nombre_apellidos
                apellidos = profesor_nombre_apellidos
                username = profesor_nombre_apellidos
                email = nombre.lower() + '.' + apellidos.split()[0].lower() + '@iespoligonosur.org'

            usuario = Usuario.objects.filter(username=username).first()
            rol = Usuario.DIRECTOR if 'Equipo Directivo' in asignatura_nombre else Usuario.PROFESOR

            if not usuario:
                usuario = Usuario(
                    username=username,
                    first_name=nombre,
                    last_name=apellidos,
                    email=email,
                    rol=rol
                )
                usuario.set_password('changeme123')
                usuario.save()

                if rol == Usuario.DIRECTOR:
                    group = Group.objects.get(name='Directores')
                    group.user_set.add(usuario)
                    Director.objects.create(usuario=usuario)
                else:
                    group = Group.objects.get(name='Profesores')
                    group.user_set.add(usuario)
                    Profesor.objects.create(usuario=usuario)
            elif rol == Usuario.DIRECTOR and usuario.rol != rol:
                try:
                    profesor = Profesor.objects.select_related('usuario').get(usuario=usuario.id)
                    profesor.delete()
                except Profesor.DoesNotExist:
                    pass
                group = Group.objects.get(name='Directores')
                group.user_set.add(usuario)
                usuario.rol = rol
                usuario.save()
                Director.objects.create(usuario=usuario)

            asignatura = Asignatura.objects.filter(nombre=asignatura_nombre).first()
            if not asignatura:
                asignatura = Asignatura.objects.create(nombre=asignatura_nombre)

            aula = Aula.objects.filter(numero=codigo).first()
            if not aula:
                aula = Aula.objects.create(numero=codigo)

            grupo = Grupo.objects.filter(nombre=curso).first()
            if not grupo:
                grupo = Grupo.objects.create(nombre=curso)

            existe = Horario.objects.filter(
                dia=dia,
                asignatura=asignatura,
                aula=aula,
                grupo=grupo,
                hora=hora,
                profesor=usuario
            ).exists()

            if not existe:
                data = {
                    'dia': dia,
                    'asignatura': asignatura.id,
                    'aula': aula.id,
                    'grupo': grupo.id,
                    'hora': hora,
                    'profesor': usuario.id,
                }
                serializer = HorarioCreateSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    self.stderr.write(f'Fila {i}: {serializer.errors}')

        self.stdout.write(self.style.SUCCESS('Importación finalizada'))


