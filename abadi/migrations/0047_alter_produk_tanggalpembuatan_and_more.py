# Generated by Django 4.1.4 on 2024-09-23 14:39

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0046_artikel_is_deleted_bahanbakusubkon_is_deleted_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 9, 23, 21, 39, 20, 890784)),
        ),
        migrations.DeleteModel(
            name='DetailSuratJalanPembelian',
        ),
        migrations.DeleteModel(
            name='SuratJalanPembelian',
        ),
    ]