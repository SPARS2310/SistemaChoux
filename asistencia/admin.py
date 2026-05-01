from django.contrib import admin

from .models import Empleado, PerfilUsuario, RegistroAcceso, Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'direccion', 'activa')
    search_fields = ('nombre', 'direccion')
    list_filter = ('activa',)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'rfid_uid', 'sucursal', 'activo', 'dia_descanso')
    search_fields = ('nombre', 'rfid_uid', 'sucursal__nombre')
    list_filter = ('activo', 'dia_descanso', 'sucursal')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'rol', 'sucursal')
    search_fields = ('user__username', 'user__email', 'sucursal__nombre')
    list_filter = ('rol', 'sucursal')


@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ('id', 'empleado', 'tipo', 'fecha_hora')
    list_filter = ('tipo', 'fecha_hora', 'empleado__sucursal')
    search_fields = ('empleado__nombre', 'empleado__rfid_uid', 'empleado__sucursal__nombre')
