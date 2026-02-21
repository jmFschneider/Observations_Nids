# Data migration: populate repertoire from chemin_image (dirname)

import os

from django.db import migrations


def populate_repertoire(apps, schema_editor):
    TranscriptionOCR = apps.get_model('ocr', 'TranscriptionOCR')
    for row in TranscriptionOCR.objects.only('id', 'chemin_image').iterator(chunk_size=500):
        repertoire = os.path.dirname(row.chemin_image).replace('\\', '/') if row.chemin_image else ''
        TranscriptionOCR.objects.filter(pk=row.pk).update(repertoire=repertoire)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0010_add_repertoire_field'),
    ]

    operations = [
        migrations.RunPython(populate_repertoire, noop),
    ]
