# Generated by Django 4.1.4 on 2024-09-03 03:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0036_alter_penyusun_keterangan_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 9, 3, 10, 26, 59, 713621)),
        ),
    ]
