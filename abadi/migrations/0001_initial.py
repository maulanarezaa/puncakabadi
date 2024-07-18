# Generated by Django 4.1.4 on 2024-07-17 06:31

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Artikel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('KodeArtikel', models.CharField(max_length=20)),
                ('keterangan', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='BahanBakuSubkon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('KodeProduk', models.CharField(max_length=20)),
                ('NamaProduk', models.CharField(max_length=20)),
                ('unit', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='confirmationorder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NoCO', models.CharField(max_length=50)),
                ('kepada', models.CharField(max_length=100)),
                ('perihal', models.CharField(max_length=50)),
                ('tanggal', models.DateField()),
                ('StatusAktif', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='DetailSPK',
            fields=[
                ('IDDetailSPK', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('KodeArtikel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.artikel')),
            ],
        ),
        migrations.CreateModel(
            name='DetailSPKDisplay',
            fields=[
                ('IDDetailSPK', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Display',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('KodeDisplay', models.CharField(max_length=20)),
                ('keterangan', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Lokasi',
            fields=[
                ('IDLokasi', models.AutoField(primary_key=True, serialize=False)),
                ('NamaLokasi', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Produk',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('KodeProduk', models.CharField(max_length=20, unique=True)),
                ('NamaProduk', models.CharField(max_length=20)),
                ('unit', models.CharField(max_length=20)),
                ('TanggalPembuatan', models.DateField(default=datetime.datetime(2024, 7, 17, 13, 31, 32, 31690))),
                ('Jumlahminimal', models.IntegerField(default=0)),
                ('keteranganPurchasing', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('keteranganProduksi', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('keteranganGudang', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('keteranganRND', models.CharField(blank=True, default='', max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProdukSubkon',
            fields=[
                ('IDProdukSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('NamaProduk', models.CharField(max_length=255)),
                ('Unit', models.CharField(max_length=20)),
                ('keterangan', models.TextField(blank=True, null=True)),
                ('KodeArtikel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.artikel')),
            ],
        ),
        migrations.CreateModel(
            name='SPK',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NoSPK', models.CharField(max_length=255)),
                ('Tanggal', models.DateField()),
                ('Keterangan', models.CharField(max_length=255)),
                ('KeteranganACC', models.BooleanField()),
                ('StatusAktif', models.BooleanField(blank=True, default=True, null=True)),
                ('StatusDisplay', models.BooleanField(blank=True, default=False, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SPPB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NoSPPB', models.CharField(max_length=255)),
                ('Tanggal', models.DateField()),
                ('Keterangan', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SubkonKirim',
            fields=[
                ('IDSubkonKirim', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('Tanggal', models.DateField()),
                ('supplier', models.CharField(max_length=255)),
                ('PO', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SuratJalanPembelian',
            fields=[
                ('NoSuratJalan', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('Tanggal', models.DateField()),
                ('supplier', models.CharField(max_length=255)),
                ('PO', models.CharField(max_length=255)),
                ('NoInvoice', models.CharField(blank=True, max_length=255, null=True)),
                ('TanggalInvoice', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SuratJalanPenerimaanProdukSubkon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NoSuratJalan', models.CharField(max_length=255)),
                ('Tanggal', models.DateField()),
                ('NoInvoice', models.CharField(blank=True, max_length=255, null=True)),
                ('TanggalInvoice', models.DateField(blank=True, null=True)),
                ('Supplier', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SuratJalanPengirimanBahanBakuSubkon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NoSuratJalan', models.CharField(max_length=255)),
                ('Tanggal', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='transactionlog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=50)),
                ('waktu', models.DateTimeField()),
                ('jenis', models.CharField(max_length=50)),
                ('pesan', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='TransaksiSubkon',
            fields=[
                ('IDTransaksiProdukSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('Tanggal', models.DateField()),
                ('Jumlah', models.IntegerField()),
                ('KodeProduk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.produksubkon')),
            ],
        ),
        migrations.CreateModel(
            name='TransaksiProduksi',
            fields=[
                ('idTransaksiProduksi', models.AutoField(primary_key=True, serialize=False)),
                ('Tanggal', models.DateField()),
                ('Jumlah', models.IntegerField()),
                ('Keterangan', models.CharField(max_length=255)),
                ('Jenis', models.CharField(max_length=20)),
                ('DetailSPK', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.detailspk')),
                ('DetailSPKDisplay', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.detailspkdisplay')),
                ('KodeArtikel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.artikel')),
                ('KodeDisplay', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.display')),
                ('Lokasi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.lokasi')),
            ],
        ),
        migrations.CreateModel(
            name='TransaksiGudang',
            fields=[
                ('IDDetailTransaksiGudang', models.AutoField(primary_key=True, serialize=False)),
                ('keterangan', models.CharField(max_length=20)),
                ('jumlah', models.IntegerField()),
                ('tanggal', models.DateField()),
                ('KeteranganACC', models.BooleanField()),
                ('DetailSPK', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.detailspk')),
                ('DetailSPKDisplay', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.detailspkdisplay')),
                ('KodeProduk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.produk')),
                ('Lokasi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.lokasi')),
            ],
        ),
        migrations.CreateModel(
            name='TransaksiBahanBakuSubkon',
            fields=[
                ('IDTransaksiBahanBakuSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('Tanggal', models.DateField()),
                ('Keterangan', models.CharField(max_length=225)),
                ('Jumlah', models.IntegerField(default=0)),
                ('KodeBahanBaku', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.bahanbakusubkon')),
            ],
        ),
        migrations.CreateModel(
            name='SaldoAwalSubkon',
            fields=[
                ('IDSaldoAwalProdukSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('Tanggal', models.DateField()),
                ('IDProdukSubkon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.produksubkon')),
            ],
        ),
        migrations.CreateModel(
            name='SaldoAwalBahanBakuSubkon',
            fields=[
                ('IDSaldoAwalBahanBakuSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('Tanggal', models.DateField()),
                ('IDBahanBakuSubkon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.bahanbakusubkon')),
            ],
        ),
        migrations.CreateModel(
            name='SaldoAwalBahanBaku',
            fields=[
                ('IDSaldoAwalBahanBaku', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('Harga', models.FloatField()),
                ('Tanggal', models.DateField(blank=True, null=True)),
                ('IDBahanBaku', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.produk')),
                ('IDLokasi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.lokasi')),
            ],
        ),
        migrations.CreateModel(
            name='SaldoAwalArtikel',
            fields=[
                ('IDSaldoAwalBahanBaku', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('Tanggal', models.DateField(blank=True, null=True)),
                ('IDArtikel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.artikel')),
                ('IDLokasi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.lokasi')),
            ],
        ),
        migrations.CreateModel(
            name='Penyusun',
            fields=[
                ('IDKodePenyusun', models.AutoField(primary_key=True, serialize=False)),
                ('Status', models.BooleanField()),
                ('versi', models.DateField(blank=True, null=True)),
                ('keterangan', models.CharField(default='', max_length=255)),
                ('KodeArtikel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.artikel')),
                ('KodeProduk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.produk')),
                ('Lokasi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.lokasi')),
            ],
        ),
        migrations.CreateModel(
            name='Penyesuaian',
            fields=[
                ('IDPenyesuaian', models.AutoField(primary_key=True, serialize=False)),
                ('TanggalMulai', models.DateField()),
                ('TanggalMinus', models.DateField(blank=True, null=True)),
                ('konversi', models.FloatField(blank=True, null=True)),
                ('KodeArtikel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.artikel')),
                ('KodeProduk', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.produk')),
                ('lokasi', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='abadi.lokasi')),
            ],
        ),
        migrations.CreateModel(
            name='PemusnahanBahanBaku',
            fields=[
                ('IDPemusnahanBahanBaku', models.AutoField(primary_key=True, serialize=False)),
                ('Tanggal', models.DateField()),
                ('Jumlah', models.FloatField()),
                ('Keterangan', models.CharField(blank=True, max_length=255, null=True)),
                ('KodeBahanBaku', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.produk')),
                ('lokasi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.lokasi')),
            ],
        ),
        migrations.CreateModel(
            name='PemusnahanArtikel',
            fields=[
                ('IDPemusnahanArtikel', models.AutoField(primary_key=True, serialize=False)),
                ('Tanggal', models.DateField()),
                ('Jumlah', models.IntegerField()),
                ('Keterangan', models.CharField(blank=True, max_length=255, null=True)),
                ('KodeArtikel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.artikel')),
                ('lokasi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.lokasi')),
            ],
        ),
        migrations.CreateModel(
            name='KonversiMaster',
            fields=[
                ('IDKodeKonversiMaster', models.AutoField(primary_key=True, serialize=False)),
                ('Kuantitas', models.FloatField()),
                ('Allowance', models.FloatField(default=0)),
                ('lastedited', models.DateTimeField(blank=True, null=True)),
                ('KodePenyusun', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.penyusun')),
            ],
        ),
        migrations.CreateModel(
            name='DetailSuratJalanPengirimanBahanBakuSubkon',
            fields=[
                ('IDDetailSJPengirimanSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('Keterangan', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('KodeBahanBaku', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.bahanbakusubkon')),
                ('NoSuratJalan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.suratjalanpengirimanbahanbakusubkon')),
            ],
        ),
        migrations.CreateModel(
            name='DetailSuratJalanPenerimaanProdukSubkon',
            fields=[
                ('IDDetailSJPenerimaanSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('Keterangan', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('Harga', models.FloatField(default=0)),
                ('KeteranganACC', models.BooleanField(default=False)),
                ('KodeProduk', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.produksubkon')),
                ('NoSuratJalan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.suratjalanpenerimaanproduksubkon')),
            ],
        ),
        migrations.CreateModel(
            name='DetailSuratJalanPembelian',
            fields=[
                ('IDDetailSJPembelian', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('KeteranganACC', models.BooleanField()),
                ('Harga', models.FloatField()),
                ('HargaDollar', models.FloatField(default=0)),
                ('KodeProduk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.produk')),
                ('NoSuratJalan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.suratjalanpembelian')),
            ],
        ),
        migrations.CreateModel(
            name='DetailSubkonKirim',
            fields=[
                ('IDDetailSubkonKirim', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('KeteranganACC', models.BooleanField()),
                ('Harga', models.FloatField()),
                ('IDSubkonKirim', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.subkonkirim')),
                ('KodeProduk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.produk')),
            ],
        ),
        migrations.CreateModel(
            name='DetailSPPB',
            fields=[
                ('IDDetailSPPB', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('DetailBahan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.produk')),
                ('DetailSPK', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.detailspk')),
                ('DetailSPKDisplay', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.detailspkdisplay')),
                ('IDCO', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='abadi.confirmationorder')),
                ('NoSPPB', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.sppb')),
            ],
        ),
        migrations.AddField(
            model_name='detailspkdisplay',
            name='KodeDisplay',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.display'),
        ),
        migrations.AddField(
            model_name='detailspkdisplay',
            name='NoSPK',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.spk'),
        ),
        migrations.AddField(
            model_name='detailspk',
            name='NoSPK',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.spk'),
        ),
        migrations.CreateModel(
            name='detailconfirmationorder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deskripsi', models.CharField(max_length=200)),
                ('kuantitas', models.IntegerField()),
                ('Harga', models.FloatField()),
                ('Artikel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.artikel')),
                ('Display', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='abadi.display')),
                ('confirmationorder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.confirmationorder')),
            ],
        ),
    ]
