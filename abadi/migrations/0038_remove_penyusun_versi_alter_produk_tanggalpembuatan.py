# Generated by Django 4.1.4 on 2024-09-03 03:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0037_alter_produk_tanggalpembuatan'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='penyusun',
            name='versi',
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 9, 3, 10, 27, 10, 349088)),
        ),
    ]
