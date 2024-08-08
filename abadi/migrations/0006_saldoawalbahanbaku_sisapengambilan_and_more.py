# Generated by Django 4.1.4 on 2024-08-02 01:53

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0005_alter_produk_tanggalpembuatan'),
    ]

    operations = [
        migrations.AddField(
            model_name='saldoawalbahanbaku',
            name='SisaPengambilan',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 8, 2, 8, 53, 31, 253521)),
        ),
    ]