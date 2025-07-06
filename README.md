# Türkiye Ekonomik Veri Analiz Araçları

Bu proje, Türkiye'nin ekonomik göstergelerini analiz etmek için bir dizi Python aracı içerir. TÜFE (Tüketici Fiyat Endeksi), USD/TRY döviz kuru, ENAG (Enflasyon Araştırma Grubu) verileri ve REDK (Reel Efektif Döviz Kuru) gibi çeşitli ekonomik göstergeleri analiz etmek ve görselleştirmek için kullanılabilir.

![Örnek Çıktı](Figure_1.png)

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
- `--end_date`: Bitiş tarihi (varsayılan: 01-07-2025)
- `--enag`: ENAG verilerini dahil et
- `--verbose`: Detaylı çıktı gösterir
- `--normalize`: Verileri normalize eder
- `--save`: Grafiği PNG dosyası olarak kaydeder

### enag.py

ENAG enflasyon verilerini içerir ve kümülatif yüzde hesaplama fonksiyonları sağlar.

```bash
python enag.py [--verbose]
```

Parametreler:
- `--verbose`: Detaylı çıktı gösterir

### enag_subs_tufe_2.py

ENAG aylık yüzde değişimi ile TÜFE aylık değişiminin yarısı arasındaki farkı hesaplar.

```bash
python enag_subs_tufe_2.py [--graph] [--verbose]
```

Parametreler:
- `--graph`: Sonuçları grafikle gösterir
- `--verbose`: Detaylı çıktı gösterir

### redk.py

TP.RK.T1.Y (Reel Efektif Döviz Kuru) verisini analiz eder ve ENAG-TÜFE/2 değerleri ile kümülatif çarpımını hesaplar.

```bash
python redk.py [--start_date DD-MM-YYYY] [--end_date DD-MM-YYYY] [--verbose] [--save]
```

Parametreler:
- `--start_date`: Başlangıç tarihi (varsayılan: 01-01-2020)
- `--end_date`: Bitiş tarihi (varsayılan: 01-06-2025)
- `--verbose`: Detaylı çıktı gösterir
- `--save`: Grafiği PNG dosyası olarak kaydeder

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

## Veri Kaynakları

- TÜFE ve REDK verileri: TCMB EVDS API'si
- ENAG verileri: Enflasyon Araştırma Grubu
- USD/TRY verileri: TCMB EVDS API'si

## Dosya Yapısı

```
testo/
├── enf.py              # Ana analiz scripti (TÜFE ve USD/TRY)
├── enag.py             # ENAG veri modülü
├── tufe_filter.py      # TÜFE veri filtreleme yardımcıları
├── redk.py             # Reel Efektif Döviz Kuru analizi
├── enag_subs_tufe_2.py # ENAG-TÜFE/2 analizi
├── Figure_1.png        # Örnek çıktı görseli
└── README.md           # Bu dosya
```

## Lisans

Bu proje açık kaynaklıdır. 