# Generated by Django 4.1.4 on 2024-05-12 03:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0037_alter_transaksiproduksi_kodeartikel'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaksiproduksi',
            name='DetailSPKDisplay',
        ),
        migrations.AddField(
            model_name='transaksiproduksi',
            name='DetailSPPBDisplay',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.detailsppb'),
        ),
    ]
