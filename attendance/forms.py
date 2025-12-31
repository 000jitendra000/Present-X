from django import forms
from .models import Semester, TimetableEntry, Subject
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password1', 'password2')

    def clean_username(self):
        # username is expected to be roll number; you can add pattern checks here
        return self.cleaned_data['username']

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['name', 'start_date', 'is_active']

class TimetableEntryForm(forms.ModelForm):
    class Meta:
        model = TimetableEntry
        fields = ['day', 'period', 'subject']

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']