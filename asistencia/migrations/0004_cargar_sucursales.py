from django.db import migrations


def cargar_sucursales(apps, schema_editor):
    Sucursal = apps.get_model('asistencia', 'Sucursal')

    sucursales = [
        'MONARCA',
        'OTAY',
        'ROSARITO',
        'TECATE',
        'SOLER',
        'RUBI',
        'LIBERTAD',
        'ZONA RIO',
        'JARDIN DORADO',
        'FLORIDO 2DA SECC',
        'REFUGIO',
        'OJO DE AGUA',
    ]

    for nombre in sucursales:
        Sucursal.objects.get_or_create(
            nombre=nombre,
            defaults={
                'direccion': '',
                'activa': True,
            },
        )


def revertir_carga_sucursales(apps, schema_editor):
    Sucursal = apps.get_model('asistencia', 'Sucursal')
    nombres = [
        'MONARCA',
        'OTAY',
        'ROSARITO',
        'TECATE',
        'SOLER',
        'RUBI',
        'LIBERTAD',
        'ZONA RIO',
        'JARDIN DORADO',
        'FLORIDO 2DA SECC',
        'REFUGIO',
        'OJO DE AGUA',
    ]
    Sucursal.objects.filter(nombre__in=nombres).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('asistencia', '0003_sucursal_perfilusuario_empleado_sucursal'),
    ]

    operations = [
        migrations.RunPython(cargar_sucursales, revertir_carga_sucursales),
    ]
