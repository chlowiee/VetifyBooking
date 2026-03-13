from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('login/', views.admin_login_view, name='admin_login'),
    # Dashboard principal
    path('', views.dashboard_view, name='dashboard'),
    
    # Gestión de citas
    path('appointments/', views.appointments_view, name='appointments'),
    path('appointments/delete/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
    
    # Gestión de usuarios
    path('users/', views.users_view, name='users'),
    path('users/toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    
    # Gestión de mascotas
    path('pets/', views.pets_view, name='pets'),
    path('pets/delete/<int:pet_id>/', views.delete_pet, name='delete_pet'),
    
    # Gestión de veterinarios
    path('veterinarians/', views.veterinarians_view, name='veterinarians'),
    path('veterinarians/toggle/<int:vet_id>/', views.toggle_vet_status, name='toggle_vet_status'),
    path('veterinarians/add/', views.add_veterinarian, name='add_veterinarian'),
    
    # Gestión de servicios
    path('services/', views.services_view, name='services'),
    path('services/toggle/<int:service_id>/', views.toggle_service_status, name='toggle_service_status'),
    
    # Horarios
    path('schedules/', views.schedules_view, name='schedules'),
    
    # Reportes
    path('reports/', views.reports_view, name='reports'),
    
    #Documentos
    path('documents/', views.upload_document_view, name='upload_document'),
    path('documents/delete/<int:document_id>/', views.delete_document_view, name='delete_document'),
    path('documents/toggle/<int:document_id>/', views.toggle_document_status_view, name='toggle_document'),

]
