# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from .models import CustomUser, Timetable

# # Registration Form
# class CustomUserCreationForm(UserCreationForm):
#     class Meta:
#         model = CustomUser
#         fields = ["username", "email", "full_name", "employee_code", "password1", "password2"]

# # Timetable Upload Form
# class TimetableForm(forms.ModelForm):
#     class Meta:
#         model = Timetable
#         fields = ['uploaded_file']


# app/forms.py
# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from .models import CustomUser, TimetableUpload

# class SimpleRegistrationForm(UserCreationForm):
#     email = forms.EmailField(required=True)

#     class Meta:
#         model = CustomUser
#         fields = ('username', 'email', 'password1', 'password2')

#     def clean_username(self):
#         uname = self.cleaned_data['username']
#         # allow letters and spaces only (treat username as full name)
#         if not all(ch.isalpha() or ch.isspace() for ch in uname):
#             raise forms.ValidationError("Username must contain letters and spaces only.")
#         return uname


# class TimetableUploadForm(forms.ModelForm):
#     class Meta:
#         model = TimetableUpload
#         fields = ('uploaded_file',)

from django import forms
from django.contrib.auth.models import User
from .models import TimetableUpload

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("❌ Passwords do not match.")
        return cleaned_data
    

class TimetableUploadForm(forms.ModelForm):
    class Meta:
        model = TimetableUpload
        fields = ('uploaded_file',)

