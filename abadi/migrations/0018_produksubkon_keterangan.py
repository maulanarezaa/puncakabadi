# Generated by Django 4.1.2 on 2024-03-30 03:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0017_alter_transaksiproduksi_detailspk'),
    ]

    operations = [
        migrations.AddField(
            model_name='produksubkon',
            name='keterangan',
            field=models.TextField(blank=True, null=True),
        ),
    ]
