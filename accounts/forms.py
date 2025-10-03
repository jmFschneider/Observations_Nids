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
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'est_valide', 'is_active')