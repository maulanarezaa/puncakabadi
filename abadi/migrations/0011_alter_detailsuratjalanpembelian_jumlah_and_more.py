# Generated by Django 4.1.4 on 2024-08-08 07:09

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0010_alter_produk_tanggalpembuatan_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detailsuratjalanpembelian',
            name='Jumlah',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 8, 8, 14, 9, 41, 236301)),
        ),
    ]
