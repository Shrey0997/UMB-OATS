from django.contrib.admin.helpers import AdminForm
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.datetime_safe import date
from UMassSchedulingApplication.settings import DEFAULT_FROM_EMAIL
from .models import Availability, SemesterDates, Tutor, Student, Course
from django.contrib.auth import login, logout, get_user_model, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import AvailabilityForm, SignupForm, StudentForm, TutorForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm

User = get_user_model()


def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')

        else:
            messages.error(request, "Username or password invalid")
            return redirect('login')

    return render(request, 'account/login.html')

def logout_view(request):
    logout(request)
    messages.success(request,"Logged out")
    return redirect('login')

def signup_view(request):
    if request.method=="POST":
        username= request.POST['username']
        firstname= request.POST['firstname']
        lastname= request.POST['lastname']
        email= request.POST['email']
        pasw1= request.POST['pasw1']
        pasw2= request.POST['pasw2']
        if(pasw1!=pasw2):
            messages.error(request,"Passwords dont match")
            return redirect('account/register.html')
        else:
            user = User.objects.create_user(username,email,pasw1)
            user.first_name = firstname
            user.last_name = lastname
            user.save()
            # Send activation email
            subject = 'Activate your account'
            message = render_to_string('account/activate_account_email.html', {
                'user': user,
                'domain': request.get_host(),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            from_email = DEFAULT_FROM_EMAIL
            to_email = email
            send_mail(subject, message, from_email, [to_email], fail_silently=False)
            messages.success(request,"Registered successfully")
            return redirect('activation_sent')

    return render(request, 'account/register.html')

def activation_sent(request):
    return render(request, 'account/activation_sent.html')

def forgot_password(request):
    if request.method == 'POST':
        email= request.POST['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No user found with the given email address')
            return redirect('forgot_password')

        # Generate and send password reset email
        subject = 'Reset your password'
        message = render_to_string('account/password_reset_email.html', {
            'user': user,
            'domain': request.get_host(),
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        from_email = DEFAULT_FROM_EMAIL
        to_email = email
        send_mail(subject, message, from_email, [to_email], fail_silently=False)
        messages.success(request, 'Password reset email has been sent. Please check your email to reset your password.')
        return redirect('forgot_password')

    return render(request, 'account/forgot_password.html')

def passwordResetconfirm(request, uidb64, token):
    try:
        # Get user id from base64 encoded uidb64
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            # Get new password from form and set it for the user
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            if password1 != password2: #check for empty as well.
                messages.error(request, 'Passwords do not match')
                return render(request, 'account/password_reset_confirm.html', {'uidb64': uidb64, 'token': token})
            else:
                user.set_password(password1)
                user.save()
                messages.success(request, 'Password has been reset successfully')
                return redirect('login')
        else:
            return render(request, 'account/password_reset_confirm.html', {'uidb64': uidb64, 'token': token})
    else:
        messages.error(request, 'The password reset link is invalid or has expired')
        return redirect('forgot_password')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully.')
        return redirect('login')
    else:
        messages.error(request, 'The activation link is invalid or has expired.')
        return redirect('home')


@login_required
def home_view(request):
    current_user = request.user
    today = date.today()
    slots = Availability.objects.all().order_by('date')
    try:
        student = current_user.student
        s_today_sessions = Availability.objects.filter(booked_by=student, date=today).order_by('timeblock')
        s_upcoming_sessions = Availability.objects.filter(booked_by=student, date__gt=today).order_by('date')
    except Student.DoesNotExist:
        s_today_sessions = []
        s_upcoming_sessions = []

    try:
        tutor = current_user.tutor
        t_today_sessions = Availability.objects.filter(tutor=tutor, date=today).order_by('timeblock')
        t_upcoming_sessions = Availability.objects.filter(tutor=tutor, date__gt=today).order_by('date')
    except Tutor.DoesNotExist:
        t_today_sessions = []
        t_upcoming_sessions = []

    return render(request, 'home.html',
                  {'slots': slots, 'today':today,
                   'tsessions': s_today_sessions, 'upsessions': s_upcoming_sessions,
                   'ttutsessions': t_today_sessions, 'uptutsessions': t_upcoming_sessions})


@login_required
def available_slots(request):
    today = date.today()
    courses = Course.objects.all()
    tutors = Tutor.objects.all()

    if request.user.student:
        student = request.user.student
        no_show = student.no_shows
        ns = True
        slots = Availability.objects.filter(course__in=student.courses.all(), date__gt=today).order_by('date')
        if no_show > 2:
            ns = False
    else:
        slots = Availability.objects.all().filter(date__gt=today).order_by('date')
    return render(request, 'available_slot.html', {'slots': slots, 'courses': courses, 'tutors': tutors, 'ns': ns})


@login_required
def book_slots(request, availability_id):
    availability = get_object_or_404(Availability, id=availability_id)

    if request.method == 'POST':
        # get the selected student
        if request.user.is_superuser:
            student_id = request.POST.get('student')
            student = get_object_or_404(Student, id=student_id)
        else:
            student = request.user.student

        # code to handle booking the slot goes here
        availability.booked_by = student
        availability.status = 'B'
        availability.save()
        return redirect('home')

    if request.user.is_superuser:
        students = Student.objects.all()
        return render(request, 'booking_page.html', {'slot': availability, 'students': students})
    else:
        return render(request, 'booking_page.html', {'slot': availability})


@login_required
def booking_page(request, availability_id):
    availability = get_object_or_404(Availability, id=availability_id)
    if availability.booked_by is not None:
        return redirect('available_slots')
    # check if the user is a student
    if not request.user.is_authenticated or not hasattr(request.user, 'student'):
        return redirect('login')
    student = request.user.student

    # check if the student is enrolled in the course
    if student.courses.filter(id=availability.course.id).count() == 0:
        return redirect('available_slots')

    return render(request, 'booking_page.html', {'slot': availability})


@login_required
def create_slot(request):
    if not request.user.is_superuser and not request.user.tutor:
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('home')

    if request.method == 'POST':
        form = AvailabilityForm(request.POST, user=request.user, include_all_tutors=True)
        if form.is_valid():
            availability = form.save(commit=False)
            if not request.user.is_superuser:
                availability.tutor = request.user.tutor
            availability.save()
            messages.success(request, 'Slot created successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid data. Please correct the errors below.')
    else:
        if request.user.is_superuser:
            form = AvailabilityForm(user=request.user, include_all_tutors=True)
        else:
            initial_data = {'tutor': request.user.tutor}
            form = AvailabilityForm(initial=initial_data, user=request.user)

    return render(request, 'create_slots.html', {'form': form})


@login_required
def profile_view(request):
    user = request.user
    if hasattr(user, 'student'):
        profile = user.student
        form_class = StudentForm
    elif hasattr(user, 'tutor'):
        profile = user.tutor
        form_class = TutorForm

    if request.user.is_superuser:
        form_class = AdminForm
        if request.method == 'POST':
            form = form_class(request.POST)
            if form.is_valid():
                form.save()
        else:
            form = form_class()  # remove the instance argument
    else:
        if request.method == 'POST':
            form = form_class(request.POST, instance=profile)
            if form.is_valid():
                form.save()
        else:
            form = form_class(instance=profile)

    return render(request, 'profile.html', {'form': form})


@login_required
def assign_roles(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        role = request.POST.get('role')
        user = User.objects.get(username=username)
        group = Group.objects.get(name=role)
        user.groups.clear()
        user.groups.add(group)
        if role == 'student':
            Student.objects.create(user=user, ums_id='123')
        elif role == 'tutor':
            Tutor.objects.create(user=user)
        return redirect('home')
    else:
        users = User.objects.all()
        roles = Group.objects.all()
        return render(request, 'assign_roles.html', {'users': users, 'roles': roles})
@login_required
def enter_dates(request):
    return render(request, 'enter_dates.html')
@login_required
def add_semester(request):
    if request.method == 'POST':
        semname=request.POST['semname']
        startdate=request.POST['start_date']
        enddate=request.POST['end_date']
    
    if startdate < enddate:
        semester = SemesterDates(name=semname, startDate=startdate, endDate=enddate)
        semester.save()
        messages.success(request, 'Semester added successfully.')
        return render(request, 'enter_dates.html')
    else:
        messages.error(request, 'Enter a valid dates.')
        return redirect('enter_dates')

@login_required
def cancel_session(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        session = Availability.objects.filter(pk=session_id).first()

        if session and session.status == 'B':
            if hasattr(request.user, 'student'):
                session.status = 'A'
                session.booked_by = None
                session.save()
                return JsonResponse({'success': True})
            elif hasattr(request.user, 'tutor'):
                session.delete()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'User is not a student or tutor.'})
        else:
            return JsonResponse({'success': False, 'error': 'Session not found or already cancelled.'})

    return redirect('home')

@login_required
def session_history(request):
    current_user = request.user
    today = date.today()
    slots = Availability.objects.all().order_by('date')
    try:
        student = current_user.student
        student_session_history = Availability.objects.filter(booked_by=student, date__lt=today).order_by('date')
    except Student.DoesNotExist:
        student_session_history = []

    try:
        tutor = current_user.tutor
        tutor_session_history = Availability.objects.filter(tutor=tutor, date__lt=today).order_by('date')
    except Tutor.DoesNotExist:
        tutor_session_history = []

    return render(request, 'session_history.html',
                  {'slots': slots, 'today': today,
                   'student_session_history': student_session_history,
                   'tutor_session_history': tutor_session_history,
                  })

def custom_page_not_found(request, exception):
    return render(request, '404.html', status=404)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'account/change_password.html', {'form': form})


@login_required
def update_profile_picture(request):
    student = request.user.student
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            student.profile_picture = form.cleaned_data['profile_picture']
            student.save()
            return redirect('profile')
    else:
        form = ProfilePictureForm()
    return render(request, 'update_profile_picture.html', {'form': form, 'student': student})