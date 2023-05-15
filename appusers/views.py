from django.contrib.admin.helpers import AdminForm
from django.forms import model_to_dict
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
    """
    View function for user login.

    If the request method is POST, it attempts to authenticate the user based on the provided username and password.
    If authentication is successful, the user is logged in and redirected to the home page.
    If authentication fails, an error message is displayed and the user is redirected back to the login page.

    Returns:
        HttpResponse: The rendered login page or a redirect response.
    """
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
    """
    View function for user logout.

    Logs out the currently authenticated user, displays a success message, and redirects to the login page.

    Returns:
        HttpResponse: A redirect response to the login page.
    """
    logout(request)
    messages.success(request,"Logged out")
    return redirect('login')

def signup_view(request):
    """
   View function for user signup.

   Handles the user registration process, including form validation, user creation,
   saving user details, sending an activation email, and redirecting to the activation_sent page.

   Returns:
       HttpResponse: A redirect response to the activation_sent page or a rendered registration page.
   """
    if request.method=="POST":
        username= request.POST['username']
        firstname= request.POST['firstname']
        lastname= request.POST['lastname']
        email= request.POST['email']
        pasw1= request.POST['pasw1']
        pasw2= request.POST['pasw2']
        if(pasw1!=pasw2):
            messages.error(request,"Passwords dont match")
            return redirect('signup')
        else:
            user = User.objects.create_user(username,email,pasw1)
            user.first_name = firstname
            user.last_name = lastname
            user.save()
            student = Student.objects.create(user=user)
            student.save()
            # Send activation email
            subject = 'Activate your account'
            message = render_to_string('emails/activate_account_email.html', {
                'user': user,
                'domain': request.get_host(),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            from_email = DEFAULT_FROM_EMAIL
            to_email = email
            send_mail(subject, message, from_email, [to_email], fail_silently=False)
            return redirect('activation_sent')

    return render(request, 'account/register.html')

def activation_sent(request):
    """
  View function for the activation_sent page.

  Renders the activation_sent.html template, which displays a message confirming that the activation email has been sent.

  Returns:
      HttpResponse: A rendered activation_sent.html page.
  """
    return render(request, 'account/activation_sent.html')

def forgot_password(request):
    """
  View function for the forgot password feature.

  Handles the form submission for resetting the user's password. Sends a password reset email
  to the user's email address if a user with the given email exists.

  Returns:
      HttpResponse: A redirect response to the forgot_password page or a rendered forgot_password page.
  """
    if request.method == 'POST':
        email= request.POST['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No user found with the given email address')
            return redirect('forgot_password')

        # Generate and send password reset email
        subject = 'Reset your password'
        message = render_to_string('emails/password_reset_email.html', {
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
    """
View function for confirming the password reset.

Validates the user's token and displays the password reset form. If the form is submitted
with a new password, the password is reset for the user.

Args:
    request (HttpRequest): The HTTP request object.
    uidb64 (str): The base64-encoded user ID.
    token (str): The password reset token.

Returns:
    HttpResponse: A redirect response to the login page or a rendered password_reset_confirm page.
"""
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
    """
View function for activating the user account.

Validates the activation token and activates the user's account if the token is valid.
Displays success or error messages accordingly.

Args:
    request (HttpRequest): The HTTP request object.
    uidb64 (str): The base64-encoded user ID.
    token (str): The activation token.

Returns:
    HttpResponse: A redirect response to the login page or a rendered activation page.
"""
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
    """
  View function for the home page.

  Renders the home.html template and retrieves information for the logged-in user,
  including their current and upcoming sessions if they are a student or tutor.

  Returns:
      HttpResponse: A rendered home.html page with the relevant information.
  """
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
    """
View function for displaying available slots.

Renders the available_slot.html template and retrieves information about available slots,
courses, and tutors. If the logged-in user is a student, it also checks for the number of
no-shows to determine whether to display the no-show warning.

Returns:
    HttpResponse: A rendered available_slot.html page with the relevant information.
"""
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
    """
View function for booking slots.

Handles the slot booking process when a user submits the booking form. Sends confirmation
emails to the student and tutor. If the user is a superuser, it allows selecting a student
to book the slot for.

Args:
    request (HttpRequest): The HTTP request object.
    availability_id (int): The ID of the availability slot to book.

Returns:
    HttpResponse: A redirect response to the home page or a rendered booking_page.html page.
"""
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
        # Send confirmation email to the student
        subject = 'Session Booked'
        message = render_to_string('emails/session_booked_email.html', {
            'user': student.user,
            'course': availability.course,
            'tutor': availability.tutor,
            'timeblock': availability.timeblock,
        })
        from_email = DEFAULT_FROM_EMAIL
        to_email = student.user.email
        send_mail(subject, message, from_email, [to_email], fail_silently=False)

        # Send confirmation email to the tutor
        subject = 'Session Booked'
        message = render_to_string('emails/session_booked_email_tutor.html', {
            'user': availability.tutor,
            'course': availability.course,
            'student': availability.booked_by,
            'timeblock': availability.timeblock,
        })
        from_email = DEFAULT_FROM_EMAIL
        to_email = availability.tutor.user.email
        send_mail(subject, message, from_email, [to_email], fail_silently=False)
        messages.success(request,"Session booked successfully")
        return redirect('home')

    if request.user.is_superuser:
        students = Student.objects.all()
        return render(request, 'booking_page.html', {'slot': availability, 'students': students})
    else:
        return render(request, 'booking_page.html', {'slot': availability})


@login_required
def booking_page(request, availability_id):
    """
View function for the booking page.

Renders the booking_page.html template and retrieves information about the availability slot.
Checks if the slot is already booked and redirects if it is. Also checks if the user is a student
and if the student is enrolled in the course associated with the slot.

Args:
    request (HttpRequest): The HTTP request object.
    availability_id (int): The ID of the availability slot.

Returns:
    HttpResponse: A redirect response to the available_slots page or a rendered booking_page.html page.
"""
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
    """
 View function for creating a session slot.

 Renders the create_slots.html template and handles the form submission for creating a new session slot.
 Sends a confirmation email to the tutor upon successful creation.

 Returns:
     HttpResponse: A redirect response to the home page or a rendered create_slots.html page.
 """
    try:
        tutor = request.user.tutor
        tutor_session_history = Availability.objects.filter(tutor=tutor).order_by('date')
    except Tutor.DoesNotExist:
        tutor_session_history = []

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
            # Send confirmation email to the tutor
            subject = 'Session Created'
            message = render_to_string('emails/session_created_email.html', {
                'user': tutor.user,
                'course': availability.course,
                'timeblock': availability.timeblock,
            })
            from_email = DEFAULT_FROM_EMAIL
            to_email = tutor.user.email
            send_mail(subject, message, from_email, [to_email], fail_silently=False)
            messages.success(request, 'Session created successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Session already exist on same date.')
            return redirect('create_slot')
    else:
        if request.user.is_superuser:
            form = AvailabilityForm(user=request.user, include_all_tutors=True)
        else:
            initial_data = {'tutor': request.user.tutor}
            form = AvailabilityForm(initial=initial_data, user=request.user)

    return render(request, 'create_slots.html', {'form': form, 'tutor_session_history' : tutor_session_history})


@login_required
def profile_view(request):
    """
View function for the profile page.

Renders the profile.html template and handles the form submission for updating the user's profile.
Depending on the user's role (student, tutor, or superuser), different forms are used.

Returns:
    HttpResponse: A rendered profile.html page with the relevant form.
"""
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
                messages.success(request, 'Profile Updated!')
        else:
            form = form_class()  # remove the instance argument
    else:
        if request.method == 'POST':
            form = form_class(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile Updated!')
        else:
            form = form_class(instance=profile)

    return render(request, 'profile.html', {'form': form})


@login_required
def assign_roles(request):
    """
View function for assigning roles to users.

Handles the form submission for assigning roles to users. Updates the user's group and creates
corresponding student or tutor objects depending on the assigned role.

Returns:
    HttpResponse: A redirect response to the home page or a rendered assign_roles.html page.
"""
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
    """
 View function for rendering the enter_dates.html template.

 Returns:
     HttpResponse: A rendered enter_dates.html page.
 """
    return render(request, 'enter_dates.html')

@login_required
def add_semester(request):
    """
    View function for adding a semester.

    Handles the form submission for adding a new semester with a name, start date, and end date.
    Validates the dates and saves the semester object if the start date is earlier than the end date.

    Returns:
        HttpResponse: A redirect response to the enter_dates page or a rendered enter_dates.html page.
    """
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
    """
 View function for canceling a session.

 Handles the cancellation of a session by the student or tutor. If the session is booked and the user is a student,
 the session status is changed to available and the booked_by field is set to None. If the user is a tutor, the session
 is deleted. Cancellation emails are sent to the affected parties.

 Returns:
     HttpResponse: A JsonResponse indicating the success or failure of the cancellation.
 """
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        session = Availability.objects.filter(pk=session_id).first()

        if session and session.status == 'B':
            if hasattr(request.user, 'student'):
                student = request.user.student
                session.status = 'A'
                session.booked_by = None
                session.save()
                send_cancellation_emails(student, session.tutor, session.course, session.timeblock)
                messages.success(request, 'Session Cancelled !')
                return JsonResponse({'success': True})
            elif hasattr(request.user, 'tutor'):
                send_cancellation_emails(session.booked_by, session.tutor, session.course, session.timeblock)
                session.delete()

                messages.success(request, 'Session Cancelled !')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'User is not a student or tutor.'})

        else:
            return JsonResponse({'success': False, 'error': 'Session not found or already cancelled.'})

    return redirect('home')

def send_cancellation_emails(student, tutor, course, timeblock):
    """
  Sends cancellation emails to the student and tutor when a session is cancelled.

  Args:
      student (Student): The student whose session is being cancelled.
      tutor (Tutor): The tutor associated with the session.
      course (Course): The course of the session.
      timeblock (str): The timeblock of the session.

  Returns:
      None
  """
    # Send cancellation email to the user student
    subject = 'Session Cancelled'
    message = render_to_string('emails/session_cancel_email.html', {
        'user': student,
        'course': course,
        'tutor': tutor,
        'timeblock': timeblock,
    })
    from_email = DEFAULT_FROM_EMAIL
    to_email = student.user.email
    send_mail(subject, message, from_email, [to_email], fail_silently=False)

    # Send cancellation email to the tutor
    subject = 'Session Cancelled'
    message = render_to_string('emails/session_cancel_email_tutor.html', {
        'user': tutor,
        'course': course,
        'student': student,
        'timeblock': timeblock,
    })
    from_email = DEFAULT_FROM_EMAIL
    to_email = tutor.user.email
    send_mail(subject, message, from_email, [to_email], fail_silently=False)

@login_required
def session_history(request):
    """
Displays the session history for the current user (student or tutor).

Returns:
    None
"""
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
    """
   View function to handle password change request.

   This view allows a logged-in user to change their password.

   If the request method is POST, the function validates the submitted form data.
   If the form is valid, the user's password is updated and the session authentication hash is updated.
   A success message is displayed, and the user is redirected to the home page.
   If the form is not valid, an error message is displayed.

   If the request method is GET, the function renders the password change form with the current user's information.

   Args:
       request (HttpRequest): The HTTP request object.

   Returns:
       HttpResponse: The HTTP response containing the rendered password change form template.

   """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Password Updated!')
            return redirect('home')
        else:
            messages.error(request, 'Please enter correct details')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'account/change_password.html', {'form': form})


def get_sessions(request):
    """
   View function to retrieve sessions for a specific tutor and date.

   This view retrieves sessions based on the specified tutor and date.
   The tutor ID and date are expected to be provided as GET parameters in the request.

   The function filters the Availability objects based on the tutor ID and date.
   It constructs a list of session dictionaries containing the timeblock and course name.
   The list is then returned as a JSON response.

   Args:
       request (HttpRequest): The HTTP request object.

   Returns:
       JsonResponse: The JSON response containing the list of session dictionaries.

   """
    tutor_id = request.GET.get('tutor')
    date = request.GET.get('date')
    sessions = Availability.objects.filter(tutor=tutor_id, date=date)
    history = []
    for session in sessions:
        session_dict = {'timeblock': session.timeblock, 'course': session.course.c_name}
        history.append(session_dict)
    return JsonResponse({'history': history})