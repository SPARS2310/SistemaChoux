from django.conf import settings
from django.db import models
from django.utils import timezone


class Sucursal(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    direccion = models.CharField(max_length=255, blank=True, default='')
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    DIA_DESCANSO_CHOICES = (
        ('LUNES', 'Lunes'),
        ('MARTES', 'Martes'),
        ('MIERCOLES', 'Miércoles'),
        ('JUEVES', 'Jueves'),
        ('VIERNES', 'Viernes'),
        ('SABADO', 'Sábado'),
        ('DOMINGO', 'Domingo'),
    )

    nombre = models.CharField(max_length=120)
    rfid_uid = models.CharField(max_length=64, unique=True)
    activo = models.BooleanField(default=True)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='empleados', null=True, blank=True)
    dia_descanso = models.CharField(
        max_length=10,
        choices=DIA_DESCANSO_CHOICES,
        default='DOMINGO'
    )

    def __str__(self):
        return f"{self.nombre} ({self.rfid_uid})"


class PerfilUsuario(models.Model):
    ROL_CHOICES = (
        ('ADMIN', 'Administrador'),
        ('ENCARGADO', 'Encargado de sucursal'),
        ('EMPLEADO', 'Empleado'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=12, choices=ROL_CHOICES, default='ENCARGADO')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, null=True, blank=True, related_name='encargados')
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, null=True, blank=True, related_name='usuario')

    def __str__(self):
        return f"{self.user.username} - {self.rol}"


class RegistroAcceso(models.Model):
    TIPO_CHOICES = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    )

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='registros')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha_hora = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.empleado.nombre} - {self.tipo} - {self.fecha_hora}"
