# Generated by Django 4.1.4 on 2024-09-04 08:44

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0039_transaksiproduksi_versiartikel_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pemusnahanartikel',
            name='VersiArtikel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.versi'),
        ),
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 9, 4, 15, 44, 57, 259683)),
        ),
    ]
