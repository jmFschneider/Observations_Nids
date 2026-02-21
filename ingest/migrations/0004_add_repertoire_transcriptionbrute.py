# Migration manuelle : champ repertoire pour agrégations par répertoire (ingest)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0003_espececandidate_code_gonm_transcrit'),
    ]

    operations = [
        migrations.AddField(
            model_name='transcriptionbrute',
            name='repertoire',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                help_text="Chemin relatif sous transcription_results/ pour agrégations par dossier",
                max_length=255,
                verbose_name="Répertoire du fichier",
            ),
        ),
    ]
