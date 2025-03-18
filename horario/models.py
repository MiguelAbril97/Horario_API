from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class Usuario(AbstractUser):
    ADMINISTRADOR = 1
    DIRECTOR = 2
    PROFESOR = 3
    ROLES = (
        (ADMINISTRADOR, 'administradores'),
        (DIRECTOR, 'directores'),
        (PROFESOR, 'profesores'),
    )
    rol = models.PositiveSmallIntegerField(choices=ROLES,default=1)
    
    def __str__(self):
        return self.username
    
class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    nivel = models.CharField(max_length=1)
    #Hace referencia a la letra de la clase, por ejemplo: 1 Eso A. Uso blank y no null para que permita valores vacíos
    clase = models.CharField(max_length=1, blank=True)
    
    def __str__(self):
        return self.nombre

class Asignatura(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre

class Aula(models.Model):
    numero = models.CharField(max_length=3)

    def __str__(self):
        return self.numero
    
class Horario(models.Model):
    DIAS = (
        ('L', 'Lunes'),
        ('M', 'Martes'),
        ('X', 'Miércoles'),
        ('J', 'Jueves'),
        ('V', 'Viernes'),
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    dia = models.CharField(choices=DIAS, max_length=1)
    hora = models.CharField(max_length=1)
    profesor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
