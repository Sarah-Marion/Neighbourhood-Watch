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
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm your Password'

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        unique_together = ('email')

class LoginForm(AuthenticationForm):
    """
    classs that creates a Login form
    """
    username = forms.CharField(widget=TextInput(attrs={'class':'validate', 'placeholder':'Username'}))
    password = forms.CharField(widget=PasswordInput(attrs={'placeholder':'Password'}))


class ProfileUpdateForm(forms.ModelForm):
    """
    class that creates an update profile form
    """
    class Meta:
        model = User
        fields = ('email',)


class NewPostForm(forms.ModelForm):
    """
    classs that creates a new post form
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['news_details'].widget.attrs['placeholder'] = 'Update your hood mates'
        self.fields['news_footage'].widget.attrs['placeholder'] = ' Add footage'

    class Meta:
        model = News
        fields = ('news_details', 'news_footage',)


class HoodForm(forms.ModelForm):
    class Meta:
        model = Hood
        fields = ('hood_location', 'hood_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hood_name'] = forms.ChoiceField(
            choices=[]
        )
        self.fields['hood_name'].required = True


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ('business_name', 'business_email', 'business_category', 'business_description')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['business_name'].widget.attrs['placeholder'] = ' Business Name'
        self.fields['business_email'].widget.attrs['placeholder'] = ' Business Email'
        self.fields['business_description'].widget.attrs['placeholder'] = ' Short Business Description'


