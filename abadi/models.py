from django.db import models

# Create your models here.
class Produk (models.Model):
    KodeProduk = models.CharField(max_length=20, primary_key = True)
    NamaProduk = models.CharField(max_length=20)
    unit = models.CharField(max_length=20)
    keterangan = models.CharField(max_length=255)
    
    def __str__ (self):
        return str(self.KodeProduk)

class Artikel (models.Model):
    KodeArtikel = models.CharField(max_length=20,primary_key=True)
    keterangan = models.CharField(max_length=255)
    
    def __str__ (self):
        return str(self.KodeArtikel)

class Lokasi(models.Model):
    IDLokasi = models.IntegerField(primary_key=True)
    NamaLokasi = models.CharField(max_length = 20)
    
    def __str__(self):
        return str(self.NamaLokasi)
    
class SuratJalanPembelian(models.Model):
    NoSuratJalan = models.CharField(max_length=255,primary_key = True)
    Tanggal = models.DateField()
    supplier = models.CharField(max_length=255)
    PO = models.CharField(max_length=255)

    def __str__ (self):
        return str(str(self.NoSuratJalan))

class DetailSuratJalanPembelian(models.Model):
    IDDetailSJPembelian = models.IntegerField(primary_key=True)
    NoSuratJalan = models.ForeignKey(SuratJalanPembelian,on_delete = models.DO_NOTHING)
    KodeProduk = models.ForeignKey(Produk,on_delete=models.DO_NOTHING)
    Jumlah = models.IntegerField()
    KeteranganACC = models.BooleanField()
    Harga = models.FloatField()

    def __str__ (self):
        return str(self.NoSuratJalan)

class TransaksiGudang(models.Model):
    IDDetailTransaksiGudang = models.IntegerField(primary_key = True)
    KodeProduk = models.ForeignKey(Produk,on_delete=models.DO_NOTHING)
    keterangan = models.CharField(max_length=20)
    jumlah = models.IntegerField()
    tanggal = models.DateField()
    KeteranganACC = models.BooleanField()
    Lokasi = models.ForeignKey(Lokasi,on_delete=models.DO_NOTHING)
    def __str__ (self):
        return str(self.id)

class Penyusun(models.Model):
    IDKodePenyusun = models.IntegerField(primary_key=True)
    KodeProduk = models.ForeignKey(Produk,on_delete=models.DO_NOTHING)
    KodeArtikel = models.ForeignKey(Artikel,on_delete= models.DO_NOTHING)
    Status = models.BooleanField()
    Lokasi = models.ForeignKey(Lokasi,on_delete=models.DO_NOTHING)

    def __str__ (self):
        return str(self.KodeArtikel) + ' - ' + str(self.KodeProduk)

class KonversiMaster(models.Model):
    IDKodeKonversiMaster = models.IntegerField(primary_key=True)
    KodePenyusun = models.ForeignKey(Penyusun,on_delete=models.DO_NOTHING)
    Kuantitas = models.FloatField()

    def __str__ (self):
        return str(self.IDKodeKonversiMaster)

class Penyesuaian(models.Model):
    IDPenyesuaian = models.IntegerField(primary_key=True)
    KodePenyusun = models.ForeignKey(Penyusun,on_delete=models.DO_NOTHING)
    TanggalMulai = models.DateField()
    TanggalAkhir = models.DateField()

    def __str__ (self):
        return str(self.IDPenyesuaian)

class DetailKonversiProduksi(models.Model):
    IDDetailKonversiProduksi = models.IntegerField(primary_key=True)
    KodePenyesuaian = models.ForeignKey(Penyesuaian,on_delete=models.DO_NOTHING)
    kuantitas = models.FloatField()

    def __str__ (self):
        return str(self.IDDetailKonversiProduksi)

class SPK (models.Model):
    NoSPK = models.CharField(max_length=255,primary_key=True)
    Tanggal = models.DateField()
    Keterangan = models.CharField(max_length=255)
    KeteranganACC = models.BooleanField()

    def __str__ (self):
        return str(self.NoSPK)
    
class DetailSPK (models.Model):
    IDDetailSPK = models.IntegerField(primary_key=True)
    NoSPK = models.ForeignKey(SPK,on_delete=models.DO_NOTHING)
    KodeArtikel = models.ForeignKey(Artikel,on_delete=models.DO_NOTHING)
    Jumlah = models.IntegerField()

    def __str__ (self):
        return str(self.NoSPK)

class TransaksiProduksi (models.Model):
    idTransaksiProduksi = models.IntegerField(primary_key=True)
    KodeArtikel = models.ForeignKey(Artikel,on_delete=models.DO_NOTHING)
    Lokasi = models.ForeignKey(Lokasi,on_delete = models.DO_NOTHING)
    Tanggal = models.DateField()
    Jumlah = models.IntegerField()
    Keterangan = models.CharField(max_length=255)
    Jenis = models.CharField(max_length = 20)
    
    def __str__ (self):
        return str(self.idTransaksiProduksi)

class SPPB (models.Model):
    NoSPPB = models.CharField(max_length=255,primary_key=True)
    Tanggal = models.DateField()
    Keterangan = models.CharField(max_length=255)

    def __str__ (self):
        return str(self.NoSPPB)

class DetailSPPB (models.Model):
    IDDetailSPPB = models.IntegerField(primary_key=True)
    NoSPPb = models.ForeignKey(SPPB, on_delete= models.DO_NOTHING)
    NoSPK = models.ForeignKey(SPK,on_delete=models.DO_NOTHING)
    Jumlah = models.IntegerField()
    
    def __str__ (self):
        return str(self.IDDetailSPPB)
    

class SaldoAwalBahanBaku (models.Model):
    IDSaldoAwalBahanBaku = models.IntegerField(primary_key = True)
    IDBahanBaku = models.ForeignKey(Produk,on_delete=models.DO_NOTHING)
    IDLokasi = models.ForeignKey(Lokasi,on_delete = models.DO_NOTHING)
    Jumlah = models.IntegerField()
    Harga = models.FloatField()

    def __str__ (self):
        return str(self.IDLokasi + str(self.IDBahanBaku))
    
class SaldoAwalArtikel (models.Model):
    IDSaldoAwalBahanBaku = models.IntegerField(primary_key = True)
    IDBahanBaku = models.ForeignKey(Artikel,on_delete=models.DO_NOTHING)
    IDLokasi = models.ForeignKey(Lokasi,on_delete = models.DO_NOTHING)
    Jumlah = models.IntegerField()

    def __str__ (self):
        return str(self.IDLokasi + str(self.IDBahanBaku))