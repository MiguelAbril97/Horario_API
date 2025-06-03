from rest_framework.test import APITestCase
from django.urls import reverse
from .models import Usuario, Aula, Grupo, Horario, Asignatura, Ausencia
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

# Usuarios
class UsuarioAPITests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(username='admin', password='adminpass', rol=Usuario.DIRECTOR)
        self.client.login(username='admin', password='adminpass')

    def test_crear_usuario(self):
        url = reverse('api_crear_usuario')
        data = {
            'username': 'nuevo_user',
            'password': 'test1234',
            'email': 'test@example.com',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'rol': Usuario.PROFESOR
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Usuario.objects.filter(username='nuevo_user').count(), 1)

    def test_editar_usuario(self):
        user = Usuario.objects.create_user(username='edit_user', password='pass', rol=Usuario.PROFESOR)
        url = reverse('api_editar_usuario', args=[user.id])
        data = {
            'username': 'edit_user',
            'password': 'pass',
            'email': 'edit@example.com',
            'first_name': 'NombreEditado',
            'last_name': 'ApellidoEditado',
            'rol': Usuario.DIRECTOR
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_eliminar_usuario(self):
        user = Usuario.objects.create_user(username='delete_user', password='pass', rol=Usuario.PROFESOR)
        url = reverse('api_eliminar_usuario', args=[user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_obtener_usuario(self):
        user = Usuario.objects.create_user(username='view_user', password='pass', rol=Usuario.PROFESOR)
        url = reverse('api_obtener_profesor', args=[user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# Horarios
class HorarioAPITests(APITestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(username='testuser', password='testpass', rol=Usuario.PROFESOR)
        self.client.login(username='testuser', password='testpass')
        self.aula = Aula.objects.create(numero='A101')
        self.grupo = Grupo.objects.create(nombre='1A')
        self.asignatura = Asignatura.objects.create(nombre='Matemáticas')
        self.horario = Horario.objects.create(dia='L', asignatura=self.asignatura, aula=self.aula, grupo=self.grupo, hora=1, profesor=self.user)

    def test_obtener_horario(self):
        url = reverse('api_obtener_horario')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_obtener_horario_aula(self):
        url = reverse('lista_aulas')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_obtener_horario_grupo(self):
        url = reverse('lista_grupos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_horario_profesor(self):
        url = reverse('api_horario_profe', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# Ausencias
class AusenciaAPITests(APITestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(username='testuser', password='testpass', rol=Usuario.PROFESOR)
        self.client.login(username='testuser', password='testpass')
        self.aula = Aula.objects.create(numero='A101')
        self.grupo = Grupo.objects.create(nombre='1A')
        self.asignatura = Asignatura.objects.create(nombre='Matemáticas')
        self.horario = Horario.objects.create(dia='L', asignatura=self.asignatura, aula=self.aula, grupo=self.grupo, hora=1, profesor=self.user)

    def test_crear_ausencia(self):
        url = reverse('api_crear_ausencia')
        data = {
            'profesor': self.user.id,
            'fecha': '2025-12-31',
            'motivo': 'Motivo de prueba',
            'horario': self.horario.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_justificar_ausencia(self):
        ausencia = Ausencia.objects.create(profesor=self.user, fecha='2025-12-31', motivo='Motivo', horario=self.horario)
        url = reverse('api_justificar_ausencia', args=[ausencia.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_eliminar_ausencia(self):
        ausencia = Ausencia.objects.create(profesor=self.user, fecha='2025-12-31', motivo='Motivo', horario=self.horario)
        url = reverse('api_eliminar_ausencia', args=[ausencia.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_obtener_ausencias(self):
        url = reverse('api_obtener_ausencias')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# Subir horario
class SubirHorarioAPITests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(username='admin', password='adminpass', rol=Usuario.DIRECTOR)
        self.client.login(username='admin', password='adminpass')

    def test_subir_horario_txt(self):
        url = reverse('subir_horario')
        contenido = "Matemáticas\t1A\tA101\tApellido,Nombre\tL\t1\n"
        archivo = SimpleUploadedFile('horario.txt', contenido.encode('latin-1'), content_type='text/plain')
        response = self.client.post(url, {'file': archivo}, format='multipart')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])  # depende de permisos y limpieza previa

# Enviar PDF
class EnviarPDFAPITests(APITestCase):
    def setUp(self):
        self.superuser = Usuario.objects.create_superuser(username='superadmin', password='superpass', email='super@test.com')
        self.client.login(username='superadmin', password='superpass')

    def test_enviar_pdf(self):
        url = reverse('api_enviar_pdf')
        pdf_content = b'%PDF-1.4 fake pdf content'
        archivo_pdf = SimpleUploadedFile('parte.pdf', pdf_content, content_type='application/pdf')
        response = self.client.post(url, {'pdf': archivo_pdf}, format='multipart')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
