from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0019_alter_numero_personnel_charfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='age',
            field=models.CharField(
                blank=True,
                default='',
                help_text="Âge des poussins ou classe d'âge (ex: pullus, juvénile, 5j)",
                max_length=50,
            ),
        ),
    ]
