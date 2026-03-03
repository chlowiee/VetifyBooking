
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('booking/', views.booking_view, name='booking'),
    path('appointments/', views.appointments_view, name='appointments'),

    # Perfil y mascotas
    path('profile/', views.profile_view, name='profile'),
    path('register-pet/', views.register_pet_view, name='register_pet'),
    path('edit-pet/<int:pet_id>/', views.edit_pet_view, name='edit_pet'),
    path('delete-pet/<int:pet_id>/', views.delete_pet_view, name='delete_pet'),
    path('documents/', views.documents_view, name='documents'),
    
    path('services-schedules/', views.services_schedules_view, name='services_schedules'),
]

