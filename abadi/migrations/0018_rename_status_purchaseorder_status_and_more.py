# Generated by Django 4.1.4 on 2024-08-22 22:49

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0017_purchaseorder_alter_produk_tanggalpembuatan_detailpo'),
    ]

    operations = [
        migrations.RenameField(
            model_name='purchaseorder',
            old_name='status',
            new_name='Status',
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 8, 23, 5, 49, 51, 161309)),
        ),
    ]
