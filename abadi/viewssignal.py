from . import models
from datetime import date, datetime,timedelta
import calendar
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from collections import defaultdict
import pandas as pd


@receiver(post_save, sender=models.TransaksiGudang)
@receiver(post_save, sender=models.SaldoAwalBahanBaku)
@receiver(post_save, sender=models.DetailSuratJalanPembelian)
@receiver(post_save, sender=models.PemusnahanBahanBaku)
@receiver(post_delete, sender=models.TransaksiGudang)
@receiver(post_delete, sender=models.SaldoAwalBahanBaku)
@receiver(post_delete, sender=models.DetailSuratJalanPembelian)
@receiver(post_delete, sender=models.PemusnahanBahanBaku)
def updatehargapurchasing(sender, instance, **kwargs):
    print(f'Updating for {sender.__name__}')
    if isinstance(instance,models.TransaksiGudang):
        tanggal = datetime.strptime(instance.tanggal, '%Y-%m-%d').date()
        kodeproduk = instance.KodeProduk
    elif isinstance(instance,models.SaldoAwalBahanBaku):
        tanggal = datetime.strptime(instance.Tanggal, '%Y-%m-%d').date()
        kodeproduk = instance.IDBahanBaku
    elif isinstance(instance,models.DetailSuratJalanPembelian):
        tanggal = datetime.strptime(instance.NoSuratJalan.Tanggal, '%Y-%m-%d').date()
        kodeproduk = instance.KodeProduk
    elif isinstance(instance,models.PemusnahanBahanBaku):
        tanggal = datetime.strptime(str(instance.Tanggal), '%Y-%m-%d').date()
        kodeproduk = instance.KodeBahanBaku
    
    data = gethargapurchasingperbulanperproduk(tanggal, kodeproduk)
    df = pd.DataFrame(data)
    print(df)
    # Konversi kolom 'Tanggal' ke tipe datetime
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])

    # Menetapkan 'Tanggal' sebagai index
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])

# Menetapkan 'Tanggal' sebagai index
    df.set_index('Tanggal', inplace=True)

    # Menambahkan kolom 'EndOfMonth'
    df['EndOfMonth'] = df.index + pd.offsets.MonthEnd(0)

    # Mengelompokkan data berdasarkan 'EndOfMonth' dan mengambil baris terakhir
    end_of_month_data = df.groupby('EndOfMonth').last().reset_index()

    # Mengubah nama kolom sesuai kebutuhan
    end_of_month_data = end_of_month_data.rename(columns={
        'EndOfMonth': 'Tanggal', 
        'Sisahariini': 'Balance', 
        'Hargasatuansisa': 'EndOfMonthPrice'
    })

        # Mengatur rentang waktu dari awal tahun hingga akhir tahun
    start_date = pd.to_datetime('2024-01-01')
    end_date = pd.to_datetime('2024-12-31')

    # Membuat DataFrame dengan seluruh bulan
    all_months = pd.date_range(start=start_date, end=end_date, freq='M')
    full_year_df = pd.DataFrame({'Tanggal': all_months})

    # Menetapkan 'Tanggal' sebagai index
    full_year_df.set_index('Tanggal', inplace=True)

    # Menggabungkan dengan data yang ada
    full_year_df = full_year_df.join(end_of_month_data.set_index('Tanggal'))

    # Mengisi NaN dengan 0 untuk bulan-bulan yang tidak memiliki data
    full_year_df.fillna({'Balance': 0, 'EndOfMonthPrice': 0}, inplace=True)

    # Cek bulan dengan data yang tidak kosong
    non_zero_months = full_year_df[full_year_df['Balance'] > 0].index

    if not non_zero_months.empty:
        first_non_zero_month = non_zero_months[0]
        
        # Inisialisasi variabel untuk menyimpan nilai bulan sebelumnya
        previous_balance = None
        previous_price = None

        for month in full_year_df.index:
            if month < first_non_zero_month:
                # Set bulan sebelum bulan dengan data menjadi 0
                full_year_df.loc[month, 'Balance'] = 0
                full_year_df.loc[month, 'EndOfMonthPrice'] = 0
            else:
                # Jika bulan saat ini adalah bulan pertama yang memiliki data
                if previous_balance is None and full_year_df.loc[month, 'Balance'] != 0:
                    previous_balance = full_year_df.loc[month, 'Balance']
                    previous_price = full_year_df.loc[month, 'EndOfMonthPrice']
                
                # Jika bulan saat ini kosong, gunakan nilai bulan sebelumnya
                if full_year_df.loc[month, 'Balance'] == 0:
                    if previous_balance is not None:
                        full_year_df.loc[month, 'Balance'] = previous_balance
                        full_year_df.loc[month, 'EndOfMonthPrice'] = previous_price

                # Update nilai bulan sebelumnya
                if full_year_df.loc[month, 'Balance'] != 0:
                    previous_balance = full_year_df.loc[month, 'Balance']
                    previous_price = full_year_df.loc[month, 'EndOfMonthPrice']
    else:
        # Jika tidak ada data sama sekali, set seluruh bulan menjadi 0
        full_year_df['Balance'] = 0
        full_year_df['EndOfMonthPrice'] = 0

    # Reset index untuk output
    full_year_df.reset_index(inplace=True)

    # Menampilkan DataFrame yang telah diolah
    print(full_year_df)
    # print(ads)
    for item in full_year_df.itertuples(index=False):
        models.CacheValue.objects.update_or_create(
            KodeProduk=kodeproduk,
            Tanggal=item.Tanggal,
            defaults={
                'Jumlah': item.Balance,
                'Harga': item.EndOfMonthPrice
            }
        )

    
    
def gethargapurchasingperbulanperproduk(tanggal, kodeproduk):
    bahanbaku = models.Produk.objects.get(KodeProduk=kodeproduk)
    awaltahun = date(tanggal.year, 1, 1)
    akhirtahun = date(tanggal.year, 12, 31)
    last_days = [date(tanggal.year, month, calendar.monthrange(tanggal.year, month)[1]) for month in range(1, 13)]

    saldoawalobj = models.SaldoAwalBahanBaku.objects.filter(
        IDBahanBaku=bahanbaku,
        Tanggal__range=(awaltahun, akhirtahun),
        IDLokasi__NamaLokasi="Gudang",
    ).first()


    masukobj = models.DetailSuratJalanPembelian.objects.filter(
        KodeProduk=bahanbaku, NoSuratJalan__Tanggal__range=(awaltahun, akhirtahun)
    )
    keluarobj = models.TransaksiGudang.objects.filter(
        KodeProduk=bahanbaku,jumlah__gte=0, tanggal__range=(awaltahun, akhirtahun)
    )
    pemusnahanobj = models.PemusnahanBahanBaku.objects.filter(
        KodeBahanBaku=bahanbaku, Tanggal__range=(awaltahun, akhirtahun),lokasi__NamaLokasi = "Gudang"
    )
    returobj = models.TransaksiGudang.objects.filter(
            jumlah__lt=0, KodeProduk=bahanbaku, tanggal__range=(awaltahun,akhirtahun)
        )
    
    
    if saldoawalobj:
            print("ada data")
            saldoawal = saldoawalobj.Jumlah
            hargasatuanawal = saldoawalobj.Harga
            hargatotalawal = saldoawal * hargasatuanawal
            tahun = saldoawalobj.Tanggal.year

    else:
        saldoawal = 0
        hargasatuanawal = 0
        hargatotalawal = saldoawal * hargasatuanawal
        tahun = awaltahun.year

    saldoawalobj = {
        "saldoawal": saldoawal,
        "hargasatuanawal": hargasatuanawal,
        "hargatotalawal": hargatotalawal,
        'tahun' : tahun
    }
    tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
    tanggalretur = returobj.values_list("tanggal", flat=True)
    tanggalpemusnahan = pemusnahanobj.values_list("Tanggal",flat=True)
    tanggalmasuk = masukobj.values_list("NoSuratJalan__Tanggal", flat=True)
    print('tanggal keluar :',tanggalkeluar)
    print('tanggal retur : ',tanggalretur)
    print('tanggal pemusnahan : ',tanggalpemusnahan)
    listtanggal = sorted(list(set(tanggalkeluar.union(tanggalretur).union(tanggalpemusnahan).union(tanggalmasuk))))
    listdata = []
    statusmasuk = False
    for i in listtanggal :
        jumlahmasukperhari = 0
        hargamasuktotalperhari = 0
        hargamasuksatuanperhari = 0
        jumlahkeluarperhari = 0
        hargakeluartotalperhari = 0
        hargakeluarsatuanperhari = 0
        sjpobj = masukobj.filter(NoSuratJalan__Tanggal=i)
        if sjpobj.exists():
            for j in sjpobj:
                hargamasuktotalperhari += j.Harga * j.Jumlah
                jumlahmasukperhari += j.Jumlah
            try:
                hargamasuksatuanperhari += hargamasuktotalperhari / jumlahmasukperhari
            except ZeroDivisionError:
                hargamasuksatuanperhari =0
            print("data SJP ada")
            print(hargamasuksatuanperhari)
            print(jumlahmasukperhari)
            dumy = {
                "Tanggal": i,
                "Jumlahstokawal": saldoawal,
                "Hargasatuanawal": hargasatuanawal, 
                "Hargatotalawal": hargatotalawal, 
                "Jumlahmasuk": jumlahmasukperhari,
                "Hargamasuksatuan": hargamasuksatuanperhari, 
                "Hargamasuktotal": hargamasuktotalperhari, 
                "Jumlahkeluar": jumlahkeluarperhari,
                "Hargakeluarsatuan": hargakeluarsatuanperhari, 
                "Hargakeluartotal": hargakeluartotalperhari, 
            }
            saldoawal += jumlahmasukperhari - jumlahkeluarperhari
            hargatotalawal += hargamasuktotalperhari - hargakeluartotalperhari
            try:
                hargasatuanawal = hargatotalawal / saldoawal
            except ZeroDivisionError:
                hargasatuanawal = 0

            print("Sisa Stok Hari Ini : ", saldoawal)
            print("harga awal Hari Ini :", hargasatuanawal)
            print("harga total Hari Ini :", hargatotalawal, "\n")
            dumy["Sisahariini"] = saldoawal
            dumy["Hargasatuansisa"] = hargasatuanawal
            dumy["Hargatotalsisa"] = hargatotalawal
            print(dumy)
            statusmasuk = True
            listdata.append(dumy)
            # print(asdasd)

        hargamasuktotalperhari = 0
        jumlahmasukperhari = 0
        hargamasuksatuanperhari = 0
        
        transaksigudangobj = keluarobj.filter(tanggal=i)
        transaksipemusnahan = pemusnahanobj.filter(Tanggal=i)


        if transaksigudangobj.exists():
            for j in transaksigudangobj:
                jumlahkeluarperhari += j.jumlah
                hargakeluartotalperhari += j.jumlah * hargasatuanawal

        if transaksipemusnahan.exists():
            for j in transaksipemusnahan:
                jumlahkeluarperhari += j.Jumlah
                hargakeluartotalperhari += j.Jumlah * hargasatuanawal

        if jumlahkeluarperhari > 0:
            hargakeluarsatuanperhari = hargakeluartotalperhari / jumlahkeluarperhari
        else:
            if statusmasuk:
                statusmasuk = False
                continue
            hargakeluartotalperhari = 0
            hargakeluarsatuanperhari = 0
            jumlahkeluarperhari = 0

        transaksireturobj = returobj.filter(tanggal=i)
        if transaksireturobj.exists():
            for j in transaksireturobj:
                jumlahmasukperhari += j.jumlah * -1
                hargamasuktotalperhari += j.jumlah * hargasatuanawal * -1
            hargamasuksatuanperhari += hargamasuktotalperhari / jumlahmasukperhari
        else:
            hargamasuktotalperhari = 0
            hargamasuksatuanperhari = 0
            jumlahmasukperhari = 0


        print("Tanggal : ", i)
        print("Sisa Stok Hari Sebelumnya : ", saldoawal)
        print("harga awal Hari Sebelumnya :", hargasatuanawal)
        print("harga total Hari Sebelumnya :", hargatotalawal)
        print("Jumlah Masuk : ", jumlahmasukperhari)
        print("Harga Satuan Masuk : ", hargamasuksatuanperhari)
        print("Harga Total Masuk : ", hargamasuktotalperhari)
        print("Jumlah Keluar : ", jumlahkeluarperhari)
        print("Harga Keluar : ", hargakeluarsatuanperhari)
        print(
            "Harga Total Keluar : ", hargakeluarsatuanperhari * jumlahkeluarperhari
        )


        dumy = {
            "Tanggal": i,
            "Jumlahstokawal": saldoawal,
            "Hargasatuanawal": hargasatuanawal,
            "Hargatotalawal": hargatotalawal,
            "Jumlahmasuk": jumlahmasukperhari,
            "Hargamasuksatuan": hargamasuksatuanperhari,
            "Hargamasuktotal": hargamasuktotalperhari,
            "Jumlahkeluar": jumlahkeluarperhari,
            "Hargakeluarsatuan": hargakeluarsatuanperhari,
            "Hargakeluartotal": hargakeluartotalperhari,
        }
        """
        Rumus dari Excel KSBB Purchasing
        Sisa = Sisa hari sebelumnya + Jumlah masuk hari ini - jumlah keluar hari ini 
        harga sisa satuan = total sisa / harga total sisa
        Harga keluar = harga satuan hari sebelumnya

        """
        dummysaldoawal = saldoawal
        dummyhargatotalawal = hargatotalawal
        dummyhargasatuanawal = hargasatuanawal

        saldoawal += jumlahmasukperhari - jumlahkeluarperhari
        hargatotalawal += hargamasuktotalperhari - hargakeluartotalperhari
        print(hargatotalawal, saldoawal)
        try:
            hargasatuanawal = hargatotalawal / saldoawal
        except:
            hargasatuanawal = 0

        print("Sisa Stok Hari Ini : ", saldoawal)
        print("harga awal Hari Ini :", hargasatuanawal)
        print("harga total Hari Ini :", hargatotalawal, "\n")
        dumy["Sisahariini"] = saldoawal
        dumy["Hargasatuansisa"] = hargasatuanawal
        dumy["Hargatotalsisa"] = hargatotalawal

        listdata.append(dumy)
    print(listdata)
    return listdata
    


# Asumsikan data Anda disimpan dalam variabel 'data'

# Fungsi untuk mendapatkan tanggal terakhir dari setiap bulan

