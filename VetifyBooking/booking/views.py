from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone

from .forms import RegisterForm, AppointmentForm
from .models import (
    Appointment,
    Pet,
    Service,
    Veterinarian,
    ClinicSchedule,
    Document,
)


# =============================
# AUTH
# =============================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'booking/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'booking/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# =============================
# HOME
# =============================

@login_required
def home_view(request):
    return render(request, 'booking/home.html')


# =============================
# BOOKINGS
# =============================

@login_required
def booking_view(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.save()
            messages.success(
                request,
                f'Appointment booked for {appointment.pet.name}!'
            )
            return redirect('appointments')
    else:
        form = AppointmentForm(user=request.user)

    return render(request, 'booking/booking.html', {'form': form})


@login_required
def appointments_view(request):
    appointments = Appointment.objects.filter(user=request.user)
    return render(
        request,
        'booking/appointments.html',
        {'appointments': appointments}
    )


@login_required
def delete_appointment(request, pk):
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        user=request.user
    )
    appointment.delete()
    messages.success(request, 'Appointment deleted successfully!')
    return redirect('appointments')


# =============================
# PROFILE & PETS
# =============================

@login_required
def profile_view(request):
    pets = Pet.objects.filter(owner=request.user)
    appointments_count = Appointment.objects.filter(
        user=request.user
    ).count()

    next_appointment = Appointment.objects.filter(
        user=request.user,
        date__gte=timezone.now().date()
    ).order_by('date', 'time').first()

    context = {
        'pets': pets,
        'appointments_count': appointments_count,
        'next_appointment': next_appointment,
        'pets_count': pets.count(),
    }

    return render(request, 'booking/profile.html', context)


@login_required
def register_pet_view(request):
    if request.method == 'POST':
        pet = Pet(owner=request.user)

        pet.name = request.POST.get('pet_name')
        pet.pet_type = request.POST.get('pet_type')
        pet.other_type = request.POST.get('other_type', '')
        pet.breed = request.POST.get('breed', '')
        pet.color = request.POST.get('color', '')
        pet.age = request.POST.get('age', 0)
        pet.weight = request.POST.get('weight', 0)
        pet.vaccination_status = request.POST.get('vaccination', 'updated')
        pet.allergies = request.POST.get('allergies', '')
        pet.friendly_with_people = request.POST.get('friendly_people') == 'on'
        pet.friendly_with_animals = request.POST.get('friendly_animals') == 'on'
        pet.nervous_at_vet = request.POST.get('nervous') == 'on'
        pet.special_care = request.POST.get('special_care') == 'on'
        pet.emergency_contact_name = request.POST.get('emergency_name', '')
        pet.emergency_contact_phone = request.POST.get('emergency_phone', '')

        if 'photo' in request.FILES:
            pet.photo = request.FILES['photo']

        pet.save()
        messages.success(
            request,
            f'¡{pet.name} ha sido registrado exitosamente! 🎉'
        )
        return redirect('profile')

    return render(request, 'booking/register_pet.html')


@login_required
def edit_pet_view(request, pet_id):
    pet = get_object_or_404(
        Pet,
        id=pet_id,
        owner=request.user
    )

    if request.method == 'POST':
        pet.name = request.POST.get('pet_name')
        pet.pet_type = request.POST.get('pet_type')
        pet.other_type = request.POST.get('other_type', '')
        pet.breed = request.POST.get('breed', '')
        pet.color = request.POST.get('color', '')
        pet.age = request.POST.get('age', 0)
        pet.weight = request.POST.get('weight', 0)
        pet.vaccination_status = request.POST.get('vaccination', 'updated')
        pet.allergies = request.POST.get('allergies', '')
        pet.friendly_with_people = request.POST.get('friendly_people') == 'on'
        pet.friendly_with_animals = request.POST.get('friendly_animals') == 'on'
        pet.nervous_at_vet = request.POST.get('nervous') == 'on'
        pet.special_care = request.POST.get('special_care') == 'on'
        pet.emergency_contact_name = request.POST.get('emergency_name', '')
        pet.emergency_contact_phone = request.POST.get('emergency_phone', '')

        if 'photo' in request.FILES:
            pet.photo = request.FILES['photo']

        pet.save()
        messages.success(
            request,
            f'¡{pet.name} ha sido actualizado exitosamente!'
        )
        return redirect('profile')

    return render(
        request,
        'booking/register_pet.html',
        {'pet': pet}
    )


@login_required
def delete_pet_view(request, pet_id):
    pet = get_object_or_404(
        Pet,
        id=pet_id,
        owner=request.user
    )
    pet_name = pet.name
    pet.delete()
    messages.success(request, f'{pet_name} ha sido eliminado.')
    return redirect('profile')


# =============================
# SERVICES & SCHEDULES
# =============================

@login_required
def services_schedules_view(request):

    services = Service.objects.filter(
        is_active=True
    ).order_by('name')

    service_icons = {
        'consulta': '🩺',
        'vacunación': '💉',
        'cirugía': '🔬',
        'urgencia': '🚑',
        'peluquería': '✂️',
        'baño': '🛁',
    }

    for service in services:
        service.icon = '💉'
        for key, icon in service_icons.items():
            if key in service.name.lower():
                service.icon = icon
                break

    days = [
        ('Lunes', 0), ('Martes', 1), ('Miércoles', 2),
        ('Jueves', 3), ('Viernes', 4),
        ('Sábado', 5), ('Domingo', 6)
    ]

    schedules = []
    today = date.today().weekday()

    for name, day in days:
        schedule = ClinicSchedule.objects.filter(
            day_of_week=day
        ).first()

        if not schedule:
            schedule = ClinicSchedule(
                day_of_week=day,
                is_open=False
            )

        schedule.day_display = name
        schedule.is_today = (day == today)
        schedules.append(schedule)

    veterinarians = Veterinarian.objects.filter(
        is_active=True
    ).order_by('name')

    return render(
        request,
        'booking/services_schedules.html',
        {
            'services': services,
            'schedules': schedules,
            'veterinarians': veterinarians,
        }
    )


# =============================
# DOCUMENTS
# =============================

@login_required
def documents_view(request):

    documents = Document.objects.filter(
        is_active=True
    ).order_by('-created_at')

    documents_by_category = {}

    for doc in documents:
        category = doc.get_category_display()
        documents_by_category.setdefault(category, []).append(doc)

    return render(
        request,
        'booking/documents.html',
        {
            'documents': documents,
            'documents_by_category': documents_by_category,
            'total_documents': documents.count(),
        }
    )