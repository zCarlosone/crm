from django.contrib import admin
from .models import Usuarios, Jefe, Supervisor, Asesor, Campana, Recursos, Analista
from django.contrib.auth.models import User

@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'dni', 'tipo_empleado')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Verifica si ya existe un usuario con ese DNI
        user, created = User.objects.get_or_create(username=obj.dni)
        
        # Si es un usuario nuevo, asigna la contraseña
        if created:
            user.set_password(obj.dni)  # La contraseña será el DNI
        else:
            user.username = obj.dni  # Asegura que el username sea el DNI
            user.set_password(obj.dni)  # Actualiza la contraseña al DNI

        user.is_staff = False
        user.is_superuser = False
        user.save()


@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('campana',)


@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ('nombre_apellido', 'dni')
    filter_horizontal = ('campana',)  # Corregido
    list_filter = ('estado', )
    search_fields = ('nombre_apellido', 'dni')


@admin.register(Asesor)
class AsesorAdmin(admin.ModelAdmin):
    list_display = ('IdAsesor', 'nombre_apellido', 'dni', 'campana', 'tipo_jornada', 
                    'modalidad', 'departamento', 'direccion', 'telefono', 'supervisor', 
                    'fecha_ingreso', 'tipo_contrato', 'estado')  # 'metodo' eliminado
    list_filter = ('campana', 'estado')  # 'tipo' eliminado
    search_fields = ('nombre_apellido', 'dni')
    ordering = ('-fecha_ingreso',)

@admin.register(Jefe)
class JefeAdmin(admin.ModelAdmin):
    list_display = ('IdJefe', 'nombre_apellido', 'dni', 'telefono')

@admin.register(Recursos)
class RecursosAdmin(admin.ModelAdmin):
    list_display = ('IdRecursos', 'nombre_apellido', 'dni', 'telefono')

@admin.register(Analista)
class AnalistaAdmin(admin.ModelAdmin):
    list_display = ('IdAnalista', 'nombre_apellido', 'dni', 'telefono')
