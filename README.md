## Base de datos

1. Crear la base de datos en MySQL:
```sql
   CREATE DATABASE citaya_db;
```

2. Configurar `.env` con tus credenciales de MySQL

3. Aplicar migraciones:
```bash
   python manage.py migrate
```

4. Ejecutar `citaya_inserciones.sql` en phpMyAdmin o MySQL Workbench

5. Encriptar contraseñas:
```bash
   python manage.py shell
```
```python
   from django.contrib.auth.hashers import make_password
   from citas.models import Administrador, Medico, Paciente

   for modelo in [Administrador, Medico, Paciente]:
       for obj in modelo.objects.all():
           obj.contrasena = make_password(obj.contrasena)
           obj.save(update_fields=['contrasena'])
   print("Listo!")
```

**Credenciales de prueba:** contraseña `Admincitaya0*` para todos los usuarios.