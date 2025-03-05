from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User 
from django.core.exceptions import ObjectDoesNotExist

# Create your models here.
class Usuarios(models.Model):
    IdUsuarios = models.AutoField(primary_key=True)
    nombre=models.CharField(max_length=50)
    apellido=models.CharField(max_length=50)
    dni = models.CharField(max_length=9)
    TIPOS_EMPLEADO = [
        ('Asesor', 'Asesor'),
        ('Supervisor', 'Supervisor'),
        ('Jefe', 'Jefe'),
        ('Analista', 'Analista'),
        ('Recursos', 'Recursos'),
    ]
    tipo_empleado = models.CharField(max_length=15, choices=TIPOS_EMPLEADO)

    def __str__(self):
        return f"{self.nombre} - {self.apellido} - {self.dni}"
    
class Campana(models.Model):
    IdCampana = models.AutoField(primary_key=True)
    campana = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.campana}"

class Horarios(models.Model):
    IdHorario = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=100)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return self.codigo

class Analista(models.Model):
    IdAnalista = models.AutoField(primary_key=True)
    nombre_apellido = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre_apellido}"
    
    @classmethod
    def get_recursos_by_user(cls, user):
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None

class Recursos(models.Model):
    IdRecursos = models.AutoField(primary_key=True)
    nombre_apellido = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre_apellido}"
    
    @classmethod
    def get_recursos_by_user(cls, user):
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None

class Jefe(models.Model):
    IdJefe = models.AutoField(primary_key=True)
    nombre_apellido = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre_apellido}"
    
    @classmethod
    def get_jefe_by_user(cls, user):
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None
    
class Supervisor(models.Model):
    IdSupervisor = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)
    nombre_apellido = models.CharField(max_length=100)
    campana = models.ManyToManyField(Campana)
    fecha_ingreso = models.DateField(null=True, blank=True)
    fecha_cese = models.DateField(null=True, blank=True)
    ESTADO_CHOICES = (
        ('Activo', 'Activo'),
        ('Cesado', 'Cesado'),
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    jefe_asociado = models.ForeignKey(Jefe, on_delete=models.SET_NULL, null=True, blank=True)
    dispositivos = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre_apellido

    @classmethod
    def get_supervisor_by_user(cls, user):
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None

class Analista(models.Model):
    IdAnalista = models.AutoField(primary_key=True)
    nombre_apellido = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre_apellido}"
    
    @classmethod
    def get_analista_by_user(cls, user):
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None

class Asesor(models.Model):
    IdAsesor = models.AutoField(primary_key=True)
    nombre_apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=9, validators=[
        RegexValidator(r'^\d{8,9}$', 'El DNI debe tener 8 o 9 dígitos.')
    ])
    campana = models.ForeignKey(Campana, on_delete=models.CASCADE)
    JORNADA_CHOICES = (
        ('Full Time', 'Full Time'),
        ('Semi Full', 'Semi Full'),
        ('Part Time', 'Part Time'),
    )
    tipo_jornada = models.CharField(max_length=20, choices=JORNADA_CHOICES)
    MODALIDAD_CHOICES = (
        ('Remoto', 'Remoto'),
        ('Presencial', 'Presencial'),
        ('Hibrido', 'Hibrido'),
    )
    horario = models.ForeignKey(Horarios, on_delete=models.SET_NULL, null=True, blank=True)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    provincia = models.CharField(max_length=50)
    departamento = models.CharField(max_length=25)
    distrito = models.CharField(max_length=50)
    direccion = models.CharField(max_length=50)
    telefono = models.IntegerField(null=True, blank=True)
    ruc = models.CharField(max_length=20, null=True, blank=True)
    usuario_sol = models.CharField(max_length=20, null=True, blank=True)
    clave_sol = models.CharField(max_length=20, null=True, blank=True)
    cuenta = models.CharField(max_length=20, null=True, blank=True)
    cuenta_int = models.CharField(max_length=20, null=True, blank=True)
    banco = models.CharField(max_length=20, null=True, blank=True)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE, null=True, related_name='asesores')
    CONTRATO_CHOICES  = (
        ('RxH', 'RxH'),
        ('Planilla', 'Planilla'),    
    )
    tipo_contrato = models.CharField(max_length=30, choices=CONTRATO_CHOICES)
    fecha_nacimiento = models.DateField()
    estado_civil = models.CharField(max_length=50, null=True, blank=True)
    correo = models.CharField(max_length=100, null=True, blank=True)
    fecha_ingreso = models.DateField()
    fecha_cese = models.DateField(null=True, blank=True)

    ESTADO_CHOICES = (
        ('Activo', 'Activo'),
        ('Cesado', 'Cesado'),
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    usuario_vicidial = models.CharField(max_length=100)
    password_vicidial = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    @classmethod
    def get_asesor_by_user(cls, user):
        try:
            return cls.objects.get(user=user)
        except ObjectDoesNotExist:
            return None   

class Cliente(models.Model):
    IdCliente = models.AutoField(primary_key=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    dni_cliente = models.CharField(
    max_length=11,
    validators=[
        RegexValidator(r'^\d{8}(\d{3})?$', 'El DNI debe tener 8 o 11 dígitos.')
        ])
    nombre = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)  # Nuevo campo para el celular
    tipificacion = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    disprodep = models.CharField(max_length=100, blank=True, null=True)
    IdAsesor = models.ForeignKey('Asesor', on_delete=models.CASCADE)
    campana = models.ForeignKey(Campana, on_delete=models.CASCADE, null=True)
    plan_sugerido = models.CharField(max_length=100, blank=True, null=True)
    oferta_sugerida = models.CharField(max_length=100, blank=True, null=True)
    velocidad_real = models.CharField(max_length=50, blank=True, null=True)
    precio = models.CharField(max_length=25, blank=True, null=True)

class Venta(models.Model):
    IdVenta = models.AutoField(primary_key=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)  # Fecha automática de creación
    cliente = models.CharField(max_length=200)
    tipo = models.CharField(max_length=200)
    dni_cliente = models.CharField(max_length=15) 
    telefono = models.CharField(max_length=20)
    distrito = models.CharField(max_length=100)
    IdAsesor = models.ForeignKey('Asesor', on_delete=models.CASCADE)

    def __str__(self):
        return f"Venta {self.IdVenta} - {self.dni_cliente}"

class Asistencia(models.Model):
    OPCIONES_ASISTENCIA = (
        ('A', 'Asistencia'),
        ('T', 'Tardanza'),
        ('D', 'Descanso'),
        ('XM', 'Descanso Médico'),
        ('FJ', 'Falta Justificada'),
        ('FI', 'Falta Injustificada'),
        ('V', 'Vacaciones'),
        ('L', 'Licencia'),
    )
    asesor = models.ForeignKey(Asesor, on_delete=models.CASCADE)
    fecha = models.DateField()
    tipo = models.CharField(max_length=2, choices=OPCIONES_ASISTENCIA)

    def __str__(self):
        return f"Asistencia de {self.asesor.nombre_apellido} el {self.fecha} ({self.get_tipo_display()})"


class CambioHorario(models.Model):
    IdCambioHorario = models.AutoField(primary_key=True)
    asesor = models.ForeignKey(Asesor, on_delete=models.CASCADE)  # Vincula el modelo CambioHorario con el modelo Asesor
    horario_anterior = models.ForeignKey(Horarios, related_name='cambios_horario_anterior', on_delete=models.SET_NULL, null=True, blank=True)
    horario_nuevo = models.ForeignKey(Horarios, related_name='cambios_horario_nuevo', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cambio de horario (ID: {self.IdCambioHorario}) para {self.asesor.nombre_apellido} el {self.fecha_cambio}"

class Turno(models.Model):
    asesor = models.ForeignKey('Asesor', on_delete=models.CASCADE)
    dia_semana = models.CharField(max_length=10, choices=[('Lunes', 'Lunes'), ('Martes', 'Martes'), ('Miercoles', 'Miercoles'), ('Jueves', 'Jueves'), ('Viernes', 'Viernes'), ('Sabado', 'Sabado'), ('Domingo', 'Domingo')])
    horario = models.ForeignKey(Horarios, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_inicio_semana = models.DateField()  # Campo para almacenar la fecha de inicio de la semana

    def __str__(self):
        return f"{self.asesor} - {self.dia_semana} - {self.horario}"
