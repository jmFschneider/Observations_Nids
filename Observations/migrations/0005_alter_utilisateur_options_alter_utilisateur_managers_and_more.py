import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models

def generate_unique_usernames(apps, schema_editor):
    Utilisateur = apps.get_model('Observations', 'Utilisateur')
    for utilisateur in Utilisateur.objects.all():
        base_username = f"{utilisateur.first_name.lower()}.{utilisateur.last_name.lower()}" if utilisateur.first_name and utilisateur.last_name else f"user{utilisateur.id}"
        unique_username = base_username
        counter = 1

        # Vérifier que le username est unique
        while Utilisateur.objects.filter(username=unique_username).exists():
            unique_username = f"{base_username}{counter}"
            counter += 1

        utilisateur.username = unique_username
        utilisateur.save()

class Migration(migrations.Migration):

    dependencies = [
        ('Observations', '0004_remove_observation_nom'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='utilisateur',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
        migrations.AlterModelManagers(
            name='utilisateur',
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.RemoveField(
            model_name='utilisateur',
            name='nom',
        ),
        migrations.RemoveField(
            model_name='utilisateur',
            name='prenom',
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='date_joined',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='first_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='first name'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='is_staff',
            field=models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='is_superuser',
            field=models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last login'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='last_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='last name'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='password',
            field=models.CharField(max_length=128, verbose_name='password'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username'),
        ),
        migrations.RunPython(generate_unique_usernames),  # Appliquer le script pour générer les usernames

        migrations.AlterField(
            model_name='utilisateur',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='email address'),
        ),
    ]
