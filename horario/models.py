from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class Usuario(AbstractUser):
    DIRECTOR = 1
    PROFESOR = 2
    ROLES = (
        (DIRECTOR, 'directores'),
        (PROFESOR, 'profesores'),
    )
    rol = models.PositiveSmallIntegerField(choices=ROLES,default=1)
    
    def __str__(self):
        return self.username

class Director (models.Model):
    models.ForeignKey(Usuario, on_delete=models.CASCADE)

class Profesor(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

class Asignatura(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre

class Aula(models.Model):
    numero = models.CharField(max_length=50)

    def __str__(self):
        return self.numero
    
class Grupo(models.Model):
    nombre = models.CharField(max_length=100)
        
    def __str__(self):
        return self.nombre

class Horario(models.Model):
    DIAS = (
        ('L', 'Lunes'),
        ('M', 'Martes'),
        ('X', 'Miércoles'),
        ('J', 'Jueves'),
        ('V', 'Viernes'),
    )
    dia = models.CharField(choices=DIAS, max_length=1, default='L')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE)
    hora = models.IntegerField(default=1)
    profesor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    
class Ausencia(models.Model):
    profesor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateField()
    motivo = models.CharField(max_length=200,blank=True)
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.profesor.username} - {self.fecha}"
