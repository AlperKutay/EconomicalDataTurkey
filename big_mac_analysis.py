import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import argparse

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

def read_big_mac_data(filename='big-mac-full-index.csv', start_date=None, end_date=None, expand_monthly=True):
    """
    Big Mac CSV dosyasını okur ve işler.
    
    Args:
        filename: CSV dosya adı
        start_date: Başlangıç tarihi (DD-MM-YYYY formatında)
        end_date: Bitiş tarihi (DD-MM-YYYY formatında)
        expand_monthly: 6 aylık veriyi aylık hale getir
        
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
        numeric_columns = ['local_price', 'dollar_ex', 'dollar_price']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
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
        
        if len(df) > 0:
            print(f"Tarih aralığı: {df['date'].min()} - {df['date'].max()}")
            print(f"Dolar fiyat aralığı: ${df['dollar_price'].min():.2f} - ${df['dollar_price'].max():.2f}")
        else:
            print("Uyarı: Filtreleme sonrası veri kalmadı!")
        
        return df
        
    except Exception as e:
        print(f"Veri okuma hatası: {e}")
        return None

def plot_big_mac_prices(df, save=False, show_values=True, start_date=None, end_date=None):
    """
    Big Mac dolar fiyatlarının grafiğini çizer.
    
    Args:
        df: Big Mac verilerini içeren DataFrame
        save: Grafiği dosya olarak kaydet
        show_values: Grafik üzerinde değerleri göster
        start_date: Başlangıç tarihi (dosya adı için)
        end_date: Bitiş tarihi (dosya adı için)
    """
    plt.figure(figsize=(16, 10))
    
    # Ana grafik
    plt.plot(df['date'], df['dollar_price'], 
             marker='o', linewidth=2, markersize=6, 
             color='#e74c3c', markerfacecolor='white', 
             markeredgecolor='#e74c3c', markeredgewidth=2)
    
    # Grafik düzenlemeleri
    date_range = f"({df['date'].min().strftime('%m-%Y')} - {df['date'].max().strftime('%m-%Y')})"
    plt.title(f'Türkiye Big Mac Dolar Fiyatları {date_range}', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Tarih', fontsize=12)
    plt.ylabel('Dolar Fiyatı ($)', fontsize=12)
    
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
    plt.annotate(f'Son: ${last_price:.2f}', 
                (last_date, last_price), 
                textcoords="offset points", 
                xytext=(10,15), 
                ha='left', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='black', lw=1))
    
    # İstatistikleri ekle
    min_price = df['dollar_price'].min()
    max_price = df['dollar_price'].max()
    avg_price = df['dollar_price'].mean()
    
    stats_text = f"""İstatistikler:
En düşük: ${min_price:.2f}
En yüksek: ${max_price:.2f}
Ortalama: ${avg_price:.2f}
Veri sayısı: {len(df)}"""
    
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
             fontsize=10)
    
    plt.tight_layout()
    
    # Grafik kaydetme
    if save:
        if start_date and end_date:
            filename = f"Big_Mac_Dolar_Fiyatlari_{start_date.replace('-', '_')}_{end_date.replace('-', '_')}.png"
        else:
            filename = f"Big_Mac_Dolar_Fiyatlari_{datetime.now().strftime('%Y%m%d')}.png"
        try:
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Grafik kaydedildi: {filename}")
        except Exception as e:
            print(f"Grafik kaydedilirken hata oluştu: {e}")
    
    plt.show()

def analyze_price_trends(df, start_date=None, end_date=None):
    """
    Fiyat trendlerini analiz eder.
    
    Args:
        df: Big Mac verilerini içeren DataFrame
        start_date: Başlangıç tarihi
        end_date: Bitiş tarihi
    """
    print("\n" + "="*50)
    print("BIG MAC FİYAT ANALİZİ")
    print("="*50)
    
    # Tarih aralığı bilgisi
    date_info = ""
    if start_date or end_date:
        date_info = f" ({start_date or 'başlangıç'} - {end_date or 'bitiş'})"
    
    # Temel istatistikler
    print(f"Analiz dönemi{date_info}")
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
                        default='big-mac-full-index.csv', 
                        help='CSV dosya adı (default: big-mac-full-index.csv)')
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
    
    args = parser.parse_args()
    
    # Veriyi oku
    df = read_big_mac_data(args.file, 
                           start_date=args.start_date, 
                           end_date=args.end_date,
                           expand_monthly=not args.no_expand)
    
    if df is None or len(df) == 0:
        print("Hata: Veri okunamadı veya filtreleme sonrası veri kalmadı!")
        exit(1)
    
    # Analiz yap
    analyze_price_trends(df, start_date=args.start_date, end_date=args.end_date)
    
    # Grafik çiz (eğer sadece analiz istenmemişse)
    if not args.analysis_only:
        plot_big_mac_prices(df, 
                           save=args.save, 
                           show_values=not args.no_values,
                           start_date=args.start_date,
                           end_date=args.end_date) 