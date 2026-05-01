# TODO - Diagnóstico error 500 en `/login/`

- [x] Revisar archivos clave (`settings.py`, `urls.py`, `views.py`, `models.py`).
- [x] Intentar correr validación local (`python manage.py check`) para capturar error.
- [ ] Configurar/activar entorno virtual local para poder ejecutar Django.
- [x] Revisar logs de Render para obtener traceback exacto del 500 en producción.
- [x] Cambiar deploy command en `Procfile` a ASGI (`daphne`) para compatibilidad con Channels.
- [x] Agregar logging en `settings.py` para ver traceback real en Render.
- [x] Endurecer login (`CustomLoginView`) para evitar fallo por usuarios sin perfil.
- [ ] Verificar que `/login/` responda sin 500.
