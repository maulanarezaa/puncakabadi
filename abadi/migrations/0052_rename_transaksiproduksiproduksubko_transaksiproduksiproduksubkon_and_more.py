# Generated by Django 4.1.4 on 2024-09-28 03:23

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0051_alter_produk_tanggalpembuatan_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TransaksiProduksiProdukSubko',
            new_name='TransaksiProduksiProdukSubkon',
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 9, 28, 10, 23, 43, 365499)),
        ),
    ]