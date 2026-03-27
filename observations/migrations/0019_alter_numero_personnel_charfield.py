from django.db import migrations, models


def int_vers_str(apps, schema_editor):
    """Convertit les valeurs entières existantes en chaînes."""
    FicheObservation = apps.get_model('observations', 'FicheObservation')
    for fiche in FicheObservation.objects.filter(numero_personnel_int__isnull=False):
        fiche.numero_personnel = str(fiche.numero_personnel_int)
        fiche.save(update_fields=['numero_personnel'])


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0018_split_nombre_poussins'),
    ]

    operations = [
        # Renommer temporairement l'ancien champ pour libérer le nom
        migrations.RenameField(
            model_name='ficheobservation',
            old_name='numero_personnel',
            new_name='numero_personnel_int',
        ),

        # Ajouter le nouveau champ CharField sous le nom définitif
        migrations.AddField(
            model_name='ficheobservation',
            name='numero_personnel',
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Numéro attribué par l'observateur (ex : A082)",
                max_length=20,
                null=True,
                verbose_name='Numéro personnel',
            ),
        ),

        # Migrer les données : int → str
        migrations.RunPython(
            int_vers_str,
            reverse_code=migrations.RunPython.noop,
        ),

        # Supprimer l'ancien champ entier
        migrations.RemoveField(
            model_name='ficheobservation',
            name='numero_personnel_int',
        ),
    ]
