# Generated by Django 4.1.4 on 2024-09-03 02:03

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0033_alter_produk_tanggalpembuatan_alter_versi_keterangan'),
    ]

    operations = [
        migrations.RenameField(
            model_name='versi',
            old_name='keterangan',
            new_name='Keterangan',
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 9, 3, 9, 3, 6, 355189)),
        ),
    ]
