# Generated by Django 4.1.4 on 2024-09-20 01:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0044_transaksisubkon_keterangan_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='produk',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 9, 20, 8, 43, 12, 217797)),
        ),
    ]
