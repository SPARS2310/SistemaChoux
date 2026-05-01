from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import path

from .views import (
    actualizar_descanso,
    crear_empleado,
    crear_empleado_usuario,
    crear_encargado,
    CustomLoginView,
    dashboard,
    mover_empleado_sucursal,
    mi_asistencia,
    rfid_event,
)

urlpatterns = [
    path('', lambda request: redirect('login'), name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('mi-asistencia/', mi_asistencia, name='mi_asistencia'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('actualizar-descanso/', actualizar_descanso, name='actualizar_descanso'),
    path('crear-empleado/', crear_empleado, name='crear_empleado'),
    path('crear-empleado-usuario/', crear_empleado_usuario, name='crear_empleado_usuario'),
    path('crear-encargado/', crear_encargado, name='crear_encargado'),
    path('mover-empleado-sucursal/', mover_empleado_sucursal, name='mover_empleado_sucursal'),
    path('api/rfid-event/', rfid_event, name='rfid_event'),
]
