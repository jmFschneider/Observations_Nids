# Administration/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Utilisateur


class UtilisateurCreationForm(UserCreationForm):
    """Formulaire de création d'utilisateur personnalisé"""

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
    """Formulaire de modification d'utilisateur personnalisé"""

    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'est_valide', 'is_active')
