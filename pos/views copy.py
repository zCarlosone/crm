from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Jefe, Asesor, Supervisor, Cliente, Campana, Asistencia, Recursos, Analista, Venta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import requests
from django.views.decorators.csrf import csrf_exempt
import json
import os
import pandas as pd
from django.conf import settings
from django.utils.timezone import now
from django.http import JsonResponse, HttpResponse
from .forms import RegistroUsuarioForm
import csv
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Cambia 'dashboard' a la URL a la que deseas redirigir después del inicio de sesión exitoso
        else:
            messages.error(request, 'Credenciales incorrectas. Por favor, inténtalo de nuevo.')
            return redirect('login')  # Redirigir de vuelta a la página de inicio de sesión con el mensaje de error en la sesión
    return render(request, 'login.html')  # Crea un template llamado 'login.html' para el formulario de inicio de sesión

def listas(request):
    context = {"tabla": None, "error": None}
    
    if request.method == "POST" and request.FILES.get("archivo_csv"):
        archivo = request.FILES["archivo_csv"]
        fs = FileSystemStorage()
        filename = fs.save(archivo.name, archivo)
        file_path = fs.path(filename)
        
        try:
            df = pd.read_csv(file_path, dtype=str, encoding="latin-1", on_bad_lines="skip")
            columnas_importantes = [
                "call_date", "phone_number", "status", "user", "full_name", "list_id", 
                "phone_number_dialed", "first_name", "address2", "list_name", 
                "list_descripcion", "status_name", "length_in_sec", "list_description"
            ]
            df = df[[col for col in columnas_importantes if col in df.columns]]
            
            if "length_in_sec" in df.columns:
                df["length_in_sec"] = pd.to_numeric(df["length_in_sec"], errors='coerce')
            
            if "list_description" in df.columns:
                conteo_listas = df["list_description"].value_counts().reset_index()
                conteo_listas.columns = ["list_description", "total_registros"]
                conteo_listas["int"] = (1 / conteo_listas["total_registros"]).round(2)
                
                if "status_name" in df.columns:
                    ventas_por_lista = df[df["status_name"] == "VENTA CON TITULAR"]["list_description"].value_counts().reset_index()
                    ventas_por_lista.columns = ["list_description", "venta"]
                    conteo_listas = conteo_listas.merge(ventas_por_lista, on="list_description", how="left").fillna(0)
                
                status_permitidos = [
                    "NO PERMITE EXPLICACION - COLGO", "AGENDADO ", "NO DESEA POR PRECIO ALTO",
                    "NO DESEA SERVICIO", "VENTA CON TITULAR", "VOLVER A LLAMAR", "YA ESCUCHO OFERTA WIN"
                ]
                df_cet_u = df[df["status_name"].isin(status_permitidos)]
                cet_u_por_lista = df_cet_u["list_description"].value_counts().reset_index()
                cet_u_por_lista.columns = ["list_description", "cet_u"]
                conteo_listas = conteo_listas.merge(cet_u_por_lista, on="list_description", how="left").fillna(0)
                
                nc_status = [
                    "LLAMADA EN VACIO", "LLAMADA MUDA", "NO CONTESTA", "NUMERO INCORRECTO",
                    "FUERA DE SERVICIO", "SIN COBERTURA", "CONTRATO VIGENTE CON SU OPER.",
                    "LISTA NEGRA DE ON", "CLIENTE DE BAJA"
                ]
                df_nc = df[df["status_name"].isin(nc_status)]
                nc_por_lista = df_nc["list_description"].value_counts().reset_index()
                nc_por_lista.columns = ["list_description", "NC"]
                conteo_listas = conteo_listas.merge(nc_por_lista, on="list_description", how="left").fillna(0)
                
                conteo_listas["CET + NC"] = conteo_listas["cet_u"] + conteo_listas["NC"]
                
                df_excluidos = df[~df["status_name"].isin(status_permitidos + nc_status)]
                otros_status = df_excluidos["list_description"].value_counts().reset_index()
                otros_status.columns = ["list_description", "BOT"]
                conteo_listas = conteo_listas.merge(otros_status, on="list_description", how="left").fillna(0)
                
                columnas_redondear = ["total_registros", "CET + NC", "cet_u", "NC", "BOT"]
                conteo_listas[columnas_redondear] = conteo_listas[columnas_redondear].astype(int)
                conteo_listas["int"] = conteo_listas["int"].round(2)
                
                conteo_listas = conteo_listas[conteo_listas["total_registros"] > 100]
                
                context["tabla"] = conteo_listas.to_html(classes=["table", "table-striped", "table-bordered"])
            
        except Exception as e:
            context["error"] = f"Error al procesar el archivo: {e}"
    
    return render(request, "procesar_csv.html", context)

def obtener_datos_api(request):
    url = "https://oll-solutions.asternicperu.com/vicidial/non_agent_api.php?function=version"
    
    try:
        response = requests.get(url, verify=False)

        if response.status_code == 200:
            # La respuesta es un string separado por "|"
            datos = response.text.strip().split("|")

            # Convertir los datos en un diccionario clave-valor
            resultado = {}
            for dato in datos:
                if ":" in dato:  # Asegurar que hay un formato clave:valor
                    clave, valor = dato.split(":", 1)
                    resultado[clave.strip()] = valor.strip()
            
            return JsonResponse(resultado)

        else:
            return JsonResponse({"error": "No se pudo obtener la data"}, status=500)

    except requests.exceptions.SSLError as e:
        return JsonResponse({"error": f"Error SSL: {str(e)}"}, status=500)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Error en la solicitud: {str(e)}"}, status=500)



@csrf_exempt
@login_required
def guardar_llamada(request):
    if request.method == "POST":
        usuario = request.user
        asesor = Asesor.get_asesor_by_user(usuario)

        if not asesor:
            return JsonResponse({"error": "Usuario no autorizado"}, status=403)
        
        # Ahora registramos el cliente
        cliente = registrar_cliente(request.POST, asesor)

        numero_cliente   = request.POST.get("numero_cliente")
        nombre_cliente   = request.POST.get("nombre_cliente")
        tiempo           = request.POST.get("tiempo")
        nombre           = request.POST.get("nombre")       # address1
        disprodep        = request.POST.get("disprodep")    # address2
        oferta_sugerida  = request.POST.get("oferta_sugerida")# address3

        print(f"Llamada guardada - Asesor: {asesor.nombre_apellido}, Cliente: {nombre_cliente}, Número: {numero_cliente}, Nombre: {nombre}, Disprodep: {disprodep}, Oferta Sugerida: {oferta_sugerida}")
        print(f"Llamada guardada - Asesor: {asesor.nombre_apellido}, Cliente: {nombre_cliente}, Número: {numero_cliente}, Nombre: {nombre}, Disprodep: {disprodep}, Oferta Sugerida: {oferta_sugerida}")

        return JsonResponse({"message": "Llamada guardada correctamente"}, status=200)

    return JsonResponse({"error": "Método no permitido"}, status=405)

import requests
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Asesor

@login_required
def obtener_llamada_vicidial(request):
    usuario = request.user  # Usuario autenticado
    asesor = Asesor.get_asesor_by_user(usuario)  # Obtener asesor autenticado

    if not asesor:
        return render(request, 'formulario_llamada.html', {"error": "Usuario no es un asesor."})

    # Obtener credenciales de Vicidial desde el modelo Asesor
    user_vicidial = asesor.usuario_vicidial
    pass_vicidial = asesor.password_vicidial

    url = f"https://oll-solutions.asternicperu.com/vicidial/non_agent_api.php?source=test&user={user_vicidial}&pass={pass_vicidial}&function=agent_status&agent_user={user_vicidial}"

    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            datos = response.text.strip().split("|")
            if len(datos) >= 11:  # Asegurar que hay suficientes datos en la respuesta
                llamada = {
                    "estado": datos[0],  # INCALL
                    "id_llamada": datos[1],
                    "id_cliente": datos[2],
                    "campaña": datos[3],
                    "tiempo": datos[4],
                    "nombre_cliente": datos[5],
                    "agente": datos[6],
                    "numero_cliente": datos[10]
                }
                return render(request, 'formulario_llamada.html', {"llamada": llamada, "asesor": asesor})
            else:
                return render(request, 'formulario_llamada.html', {"error": "Respuesta incompleta de la API."})
        else:
            return render(request, 'formulario_llamada.html', {"error": "No se pudo obtener la llamada."})
    except Exception as e:
        return render(request, 'formulario_llamada.html', {"error": str(e)})

@login_required
def formulario_llamada(request):
    numero_cliente = request.GET.get("numero_cliente", "")
    nombre_cliente = request.GET.get("nombre_cliente", "")
    address1 = request.GET.get("address1", "")
    address2 = request.GET.get("address2", "")
    address3 = request.GET.get("address3", "")
    province = request.GET.get("province", "")  # <-- Nuevo campo para Campaña
    address3 = request.GET.get("address3", "")
    province = request.GET.get("province", "")  # <-- Nuevo campo para Campaña

    print(f"Numero Cliente: {numero_cliente}")
    print(f"Nombre Cliente: {nombre_cliente}")
    print(f"Address1 (Nombre): {address1}")
    print(f"Address2 (Disprodep): {address2}")
    print(f"Address3 (Oferta Sugerida): {address3}")
    print(f"province (Campana): {province}")  # <-- Verifica que se recibe
    print(f"Address3 (Oferta Sugerida): {address3}")
    print(f"province (Campana): {province}")  # <-- Verifica que se recibe

    
    return render(request, "formulario_llamada.html", {
        "numero_cliente": numero_cliente,
        "nombre_cliente": nombre_cliente,
        "nombre": address1,
        "disprodep": address2,
        "oferta_sugerida": address3,
        "campana": province  # <-- Pasamos el título como Campaña
    })

def obtener_fechas_mes_actual():
    fecha_actual = timezone.now().date()
    primer_dia_mes_actual = fecha_actual.replace(day=1)
    ultimo_dia_mes_actual = primer_dia_mes_actual.replace(
        day=1,
        month=(primer_dia_mes_actual.month % 12) + 1,
        year=primer_dia_mes_actual.year + (1 if primer_dia_mes_actual.month == 12 else 0)
    ) - timezone.timedelta(seconds=1)

    return fecha_actual, primer_dia_mes_actual, ultimo_dia_mes_actual


def registrar_cliente(data, asesor):
    """
    Registra un nuevo Cliente usando los datos proporcionados y la instancia del asesor.
    
    :param data: Diccionario con los datos del formulario.
    :param asesor: Instancia del modelo Asesor.
    :return: Instancia creada de Cliente.
    """
    campana_input = data.get("campana")
    campana_mapeo = {
        "C0004": "horizontal",
        "C0016": "cross",
        "C0012": "gamer",
        "C0002": "asistencias",
    }

    campana_nombre = campana_mapeo.get(campana_input)

    if campana_nombre:
        try:
            campana = Campana.objects.get(campana__iexact=campana_nombre)
        except Campana.DoesNotExist:
            campana = None
    elif campana_input:  # Si se envió algún valor no mapeado, intenta buscar por ID
        try:
            campana = Campana.objects.get(IdCampana=int(campana_input))
        except (Campana.DoesNotExist, ValueError, TypeError):
            campana = None
    else:
        campana = None

    cliente = Cliente.objects.create(
        dni_cliente     = data.get("nombre_cliente"),  # Campo DNI
        nombre          = data.get("nombre"),
        telefono        = data.get("numero_cliente"),    # Asignamos el teléfono
        tipificacion    = data.get("tipificacion"),
        descripcion     = data.get("descripcion"),
        disprodep       = data.get("disprodep"),
        IdAsesor        = asesor,
        campana         = campana,
        oferta_sugerida = data.get("oferta_sugerida"),
        velocidad_real  = data.get("velocidad_real"),
        precio          = data.get("precio")
    )
    return cliente

def registrar_asistencia(request, asesores_en_campana):
    if request.method == "POST":
        # Obtener la fecha actual para registrar la asistencia
        fecha_actual = timezone.now().date()

        registros_guardados = 0
        errores = []

        # Recorrer cada asesor y registrar su asistencia
        for asesor in asesores_en_campana:
            asistencia_value = request.POST.get(f'asistencia_{asesor.IdAsesor}')

            if asistencia_value:  # Solo registrar si hay un valor válido
                try:
                    # Evitar duplicados: Verificar si ya existe un registro para este asesor y fecha
                    if not Asistencia.objects.filter(asesor=asesor, fecha=fecha_actual).exists():
                        # Crear una nueva instancia de Asistencia
                        Asistencia.objects.create(
                            asesor=asesor,
                            fecha=fecha_actual,
                            tipo=asistencia_value
                        )
                        registros_guardados += 1
                except Exception as e:
                    errores.append(f"Error al guardar asistencia para {asesor.nombre_apellido}: {e}")

        # Agregar mensajes de éxito y error
        if registros_guardados > 0:
            messages.success(request, f"Asistencias registradas correctamente: {registros_guardados}.")
        if errores:
            messages.error(request, f"Errores encontrados: {'; '.join(errores)}.")

        return redirect('dashboard')

    messages.error(request, "Método no permitido.")
    return redirect('dashboard')

def registrar_estado(request):
    asesor_id = request.POST.get('asesor_id')
    nuevo_estado = request.POST.get('nuevo_estado')
    nueva_fecha_cese = request.POST.get('fecha_cese')

    if asesor_id and nuevo_estado in ['Activo', 'Cesado']:
        asesor = Asesor.objects.get(pk=asesor_id)
        asesor.estado = nuevo_estado
        asesor.fecha_cese = nueva_fecha_cese
        asesor.save()
        messages.success(request, f'Estado de asesor {asesor.nombre_apellido} actualizado con éxito.')

    return redirect('dashboard')

def search_excel(request):
    if request.method == "GET":
        nro_doc = request.GET.get("nro_doc", "").strip()
        if not nro_doc:
            return JsonResponse({"error": "Falta el parámetro nro_doc"}, status=400)

        file_path = os.path.join(settings.BASE_DIR, 'pos', 'base', 'L3_WIN-HOR_CET2INT_G3_G4_T2_ALLB_ENE.xlsx')
        
        try:
            # Si conoces el nombre o índice de la hoja, especifícalo aquí.
            # Por ejemplo, si los datos están en la primera hoja:
            df = pd.read_excel(file_path, sheet_name=0)
            # O, si sabes el nombre, por ejemplo:
            # df = pd.read_excel(file_path, sheet_name="Datos")
            print("Total filas leídas:", df.shape[0])
        except Exception as e:
            return JsonResponse({"error": f"Error al leer el archivo: {str(e)}"}, status=500)
        
        # Limpieza de los nombres de columna
        df.columns = df.columns.str.strip()
        
        # Filtrado por la columna NRO_DOC, asegurando convertir a string y eliminar espacios
        df_filtrado = df[df['NRO_DOC'].astype(str).str.strip() == nro_doc]
        resultados = df_filtrado.to_dict(orient='records')
        
        return JsonResponse({"results": resultados}, safe=False)
    
    return HttpResponse(status=405)


@login_required
def dashboard(request):
    fecha_actual, primer_dia_mes_actual, ultimo_dia_mes_actual = obtener_fechas_mes_actual()

    asesor_autenticado = Asesor.get_asesor_by_user(request.user)
    supervisor_autenticado = Supervisor.get_supervisor_by_user(request.user)
    jefe_autenticado = Jefe.get_jefe_by_user(request.user)
    analista_autenticado = Analista.get_analista_by_user(request.user)
    recursos_autenticado = Recursos.get_recursos_by_user(request.user)

    if asesor_autenticado:
        if request.method == "POST":
            dni_cliente = request.POST.get("doc_cliente")
            cliente = request.POST.get("cliente")
            telefono = request.POST.get("telf_cliente")
            distrito = request.POST.get("distrito")

            # Validamos que el asesor esté en la base de datos
            if not Asesor.objects.filter(IdAsesor=asesor_autenticado.IdAsesor).exists():
                return render(request, "dashboard.html", {"error": "Asesor no válido"})

            # Buscar si el cliente ya está registrado sin importar el asesor
            venta_existente = Venta.objects.filter(dni_cliente=dni_cliente).first()

            if venta_existente:
                # Si ya existe con otro asesor, actualiza los datos y reasigna al nuevo asesor
                venta_existente.telefono = telefono
                venta_existente.cliente = cliente
                venta_existente.distrito = distrito
                venta_existente.IdAsesor = asesor_autenticado  # Se asigna el nuevo asesor
                venta_existente.save()
            else:
                # Si no existe, crea un nuevo registro
                Venta.objects.create(
                    dni_cliente=dni_cliente,
                    cliente=cliente,
                    telefono=telefono,
                    distrito=distrito,
                    IdAsesor=asesor_autenticado
                )

            return redirect("dashboard")  # Redirige para actualizar la página

        return render(request, 'dashboard.html')
    elif supervisor_autenticado:
        campana_del_supervisor = supervisor_autenticado.campana.all()
        asesores_en_gestion = Asesor.objects.filter(campana__in=campana_del_supervisor, estado='Activo')

        # Obtener los clientes registrados por los asesores activos de este supervisor
        clientes = Cliente.objects.filter(IdAsesor__in=asesores_en_gestion)

        if request.method == "POST":
            action = request.POST.get('action')
            if action == 'registrar_asistencia':
                return registrar_asistencia(request, asesores_en_gestion)
            elif action == 'registrar_estado':
                return registrar_estado(request, asesores_en_gestion)  # Asegúrate de pasar `asesores_en_gestion`
            elif action == 'registrar_usuario_interno':
                return registrar_usuario_interno(request)

        horas = [f"{hora}:00" for hora in range(8, 23)]
        clientes_por_hora = {hora: 0 for hora in horas}
        fecha_actual = timezone.now().date()
        tipificaciones_data = {}
        for cliente in clientes:
            if cliente.tipificacion in tipificaciones_data:
                tipificaciones_data[cliente.tipificacion] += 1
            else:
                tipificaciones_data[cliente.tipificacion] = 1
                # Filtrar solo los clientes registrados hoy
        clientes_hoy = clientes.filter(fecha_hora__date=fecha_actual)
        
        # Obtener la distribución de tipificaciones SOLO para hoy
        tipificaciones_hoy = {}
        for cliente in clientes_hoy:
            if cliente.tipificacion in tipificaciones_hoy:
                tipificaciones_hoy[cliente.tipificacion] += 1
            else:
                tipificaciones_hoy[cliente.tipificacion] = 1

        # Cantidad de clientes registrados hoy
        clientes_por_dia_hoy = {fecha_actual.strftime('%Y-%m-%d'): clientes_hoy.count()}

        # Rendimiento de asesores solo con los clientes registrados hoy
        rendimiento_asesores_hoy = {}
        for cliente in clientes_hoy:
            asesor_nombre_apellido = cliente.IdAsesor.nombre_apellido if cliente.IdAsesor else "Sin asignar"
            if asesor_nombre_apellido in rendimiento_asesores_hoy:
                rendimiento_asesores_hoy[asesor_nombre_apellido] += 1
            else:
                rendimiento_asesores_hoy[asesor_nombre_apellido] = 1

        clientes_por_dia = {}
        for cliente in clientes:
            fecha_str = cliente.fecha_hora.date().strftime('%Y-%m-%d')
            if fecha_str in clientes_por_dia:
                clientes_por_dia[fecha_str] += 1
            else:
                clientes_por_dia[fecha_str] = 1
        rendimiento_asesores = {}
        for cliente in clientes:
            asesor_nombre_apellido = cliente.IdAsesor.nombre_apellido if cliente.IdAsesor else "Sin asignar"
            if asesor_nombre_apellido in rendimiento_asesores:
                rendimiento_asesores[asesor_nombre_apellido] += 1
            else:
                rendimiento_asesores[asesor_nombre_apellido] = 1
                # Ordenar por fecha
        clientes_por_dia = dict(sorted(clientes_por_dia.items()))
        # Obtener el nombre del día de la semana actual en español para Lima, Perú
        es_domingo = fecha_actual.weekday() == 4
        today = timezone.now().date()  # Fecha actual 2023-10-27
        days_until_sunday = (today.weekday() - 4) % 7  # Ajustamos para encontrar el último domingo
        last_sunday = today - timezone.timedelta(days=days_until_sunday)  # Restar días para obtener el último domingo

        context = {
            'campana_del_supervisor': campana_del_supervisor,
            'asesores_en_gestion': asesores_en_gestion,
            'clientes': clientes,  # Aquí pasas los clientes al contexto
            'tipificaciones_data': tipificaciones_data,
            'clientes_por_dia': clientes_por_dia,
            'rendimiento_asesores' : rendimiento_asesores,
            'clientes_hoy': clientes_hoy,  
            'tipificaciones_hoy': tipificaciones_hoy,
            'clientes_por_dia_hoy': clientes_por_dia_hoy,
            'rendimiento_asesores_hoy': rendimiento_asesores_hoy,
        }

        return render(request, 'dashboard_sup.html', context)

    elif jefe_autenticado:
        return render(request, 'dashboard_jefe.html')
    elif recursos_autenticado:
        return render(request, 'dashboard_rh.html')
    elif analista_autenticado:
        return render(request, 'dashboard_analista.html')

def registrar_usuario_interno(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nombre = data.get("nombre")
            apellido = data.get("apellido")
            dni = data.get("dni")
            tipo_empleado = data.get("tipo_empleado")

            if not all([nombre, apellido, dni, tipo_empleado]):
                return JsonResponse({"error": "Faltan datos"}, status=400)

            return JsonResponse({"mensaje": "Usuario registrado correctamente"}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
def procesar_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        archivo = request.FILES['csv_file']
        datos = []
        try:
            decoded_file = archivo.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            for row in reader:
                datos.append({
                    'lista': row.get('Lista', ''),
                    'nc': int(row.get('NC', 0)),
                    'cet': int(row.get('CET', 0)),
                    'recorrido': int(row.get('Recorrido', 0)),
                    'ventas': int(row.get('Ventas', 0))
                })
            return JsonResponse(datos, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def pantalla(request):
    return render(request, 'pantalla.html')

from collections import Counter

def obtener_clientes_actualizados(request):
    try:
        # Cargar datos de la BD
        ventas = Venta.objects.all().values(
            "dni_cliente", "cliente", "telefono", "distrito", 
            "IdAsesor__nombre_apellido", "fecha_hora"
        )

        # Leer archivo Excel
        ruta_excel = os.path.join("base", "VENTAS ATQ 1ERA HORA.xlsx")
        df_excel = pd.read_excel(ruta_excel, dtype={"N° doc cliente": str})  # Convertir DNI a str

        # Convertir datos de BD a lista
        ventas_list = list(ventas)
        for venta in ventas_list:
            venta["fecha_hora"] = venta["fecha_hora"].strftime("%Y-%m-%d")  # Solo fecha
            
            # Buscar en el Excel el Estado del Pedido
            estado_pedido = df_excel.loc[df_excel["N° doc cliente"] == venta["dni_cliente"], "Estado del Pedido"]
            venta["estado_pedido"] = estado_pedido.values[0] if not estado_pedido.empty else "NO DISPONIBLE"

        print("Ventas obtenidas:", ventas_list)  # Debug
        return JsonResponse(ventas_list, safe=False)

    except Exception as e:
        print("Error:", str(e))
        return JsonResponse({"error": str(e)}, status=500)

def logout_view(request):

    logout(request)

    return redirect('login')  # Cambia 'login' a la URL a la que deseas redirigir después del cierre de sesión