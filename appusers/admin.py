from django.contrib import admin
from .models import Tutor, Student, Course, Department, Availability

# Register your models here.
admin.site.register(Tutor)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Department)
admin.site.register(Availability)


