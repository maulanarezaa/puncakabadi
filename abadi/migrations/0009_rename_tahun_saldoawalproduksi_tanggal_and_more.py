# Generated by Django 4.1.4 on 2024-08-07 13:24

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0008_saldoawalproduksi_alter_produk_tanggalpembuatan'),
    ]

    operations = [
        migrations.RenameField(
            model_name='saldoawalproduksi',
            old_name='tahun',
            new_name='Tanggal',
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 8, 7, 20, 24, 8, 675221)),
        ),
    ]
