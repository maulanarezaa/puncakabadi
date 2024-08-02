# Generated by Django 4.1.4 on 2024-08-01 07:03

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0003_alter_cachevalue_harga_alter_cachevalue_jumlah_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produk',
            name='TanggalPembuatan',
            field=models.DateField(default=datetime.datetime(2024, 8, 1, 14, 3, 14, 786594)),
        ),
        migrations.CreateModel(
            name='transaksicat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Tanggal', models.DateField()),
                ('SisaPengambilan', models.FloatField(default=0)),
                ('KodeProduk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.produk')),
            ],
        ),
    ]
