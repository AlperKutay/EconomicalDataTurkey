# Türkiye Ekonomik Veri Analiz Araçları

Bu proje, Türkiye'nin ekonomik göstergelerini analiz etmek için bir dizi Python aracı içerir. TÜFE (Tüketici Fiyat Endeksi), USD/TRY döviz kuru, ENAG (Enflasyon Araştırma Grubu) verileri ve REDK (Reel Efektif Döviz Kuru) gibi çeşitli ekonomik göstergeleri analiz etmek ve görselleştirmek için kullanılabilir.

![Örnek Çıktı](Figure_1.png)

## Oluşturulan Grafik Dosyaları

Scriptler çalıştırıldığında aşağıdaki PNG dosyaları oluşturulur:

### 1. REDK Üç Panel Analizi
![REDK Basit Çarpım](REDK_Basit_Carpim_01_01_2005_01_06_2025.png)

**Dosya**: `REDK_Basit_Carpim_[başlangıç]_[bitiş].png`

Bu grafik üç alt panel içerir:
- **Üst Panel**: Orijinal TP.RK.T1.Y (REDK) değerleri
- **Orta Panel**: (ENAG + TÜFE)/2 yeniden oranlanmış değerler
- **Alt Panel**: Türkiye Big Mac dolar fiyatları (6 aylık veri aylık hale genişletilmiş)

### 2. REDK Kümülatif Karşılaştırma
![REDK Kümülatif Çarpım](REDK_Kumulatif_Carpim_01_01_2005_01_06_2025.png)

**Dosya**: `REDK_Kumulatif_Carpim_[başlangıç]_[bitiş].png`

Bu grafik iki çizgiyi karşılaştırır:
- **Mor Çizgi**: REDK kümülatif çarpım sonuçları (ENAG-TÜFE ayarlamalı)
- **Mavi Çizgi**: Orijinal REDK değerleri (kesikli çizgi, şeffaf)

### 3. Big Mac Standalone Analizi
![Big Mac Dolar Fiyatları](Big_Mac_Dolar_Fiyatlari_01_01_2020_01_06_2025.png)

**Dosya**: `Big_Mac_Dolar_Fiyatlari_[başlangıç]_[bitiş].png`

Bu grafik şunları gösterir:
- Türkiye Big Mac dolar fiyatlarının zaman serisi analizi
- 6 aylık orijinal veri aylık hale genişletilmiş
- İstatistik kutusu (min, max, ortalama fiyatlar)
- Son fiyat vurgulanmış
- Detaylı fiyat etiketleri

## Gereksinimler

- Python 3.6+
- pandas
- matplotlib
- numpy
- evds (TCMB EVDS API'si için)

```bash
pip install pandas matplotlib numpy evds
```

## Modüller

### enf.py

TÜFE ve USD/TRY döviz kuru karşılaştırması yapar.

```bash
python enf.py [--start_date DD-MM-YYYY] [--end_date DD-MM-YYYY] [--enag] [--verbose] [--normalize] [--save]
```

Parametreler:
- `--start_date`: Başlangıç tarihi (varsayılan: 01-09-2020)
- `--end_date`: Bitiş tarihi (varsayılan: mevcut tarih)
- `--enag`: ENAG verilerini dahil et
- `--verbose`: Detaylı çıktı göster
- `--normalize`: Verileri normalize et
- `--save`: Grafiği PNG dosyası olarak kaydet

### enag.py

ENAG (Enflasyon Araştırma Grubu) verilerini işlemek için yardımcı modül.

### redk.py

TP.RK.T1.Y (Reel Efektif Döviz Kuru) verisini analiz eder, ENAG-TÜFE/2 değerleri ile kümülatif çarpımını hesaplar ve Big Mac Endeksi grafiğini de gösterir.

```bash
python redk.py [--start_date DD-MM-YYYY] [--end_date DD-MM-YYYY] [--verbose] [--save]
```

Parametreler:
- `--start_date`: Başlangıç tarihi (varsayılan: 01-01-2005)
- `--end_date`: Bitiş tarihi (varsayılan: 01-06-2025)
- `--verbose`: Detaylı çıktı gösterir
- `--save`: Grafiği PNG dosyası olarak kaydeder

**Çıktı**: Üç alt grafik içeren bir görselleştirme:
1. **REDK Analizi**: Orijinal TP.RK.T1.Y verileri
2. **ENAG-TÜFE Analizi**: (ENAG + TÜFE)/2 yeniden oranlanmış veriler
3. **Big Mac Analizi**: Türkiye Big Mac dolar fiyatları

**Grafik Özellikleri**:
- Tüm grafikler 6 aylık X-ekseni etiketleme (MM-YYYY formatında)
- Tutarlı zaman çizelgesi ve profesyonel görünüm
- Synchronized tarih aralıkları

### big_mac_analysis.py

Türkiye Big Mac Endeksi dolar fiyatlarını analiz eder ve görselleştirir. 6 aylık veriyi aylık hale getirerek daha ayrıntılı analiz sağlar.

```bash
python big_mac_analysis.py [--file FILENAME] [--start_date DD-MM-YYYY] [--end_date DD-MM-YYYY] [--save] [--no-values] [--analysis-only] [--no-expand]
```

Parametreler:
- `--file`: CSV dosya adı (varsayılan: big-mac-full-index.csv)
- `--start_date`: Başlangıç tarihi (DD-MM-YYYY formatında)
- `--end_date`: Bitiş tarihi (DD-MM-YYYY formatında)
- `--save`: Grafiği PNG dosyası olarak kaydeder
- `--no-values`: Grafik üzerinde değerleri göstermez
- `--analysis-only`: Sadece analiz yapar, grafik çizmez
- `--no-expand`: 6 aylık veriyi aylık hale getirmez

**Özellikler**:
- 6 aylık Big Mac verilerini aylık hale genişletir (her veriyi bir sonraki veri noktasına kadar tekrarlar)
- Tarih aralığı filtreleme
- Detaylı fiyat analizi ve yıllık değişim hesaplaması
- Dinamik grafik etiketleme (veri yoğunluğuna göre)

### tufe_filter.py

TÜFE verilerini filtrelemek için yardımcı modül. Özellikle Eylül 2020 öncesi veriler için kullanılır.

## Örnek Kullanım

### TÜFE ve USD/TRY Karşılaştırması

```bash
python enf.py --save
```

Bu komut, TÜFE ve USD/TRY verilerini karşılaştırır ve sonuçları grafikle gösterir.

### ENAG Dahil TÜFE ve USD/TRY Karşılaştırması

```bash
python enf.py --enag --save
```

Bu komut, TÜFE, USD/TRY ve ENAG verilerini karşılaştırır ve sonuçları grafikle gösterir.

### REDK ve ENAG-TÜFE/2 Kümülatif Çarpımı

```bash
python redk.py --save
```

Bu komut, REDK verisini çeker ve 09-2020'den itibaren ENAG-TÜFE/2 değerleri ile kümülatif çarpımını hesaplar. Sonuçları grafikle gösterir ve kaydeder.

### Big Mac Analizi

```bash
python big_mac_analysis.py --save
```

Bu komut, Big Mac Endeksi verilerini analiz eder, Türkiye'nin Big Mac dolar fiyatlarının zaman serisi grafiğini çizer ve detaylı istatistiksel analiz yapar.

## Veri Kaynakları

- TÜFE ve REDK verileri: TCMB EVDS API'si
- ENAG verileri: Enflasyon Araştırma Grubu
- USD/TRY verileri: TCMB EVDS API'si
- Big Mac Endeksi: [The Economist Big Mac Index](https://github.com/TheEconomist/big-mac-data)
  - Resmi Big Mac Index veri seti ve metodolojisi
  - MIT lisansı altında açık kaynak
  - Aylık güncellemeler ve tam tarihsel veri

## Dosya Yapısı

```
testo/
├── enf.py                  # Ana analiz scripti (TÜFE ve USD/TRY)
├── enag.py                 # ENAG veri modülü
├── tufe_filter.py          # TÜFE veri filtreleme yardımcıları
├── redk.py                 # Reel Efektif Döviz Kuru analizi
├── enag_subs_tufe_2.py     # ENAG-TÜFE/2 analizi
├── big_mac_analysis.py     # Big Mac Endeksi analizi
├── big-mac-full-index.csv  # Big Mac Endeksi verileri (sadece Türkiye)
├── Figure_1.png            # Örnek çıktı görseli
├── REDK_Basit_Carpim_[tarih].png      # REDK üç panel analizi
├── REDK_Kumulatif_Carpim_[tarih].png  # REDK kümülatif karşılaştırma
├── Big_Mac_Dolar_Fiyatlari_[tarih].png # Big Mac standalone analizi
└── README.md               # Bu dosya
```

## Lisans

Bu proje açık kaynaklıdır.
