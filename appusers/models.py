import datetime
from django.contrib.auth.models import User
from django.db import models

# Create your models here.

TIMEBLOCK_CHOICES = (
    ("A", "8:00 AM - 9:00 AM"),
    ("B", "9:00 AM - 10:00 AM"),
    ("C", "10:00 AM - 11:00 AM"),
    ("D", "11:00 AM - 12:00 PM"),
    ("E", "12:00 PM - 1:00 PM"),
    ("F", "1:00 PM - 2:00 PM"),
    ("G", "2:00 PM - 3:00 PM"),
    ("H", "3:00 PM - 4:00 PM"),
    ("I", "4:00 PM - 5:00 PM"),
)

STATUS_CHOICES = [
    ('A', 'Available'),
    ('B', 'Booked'),
    ('C', 'Canceled')
]


class Course(models.Model):
    """
    Represents a course.

    Attributes:
        c_name (CharField): The name of the course.
        c_code (CharField): The code of the course.
    """
    c_name = models.CharField(max_length=100)
    c_code = models.CharField(max_length=50, unique=True, null=False)

    def __str__(self):
        return self.c_name


class Student(models.Model):
    """
    Represents a student.

    Attributes:
        user (OneToOneField): The associated user.
        ums_id (CharField): The UMS ID of the student.
        courses (ManyToManyField): The courses taken by the student.
        no_shows (IntegerField): The number of no-shows by the student.
        profile_picture (FileField): The profile picture of the student.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ums_id = models.CharField(max_length=20, null=True, blank=True)
    courses = models.ManyToManyField(Course, related_name='students')
    no_shows = models.IntegerField(max_length=1, default=0)
    profile_picture = models.FileField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def booked_slots(self):
        return self.booked_slots.all()


class Tutor(models.Model):
    """
    Represents a tutor.

    Attributes:
        user (OneToOneField): The associated user.
        courses (ManyToManyField): The courses taught by the tutor.
        profile_picture (URLField): The URL of the tutor's profile picture.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course, related_name='tutors')
    profile_picture = models.URLField(default='static/images/favicons/Blue_logo.png', null=True, blank=True)

    def availabilities(self):
        return self.availabilities.all()

    def __str__(self):
        return self.user.username


class Availability(models.Model):
    """
    Represents the availability of a tutor.

    Attributes:
        tutor (ForeignKey): The associated tutor.
        date (DateField): The date of availability.
        timeblock (CharField): The selected time block.
        booked_by (ForeignKey): The student who booked the slot.
        course (ForeignKey): The associated course.
        status (CharField): The status of the availability.
        semester (CharField): The semester of the availability.
    """
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, null=True, blank=True, related_name='availabilities')
    date = models.DateField()
    timeblock = models.CharField(max_length=1, choices=TIMEBLOCK_CHOICES)
    booked_by = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='booked_slots')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    semester = models.CharField(max_length=25, null=True)

    def __str__(self):
        """
       Returns a string representation of the Availability object.

       The string format is "{tutor} - {date} - {timeblock} with {booked_by} is {status}".

       Returns:
           str: The string representation of the Availability object.
       """
        return f"{self.tutor} - {self.date} - {self.get_timeblock_display()} with {self.booked_by} is {self.status}"

    def check_semester(self):
        today = self.date
        if today.month >= 1 and today.month <= 4:
            self.semester = 'SPRING'
        elif today.month >= 5 and today.month <= 8:
            self.semester = 'SUMMER'
        elif today.month >= 9 and today.month <= 12:
            self.semester = 'FALL'
        else:
            # default to Spring if current month is invalid
            self.semester = 'SPRING'

    def save(self, *args, **kwargs):
        self.check_semester()
        super().save(*args, **kwargs)


class Department(models.Model):
    """
    Represents a department.

    Attributes:
        d_name (CharField): The name of the department.
    """
    d_name = models.CharField(max_length=100)

    def __str__(self):
        return self.d_name


class SemesterDates(models.Model):
    """
   Represents the dates of a semester.

   Attributes:
       name (CharField): The name of the semester.
       startDate (DateField): The start date of the semester.
       endDate (DateField): The end date of the semester.
       currentSemester (BooleanField): Indicates if the semester is the current one.
   """
    name = models.CharField(max_length=20, primary_key=True)
    startDate = models.DateField(null=False)
    endDate = models.DateField(null=False)
    currentSemester = models.BooleanField(default=False)
