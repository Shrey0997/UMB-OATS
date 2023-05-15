from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.files.base import ContentFile
from django.forms import DateInput
from django.contrib.auth.models import User
from .models import Availability, Tutor, Student



class AvailabilityForm(forms.ModelForm):
    """
   Form for creating and updating availability.

   Allows tutors to specify their availability for a specific date and time block.

   Attributes:
       tutor (ModelChoiceField): The associated tutor.
       date (DateField): The date of availability.
       timeblock (CharField): The selected time block.
       booked_by (ModelChoiceField): The student who booked the slot.
       course (ModelChoiceField): The associated course.
       status (CharField): The status of the availability.
       semester (CharField): The semester of the availability.
   """
    class Meta:
        model = Availability
        fields = ['tutor', 'date', 'timeblock', 'course', 'booked_by', 'status', 'semester']
        widgets = {
            'date': DateInput(attrs={'type': 'date', 'onchange': 'setSemester()'}),
        }
        labels = {
            'booked_by': 'Student'
        }
        initial = {'status': 'A'}
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.include_all_tutors = kwargs.pop('include_all_tutors', False)
        initial = kwargs.pop('initial', {})
        initial['status'] = 'A'
        kwargs['initial'] = initial
        super(AvailabilityForm, self).__init__(*args, **kwargs)

        if self.user.is_superuser and self.include_all_tutors:
            self.fields['tutor'] = forms.ModelChoiceField(queryset=Tutor.objects.all())
        elif not self.user.is_superuser:
            self.fields['tutor'].widget = forms.HiddenInput()
            self.fields['tutor'].initial = self.user.tutor

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        timeblock = cleaned_data.get('timeblock')
        if not self.user.is_superuser:
            tutor = self.user.tutor
        else:
            tutor = cleaned_data.get('tutor')
        if Availability.objects.filter(tutor=tutor, date=date, timeblock=timeblock).exists():
            raise forms.ValidationError('A slot already exists for the selected tutor, date, and timeblock.')
        return cleaned_data


class SignupForm(UserCreationForm):
    """
Form for user registration.

Inherits from UserCreationForm and adds an email field.

Attributes:
    email (EmailField): The email address of the user.
    username (CharField): The username of the user.
"""
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    username = forms.CharField(required=True, help_text='Required. Enter a valid username.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super(SignupForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        if commit:
            user.save()
        return user

class BaseForm(forms.ModelForm):
    """
   Base form for student and tutor forms.

   Inherits from ModelForm and adds additional fields and behaviors.

   Attributes:
       first_name (CharField): The first name of the user.
       last_name (CharField): The last name of the user.
       profile_picture (FileField): The profile picture of the user.
   """
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    profile_picture = forms.FileField(required=False)

    class Meta:
        model = Student
        fields = ['ums_id', 'courses']

        widgets = {
            'courses': forms.CheckboxSelectMultiple(),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'ums_id': forms.TextInput(attrs={'class': 'form-control'}),
            'courses': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

        

    def __init__(self, *args, **kwargs):
        """
       Initializes the form instance.

       Sets initial values for first_name and last_name fields and updates widget attributes.

       Args:
           *args: Variable-length arguments.
           **kwargs: Arbitrary keyword arguments.
       """
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        """
      Saves the form.

      Updates the associated User model with first_name and last_name values.
      Saves the profile picture if provided.

      Args:
          commit (bool): A boolean value indicating whether to save the form or not.

      Returns:
          The saved model instance.
      """
        user = self.instance.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Use the ContentFile object to create a new file object from the uploaded image data
            file_data = ContentFile(profile_picture.read())
            filename = profile_picture.name
            # Set the profile picture field to the newly created file object
            self.instance.profile_picture.save(filename, file_data, save=False)

        if commit:
            user.save()
        return super().save(commit=commit)

class TutorForm(BaseForm):
    """
  Form for creating and updating tutor profiles.

  Inherits from BaseForm and sets the fields to be displayed.

  Attributes:
      fields (list): The fields to be displayed in the form.
  """
    class Meta(BaseForm.Meta):
        fields = ['courses']

class StudentForm(BaseForm):
    """
    Form for creating and updating student profiles.

    Inherits from BaseForm without any modifications.
    """
    pass

class AdminForm(UserChangeForm):
    """
    Form for updating admin user profiles.

    Inherits from UserChangeForm and adds initialization and saving behavior.

    Attributes:
        fields (tuple): The fields to be displayed in the form.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['first_name'] = self.first_name
        self.initial['last_name'] = self.last_name
        self.initial['username'] = self.username
        self.initial['email'] = self.email

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
