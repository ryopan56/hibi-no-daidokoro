from django import forms
from django.contrib.auth import get_user_model

from .models import NotificationSettings


User = get_user_model()


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['login_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login_id'].label = 'login_id'
        self.fields['login_id'].widget.attrs.update(
            {
                'placeholder': 'hino-kitchen',
                'autocomplete': 'username',
            }
        )
        self.fields['password1'].label = 'password'
        self.fields['password1'].widget.attrs.update(
            {
                'placeholder': '8文字以上を目安に入力',
                'autocomplete': 'new-password',
            }
        )
        self.fields['password2'].label = 'password_confirm'
        self.fields['password2'].widget.attrs.update(
            {
                'placeholder': 'もう一度入力',
                'autocomplete': 'new-password',
            }
        )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'パスワードが一致しません。')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    login_id = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login_id'].label = 'login_id'
        self.fields['login_id'].widget.attrs.update(
            {
                'placeholder': 'hino-kitchen',
                'autocomplete': 'username',
            }
        )
        self.fields['password'].label = 'password'
        self.fields['password'].widget.attrs.update(
            {
                'placeholder': '••••••••',
                'autocomplete': 'current-password',
            }
        )


class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = NotificationSettings
        fields = ['notifications_enabled', 'weekly_praise_enabled']
