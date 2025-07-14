import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import argparse
import sys
import os

# Add the current directory to Python path to import us_enf
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from us_enf import get_cpi, get_cpi_range

def calculate_inflation_adjusted_prices(df, base_date=None):
    """
    US CPI verilerini kullanarak enflasyon ayarlı fiyatlar hesaplar.
    
    Args:
        df: Big Mac verilerini içeren DataFrame
        base_date: Baz tarih (YYYY-MM-DD formatında). None ise ilk tarih kullanılır.
        
    Returns:
        df: Enflasyon ayarlı fiyatlarla güncellenmiş DataFrame
    """
    print("\nEnflasyon ayarlı fiyatlar hesaplanıyor...")
    
    # Baz tarihi belirle
    if base_date is None:
        base_date = df['date'].min().strftime('%Y-%m-%d')
    
    print(f"Baz tarih: {base_date}")
    
    # Baz CPI değerini al
    print(f"Baz tarih ({base_date}) için CPI verisi alınıyor...")
    base_cpi_data = get_cpi('CPIAUCSL', base_date, return_data=True)
    
    if base_cpi_data is None:
        print("Baz CPI değeri alınamadı, enflasyon ayarlaması yapılamayacak!")
        return df
    
    base_cpi = base_cpi_data['value']
    print(f"Baz CPI değeri: {base_cpi} (tarih: {base_cpi_data['date']})")
    
    # Veri aralığını belirle (biraz genişlet)
    data_start = df['date'].min() - timedelta(days=180)
    data_end = df['date'].max() + timedelta(days=180)
    
    start_date_str = data_start.strftime('%Y-%m-%d')
    end_date_str = data_end.strftime('%Y-%m-%d')
    
    print(f"CPI veri aralığı alınıyor: {start_date_str} - {end_date_str}")
    
    # Tüm CPI verilerini tek seferde al
    cpi_observations = get_cpi_range('CPIAUCSL', start_date_str, end_date_str)
    
    if not cpi_observations:
        print("CPI verileri alınamadı, enflasyon ayarlaması yapılamayacak!")
        return df
    
    print(f"Toplam {len(cpi_observations)} CPI gözlemi alındı")
    
    # CPI verilerini pandas DataFrame'e çevir daha hızlı işlem için
    import pandas as pd
    cpi_df = pd.DataFrame(cpi_observations)
    cpi_df['date'] = pd.to_datetime(cpi_df['date'])
    cpi_df = cpi_df.sort_values('date')
    
    def find_closest_cpi(target_date):
        """Verilen tarihe en yakın CPI değerini bul"""
        differences = abs(cpi_df['date'] - target_date)
        closest_idx = differences.idxmin()
        return cpi_df.loc[closest_idx, 'value'], cpi_df.loc[closest_idx, 'date']
    
    # Her tarih için enflasyon ayarlı fiyat hesapla
    df = df.copy()
    df['inflation_adjusted_price'] = df['dollar_price']
    df['original_dollar_price'] = df['dollar_price'].copy()
    
    processed_dates = set()
    
    for idx, row in df.iterrows():
        target_date = row['date']
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Aynı tarihi tekrar işleme
        if date_str in processed_dates:
            continue
        
        # En yakın CPI değerini bul
        current_cpi, actual_cpi_date = find_closest_cpi(target_date)
        
        # Bu tarih için enflasyon ayarlı fiyat hesapla
        # Ayarlı fiyat = orijinal_fiyat * (baz_cpi / mevcut_cpi)
        inflation_factor = base_cpi / current_cpi
        
        # Aynı tarihteki tüm satırları güncelle
        mask = df['date'].dt.strftime('%Y-%m-%d') == date_str
        df.loc[mask, 'inflation_adjusted_price'] = df.loc[mask, 'dollar_price'] * inflation_factor
        
        # İlk satırdan örnek değerleri al
        if len(df[mask]) > 0:
            original_price = df.loc[mask, 'dollar_price'].iloc[0]
            adjusted_price = df.loc[mask, 'inflation_adjusted_price'].iloc[0]
            days_diff = abs((actual_cpi_date.date() - target_date.date()).days)
            print(f"{date_str}: CPI={current_cpi:.2f} ({actual_cpi_date.strftime('%Y-%m-%d')}, {days_diff}d diff), Orijinal=${original_price:.2f}, Ayarlı=${adjusted_price:.2f}")
        
        processed_dates.add(date_str)
    
    # Enflasyon ayarlı fiyatları dollar_price kolonuna kopyala (mevcut sistemi bozmamak için)
    df['dollar_price'] = df['inflation_adjusted_price']
    
    print(f"Enflasyon ayarlaması tamamlandı! ({len(processed_dates)} farklı tarih işlendi)")
    print(f"Baz tarih ({base_date}) CPI: {base_cpi}")
    print(f"Ortalama enflasyon ayarlı fiyat: ${df['dollar_price'].mean():.2f}")
    
    return df

def expand_big_mac_data_to_monthly(df):
    """
    6 aylık Big Mac verilerini aylık hale getirir.
    Her veri noktasını bir sonraki veri noktasına kadar tekrarlar.
    
    Args:
        df: Big Mac verilerini içeren DataFrame
        
    Returns:
        expanded_df: Aylık olarak genişletilmiş DataFrame
    """
    expanded_data = []
    
    for i in range(len(df)):
        current_date = df['date'].iloc[i]
        current_row = df.iloc[i].copy()
        
        # Sonraki tarihi bul
        if i < len(df) - 1:
            next_date = df['date'].iloc[i + 1]
        else:
            # Son veri için 6 ay ekle
            next_date = current_date + pd.DateOffset(months=6)
        
        # Mevcut tarihten bir sonraki tarihe kadar aylık veriler oluştur
        temp_date = current_date
        while temp_date < next_date:
            row_copy = current_row.copy()
            row_copy['date'] = temp_date
            expanded_data.append(row_copy)
            temp_date = temp_date + pd.DateOffset(months=1)
    
    expanded_df = pd.DataFrame(expanded_data)
    expanded_df = expanded_df.sort_values('date').reset_index(drop=True)
    
    print(f"Orijinal veri: {len(df)} satır (6 aylık)")
    print(f"Genişletilmiş veri: {len(expanded_df)} satır (aylık)")
    
    return expanded_df

def read_big_mac_data(filename='big-mac-data/output-data/big-mac-tr-index.csv', start_date=None, end_date=None, expand_monthly=True, use_adjusted=False, inflation_adjusted=False, base_date=None):
    """
    Big Mac CSV dosyasını okur ve işler.
    
    Args:
        filename: CSV dosya adı
        start_date: Başlangıç tarihi (DD-MM-YYYY formatında)
        end_date: Bitiş tarihi (DD-MM-YYYY formatında)
        expand_monthly: 6 aylık veriyi aylık hale getir
        use_adjusted: GDP-adjusted fiyat kullan (adj_price kolonu)
        inflation_adjusted: US CPI ile enflasyon ayarlaması yap
        base_date: Enflasyon ayarlaması için baz tarih (YYYY-MM-DD formatında)
        
    Returns:
        df: İşlenmiş pandas DataFrame
    """
    try:
        df = pd.read_csv(filename)
        print(f"Veri başarıyla okundu: {len(df)} satır")
        
        # Tarih sütununu datetime formatına çevir
        df['date'] = pd.to_datetime(df['date'])
        
        # Tarihe göre sırala
        df = df.sort_values('date')
        
        # Numerik kolonları float'a çevir
        price_column = 'adj_price' if use_adjusted else 'dollar_price'
        numeric_columns = ['local_price', 'dollar_ex', 'dollar_price', 'adj_price']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Fiyat kolonunu belirle ve dollar_price olarak kopyala (geriye uyumluluk için)
        if use_adjusted and 'adj_price' in df.columns:
            df['dollar_price'] = df['adj_price'].copy()
            print(f"GDP-adjusted fiyatlar kullanılıyor (adj_price kolonu)")
        else:
            print(f"Ham fiyatlar kullanılıyor (dollar_price kolonu)")
        
        # Tarih filtreleme
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%d-%m-%Y')
                df = df[df['date'] >= start_dt]
                print(f"Başlangıç tarihinden sonra: {len(df)} satır")
            except ValueError:
                print(f"Geçersiz başlangıç tarihi formatı: {start_date}")
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%d-%m-%Y')
                df = df[df['date'] <= end_dt]
                print(f"Bitiş tarihinden önce: {len(df)} satır")
            except ValueError:
                print(f"Geçersiz bitiş tarihi formatı: {end_date}")
        
        # Aylık genişletme
        if expand_monthly and len(df) > 0:
            df = expand_big_mac_data_to_monthly(df)
        
        # Enflasyon ayarlaması
        if inflation_adjusted and len(df) > 0:
            df = calculate_inflation_adjusted_prices(df, base_date)
        
        if len(df) > 0:
            print(f"Tarih aralığı: {df['date'].min()} - {df['date'].max()}")
            price_type = "GDP-adjusted" if use_adjusted else "Ham"
            if inflation_adjusted:
                price_type = f"{price_type} + US CPI Enflasyon Ayarlı"
            print(f"{price_type} dolar fiyat aralığı: ${df['dollar_price'].min():.2f} - ${df['dollar_price'].max():.2f}")
        else:
            print("Uyarı: Filtreleme sonrası veri kalmadı!")
        
        return df
        
    except Exception as e:
        print(f"Veri okuma hatası: {e}")
        return None

def read_global_big_mac_data(filename='big-mac-data/output-data/big-mac-full-index.csv', start_date=None, end_date=None, expand_monthly=True, use_adjusted=False, inflation_adjusted=False, base_date=None):
    """
    Global Big Mac CSV dosyasını okur ve global ortalama hesaplar.
    
    Args:
        filename: CSV dosya adı
        start_date: Başlangıç tarihi (DD-MM-YYYY formatında)
        end_date: Bitiş tarihi (DD-MM-YYYY formatında)
        expand_monthly: 6 aylık veriyi aylık hale getir
        use_adjusted: GDP-adjusted fiyat kullan (adj_price kolonu)
        inflation_adjusted: US CPI ile enflasyon ayarlaması yap
        base_date: Enflasyon ayarlaması için baz tarih (YYYY-MM-DD formatında)
        
    Returns:
        df: Global ortalama Big Mac verilerini içeren DataFrame
    """
    try:
        df = pd.read_csv(filename)
        print(f"Global veri başarıyla okundu: {len(df)} satır")
        
        # Tarih sütununu datetime formatına çevir
        df['date'] = pd.to_datetime(df['date'])
        
        # Numerik kolonları float'a çevir
        price_column = 'adj_price' if use_adjusted else 'dollar_price'
        df[price_column] = pd.to_numeric(df[price_column], errors='coerce')
        
        # Her tarih için global ortalama hesapla
        global_avg = df.groupby('date')[price_column].mean().reset_index()
        global_avg['iso_a3'] = 'GLOBAL'
        global_avg['name'] = 'Global Average'
        global_avg['local_price'] = global_avg[price_column]  # Global için local_price = price
        global_avg['dollar_ex'] = 1.0  # Global için döviz kuru 1
        global_avg['dollar_price'] = global_avg[price_column]  # Geriye uyumluluk için
        
        price_type = "GDP-adjusted" if use_adjusted else "Ham"
        print(f"Global {price_type} ortalama veri: {len(global_avg)} satır")
        
        # Tarihe göre sırala
        global_avg = global_avg.sort_values('date')
        
        # Tarih filtreleme
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%d-%m-%Y')
                global_avg = global_avg[global_avg['date'] >= start_dt]
                print(f"Başlangıç tarihinden sonra: {len(global_avg)} satır")
            except ValueError:
                print(f"Geçersiz başlangıç tarihi formatı: {start_date}")
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%d-%m-%Y')
                global_avg = global_avg[global_avg['date'] <= end_dt]
                print(f"Bitiş tarihinden önce: {len(global_avg)} satır")
            except ValueError:
                print(f"Geçersiz bitiş tarihi formatı: {end_date}")
        
        # Aylık genişletme
        if expand_monthly and len(global_avg) > 0:
            global_avg = expand_big_mac_data_to_monthly(global_avg)
        
        # Enflasyon ayarlaması (global için)
        if inflation_adjusted and len(global_avg) > 0:
            print(f"\nGlobal veriler için enflasyon ayarlaması yapılıyor...")
            global_avg = calculate_inflation_adjusted_prices(global_avg, base_date)
        
        if len(global_avg) > 0:
            print(f"Global tarih aralığı: {global_avg['date'].min()} - {global_avg['date'].max()}")
            if inflation_adjusted:
                price_type = f"{price_type} + US CPI Enflasyon Ayarlı"
            print(f"Global {price_type} dolar fiyat aralığı: ${global_avg['dollar_price'].min():.2f} - ${global_avg['dollar_price'].max():.2f}")
        else:
            print("Uyarı: Global veri filtreleme sonrası veri kalmadı!")
        
        return global_avg
        
    except Exception as e:
        print(f"Global veri okuma hatası: {e}")
        return None

def plot_big_mac_prices(df, save=False, show_values=True, start_date=None, end_date=None, global_df=None, use_adjusted=False, global_adjusted=False, inflation_adjusted=False):
    """
    Big Mac dolar fiyatlarının grafiğini çizer.
    
    Args:
        df: Big Mac verilerini içeren DataFrame
        save: Grafiği dosya olarak kaydet
        show_values: Grafik üzerinde değerleri göster
        start_date: Başlangıç tarihi (dosya adı için)
        end_date: Bitiş tarihi (dosya adı için)
        global_df: Global ortalama verilerini içeren DataFrame (opsiyonel)
        use_adjusted: GDP-adjusted fiyat kullanılıyor mu (Türkiye için)
        global_adjusted: Global için GDP-adjusted fiyat kullanılıyor mu
        inflation_adjusted: US CPI ile enflasyon ayarlaması yapılıyor mu
    """
    plt.figure(figsize=(16, 10))
    
    # Fiyat tipini belirle
    price_type = "GDP-Adjusted" if use_adjusted else "Ham"
    if inflation_adjusted:
        price_type = f"{price_type} + US CPI Enflasyon Ayarlı"
    turkey_label = f'Türkiye ({price_type})'
    
    # Ana grafik (Türkiye)
    plt.plot(df['date'], df['dollar_price'], 
             marker='o', linewidth=2, markersize=6, 
             color='#e74c3c', markerfacecolor='white', 
             markeredgecolor='#e74c3c', markeredgewidth=2,
             label=turkey_label, zorder=3)
    
    # Global ortalama çizgisi (eğer verilmişse)
    if global_df is not None and len(global_df) > 0:
        global_price_type = "GDP-Adjusted" if global_adjusted else "Ham"
        if inflation_adjusted:
            global_price_type = f"{global_price_type} + US CPI Enflasyon Ayarlı"
        global_label = f'Global Ortalama ({global_price_type})'
        plt.plot(global_df['date'], global_df['dollar_price'], 
                 marker='s', linewidth=2, markersize=4, 
                 color='#2ecc71', markerfacecolor='white', 
                 markeredgecolor='#2ecc71', markeredgewidth=1,
                 label=global_label, alpha=0.8, zorder=2)
    
    # Grafik düzenlemeleri
    date_range = f"({df['date'].min().strftime('%m-%Y')} - {df['date'].max().strftime('%m-%Y')})"
    title = f'Türkiye Big Mac {price_type} Dolar Fiyatları {date_range}'
    if global_df is not None:
        global_price_type = "GDP-Adjusted" if global_adjusted else "Ham"
        if inflation_adjusted:
            global_price_type = f"{global_price_type} + US CPI Enflasyon Ayarlı"
        title += f' (Global {global_price_type} Ortalama ile Karşılaştırma)'
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Tarih', fontsize=12)
    plt.ylabel('Dolar Fiyatı ($)', fontsize=12)
    
    # Legend ekle (eğer global veri varsa veya adjusted kullanılıyorsa)
    if global_df is not None or use_adjusted:
        plt.legend(loc='upper left', fontsize=10)
    
    # Grid
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Y ekseni formatı
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))
    
    # X ekseni formatı
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
    
    # X ekseni etiketleme - 6 ayda bir için tutarlılık
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    
    plt.xticks(rotation=45)
    
    # Değerleri grafikte göster
    if show_values:
        # Veri yoğunluğuna göre gösterim aralığını ayarla
        step = max(1, len(df) // 20)  # En fazla 20 değer göster
        for i in range(0, len(df), step):
            date = df['date'].iloc[i]
            price = df['dollar_price'].iloc[i]
            plt.annotate(f'${price:.2f}', 
                       (date, price), 
                       textcoords="offset points", 
                       xytext=(0,10), 
                       ha='center', fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))
    
    # Son değeri özel olarak vurgula
    last_date = df['date'].iloc[-1]
    last_price = df['dollar_price'].iloc[-1]
    tr_label = f'TR Son ({price_type}): ${last_price:.2f}'
    plt.annotate(tr_label, 
                (last_date, last_price), 
                textcoords="offset points", 
                xytext=(10,15), 
                ha='left', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='black', lw=1))
    
    # Global son değeri de vurgula (eğer varsa)
    if global_df is not None and len(global_df) > 0:
        global_last_date = global_df['date'].iloc[-1]
        global_last_price = global_df['dollar_price'].iloc[-1]
        global_price_type = "GDP-Adjusted" if global_adjusted else "Ham"
        if inflation_adjusted:
            global_price_type = f"{global_price_type} + US CPI Enflasyon Ayarlı"
        global_label = f'Global Son ({global_price_type}): ${global_last_price:.2f}'
        plt.annotate(global_label, 
                    (global_last_date, global_last_price), 
                    textcoords="offset points", 
                    xytext=(-10,15), 
                    ha='right', fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1))
    
    # İstatistikleri ekle
    min_price = df['dollar_price'].min()
    max_price = df['dollar_price'].max()
    avg_price = df['dollar_price'].mean()
    
    stats_text = f"""Türkiye İstatistikleri ({price_type}):
En düşük: ${min_price:.2f}
En yüksek: ${max_price:.2f}
Ortalama: ${avg_price:.2f}
Veri sayısı: {len(df)}"""
    
    # Global istatistikleri de ekle (eğer varsa)
    if global_df is not None and len(global_df) > 0:
        global_min = global_df['dollar_price'].min()
        global_max = global_df['dollar_price'].max()
        global_avg = global_df['dollar_price'].mean()
        global_price_type = "GDP-Adjusted" if global_adjusted else "Ham"
        if inflation_adjusted:
            global_price_type = f"{global_price_type} + US CPI Enflasyon Ayarlı"
        
        stats_text += f"""

Global İstatistikleri ({global_price_type}):
En düşük: ${global_min:.2f}
En yüksek: ${global_max:.2f}
Ortalama: ${global_avg:.2f}"""
    
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
             fontsize=10)
    
    plt.tight_layout()
    
    # Grafik kaydetme
    if save:
        price_suffix = "_adjusted" if use_adjusted else ""
        inflation_suffix = "_inflation_adjusted" if inflation_adjusted else ""
        global_suffix = "_global_adjusted" if global_adjusted else ""
        if start_date and end_date:
            filename = f"graphs/Big_Mac_Dolar_Fiyatlari{price_suffix}{inflation_suffix}{global_suffix}_{start_date.replace('-', '_')}_{end_date.replace('-', '_')}.png"
        else:
            filename = f"graphs/Big_Mac_Dolar_Fiyatlari{price_suffix}{inflation_suffix}{global_suffix}_{datetime.now().strftime('%Y%m%d')}.png"
        try:
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Grafik kaydedildi: {filename}")
        except Exception as e:
            print(f"Grafik kaydedilirken hata oluştu: {e}")
    
    plt.show()

def analyze_price_trends(df, start_date=None, end_date=None, use_adjusted=False, inflation_adjusted=False):
    """
    Fiyat trendlerini analiz eder.
    
    Args:
        df: Big Mac verilerini içeren DataFrame
        start_date: Başlangıç tarihi
        end_date: Bitiş tarihi
        use_adjusted: GDP-adjusted fiyat kullanılıyor mu
        inflation_adjusted: US CPI ile enflasyon ayarlaması yapılıyor mu
    """
    print("\n" + "="*50)
    price_type = "GDP-ADJUSTED" if use_adjusted else "HAM"
    if inflation_adjusted:
        price_type = f"{price_type} + US CPI ENFLASYON AYARLI"
    print(f"BIG MAC {price_type} FİYAT ANALİZİ")
    print("="*50)
    
    # Tarih aralığı bilgisi
    date_info = ""
    if start_date or end_date:
        date_info = f" ({start_date or 'başlangıç'} - {end_date or 'bitiş'})"
    
    # Temel istatistikler
    print(f"Analiz dönemi{date_info}")
    print(f"Fiyat tipi: {price_type}")
    print(f"Toplam veri sayısı: {len(df)}")
    print(f"Tarih aralığı: {df['date'].min().strftime('%d-%m-%Y')} - {df['date'].max().strftime('%d-%m-%Y')}")
    print(f"En düşük fiyat: ${df['dollar_price'].min():.2f}")
    print(f"En yüksek fiyat: ${df['dollar_price'].max():.2f}")
    print(f"Ortalama fiyat: ${df['dollar_price'].mean():.2f}")
    print(f"Medyan fiyat: ${df['dollar_price'].median():.2f}")
    print(f"Standart sapma: ${df['dollar_price'].std():.2f}")
    
    # Yıllık değişim analizi (eğer yeterli veri varsa)
    if len(df) > 12:
        print(f"\nYILLIK DEĞİŞİM ANALİZİ:")
        print("-" * 30)
        
        df['year'] = df['date'].dt.year
        yearly_avg = df.groupby('year')['dollar_price'].mean()
        
        for i in range(1, min(len(yearly_avg), 6)):  # En fazla 5 yılın değişimini göster
            current_year = yearly_avg.index[i]
            previous_year = yearly_avg.index[i-1]
            current_price = yearly_avg.iloc[i]
            previous_price = yearly_avg.iloc[i-1]
            change = ((current_price - previous_price) / previous_price) * 100
            
            print(f"{previous_year} → {current_year}: ${previous_price:.2f} → ${current_price:.2f} ({change:+.1f}%)")
    
    # En yüksek ve en düşük fiyat tarihler
    min_idx = df['dollar_price'].idxmin()
    max_idx = df['dollar_price'].idxmax()
    
    print(f"\nEKSTREM DEĞERLER:")
    print("-" * 20)
    print(f"En düşük fiyat: ${df.loc[min_idx, 'dollar_price']:.2f} ({df.loc[min_idx, 'date'].strftime('%d-%m-%Y')})")
    print(f"En yüksek fiyat: ${df.loc[max_idx, 'dollar_price']:.2f} ({df.loc[max_idx, 'date'].strftime('%d-%m-%Y')})")
    
    # Toplam değişim
    first_price = df['dollar_price'].iloc[0]
    last_price = df['dollar_price'].iloc[-1]
    total_change = ((last_price - first_price) / first_price) * 100
    
    print(f"\nTOPLAM DEĞİŞİM:")
    print("-" * 15)
    print(f"İlk fiyat ({df['date'].iloc[0].strftime('%d-%m-%Y')}): ${first_price:.2f}")
    print(f"Son fiyat ({df['date'].iloc[-1].strftime('%d-%m-%Y')}): ${last_price:.2f}")
    print(f"Toplam değişim: {total_change:+.1f}%")

if __name__ == "__main__":
    # Argparse setup
    parser = argparse.ArgumentParser(description='Big Mac dolar fiyatları analiz scripti')
    parser.add_argument('--file', '-f', 
                        default='big-mac-data/output-data/big-mac-tr-index.csv', 
                        help='CSV dosya adı (default: big-mac-data/output-data/big-mac-tr-index.csv)')
    parser.add_argument('--start_date', '-s', 
                        default=None, 
                        help='Başlangıç tarihi (DD-MM-YYYY formatında)')
    parser.add_argument('--end_date', '-e', 
                        default=None, 
                        help='Bitiş tarihi (DD-MM-YYYY formatında)')
    parser.add_argument('--save', action='store_true', 
                        help='Grafiği dosya olarak kaydet')
    parser.add_argument('--no-values', action='store_true', 
                        help='Grafik üzerinde değerleri gösterme')
    parser.add_argument('--analysis-only', action='store_true', 
                        help='Sadece analiz yap, grafik çizme')
    parser.add_argument('--no-expand', action='store_true', 
                        help='6 aylık veriyi aylık hale getirme')
    parser.add_argument('--add-global-average', action='store_true', 
                        help='Grafik üzerine global ortalama fiyatları ekle')
    parser.add_argument('--adjusted-turkey', action='store_true', 
                        help='Türkiye için GDP-adjusted fiyatları kullan (adj_price kolonu)')
    parser.add_argument('--add-adjusted-global', action='store_true', 
                        help='Grafik üzerine global GDP-adjusted ortalama fiyatları ekle')
    parser.add_argument('--enf-adjusted', action='store_true', 
                        help='US CPI verilerini kullanarak enflasyon ayarlı fiyatları hesapla')
    parser.add_argument('--base-date', 
                        help='Enflasyon ayarlaması için baz tarih (YYYY-MM-DD formatında). Belirtilmezse ilk tarih kullanılır.')
    
    args = parser.parse_args()
    
    # Veriyi oku
    df = read_big_mac_data(args.file, 
                           start_date=args.start_date, 
                           end_date=args.end_date,
                           expand_monthly=not args.no_expand,
                           use_adjusted=args.adjusted_turkey,
                           inflation_adjusted=args.enf_adjusted,
                           base_date=args.base_date)
    
    if df is None or len(df) == 0:
        print("Hata: Veri okunamadı veya filtreleme sonrası veri kalmadı!")
        exit(1)
    
    # Global ortalama verilerini oku (eğer isteniyorsa)
    global_df = None
    global_adjusted = False
    
    if args.add_global_average or args.add_adjusted_global:
        global_adjusted = args.add_adjusted_global
        global_type = "GDP-adjusted" if global_adjusted else "ham"
        if args.enf_adjusted:
            global_type = f"{global_type} + US CPI enflasyon ayarlı"
        print(f"\nGlobal {global_type} ortalama verileri okunuyor...")
        global_df = read_global_big_mac_data(start_date=args.start_date, 
                                           end_date=args.end_date,
                                           expand_monthly=not args.no_expand,
                                           use_adjusted=global_adjusted,
                                           inflation_adjusted=args.enf_adjusted,
                                           base_date=args.base_date)
        if global_df is None or len(global_df) == 0:
            print("Uyarı: Global ortalama verisi okunamadı, sadece Türkiye verisi gösterilecek!")
            global_df = None
    
    # Analiz yap
    analyze_price_trends(df, start_date=args.start_date, end_date=args.end_date, use_adjusted=args.adjusted_turkey, inflation_adjusted=args.enf_adjusted)
    
    # Grafik çiz (eğer sadece analiz istenmemişse)
    if not args.analysis_only:
        plot_big_mac_prices(df, 
                           save=args.save, 
                           show_values=not args.no_values,
                           start_date=args.start_date,
                           end_date=args.end_date,
                           global_df=global_df,
                           use_adjusted=args.adjusted_turkey,
                           global_adjusted=global_adjusted,
                           inflation_adjusted=args.enf_adjusted) 