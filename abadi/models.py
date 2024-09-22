from django.db import models
import datetime


# Create your models here.
class ProdukQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)
    def deleted(self):
        return self.filter(is_deleted=True)

class ProdukManager(models.Manager):
    def get_queryset(self):
        return ProdukQuerySet(self.model, using=self._db).active()
    def with_deleted(self):
        return ProdukQuerySet(self.model, using=self._db)  # Mengembalikan semua (termasuk yang dihapus)
    def isdeleted(self):
        return ProdukQuerySet(self.model, using=self._db).deleted()  # Khusus untuk produk yang di-soft delete
    
class ArtikelQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)
    def deleted(self):
        return self.filter(is_deleted=True)

class ArtikelManager(models.Manager):
    def get_queryset(self):
        return ArtikelQuerySet(self.model, using=self._db).active()
    def with_deleted(self):
        return ArtikelQuerySet(self.model, using=self._db)  # Mengembalikan semua (termasuk yang dihapus)
    def isdeleted(self):
        return ArtikelQuerySet(self.model, using=self._db).deleted()  # Khusus untuk produk yang di-soft delete
    
class DisplayQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)
    def deleted(self):
        return self.filter(is_deleted=True)

class DisplayManager(models.Manager):
    def get_queryset(self):
        return DisplayQuerySet(self.model, using=self._db).active()
    def with_deleted(self):
        return DisplayQuerySet(self.model, using=self._db)  # Mengembalikan semua (termasuk yang dihapus)
    def isdeleted(self):
        return DisplayQuerySet(self.model, using=self._db).deleted()  # Khusus untuk produk yang di-soft delete
    
class BahanBakuSubkonQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)
    def deleted(self):
        return self.filter(is_deleted=True)

class BahanBakuSubkonManager(models.Manager):
    def get_queryset(self):
        return BahanBakuSubkonQuerySet(self.model, using=self._db).active()
    def with_deleted(self):
        return BahanBakuSubkonQuerySet(self.model, using=self._db)  # Mengembalikan semua (termasuk yang dihapus)
    def isdeleted(self):
        return BahanBakuSubkonQuerySet(self.model, using=self._db).deleted()  # Khusus untuk produk yang di-soft delete
    
class ProdukSubkonQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)
    def deleted(self):
        return self.filter(is_deleted=True)

class ProdukSubkonManager(models.Manager):
    def get_queryset(self):
        return ProdukSubkonQuerySet(self.model, using=self._db).active()
    def with_deleted(self):
        return ProdukSubkonQuerySet(self.model, using=self._db)  # Mengembalikan semua (termasuk yang dihapus)
    def isdeleted(self):
        return ProdukSubkonQuerySet(self.model, using=self._db).deleted()  # Khusus untuk produk yang di-soft delete
    
class Produk(models.Model):
    id = models.AutoField(primary_key=True)
    KodeProduk = models.CharField(max_length=20,unique=True)
    NamaProduk = models.CharField(max_length=20)
    unit = models.CharField(max_length=20)
    TanggalPembuatan = models.DateField(default=datetime.datetime.now())
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
    is_deleted = models.BooleanField(default=False)
    objects = ProdukManager()

    def __str__(self):
        return str(self.KodeProduk)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()


class Artikel(models.Model):
    KodeArtikel = models.CharField(max_length=20)
    keterangan = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    objects = ArtikelManager()

    def __str__(self):
        return str(self.KodeArtikel)
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()


class Display(models.Model):
    KodeDisplay = models.CharField(max_length=20)
    keterangan = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    objects = DisplayManager()

    def __str__(self):
        return str(self.KodeDisplay)
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

class BahanBakuSubkon(models.Model):
    KodeProduk = models.CharField(max_length=20)
    NamaProduk = models.CharField(max_length=20)
    unit = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)
    objects = BahanBakuSubkonManager()

    def __str__(self):
        return f"{self.KodeProduk} - {self.NamaProduk}"
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()


class ProdukSubkon(models.Model):
    IDProdukSubkon = models.AutoField(primary_key=True)
    NamaProduk = models.CharField(max_length=255)
    Unit = models.CharField(max_length=20)
    KodeArtikel = models.ForeignKey(Artikel, on_delete=models.CASCADE)
    keterangan = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    objects = ProdukSubkonManager()


    def __str__(self):
        return str(self.NamaProduk)
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()


class Lokasi(models.Model):
    IDLokasi = models.AutoField(primary_key=True)
    NamaLokasi = models.CharField(max_length=20)

    def __str__(self):
        return str(self.NamaLokasi)
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

class PurchaseOrder(models.Model):
    KodePO = models.CharField(max_length=100, unique=True)
    Tanggal = models.DateField()
    Status = models.BooleanField()

    def __str__(self):
        return f"{self.KodePO} - {self.Tanggal}"

class DetailPO(models.Model):
    KodePO = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    KodeProduk = models.ForeignKey(Produk,on_delete=models.CASCADE)
    Jumlah = models.FloatField()

    def __str__(self):
        return f"{self.KodePO} - {self.KodeProduk} - {self.Jumlah}"



class SuratJalanPembelian(models.Model):
    NoSuratJalan = models.CharField(max_length=255, primary_key=True)
    Tanggal = models.DateField()
    supplier = models.CharField(max_length=255)
    NoInvoice = models.CharField(max_length=255,null=True,blank=True)
    TanggalInvoice = models.DateField(blank=True,null=True)

    def __str__(self):
        return f"{self.NoSuratJalan} - {self.Tanggal}"


class DetailSuratJalanPembelian(models.Model):
    IDDetailSJPembelian = models.AutoField(primary_key=True)
    NoSuratJalan = models.ForeignKey(SuratJalanPembelian, on_delete=models.CASCADE)
    KodeProduk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    Jumlah = models.FloatField()
    KeteranganACC = models.BooleanField()
    Harga = models.FloatField()
    HargaDollar = models.FloatField(default=0)
    PPN = models.BooleanField(default=True)
    PO = models.ForeignKey(DetailPO,on_delete=models.SET_NULL,blank=True,null=True)
    hargappn = models.FloatField(default=0)
    


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
    jumlah = models.FloatField()
    tanggal = models.DateField()
    KeteranganACC = models.BooleanField()
    KeteranganACCPurchasing = models.BooleanField()
    Lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    DetailSPK = models.ForeignKey(
        DetailSPK, on_delete=models.CASCADE, null=True, blank=True
    )
    DetailSPKDisplay = models.ForeignKey(
        DetailSPKDisplay, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.tanggal} - {self.KodeProduk}"

class Versi(models.Model):
    KodeArtikel = models.ForeignKey(Artikel,on_delete=models.CASCADE)
    Versi = models.CharField(max_length=50)
    Tanggal = models.DateField()
    Keterangan = models.TextField(null=True,blank=True)
    isdefault = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.KodeArtikel} - {self.Versi} - {self.Keterangan} - {self.isdefault}'


class Penyusun(models.Model):
    IDKodePenyusun = models.AutoField(primary_key=True)
    KodeProduk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    KodeArtikel = models.ForeignKey(Artikel, on_delete=models.CASCADE)
    Status = models.BooleanField()
    Lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    keterangan = models.CharField(max_length=255, default="",null=True,blank=True)
    KodeVersi = models.ForeignKey(Versi,on_delete=models.CASCADE,null=True,blank=True)
    Kuantitas = models.FloatField(default=0)
    Allowance = models.FloatField(default=0)
    lastedited = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            str(self.KodeArtikel)
            + " - "
            + str(self.KodeProduk)
            + " - "
            + str(self.KodeVersi)
        )


class Penyesuaian(models.Model):
    IDPenyesuaian = models.AutoField(primary_key=True)
    KodeProduk = models.ForeignKey(Produk,on_delete=models.CASCADE,null=True,blank=True)
    KodeArtikel = models.ForeignKey(Artikel,on_delete=models.CASCADE,null=True,blank=True)
    TanggalMulai = models.DateField()
    TanggalMinus = models.DateField(null=True, blank=True)
    konversi = models.FloatField()
    lokasi = models.ForeignKey(Lokasi,on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f"{self.KodeArtikel} {self.KodeProduk} {self.TanggalMulai} - {self.TanggalMinus}"
    
class PenyesuaianArtikel(models.Model):
    IDPenyesuaian = models.AutoField(primary_key=True)
    KodeArtikel = models.ForeignKey(Artikel,on_delete=models.CASCADE,null=True,blank=True)
    TanggalMulai = models.DateField()
    TanggalMinus = models.DateField(null=True, blank=True)
    konversi = models.FloatField()
    lokasi = models.ForeignKey(Lokasi,on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f"{self.KodeArtikel} {self.TanggalMulai} - {self.TanggalMinus}"


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
    DetailBahan = models.ForeignKey(Produk, on_delete=models.CASCADE, null=True, blank=True)

    DetailSPKDisplay = models.ForeignKey(
        DetailSPKDisplay, on_delete=models.CASCADE, null=True, blank=True
    )
    Jumlah = models.IntegerField()
    IDCO = models.ForeignKey(
        confirmationorder, on_delete=models.SET_NULL, null=True, blank=True
    )
    VersiArtikel=models.ForeignKey(Versi,on_delete=models.CASCADE,null=True,blank=True)


    def __str__(self):
        return f"{self.IDDetailSPPB} - {self.NoSPPB} - {self.NoSPPB.Tanggal} - {self.DetailSPK} - {self.Jumlah}"


class TransaksiProduksi(models.Model):
    idTransaksiProduksi = models.AutoField(primary_key=True)
    KodeArtikel = models.ForeignKey(Artikel, on_delete=models.CASCADE, null=True,blank=True)
    KodeDisplay = models.ForeignKey(Display, on_delete=models.CASCADE, null= True,blank=True)
    Lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Tanggal = models.DateField()
    Jumlah = models.IntegerField()
    Keterangan = models.CharField(max_length=255)
    Jenis = models.CharField(max_length=20)
    DetailSPK = models.ForeignKey(
        DetailSPK, on_delete=models.CASCADE, null=True, blank=True
    )
    DetailSPKDisplay = models.ForeignKey(
        DetailSPKDisplay, on_delete=models.CASCADE, null=True, blank=True
    )
    VersiArtikel=models.ForeignKey(Versi,on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        if self.KodeArtikel is not None:
            return f"{self.Jenis} - {self.KodeArtikel.KodeArtikel} - {self.Lokasi} - {self.Tanggal} - {self.Jumlah} - {self.VersiArtikel}"
        else:
            return f"{self.Jenis} - {self.KodeDisplay.KodeDisplay} - {self.Lokasi} - {self.Tanggal} - {self.Jumlah}"


class SaldoAwalBahanBaku(models.Model):
    IDSaldoAwalBahanBaku = models.AutoField(primary_key=True)
    IDBahanBaku = models.ForeignKey(Produk, on_delete=models.CASCADE)
    IDLokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Jumlah = models.FloatField()
    Harga = models.FloatField()
    Tanggal = models.DateField(null=True, blank=True)
    SisaPengambilan = models.FloatField(default=0)

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
    Keterangan = models.CharField(max_length=255,null=True, blank=True)
    VersiArtikel = models.ForeignKey(Versi,on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return str(self.KodeArtikel) + "-" + str(self.Tanggal)


class PemusnahanBahanBaku(models.Model):
    IDPemusnahanBahanBaku = models.AutoField(primary_key=True)
    Tanggal = models.DateField()
    KodeBahanBaku = models.ForeignKey(Produk, on_delete=models.CASCADE)
    lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Jumlah = models.FloatField()
    Keterangan = models.CharField(max_length=255,null=True, blank=True)

    def __str__(self):
        return str(self.KodeBahanBaku) + "-" + str(self.Tanggal)

class PemusnahanProdukSubkon(models.Model):
    IDPemusnahanArtikel = models.AutoField(primary_key=True)
    Tanggal = models.DateField()
    KodeProdukSubkon = models.ForeignKey(ProdukSubkon, on_delete=models.CASCADE)
    lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()
    Keterangan = models.CharField(max_length=255,null=True, blank=True)

    def __str__(self):
        return str(self.KodeProdukSubkon) + "-" + str(self.Tanggal)


class PemusnahanBahanBakuSubkon(models.Model):
    IDPemusnahanBahanBaku = models.AutoField(primary_key=True)
    Tanggal = models.DateField()
    KodeBahanBaku = models.ForeignKey(BahanBakuSubkon, on_delete=models.CASCADE)
    lokasi = models.ForeignKey(Lokasi, on_delete=models.CASCADE)
    Jumlah = models.FloatField()
    Keterangan = models.CharField(max_length=255,null=True, blank=True)

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
    Artikel = models.ForeignKey(Artikel, on_delete=models.CASCADE, null=True)
    Display = models.ForeignKey(Display, on_delete=models.CASCADE, null=True)
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





""" SECTION SUBKON """


# Untuk Masuk Transaksi Bahan Baku Subkon
class TransaksiBahanBakuSubkon(models.Model):
    IDTransaksiBahanBakuSubkon = models.AutoField(primary_key=True)
    KodeBahanBaku = models.ForeignKey(BahanBakuSubkon, on_delete=models.CASCADE)
    Tanggal = models.DateField()
    Keterangan = models.CharField(max_length=225)
    Jumlah = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.Tanggal} - {self.KodeBahanBaku}"


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
    NoInvoice = models.CharField(max_length=255,null=True,blank=True)
    TanggalInvoice = models.DateField(blank=True,null=True)
    Supplier = models.CharField(max_length=255,null=True,blank=True)

    def __str__(self):
        return f"{self.NoSuratJalan} - {self.Tanggal}"


class DetailSuratJalanPenerimaanProdukSubkon(models.Model):
    IDDetailSJPenerimaanSubkon = models.AutoField(primary_key=True)
    NoSuratJalan = models.ForeignKey(
        SuratJalanPenerimaanProdukSubkon, on_delete=models.CASCADE
    )
    KodeProduk = models.ForeignKey(ProdukSubkon, on_delete=models.CASCADE, null=True)
    Jumlah = models.IntegerField()
    Keterangan = models.CharField(max_length=255, null=True, blank=True, default="")
    Harga = models.FloatField(default=0)
    KeteranganACC = models.BooleanField(default=False)
    Potongan = models.BooleanField(default=True)
    hargapotongan = models.FloatField(default=0)


    def __str__(self):
        return f"{self.NoSuratJalan} - {self.KodeProduk} - {self.Jumlah}"


# Untuk Transaksi Keluar Produk SUBKON ke area Produksi
class TransaksiSubkon(models.Model):
    IDTransaksiProdukSubkon = models.AutoField(primary_key=True)
    KodeProduk = models.ForeignKey(ProdukSubkon, on_delete=models.CASCADE)
    Tanggal = models.DateField()
    Jumlah = models.IntegerField()
    Keterangan = models.TextField(null=True)

    def __str__(self):
        return str(self.IDProdukSubkon.NamaProduk) + "-" + str(self.Tanggal)


class SaldoAwalBahanBakuSubkon(models.Model):
    IDSaldoAwalBahanBakuSubkon = models.AutoField(primary_key=True)
    IDBahanBakuSubkon = models.ForeignKey(BahanBakuSubkon, on_delete=models.CASCADE)
    Jumlah = models.IntegerField()
    Tanggal = models.DateField()

    def __str__(self):
        return str(self.IDBahanBakuSubkon.NamaProduk)

class CacheValue(models.Model):
    KodeProduk = models.ForeignKey(Produk,on_delete=models.CASCADE)
    Tanggal = models.DateField()
    Jumlah = models.FloatField(default=0)
    Harga = models.FloatField(default=0)

    def __str__(self):
        return f'{self.KodeProduk} - {self.Tanggal}'

class TransaksiCat(models.Model):
    KodeProduk = models.ForeignKey(Produk,on_delete=models.CASCADE)
    Tanggal = models.DateField()
    SisaPengambilan = models.FloatField(default=0)
    def __str__(self):
        return f'{self.KodeProduk} - {self.Tanggal}'

class SaldoAwalProduksi(models.Model):
    Saldo = models.FloatField()
    Tanggal = models.DateField()
    
    def __str__(self):
        return f'{self.Tanggal.year} - {self.Saldo}'

class HargaArtikel(models.Model):
    Tanggal = models.DateField()
    KodeArtikel = models.ForeignKey(Artikel,on_delete=models.CASCADE)
    Harga = models.FloatField()

    def __str__(self):
        return f'{self.KodeArtikel} - {self.Tanggal} - {self.Harga}'

# Gadipakai
class Stokadjustmenproduksi (models.Model):
    KodeProduk = models.ForeignKey(Produk,on_delete=models.CASCADE)
    Tanggal = models.DateField()
    Jumlah = models.FloatField()
    Keterangan = models.TextField()
    Timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.KodeProduk} - {self.Tanggal} - {self.Jumlah}'



class transaksimutasikodestok(models.Model):
    KodeProdukAsal = models.ForeignKey(Produk,on_delete=models.CASCADE,related_name='mutasi_produk_asal')
    KodeProdukTujuan = models.ForeignKey(Produk,on_delete=models.CASCADE,related_name='mutasi_produk_tujuan')
    Jumlah = models.FloatField()
    Keterangan = models.TextField()
    Tanggal = models.DateField()
    Lokasi = models.ForeignKey(Lokasi,on_delete=models.CASCADE,null=True,blank=True)
    
    def __str__(self):
        return f'{self.KodeProdukAsal} - {self.KodeProdukTujuan} - {self.Tanggal} - {self.Jumlah}'