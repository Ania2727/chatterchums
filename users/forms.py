from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'email'}), required=True
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'username'}), required=True
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'password'}), required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 're-enter password'}), required=True
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'password'})
    )

class UserProfileForm(forms.ModelForm):
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'maxlength': '500',
            'placeholder': 'Tell us about yourself...'
        }),
        max_length=500,
        required=False
    )

    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_pic', 'show_interests']  # додайте show_interests
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'show_interests': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'show_interests': 'Show my interests on my profile',
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
