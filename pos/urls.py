from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.login_view, name='root'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/datos/', views.obtener_datos_api, name='obtener_datos_api'),
    path('api/guardar_llamada/', views.guardar_llamada, name='guardar_llamada'),
    path('api/llamada/', views.obtener_llamada_vicidial, name='obtener_llamada_vicidial'),  # Agregada
    path('formulario_llamada/', views.formulario_llamada, name='formulario_llamada'),
    path('registrar_estado/', views.registrar_estado, name='registrar_estado'),
    path('search_excel/', views.search_excel, name='search_excel'),
    path('registrar-usuario/', views.registrar_usuario_interno, name='registrar_usuario_interno'),
    path('procesar_csv/', views.procesar_csv, name='procesar_csv'),
    path('clientes_actualizados/', views.obtener_clientes_actualizados, name='obtener_clientes_actualizados'),
    path('pantalla/', views.pantalla, name='pantalla'),
]