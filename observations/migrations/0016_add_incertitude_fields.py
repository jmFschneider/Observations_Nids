# Generated manually for incertitude feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0015_alter_historiqueverrouillage_motif_liberation'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='nombre_oeufs_incertain',
            field=models.BooleanField(
                default=False,
                verbose_name="Estimation incertaine (œufs)",
                help_text="Cocher si le nombre d'œufs est une estimation approximative"
            ),
        ),
        migrations.AddField(
            model_name='observation',
            name='nombre_poussins_incertain',
            field=models.BooleanField(
                default=False,
                verbose_name="Estimation incertaine (poussins)",
                help_text="Cocher si le nombre de poussins est une estimation approximative"
            ),
        ),
    ]
