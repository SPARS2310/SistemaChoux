from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import path

from .views import (
    actualizar_descanso,
    crear_empleado,
    crear_encargado,
    dashboard,
    mover_empleado_sucursal,
    rfid_event,
)

urlpatterns = [
    path('', lambda request: redirect('login'), name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', LoginView.as_view(template_name='asistencia/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('actualizar-descanso/', actualizar_descanso, name='actualizar_descanso'),
    path('crear-empleado/', crear_empleado, name='crear_empleado'),
    path('crear-encargado/', crear_encargado, name='crear_encargado'),
    path('mover-empleado-sucursal/', mover_empleado_sucursal, name='mover_empleado_sucursal'),
    path('api/rfid-event/', rfid_event, name='rfid_event'),
]
