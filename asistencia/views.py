import json
from datetime import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import IntegrityError
from django.db.models import Max, Min
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Empleado, PerfilUsuario, RegistroAcceso, Sucursal


def _get_contexto_usuario(user):
    if user.is_superuser:
        return 'ADMIN', None
    perfil = getattr(user, 'perfil', None)
    if not perfil:
        return 'ENCARGADO', None
    return perfil.rol, perfil.sucursal_id


def _filtrar_por_permiso(queryset, user):
    rol, sucursal_id = _get_contexto_usuario(user)
    if rol == 'ADMIN':
        return queryset, rol, None
    if sucursal_id:
        return queryset.filter(empleado__sucursal_id=sucursal_id), rol, sucursal_id
    return queryset.none(), rol, None


def _build_resumen(registros, desde=None, hasta=None):
    if desde:
        registros = registros.filter(fecha_hora__date__gte=desde)
    if hasta:
        registros = registros.filter(fecha_hora__date__lte=hasta)

    grupos = (
        registros.values(
            'empleado_id',
            'empleado__nombre',
            'empleado__rfid_uid',
            'empleado__sucursal__nombre',
            'fecha_hora__date'
        )
        .annotate(
            primera_entrada=Min('fecha_hora'),
            ultima_marca=Max('fecha_hora')
        )
        .order_by('-fecha_hora__date', 'empleado__sucursal__nombre', 'empleado__nombre')
    )

    resumen = []
    for g in grupos:
        primera_entrada = (
            registros.filter(
                empleado_id=g['empleado_id'],
                fecha_hora__date=g['fecha_hora__date'],
                tipo='ENTRADA'
            ).order_by('fecha_hora').first()
        )
        ultima_salida = (
            registros.filter(
                empleado_id=g['empleado_id'],
                fecha_hora__date=g['fecha_hora__date'],
                tipo='SALIDA'
            ).order_by('-fecha_hora').first()
        )

        resumen.append({
            'fecha': g['fecha_hora__date'],
            'empleado': g['empleado__nombre'],
            'uid': g['empleado__rfid_uid'],
            'sucursal': g['empleado__sucursal__nombre'] or 'Sin sucursal',
            'hora_entrada': primera_entrada.fecha_hora if primera_entrada else None,
            'hora_salida': ultima_salida.fecha_hora if ultima_salida else None,
        })
    return resumen


class CustomLoginView(LoginView):
    """Vista de login personalizada que redirije según el rol del usuario."""
    template_name = 'asistencia/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        perfil = getattr(self.request.user, 'perfil', None)
        if perfil and perfil.rol == 'EMPLEADO':
            return reverse_lazy('mi_asistencia')
        return reverse_lazy('dashboard')


@login_required
def dashboard(request):
    fecha_desde = request.GET.get('desde') or ''
    fecha_hasta = request.GET.get('hasta') or ''
    sucursal_filtro = request.GET.get('sucursal') or ''

    desde = None
    hasta = None
    if fecha_desde:
        try:
            desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        except ValueError:
            fecha_desde = ''
    if fecha_hasta:
        try:
            hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        except ValueError:
            fecha_hasta = ''

    base = RegistroAcceso.objects.select_related('empleado', 'empleado__sucursal')
    base, rol, sucursal_restringida = _filtrar_por_permiso(base, request.user)

    if rol == 'ADMIN' and sucursal_filtro:
        base = base.filter(empleado__sucursal_id=sucursal_filtro)

    ultimos = base.order_by('-fecha_hora')[:20]
    resumen = _build_resumen(base, desde, hasta)

    empleados = Empleado.objects.select_related('sucursal').order_by('nombre')
    if rol != 'ADMIN':
        empleados = empleados.filter(sucursal_id=sucursal_restringida)

    sucursales = Sucursal.objects.filter(activa=True).order_by('nombre')
    if rol != 'ADMIN' and sucursal_restringida:
        sucursales = sucursales.filter(id=sucursal_restringida)

    return render(
        request,
        'asistencia/dashboard.html',
        {
            'ultimos': ultimos,
            'resumen': resumen,
            'empleados': empleados,
            'sucursales': sucursales,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'sucursal_filtro': sucursal_filtro,
            'dias_descanso': Empleado.DIA_DESCANSO_CHOICES,
            'rol': rol,
        }
    )


@login_required
def crear_empleado(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Solo POST')

    rol, sucursal_id = _get_contexto_usuario(request.user)
    if rol not in ('ADMIN', 'ENCARGADO'):
        return HttpResponseBadRequest('No autorizado')

    nombre = (request.POST.get('nombre') or '').strip()
    rfid_uid = (request.POST.get('rfid_uid') or '').strip()
    dia_descanso = request.POST.get('dia_descanso')
    sucursal_destino_id = request.POST.get('sucursal_id')

    if not nombre or not rfid_uid or not dia_descanso:
        return HttpResponseBadRequest('Faltan datos')

    validos = {v for v, _ in Empleado.DIA_DESCANSO_CHOICES}
    if dia_descanso not in validos:
        return HttpResponseBadRequest('Día de descanso inválido')

    if rol == 'ADMIN':
        if not sucursal_destino_id:
            return HttpResponseBadRequest('Falta sucursal')
        sucursal = get_object_or_404(Sucursal, id=sucursal_destino_id, activa=True)
    else:
        if not sucursal_id:
            return HttpResponseBadRequest('Encargado sin sucursal asignada')
        sucursal = get_object_or_404(Sucursal, id=sucursal_id, activa=True)

    try:
        Empleado.objects.create(
            nombre=nombre,
            rfid_uid=rfid_uid,
            dia_descanso=dia_descanso,
            sucursal=sucursal,
            activo=True,
        )
    except IntegrityError:
        return HttpResponseBadRequest('UID RFID ya registrado')

    return redirect('dashboard')


@login_required
def crear_encargado(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Solo POST')

    rol, _ = _get_contexto_usuario(request.user)
    if rol != 'ADMIN':
        return HttpResponseBadRequest('Solo ADMIN puede crear encargados')

    username = (request.POST.get('username') or '').strip()
    password = request.POST.get('password') or ''
    sucursal_id = request.POST.get('sucursal_id')

    if not username or not password or not sucursal_id:
        return HttpResponseBadRequest('Faltan datos')

    sucursal = get_object_or_404(Sucursal, id=sucursal_id, activa=True)

    try:
        user = User.objects.create_user(username=username, password=password)
    except IntegrityError:
        return HttpResponseBadRequest('El usuario ya existe')

    PerfilUsuario.objects.update_or_create(
        user=user,
        defaults={'rol': 'ENCARGADO', 'sucursal': sucursal}
    )

    return redirect('dashboard')


@login_required
def crear_empleado_usuario(request):
    """Crear una cuenta de usuario para un empleado existente."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Solo POST')

    rol, sucursal_id = _get_contexto_usuario(request.user)
    if rol not in ('ADMIN', 'ENCARGADO'):
        return HttpResponseBadRequest('No autorizado')

    username = (request.POST.get('username') or '').strip()
    password = request.POST.get('password') or ''
    empleado_id = request.POST.get('empleado_id')

    if not username or not password or not empleado_id:
        return HttpResponseBadRequest('Faltan datos')

    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    # Verificar permisos
    if rol == 'ENCARGADO' and (not sucursal_id or empleado.sucursal_id != sucursal_id):
        return HttpResponseBadRequest('No autorizado para este empleado')

    try:
        user = User.objects.create_user(username=username, password=password)
    except IntegrityError:
        return HttpResponseBadRequest('El usuario ya existe')

    PerfilUsuario.objects.update_or_create(
        user=user,
        defaults={'rol': 'EMPLEADO', 'empleado': empleado}
    )

    return redirect('dashboard')


@login_required
def eliminar_empleado(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Solo POST')

    rol, sucursal_id = _get_contexto_usuario(request.user)
    if rol not in ('ADMIN', 'ENCARGADO'):
        return HttpResponseBadRequest('No autorizado')

    empleado_id = request.POST.get('empleado_id')
    if not empleado_id:
        return HttpResponseBadRequest('Faltan datos')

    empleado = get_object_or_404(Empleado, id=empleado_id)

    if rol == 'ENCARGADO' and (not sucursal_id or empleado.sucursal_id != sucursal_id):
        return HttpResponseBadRequest('No autorizado para este empleado')

    perfil_empleado = PerfilUsuario.objects.filter(empleado=empleado).first()
    if perfil_empleado:
        user = perfil_empleado.user
        perfil_empleado.delete()
        user.delete()

    empleado.delete()
    return redirect('dashboard')


@login_required
def mover_empleado_sucursal(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Solo POST')

    rol, _ = _get_contexto_usuario(request.user)
    if rol != 'ADMIN':
        return HttpResponseBadRequest('Solo ADMIN puede mover empleados entre sucursales')

    empleado_id = request.POST.get('empleado_id')
    sucursal_id = request.POST.get('sucursal_id')

    if not empleado_id or not sucursal_id:
        return HttpResponseBadRequest('Faltan datos')

    empleado = get_object_or_404(Empleado, id=empleado_id)
    sucursal = get_object_or_404(Sucursal, id=sucursal_id, activa=True)

    empleado.sucursal = sucursal
    empleado.save(update_fields=['sucursal'])

    return redirect('dashboard')


@login_required
def actualizar_descanso(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Solo POST')

    empleado_id = request.POST.get('empleado_id')
    dia_descanso = request.POST.get('dia_descanso')

    if not empleado_id or not dia_descanso:
        return HttpResponseBadRequest('Faltan datos')

    empleado = get_object_or_404(Empleado, id=empleado_id)
    rol, sucursal_id = _get_contexto_usuario(request.user)

    if rol != 'ADMIN' and (not sucursal_id or empleado.sucursal_id != sucursal_id):
        return HttpResponseBadRequest('No autorizado para este empleado')

    validos = {v for v, _ in Empleado.DIA_DESCANSO_CHOICES}
    if dia_descanso not in validos:
        return HttpResponseBadRequest('Día de descanso inválido')

    empleado.dia_descanso = dia_descanso
    empleado.save(update_fields=['dia_descanso'])

    return redirect('dashboard')


@csrf_exempt
def rfid_event(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Solo POST')

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('JSON inválido')

    uid = data.get('uid')
    if not uid:
        return HttpResponseBadRequest('Falta uid')

    try:
        empleado = Empleado.objects.select_related('sucursal').get(rfid_uid=uid, activo=True)
    except Empleado.DoesNotExist:
        return JsonResponse(
            {'ok': False, 'error': 'Tarjeta no registrada o empleado inactivo'},
            status=404
        )

    ultimo = RegistroAcceso.objects.filter(empleado=empleado).order_by('-fecha_hora').first()
    tipo = 'ENTRADA' if (not ultimo or ultimo.tipo == 'SALIDA') else 'SALIDA'

    reg = RegistroAcceso.objects.create(
        empleado=empleado,
        tipo=tipo,
        fecha_hora=timezone.now()
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'accesos',
        {
            'type': 'nuevo_acceso',
            'payload': {
                'empleado': empleado.nombre,
                'uid': empleado.rfid_uid,
                'tipo': reg.tipo,
                'sucursal': empleado.sucursal.nombre if empleado.sucursal else 'Sin sucursal',
                'fecha_hora': reg.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
            }
        }
    )

    return JsonResponse({
        'ok': True,
        'empleado': empleado.nombre,
        'uid': empleado.rfid_uid,
        'tipo': reg.tipo,
        'sucursal': empleado.sucursal.nombre if empleado.sucursal else 'Sin sucursal',
        'fecha_hora': reg.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
    })


@login_required
def mi_asistencia(request):
    """Vista para empleados donde ven solo sus entradas, salidas y faltas."""
    perfil = getattr(request.user, 'perfil', None)
    
    # Solo empleados pueden acceder a esta vista
    if not perfil or perfil.rol != 'EMPLEADO' or not perfil.empleado:
        return redirect('dashboard')
    
    empleado = perfil.empleado
    fecha_desde = request.GET.get('desde') or ''
    fecha_hasta = request.GET.get('hasta') or ''
    
    desde = None
    hasta = None
    if fecha_desde:
        try:
            desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        except ValueError:
            fecha_desde = ''
    if fecha_hasta:
        try:
            hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        except ValueError:
            fecha_hasta = ''
    
    registros = empleado.registros.select_related('empleado')
    
    if desde:
        registros = registros.filter(fecha_hora__date__gte=desde)
    if hasta:
        registros = registros.filter(fecha_hora__date__lte=hasta)
    
    registros = registros.order_by('-fecha_hora')
    
    # Construir resumen de asistencias
    grupos = (
        registros.values('fecha_hora__date')
        .annotate(
            primera_entrada=Min('fecha_hora'),
            ultima_marca=Max('fecha_hora')
        )
        .order_by('-fecha_hora__date')
    )
    
    resumen = []
    for g in grupos:
        entrada = registros.filter(
            fecha_hora__date=g['fecha_hora__date'],
            tipo='ENTRADA'
        ).order_by('fecha_hora').first()
        
        salida = registros.filter(
            fecha_hora__date=g['fecha_hora__date'],
            tipo='SALIDA'
        ).order_by('-fecha_hora').first()
        
        # Determinar si fue falta (sin entrada)
        es_falta = entrada is None
        dia_semana = g['fecha_hora__date'].strftime('%A')
        
        resumen.append({
            'fecha': g['fecha_hora__date'],
            'dia_semana': dia_semana,
            'hora_entrada': entrada.fecha_hora if entrada else None,
            'hora_salida': salida.fecha_hora if salida else None,
            'es_falta': es_falta,
            'es_dia_descanso': _es_dia_descanso(empleado, g['fecha_hora__date']),
        })
    
    ultimos = registros[:10]
    
    return render(
        request,
        'asistencia/mi_asistencia.html',
        {
            'empleado': empleado,
            'resumen': resumen,
            'ultimos': ultimos,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    )


def _es_dia_descanso(empleado, fecha):
    """Verifica si la fecha cae en el día de descanso del empleado."""
    dias_map = {
        'LUNES': 0,
        'MARTES': 1,
        'MIERCOLES': 2,
        'JUEVES': 3,
        'VIERNES': 4,
        'SABADO': 5,
        'DOMINGO': 6,
    }
    return fecha.weekday() == dias_map.get(empleado.dia_descanso, 6)
