# Generated by Django 4.1.4 on 2024-06-30 04:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0053_detailsuratjalanpenerimaanproduksubkon_noinvoice_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='detailsuratjalanpenerimaanproduksubkon',
            name='NoInvoice',
        ),
        migrations.RemoveField(
            model_name='detailsuratjalanpenerimaanproduksubkon',
            name='TanggalInvoice',
        ),
    ]
