from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.models import User
from booking.models import Appointment, Pet, Service, Veterinarian, ClinicSchedule
from .decorators import admin_required
import json


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def admin_login_view(request):
    """Vista de login exclusiva para administradores"""
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard:dashboard')
        else:
            messages.error(request, 'Credenciales inválidas o no tienes permisos de administrador')
    
    return render(request, 'admin_dashboard/login.html')


@admin_required
def dashboard_view(request):
    """Vista principal del dashboard con estadísticas"""
    
    # KPIs generales
    total_appointments = Appointment.objects.count()
    total_users = User.objects.filter(is_superuser=False).count()
    total_pets = Pet.objects.count()
    total_vets = Veterinarian.objects.filter(is_active=True).count()
    
    # Citas de hoy
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(date=today).count()
    
    # Citas pendientes (futuras)
    pending_appointments = Appointment.objects.filter(date__gte=today).count()
    
    # Estadísticas de los últimos 7 días
    last_7_days = today - timedelta(days=7)
    recent_appointments = Appointment.objects.filter(date__gte=last_7_days)
    
    # Datos para gráfica de citas por día (últimos 7 días)
    appointments_by_day = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Appointment.objects.filter(date=day).count()
        appointments_by_day.append({
            'date': day.strftime('%d/%m'),
            'count': count
        })
    
    # Mascotas por tipo
    pets_by_type = Pet.objects.values('pet_type').annotate(count=Count('id'))
    
    # Servicios más solicitados
    top_services = Service.objects.filter(is_active=True)[:5]
    
    # Últimas citas registradas
    latest_appointments = Appointment.objects.select_related('user').order_by('-created_at')[:10]
    
    # Veterinarios activos
    active_vets = Veterinarian.objects.filter(is_active=True)[:5]
    
    context = {
        'total_appointments': total_appointments,
        'total_users': total_users,
        'total_pets': total_pets,
        'total_vets': total_vets,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'appointments_by_day': json.dumps(appointments_by_day),
        'pets_by_type': pets_by_type,
        'top_services': top_services,
        'latest_appointments': latest_appointments,
        'active_vets': active_vets,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@admin_required
def appointments_view(request):
    """Vista de gestión de citas"""
    
    # Filtros
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', '')
    search = request.GET.get('search', '')
    
    appointments = Appointment.objects.select_related('user', 'pet').order_by('-date', '-time')
    
    # Aplicar filtros
    if status_filter == 'today':
        appointments = appointments.filter(date=timezone.now().date())
    elif status_filter == 'upcoming':
        appointments = appointments.filter(date__gte=timezone.now().date())
    elif status_filter == 'past':
        appointments = appointments.filter(date__lt=timezone.now().date())
    
    if date_filter:
        appointments = appointments.filter(date=date_filter)
    
    if search:
        appointments = appointments.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(pet__name__icontains=search)
        )
    
    context = {
        'appointments': appointments,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search': search,
        'total_count': appointments.count(),
    }
    
    return render(request, 'admin_dashboard/appointments.html', context)


@admin_required
def users_view(request):
    """Vista de gestión de usuarios"""
    
    search = request.GET.get('search', '')
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Agregar estadísticas por usuario
    users_data = []
    for user in users:
        users_data.append({
            'user': user,
            'pets_count': Pet.objects.filter(owner=user).count(),
            'appointments_count': Appointment.objects.filter(user=user).count(),
        })
    
    context = {
        'users_data': users_data,
        'search': search,
        'total_count': users.count(),
    }
    
    return render(request, 'admin_dashboard/users.html', context)


@admin_required
def pets_view(request):
    """Vista de gestión de mascotas"""
    
    type_filter = request.GET.get('type', 'all')
    search = request.GET.get('search', '')
    
    pets = Pet.objects.select_related('owner').order_by('-created_at')
    
    if type_filter != 'all':
        pets = pets.filter(pet_type=type_filter)
    
    if search:
        pets = pets.filter(
            Q(name__icontains=search) |
            Q(owner__username__icontains=search) |
            Q(breed__icontains=search)
        )
    
    # Estadísticas
    total_dogs = Pet.objects.filter(pet_type='dog').count()
    total_cats = Pet.objects.filter(pet_type='cat').count()
    total_others = Pet.objects.filter(pet_type='other').count()
    
    context = {
        'pets': pets,
        'type_filter': type_filter,
        'search': search,
        'total_count': pets.count(),
        'total_dogs': total_dogs,
        'total_cats': total_cats,
        'total_others': total_others,
    }
    
    return render(request, 'admin_dashboard/pets.html', context)


@admin_required
def veterinarians_view(request):
    """Vista de gestión de veterinarios"""
    
    specialty_filter = request.GET.get('specialty', 'all')
    search = request.GET.get('search', '')
    
    vets = Veterinarian.objects.all().order_by('name')
    
    if specialty_filter != 'all':
        vets = vets.filter(specialty=specialty_filter)
    
    if search:
        vets = vets.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(license_number__icontains=search)
        )
    
    context = {
        'veterinarians': vets,
        'specialty_filter': specialty_filter,
        'search': search,
        'total_count': vets.count(),
        'active_count': vets.filter(is_active=True).count(),
    }
    
    return render(request, 'admin_dashboard/veterinarians.html', context)


@admin_required
def services_view(request):
    """Vista de gestión de servicios"""
    
    search = request.GET.get('search', '')
    
    services = Service.objects.all().order_by('name')
    
    if search:
        services = services.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    context = {
        'services': services,
        'search': search,
        'total_count': services.count(),
        'active_count': services.filter(is_active=True).count(),
    }
    
    return render(request, 'admin_dashboard/services.html', context)


@admin_required
def schedules_view(request):
    clinic_schedules = ClinicSchedule.objects.all()

    open_days = clinic_schedules.filter(is_open=True).count()

    context = {
        'clinic_schedules': clinic_schedules,
        'open_days': open_days,
    }

    return render(request, 'admin_dashboard/schedules.html', context)


@admin_required
def reports_view(request):
    """Vista de reportes y estadísticas avanzadas"""
    
    # Período de reporte
    period = request.GET.get('period', '30')  # días
    days = int(period)
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Citas en el período
    appointments_in_period = Appointment.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Nuevos usuarios en el período
    new_users = User.objects.filter(
        date_joined__gte=start_date,
        is_superuser=False
    ).count()
    
    # Nuevas mascotas en el período
    new_pets = Pet.objects.filter(
        created_at__gte=start_date
    ).count()
    
    # Citas por mes (últimos 6 meses)
    appointments_by_month = []
    for i in range(5, -1, -1):
        month_date = end_date - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1)
        
        count = Appointment.objects.filter(
            date__gte=month_start,
            date__lt=month_end
        ).count()
        
        appointments_by_month.append({
            'month': month_date.strftime('%B'),
            'count': count
        })
    
    # Top 5 usuarios con más citas
    top_users = User.objects.filter(is_superuser=False).annotate(
        appointments_count=Count('appointments')
    ).order_by('-appointments_count')[:5]
    
    # Servicios más solicitados (simulado con citas)
    service_stats = Service.objects.filter(is_active=True).annotate(
        usage_count=Count('id')
    )[:10]
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_appointments': appointments_in_period.count(),
        'new_users': new_users,
        'new_pets': new_pets,
        'appointments_by_month': json.dumps(appointments_by_month),
        'top_users': top_users,
        'service_stats': service_stats,
    }
    
    return render(request, 'admin_dashboard/reports.html', context)


@admin_required
def delete_appointment(request, appointment_id):
    """Eliminar una cita"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    messages.success(request, 'Cita eliminada exitosamente')
    return redirect('admin_dashboard:appointments')


@admin_required
def toggle_user_status(request, user_id):
    """Activar/desactivar usuario"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = "activado" if user.is_active else "desactivado"
    messages.success(request, f'Usuario {status} exitosamente')
    return redirect('admin_dashboard:users')


@admin_required
def delete_pet(request, pet_id):
    """Eliminar una mascota"""
    pet = get_object_or_404(Pet, id=pet_id)
    pet_name = pet.name
    pet.delete()
    messages.success(request, f'{pet_name} ha sido eliminado')
    return redirect('admin_dashboard:pets')


@admin_required
def toggle_vet_status(request, vet_id):
    """Activar/desactivar veterinario"""
    vet = get_object_or_404(Veterinarian, id=vet_id)
    vet.is_active = not vet.is_active
    vet.save()
    status = "activado" if vet.is_active else "desactivado"
    messages.success(request, f'Veterinario {status} exitosamente')
    return redirect('admin_dashboard:veterinarians')


@admin_required
def toggle_service_status(request, service_id):
    """Activar/desactivar servicio"""
    service = get_object_or_404(Service, id=service_id)
    service.is_active = not service.is_active
    service.save()
    status = "activado" if service.is_active else "desactivado"
    messages.success(request, f'Servicio {status} exitosamente')
    return redirect('admin_dashboard:services')


@admin_required
def upload_document_view(request):
    """Vista para subir documentos PDF"""
    from booking.models import Document
    from django.contrib import messages
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        icon = request.POST.get('icon', '📄')
        file = request.FILES.get('file')
        
        if not all([title, category, file]):
            messages.error(request, 'Por favor completa todos los campos obligatorios.')
            return redirect('admin_dashboard:upload_document')
        
        # Validar que sea un PDF
        if not file.name.endswith('.pdf'):
            messages.error(request, 'Solo se permiten archivos PDF.')
            return redirect('admin_dashboard:upload_document')
        
        try:
            document = Document.objects.create(
                title=title,
                description=description,
                category=category,
                icon=icon,
                file=file,
                uploaded_by=request.user
            )
            messages.success(request, f'Documento "{title}" subido exitosamente.')
            return redirect('admin_dashboard:upload_document')
        except Exception as e:
            messages.error(request, f'Error al subir el documento: {str(e)}')
            return redirect('admin_dashboard:upload_document')
    
    # GET request
    documents = Document.objects.all().order_by('-created_at')
    
    context = {
        'documents': documents,
        'category_choices': Document.CATEGORY_CHOICES,
    }
    
    return render(request, 'admin_dashboard/upload_document.html', context)


@admin_required
def delete_document_view(request, document_id):
    """Vista para eliminar un documento"""
    from booking.models import Document
    from django.contrib import messages
    import os
    
    try:
        document = Document.objects.get(id=document_id)
        
        # Eliminar el archivo físico
        if document.file:
            if os.path.isfile(document.file.path):
                os.remove(document.file.path)
        
        document_title = document.title
        document.delete()
        
        messages.success(request, f'Documento "{document_title}" eliminado exitosamente.')
    except Document.DoesNotExist:
        messages.error(request, 'El documento no existe.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el documento: {str(e)}')
    
    return redirect('admin_dashboard:upload_document')


@admin_required
def toggle_document_status_view(request, document_id):
    """Vista para activar/desactivar un documento"""
    from booking.models import Document
    from django.contrib import messages
    
    try:
        document = Document.objects.get(id=document_id)
        document.is_active = not document.is_active
        document.save()
        
        status = "activado" if document.is_active else "desactivado"
        messages.success(request, f'Documento "{document.title}" {status} exitosamente.')
    except Document.DoesNotExist:
        messages.error(request, 'El documento no existe.')
    except Exception as e:
        messages.error(request, f'Error al cambiar el estado: {str(e)}')
    
    return redirect('admin_dashboard:upload_document')

@admin_required
def add_veterinarian(request):
    if request.method == 'POST':
        Veterinarian.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            license_number=request.POST.get('license_number'),
            specialty=request.POST.get('specialty'),
            years_experience=request.POST.get('years_experience', 0),
            start_time=request.POST.get('start_time', '08:00'),
            end_time=request.POST.get('end_time', '17:00'),
            is_active=True
        )
        messages.success(request, 'Veterinario agregado exitosamente.')
    return redirect('admin_dashboard:veterinarians')