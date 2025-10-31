from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Utilisateur


class UtilisateurCreationForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'first_name', 'last_name', 'est_valide')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'observateur'
        user.est_valide = False
        user.status = 'pending'
        if commit:
            user.save()
        return user


class UtilisateurChangeForm(UserChangeForm):
    class Meta:
        model = Utilisateur
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'est_valide',
            'est_transcription',
            'is_active',
        )


class MotDePasseOublieForm(forms.Form):
    """Formulaire pour demander une réinitialisation de mot de passe"""

    email = forms.EmailField(
        label="Adresse email",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'votre.email@exemple.com',
                'autofocus': True,
            }
        ),
    )


class NouveauMotDePasseForm(forms.Form):
    """Formulaire pour définir un nouveau mot de passe"""

    password1 = forms.CharField(
        label="Nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text="Minimum 8 caractères, lettres et chiffres recommandés",
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        return password2

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password and len(password) < 8:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        return password
