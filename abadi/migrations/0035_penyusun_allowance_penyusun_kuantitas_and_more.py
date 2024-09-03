# Generated by Django 4.1.4 on 2024-09-03 02:18

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0034_rename_keterangan_versi_keterangan_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='penyusun',
            name='Allowance',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='penyusun',
            name='Kuantitas',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='penyusun',
            name='lastedited',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 9, 3, 9, 18, 8, 977584)),
        ),
    ]
