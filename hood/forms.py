from django import forms
from .models import Hood, Location, Business, News
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms.widgets import TextInput, PasswordInput


class SignUpForm(UserCreationForm):
    """
    Class that creates a Sign up form
    """
    email = forms.EmailField(max_length=250)

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = ' Username'
        self.fields['email'].widget.attrs['placeholder'] = ' Email'
        self.fields['1st_password'].widget.attrs['placeholder'] = 'Password'
        self.fields['2nd_password'].widget.attrs['placeholder'] = 'Confirm your Password'

    class Meta:
        model = User
        fields = ('username', 'email', '1st_password', '2nd_password')
        unique_together = ('email',)

class LoginForm(AuthenticationForm):
    """
    classs that creates a Login form
    """
    username = forms.CharField(widget=TextInput(attrs={'class':'validate', 'placeholder':'Username'}))
    password = forms.CharField(widget=PasswordInput(attrs={'placeholder':'Password'}))


class ProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('email',)

