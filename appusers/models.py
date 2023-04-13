from django.contrib.auth.models import User
from django.db import models

# Create your models here.
TIMEBLOCK_CHOICES = (
    ("A", "8:00-8:20"),
    ("B", "8:20-8:40"),
    ("C", "8:40-9:00"),
    ("D", "9:00-9:20"),
    ("E", "9:20-9:40"),
    ("F", "9:40-10:00"),
)
STATUS_CHOICES = [
    ('A', 'Available'),
    ('B', 'Booked'),
    ('C', 'Canceled')
]

class Course(models.Model):
    c_name = models.CharField(max_length=100)
    c_code = models.CharField(max_length=50, unique=True, null=False)

    def __str__(self):
        return self.c_code

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ums_id = models.CharField(max_length=20, unique=True, null=False)
    courses = models.ManyToManyField(Course, related_name='students')

    def __str__(self):
        return self.user.username
    def booked_slots(self):
        return self.booked_slots.all()

class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course, related_name='tutors')
    def availabilities(self):
        return self.availabilities.all()

    def __str__(self):
        return self.user.username
class Availability (models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, null=True, blank=True, related_name='availabilities')
    date = models.DateField()
    timeblock = models.CharField(max_length=1, choices=TIMEBLOCK_CHOICES)
    booked_by = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_slots')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    semester = models.CharField(max_length=8, null=True)
    def __str__(self):
        return f"{self.tutor} - {self.date} - {self.get_timeblock_display()} with {self.booked_by} is {self.status}"
    def check_semester(self):
        today = self.date
        if today.month >= 1 and today.month <= 4:
            self.semester = 'SP'
        elif today.month >= 5 and today.month <= 8:
            self.semester = 'SU'
        elif today.month >= 9 and today.month <= 12:
            self.semester = 'F'
        else:
            # default to Spring if current month is invalid
            self.semester = 'SP'

    def save(self, *args, **kwargs):
        self.check_semester()
        super().save(*args, **kwargs)
    
class Department (models.Model):
    d_name = models.CharField(max_length=100)
    def __str__(self):
        return self.d_name

