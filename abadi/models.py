from django.db import models
import datetime


# Create your models here.
class Produk(models.Model):
    KodeProduk = models.CharField(max_length=20, primary_key=True)
    NamaProduk = models.CharField(max_length=20)
    unit = models.CharField(max_length=20)
    TanggalPembuatan = models.DateField(auto_now_add=True)
    Jumlahminimal = models.IntegerField(default=0)
    keteranganPurchasing = models.CharField(
        max_length=255, null=True, blank=True, default=""
    )
    keteranganProduksi = models.CharField(
        max_length=255, null=True, blank=True, default=""
    )
    keteranganGudang = models.CharField(
        max_length=255, null=True, blank=True, default=""
    )
    keteranganRND = models.CharField(max_length=255, null=True, blank=True, default="")

    def __str__(self):
        return str(self.KodeProduk)


class Artikel(models.Model):
    KodeArtikel = models.CharField(max_length=20)
    keterangan = models.CharField(max_length=255)

    def __str__(self):
        return str(self.KodeArtikel)


class Display(models.Model):
    KodeDisplay = models.CharField(max_length=20)
    keterangan = models.CharField(max_length=255)

    def __str__(self):
        return str(self.KodeDisplay)


class ProdukSubkon(models.Model):
    IDProdukSubkon = models.AutoField(primary_key=True)
    NamaProduk = models.CharField(max_length=255)
    Unit = models.CharField(max_length=20)
    KodeArtikel = models.ForeignKey(Artikel, on_delete=models.CASCADE)
    keterangan = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.NamaProduk)


class Lokasi(models.Model):
    IDLokasi = models.AutoField(primary_key=True)
    NamaLokasi = models.CharField(max_length=20)

    def __str__(self):
        return str(self.NamaLokasi)


class SuratJalanPembelian(models.Model):
    NoSuratJalan = models.CharField(max_length=255, primary_key=True)
    Tanggal = models.DateField()
    supplier = models.CharField(max_length=255)
    PO = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.NoSuratJalan} - {self.Tanggal}"


class DetailSuratJalanPembelian(models.Model):
    IDDetailSJPembelian = models.AutoField(primary_key=True)
    NoSuratJalan = models.ForeignKey(SuratJalanPembelian, on_delete=models.CASCADE)
    KodeProduk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()
    KeteranganACC = models.BooleanField()
    Harga = models.FloatField()

    def __str__(self):
        return str(self.NoSuratJalan) + " " + str(self.KodeProduk)


class SPK(models.Model):
    NoSPK = models.CharField(max_length=255)
    Tanggal = models.DateField()
    Keterangan = models.CharField(max_length=255)
    KeteranganACC = models.BooleanField()
    StatusAktif = models.BooleanField(default=True, null=True, blank=True)
    StatusDisplay = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return str(self.NoSPK)


class DetailSPK(models.Model):
    IDDetailSPK = models.AutoField(primary_key=True)
    NoSPK = models.ForeignKey(SPK, on_delete=models.CASCADE)
    KodeArtikel = models.ForeignKey(Artikel, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()

    def __str__(self):
        return str(self.NoSPK) + " " + str(self.KodeArtikel)


class DetailSPKDisplay(models.Model):
    IDDetailSPK = models.AutoField(primary_key=True)
    NoSPK = models.ForeignKey(SPK, on_delete=models.CASCADE)
    KodeDisplay = models.ForeignKey(Display, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()

    def __str__(self):
        return str(self.NoSPK) + " " + str(self.KodeDisplay)


class TransaksiGudang(models.Model):
    IDDetailTransaksiGudang = models.AutoField(primary_key=True)
    KodeProduk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    keterangan = models.CharField(max_length=20)
    jumlah = models.IntegerField()
    tanggal = models.DateField()
    KeteranganACC = models.BooleanField()
    Lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    DetailSPK = models.ForeignKey(
        DetailSPK, on_delete=models.CASCADE, null=True, blank=True
    )
    DetailSPKDisplay = models.ForeignKey(
        DetailSPKDisplay, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.tanggal} - {self.KodeProduk}"


class Penyusun(models.Model):
    IDKodePenyusun = models.AutoField(primary_key=True)
    KodeProduk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    KodeArtikel = models.ForeignKey(Artikel, on_delete=models.CASCADE)
    Status = models.BooleanField()
    Lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    versi = models.DateField(null=True, blank=True)
    keterangan = models.CharField(max_length=255, default="")

    def __str__(self):
        return (
            str(self.KodeArtikel)
            + " - "
            + str(self.KodeProduk)
            + " - "
            + str(self.versi)
        )


class KonversiMaster(models.Model):
    IDKodeKonversiMaster = models.AutoField(primary_key=True)
    KodePenyusun = models.ForeignKey(Penyusun, on_delete=models.CASCADE)
    Kuantitas = models.FloatField()
    lastedited = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.KodePenyusun)


class Penyesuaian(models.Model):
    IDPenyesuaian = models.AutoField(primary_key=True)
    KodePenyusun = models.ForeignKey(Penyusun, on_delete=models.CASCADE)
    TanggalMulai = models.DateField()
    TanggalMinus = models.DateField(null=True, blank=True)

    konversi = models.FloatField(blank=True, null=True)

    def __str__(self):
        return str(self.KodePenyusun)


class SPPB(models.Model):
    NoSPPB = models.CharField(max_length=255)
    Tanggal = models.DateField()
    Keterangan = models.CharField(max_length=255)

    def __str__(self):
        return str(self.NoSPPB)


class confirmationorder(models.Model):
    NoCO = models.CharField(max_length=50)
    kepada = models.CharField(max_length=100)
    perihal = models.CharField(max_length=50)
    tanggal = models.DateField()
    StatusAktif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.NoCO} - {self.tanggal} - {self.StatusAktif}"


class DetailSPPB(models.Model):
    IDDetailSPPB = models.AutoField(primary_key=True)
    NoSPPB = models.ForeignKey(SPPB, on_delete=models.CASCADE)
    DetailSPK = models.ForeignKey(
        DetailSPK, on_delete=models.CASCADE, null=True, blank=True
    )
    DetailSPKDisplay = models.ForeignKey(
        DetailSPKDisplay, on_delete=models.CASCADE, null=True, blank=True
    )
    Jumlah = models.IntegerField()
    IDCO = models.ForeignKey(
        confirmationorder, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.IDDetailSPPB} - {self.NoSPPB} - {self.NoSPPB.Tanggal} - {self.DetailSPK} - {self.Jumlah}"


class TransaksiProduksi(models.Model):
    idTransaksiProduksi = models.AutoField(primary_key=True)
    KodeArtikel = models.ForeignKey(Artikel, on_delete=models.CASCADE, null=True)
    Lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Tanggal = models.DateField()
    Jumlah = models.IntegerField()
    Keterangan = models.CharField(max_length=255)
    Jenis = models.CharField(max_length=20)
    DetailSPK = models.ForeignKey(
        DetailSPK, on_delete=models.CASCADE, null=True, blank=True
    )
    DetailSPPBDisplay = models.ForeignKey(
        DetailSPPB, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        if self.KodeArtikel is not None:
            return f"{self.Jenis} - {self.KodeArtikel.KodeArtikel} - {self.Lokasi} - {self.Tanggal} - {self.Jumlah}"
        else:
            return f"{self.Jenis} - {self.DetailSPPBDisplay.DetailSPKDisplay.KodeDisplay} - {self.Lokasi} - {self.Tanggal} - {self.Jumlah}"


class SaldoAwalBahanBaku(models.Model):
    IDSaldoAwalBahanBaku = models.AutoField(primary_key=True)
    IDBahanBaku = models.ForeignKey(Produk, on_delete=models.CASCADE)
    IDLokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()
    Harga = models.FloatField()
    Tanggal = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.IDLokasi} - {self.IDBahanBaku}- {self.Tanggal}"


class SaldoAwalArtikel(models.Model):
    IDSaldoAwalBahanBaku = models.AutoField(primary_key=True)
    IDArtikel = models.ForeignKey(Artikel, on_delete=models.CASCADE)
    IDLokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()
    Tanggal = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.IDLokasi} - {self.IDArtikel} - {self.Tanggal}"


class SaldoAwalSubkon(models.Model):
    IDSaldoAwalProdukSubkon = models.AutoField(primary_key=True)
    IDProdukSubkon = models.ForeignKey(ProdukSubkon, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()
    Tanggal = models.DateField()

    def __str__(self):
        return str(self.IDProdukSubkon.NamaProduk)


class PemusnahanArtikel(models.Model):
    IDPemusnahanArtikel = models.AutoField(primary_key=True)
    Tanggal = models.DateField()
    KodeArtikel = models.ForeignKey(Artikel, on_delete=models.CASCADE)
    lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()

    def __str__(self):
        return str(self.KodeArtikel) + "-" + str(self.Tanggal)


class PemusnahanBahanBaku(models.Model):
    IDPemusnahanBahanBaku = models.AutoField(primary_key=True)
    Tanggal = models.DateField()
    KodeBahanBaku = models.ForeignKey(Produk, on_delete=models.CASCADE)
    lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()

    def __str__(self):
        return str(self.KodeBahanBaku) + "-" + str(self.Tanggal)


class transactionlog(models.Model):
    user = models.CharField(max_length=50)
    waktu = models.DateTimeField()
    jenis = models.CharField(max_length=50)
    pesan = models.TextField()

    def __str__(self):
        return str(f"{self.user} - {self.waktu} - {self.jenis}")


class detailconfirmationorder(models.Model):
    confirmationorder = models.ForeignKey(confirmationorder, on_delete=models.CASCADE)
    Artikel = models.ForeignKey(Artikel, on_delete=models.CASCADE)
    deskripsi = models.CharField(max_length=200)
    kuantitas = models.IntegerField()
    Harga = models.FloatField()


class SubkonKirim(models.Model):
    IDSubkonKirim = models.CharField(max_length=255, primary_key=True)
    Tanggal = models.DateField()
    supplier = models.CharField(max_length=255)
    PO = models.CharField(max_length=255)

    def __str__(self):
        return str(str(self.IDSubkonKirim))


class DetailSubkonKirim(models.Model):
    IDDetailSubkonKirim = models.AutoField(primary_key=True)
    IDSubkonKirim = models.ForeignKey(SubkonKirim, on_delete=models.CASCADE)
    KodeProduk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()
    KeteranganACC = models.BooleanField()
    Harga = models.FloatField()

    def __str__(self):
        return str(self.IDSubkonKirim) + " " + str(self.KodeProduk)


class BahanBakuSubkon(models.Model):
    KodeProduk = models.CharField(max_length=20)
    NamaProduk = models.CharField(max_length=20)
    unit = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.KodeProduk} - {self.NamaProduk}"


""" SECTION SUBKON """


# Untuk Masuk Transaksi Bahan Baku Subkon
class TransaksiBahanBakuSubkon(models.Model):
    IDTransaksiBahanBakuSubkon = models.AutoField(primary_key=True)
    KodeBahanBaku = models.ForeignKey(BahanBakuSubkon, on_delete=models.CASCADE)
    Tanggal = models.DateField()
    Keterangan = models.CharField(max_length=225)
    Jumlah = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.tanggal} - {self.KodeBahanBaku}"


# Untuk Surat Jalan Pengriman dari Perusahaan ke vendor Subkon
class SuratJalanPengirimanBahanBakuSubkon(models.Model):
    NoSuratJalan = models.CharField(max_length=255)
    Tanggal = models.DateField()

    def __str__(self):
        return f"{self.NoSuratJalan} - {self.Tanggal}"


class DetailSuratJalanPengirimanBahanBakuSubkon(models.Model):
    IDDetailSJPengirimanSubkon = models.AutoField(primary_key=True)
    NoSuratJalan = models.ForeignKey(
        SuratJalanPengirimanBahanBakuSubkon, on_delete=models.CASCADE
    )
    KodeBahanBaku = models.ForeignKey(
        BahanBakuSubkon, on_delete=models.CASCADE, null=True
    )
    Jumlah = models.IntegerField()
    Keterangan = models.CharField(max_length=255, null=True, blank=True, default="")

    def __str__(self):
        return f"{self.NoSuratJalan} - {self.KodeDisplay} - {self.Jumlah}"


# Untuk Surat Jalan Penerimaan Produk Subkon
class SuratJalanPenerimaanProdukSubkon(models.Model):
    NoSuratJalan = models.CharField(max_length=255)
    Tanggal = models.DateField()

    def __str__(self):
        return f"{self.NoSuratJalan} - {self.Tanggal}"


class DetailSuratJalanPenerimaanProdukSubkon(models.Model):
    IDDetailSJPengirimanSubkon = models.AutoField(primary_key=True)
    NoSuratJalan = models.ForeignKey(
        SuratJalanPenerimaanProdukSubkon, on_delete=models.CASCADE
    )
    KodeProduk = models.ForeignKey(ProdukSubkon, on_delete=models.CASCADE, null=True)
    Jumlah = models.IntegerField()
    Keterangan = models.CharField(max_length=255, null=True, blank=True, default="")

    def __str__(self):
        return f"{self.NoSuratJalan} - {self.KodeDisplay} - {self.Jumlah}"


# Untuk Transaksi Keluar Produk SUBKON ke area Produksi
class TransaksiSubkon(models.Model):
    IDTransaksiProdukSubkon = models.AutoField(primary_key=True)
    KodeProduk = models.ForeignKey(ProdukSubkon, on_delete=models.CASCADE)
    Tanggal = models.DateField()
    Jumlah = models.IntegerField()

    def __str__(self):
        return str(self.IDProdukSubkon.NamaProduk) + "-" + str(self.Tanggal)
    

class SaldoAwalBahanBakuSubkon(models.Model):
    IDSaldoAwalBahanBakuSubkon = models.AutoField(primary_key=True)
    IDBahanBakuSubkon = models.ForeignKey(BahanBakuSubkon, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()
    Tanggal = models.DateField()

    def __str__(self):
        return str(self.IDBahanBakuSubkon.NamaProduk)
