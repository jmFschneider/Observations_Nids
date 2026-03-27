from django.db import migrations, models
import django.core.validators


def migrer_poussins_vers_vol_t(apps, schema_editor):
    """Copie l'ancienne valeur nombre_poussins vers nombre_poussins_vol_t."""
    ResumeObservation = apps.get_model('observations', 'ResumeObservation')
    ResumeObservation.objects.filter(nombre_poussins__isnull=False).update(
        nombre_poussins_vol_t=models.F('nombre_poussins')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0017_add_note_correction'),
    ]

    operations = [
        # 1. Supprimer la contrainte qui référence l'ancien champ
        migrations.RemoveConstraint(
            model_name='resumeobservation',
            name='resume_poussins_le_eclos',
        ),

        # 2. Ajouter les 3 nouveaux champs
        migrations.AddField(
            model_name='resumeobservation',
            name='nombre_poussins_1_2',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resumeobservation',
            name='nombre_poussins_3_4',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resumeobservation',
            name='nombre_poussins_vol_t',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),

        # 3. Migrer les données existantes → vol_t
        migrations.RunPython(
            migrer_poussins_vers_vol_t,
            reverse_code=migrations.RunPython.noop,
        ),

        # 4. Supprimer l'ancien champ
        migrations.RemoveField(
            model_name='resumeobservation',
            name='nombre_poussins',
        ),

        # 5. Ajouter la nouvelle contrainte sur vol_t
        migrations.AddConstraint(
            model_name='resumeobservation',
            constraint=models.CheckConstraint(
                name='resume_poussins_vol_t_le_eclos',
                condition=(
                    models.Q(nombre_poussins_vol_t__isnull=True)
                    | models.Q(nombre_oeufs_eclos__isnull=True)
                    | models.Q(nombre_poussins_vol_t__lte=models.F('nombre_oeufs_eclos'))
                ),
            ),
        ),
    ]
