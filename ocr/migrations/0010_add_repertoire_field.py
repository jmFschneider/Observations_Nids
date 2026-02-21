# Generated manually for feature/ocr-repertoire-compteurs

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0009_remove_transcriptionocr_ocr_transcr_fiche_i_830756_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transcriptionocr',
            name='repertoire',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                help_text="Répertoire parent (dirname de chemin_image) pour agrégations par dossier",
                max_length=255,
                verbose_name="Répertoire de l'image",
            ),
        ),
        migrations.AddIndex(
            model_name='transcriptionocr',
            index=models.Index(
                fields=['statut', 'repertoire'],
                name='ocr_statut_repertoire_idx',
            ),
        ),
    ]
