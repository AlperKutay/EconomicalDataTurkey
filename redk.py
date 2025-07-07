from evds import evdsAPI
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import numpy as np
from datetime import datetime
from enag_subs_tufe_2 import calculate_enag_subtract_tufe
from enf import analyze_economic_data
from big_mac_analysis import read_big_mac_data

def fetch_and_process_redk_data(start_date, end_date, api_key='kk11ju7Bis', verbose=False):
    """
    TP.RK.T1.Y verisini çeker ve işler.
    
    Args:
        start_date: Başlangıç tarihi (DD-MM-YYYY formatında)
        end_date: Bitiş tarihi (DD-MM-YYYY formatında)
        api_key: EVDS API anahtarı
        verbose: Detaylı çıktı göster
        
    Returns:
        df_redk: İşlenmiş REDK verisi içeren dataframe
        start_idx: 09-2020 tarihinin indeksi
    """
    evds = evdsAPI(api_key)
    
    try:
        df_redk = evds.get_data(
            series=["TP.RK.T1.Y"],
            startdate=start_date,
            enddate=end_date,
            frequency=5
        )
        
        print("Veri başarıyla çekildi!")
        if verbose:
            print(f"Veri boyutu: {df_redk.shape}")
            print(f"Kolonlar: {df_redk.columns.tolist()}")
            print(f"İlk 5 satır:\n{df_redk.head()}")
        
    except Exception as e:
        print(f"Veri çekilirken hata oluştu: {e}")
        return None, None

    # Veri işleme
    df_redk = df_redk.sort_index()
    df_redk["TP_RK_T1_Y"] = pd.to_numeric(df_redk["TP_RK_T1_Y"], errors="coerce")

    # Tarih sütununu doğru datetime formatına çevir
    df_redk["Tarih"] = pd.to_datetime(df_redk["Tarih"])

    # NaN değerleri temizle
    df_redk = df_redk.dropna()

    if df_redk.empty:
        print("Uyarı: Veri bulunamadı veya tüm değerler NaN!")
        return None, None

    print(f"İşlenen veri sayısı: {len(df_redk)}")
    print(f"En düşük değer: {df_redk['TP_RK_T1_Y'].min():.2f}")
    print(f"En yüksek değer: {df_redk['TP_RK_T1_Y'].max():.2f}")
    print(f"Ortalama değer: {df_redk['TP_RK_T1_Y'].mean():.2f}")

    # Tarih formatını düzenle (datetime objelerinden)
    df_redk["Ay-Yıl"] = df_redk["Tarih"].dt.strftime("%m-%Y")

    # 09-2020'den itibaren olan değerleri bul
    start_idx = None
    for i, row in df_redk.iterrows():
        date = row["Tarih"]
        if date.year == 2020 and date.month == 9:
            start_idx = df_redk.index.get_loc(i)
            break

    if start_idx is None:
        print("Uyarı: 09-2020 tarihi bulunamadı!")
        return df_redk, None
    
    return df_redk, start_idx

def calculate_redk_multipliers(df_redk, start_idx, data, average_enag_tufe=False, enag_only=False, verbose=False):
    """
    REDK değerlerini çarpanlarla çarpar.
    
    Args:
        df_redk: REDK verisi içeren dataframe
        start_idx: 09-2020 tarihinin indeksi
        multiplier_values: Çarpan değerleri
        verbose: Detaylı çıktı göster
        
    Returns:
        df_redk: Çarpım sonuçları eklenmiş dataframe
    """
    if start_idx is None:
        return df_redk

    tufe_data = data["TÜFE Endeksi"]
    enag_and_tufe_avg_data = data["ENAG Ortalama (12 Ay)"]
    enag_data = data["ENAG Endeksi"]
    usd_value = data["USD Ham Değer"]
    if average_enag_tufe:
        calculated_values = enag_and_tufe_avg_data
    elif enag_only:
        calculated_values = enag_data
    else:
        calculated_values = tufe_data

    # Kümülatif çarpım için yeni kolon oluştur
    df_redk["Çarpım Sonucu"] = np.nan

    # 01-09-2020 öncesi için orijinal REDK değerlerini ekle
    if start_idx > 0:
        print(f"01-09-2020 öncesi için orijinal REDK değerleri ekleniyor...")
        for i in range(0, start_idx):
            df_redk.loc[df_redk.index[i], "Çarpım Sonucu"] = df_redk["TP_RK_T1_Y"].iloc[i]
            if verbose and i < 5:
                print(f"Tarih: {df_redk['Ay-Yıl'].iloc[i]}, Değer: {df_redk['TP_RK_T1_Y'].iloc[i]:.2f}")

    # İlk değeri al
    first_redk_value = df_redk["TP_RK_T1_Y"].iloc[start_idx]
    print(f"Başlangıç değeri (09-2020): {first_redk_value}")

    # İlk değer için çarpan yok, direkt kopyala
    df_redk.loc[df_redk.index[start_idx], "Çarpım Sonucu"] = first_redk_value

    if verbose:
        print(f"\nBasit Çarpım Hesaplaması (İlk 10):")
        print("=" * 100)
        print(f"{'Tarih':<10} {'REDK':<8} {'Çarpan':<8} {'Hesaplama':<25} {'Sonuç':<10}")
        print("-" * 100)

        # İlk değeri göster
        print(f"{'09-2020':<10} {first_redk_value:<8.2f} {'Başlangıç':<8} {'Başlangıç Değeri':<25} {first_redk_value:<10.2f}")

    # Minimum uzunluğu bul
    max_calc_idx = min(len(calculated_values), len(df_redk) - start_idx)

    # Her bir REDK değerini ilgili çarpanla çarp
    for i in range(1, max_calc_idx):
        idx = start_idx + i
        if idx < len(df_redk):
            date = df_redk["Ay-Yıl"].iloc[idx]
            redk_value = df_redk["TP_RK_T1_Y"].iloc[idx]
            
            # Basit çarpım - Her REDK değerini kendi çarpanıyla çarp
            enf_diff = (redk_value * usd_value.iloc[idx]) 
            enf_new = (enf_diff * calculated_values.iloc[idx] / tufe_data.iloc[idx])
            redk_new = (enf_new / usd_value.iloc[idx])
            df_redk.loc[df_redk.index[idx], "Çarpım Sonucu"] = redk_new
            
            # İlk 10 değeri göster
            if verbose and i < 10:
                calculation = f"100 / (100 / {redk_value:.2f} + {calculated_values[i-1]:.4f})"
                print(f"{date:<10} {redk_value:<8.2f} {calculation:<25} {redk_new:<10.2f}")
    
    return df_redk

# Argparse setup
parser = argparse.ArgumentParser(description='TP.RK.T1.Y veri analizi scripti')
parser.add_argument('--start_date', '-s', 
                    default='01-01-2005', 
                    help='Başlangıç tarihi (DD-MM-YYYY formatında, default: 01-01-2020)')
parser.add_argument('--end_date', '-e', 
                    default='01-06-2025', 
                    help='Bitiş tarihi (DD-MM-YYYY formatında, default: 01-01-2025)')
parser.add_argument('--verbose', '-v', action='store_true', help='Verbose mod')
parser.add_argument('--save', action='store_true', help='Grafiği dosya olarak kaydet')
parser.add_argument('--save_name', type=str, help='Grafiği dosya olarak kaydet')
parser.add_argument('--normalize', action='store_true', help='Normalize et')
parser.add_argument('--average_enag_tufe', action='store_true', help='ENAG ve TÜFE ortalamasını kullan')
parser.add_argument('--enag_only', action='store_true', help='ENAG verisini kullan')
parser.add_argument('--tufe_only', action='store_true', help='TÜFE verisini kullan')
parser.add_argument('--add_big_mac', action='store_true', help='Big Mac verisini kullan')
parser.add_argument('--same_scale', action='store_true', help='Aynı eksen skalası kullan')
args = parser.parse_args()

if __name__ == "__main__":
    start_date = args.start_date
    end_date = args.end_date
    if args.average_enag_tufe and args.enag_only:
        print("Hata: average_enag_tufe ve enag_only aynı anda kullanılamaz!")
        exit(1)
    if args.same_scale and args.add_big_mac:
        print("Hata: same_scale ve add_big_mac aynı anda kullanılamaz!")
        exit(1)
    print(f"TP.RK.T1.Y verisi çekiliyor: {start_date} - {end_date}")

    data = analyze_economic_data(
        start_date=args.start_date,
        end_date=args.end_date,
        include_enag=True,
        verbose=args.verbose,
        normalize=args.normalize
    )

    # REDK verisini çek ve işle
    df_redk, start_idx = fetch_and_process_redk_data(start_date, end_date, verbose=args.verbose)
    
    if df_redk is None or start_idx is None:
        exit(1)
        
    # REDK değerlerini çarpanlarla çarp
    df_redk = calculate_redk_multipliers(df_redk, start_idx, data, average_enag_tufe=args.average_enag_tufe, enag_only=args.enag_only, verbose=args.verbose)

    # Big Mac verisini oku
    if args.add_big_mac:
        print("\nBig Mac verisi okunuyor...")
        df_bigmac = read_big_mac_data('big-mac-full-index.csv', 
                                    start_date=start_date, 
                                    end_date=end_date, 
                                    expand_monthly=True)
    
    if not args.same_scale:
            # Grafik oluştur - 3 alt grafik
        num_plots = 3 if args.add_big_mac else 2
        num_plots = num_plots + 1 if args.tufe_only else num_plots
        plt.figure(figsize=(16, 15))

        # İlk grafik: REDK
        plt.subplot(num_plots, 1, 1)
        plt.plot(df_redk["Tarih"], df_redk["TP_RK_T1_Y"], 
                label="TP.RK.T1.Y", linewidth=2, color='blue')
        plt.title(f"TP.RK.T1.Y Veri Analizi ({start_date} - {end_date})", fontsize=14)
        plt.ylabel("Değer")
        plt.legend()
        plt.grid(True, alpha=0.3)

        # X ekseni formatını ayarla - 6 ayda bir (tarihleri doğru formatla)
        ax1 = plt.gca()
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        # Her 10 datada bir değer göster
        step = max(1, len(df_redk) // 10)
        for i in range(0, len(df_redk), step):
            date = df_redk["Tarih"].iloc[i]
            value = df_redk["TP_RK_T1_Y"].iloc[i]
            if pd.notna(value) and np.isfinite(value):
                plt.text(date, value, f'{value:.1f}', 
                        ha='center', va='bottom', fontsize=8, color='blue')

        # İkinci grafik: (ENAG + TÜFE)/2 Yeniden Oranlı
        plt.subplot(num_plots, 1, 2)
        plt.plot(df_redk["Tarih"], df_redk["Çarpım Sonucu"], 
                label="(ENAG + TÜFE)/2 Yeniden Oranlı", linewidth=2, color='green')
        plt.title(f"(ENAG + TÜFE)/2 Yeniden Oranlı", fontsize=14)
        plt.ylabel("Değer")
        plt.legend()
        plt.grid(True, alpha=0.3)

        # X ekseni formatını ayarla - 6 ayda bir (tarihleri doğru formatla)
        ax2 = plt.gca()
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        # Her 10 datada bir değer göster
        valid_indices = df_redk.index[df_redk["Çarpım Sonucu"].notna()]
        step = max(1, len(valid_indices) // 10)
        for i in range(0, len(valid_indices), step):
            idx = valid_indices[i]
            date = df_redk.loc[idx, "Tarih"]
            value = df_redk.loc[idx, "Çarpım Sonucu"]
            if pd.notna(value) and np.isfinite(value):
                plt.text(date, value, f'{value:.1f}', 
                        ha='center', va='bottom', fontsize=8, color='green')

        # Üçüncü grafik: Big Mac Dolar Fiyatları
        if args.add_big_mac:
            if df_bigmac is not None:
                plt.subplot(num_plots, 1, 3)
                plt.plot(df_bigmac['date'], df_bigmac['dollar_price'], 
                        marker='o', linewidth=2, markersize=4, 
                        color='#e74c3c', markerfacecolor='white', 
                        markeredgecolor='#e74c3c', markeredgewidth=1)
                
                plt.title('Türkiye Big Mac Dolar Fiyatları', fontsize=14)
                plt.xlabel("Tarih")
                plt.ylabel("Dolar Fiyatı ($)")
                plt.grid(True, alpha=0.3)
                
                # X ekseni formatını ayarla - 6 ayda bir (Big Mac için de)
                ax3 = plt.gca()
                ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
                ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
                plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
                
                # Y ekseni formatı
                ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))
                
                # Her 5 datada bir değer göster
                for i in range(0, len(df_bigmac), 5):
                    date = df_bigmac['date'].iloc[i]
                    price = df_bigmac['dollar_price'].iloc[i]
                    if pd.notna(price) and np.isfinite(price):
                        plt.text(date, price, f'${price:.2f}', 
                                ha='center', va='bottom', fontsize=7, color='red')
                
                # Son değeri vurgula
                last_date = df_bigmac['date'].iloc[-1]
                last_price = df_bigmac['dollar_price'].iloc[-1]
                plt.text(last_date, last_price + 0.2, f'${last_price:.2f}', 
                        ha='center', va='bottom', fontsize=8, fontweight='bold', 
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='lightgreen', alpha=0.8))
            else:
                plt.text(0.5, 0.5, 'Big Mac verisi yüklenemedi', ha='center', va='center', 
                        transform=plt.gca().transAxes, fontsize=12)
                plt.title('Big Mac Verisi - Hata', fontsize=14)
        if args.save:
            if args.save_name:
                filename = args.save_name
            else:
                filename = f"REDK_BigMac_{start_date.replace('-', '_')}_{end_date.replace('-', '_')}.png"
            
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Grafik kaydedildi: {filename}")
                
        else:
            plt.tight_layout()
            #plt.show()

    # Grafik kaydetme
    if args.same_scale:
        
        # Kümülatif çarpım grafiği oluştur ve kaydet
        plt.figure(figsize=(16, 8))
        plt.plot(df_redk["Tarih"], df_redk["Çarpım Sonucu"], 
                label="REDK Kümülatif Çarpım", linewidth=2, color='purple')
        plt.plot(df_redk["Tarih"], df_redk["TP_RK_T1_Y"], 
                label="Orijinal REDK", linewidth=2, color='blue', linestyle='--', alpha=0.7)
        plt.title(f"REDK Kümülatif Çarpım Analizi ({start_date} - {end_date})", fontsize=14)
        plt.xlabel("Tarih")
        plt.ylabel("Değer")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # X ekseni formatını ayarla - 6 ayda bir
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.xticks(rotation=45)
        
        # Her 10 datada bir değer göster
        valid_indices = df_redk.index[df_redk["Çarpım Sonucu"].notna()]
        step = max(1, len(valid_indices) // 10)
        for i in range(0, len(valid_indices), step):
            idx = valid_indices[i]
            date = df_redk.loc[idx, "Tarih"]
            value = df_redk.loc[idx, "Çarpım Sonucu"]
            if pd.notna(value) and np.isfinite(value):
                plt.text(date, value, f'{value:.1f}', 
                        ha='center', va='bottom', fontsize=8, color='purple')
        
        plt.tight_layout()
        
        # Kümülatif çarpım grafiğini kaydet
        if args.save:
            if args.save_name:
                filename = args.save_name
            else:
                filename = f"REDK_Kumulatif_Carpim_{start_date.replace('-', '_')}_{end_date.replace('-', '_')}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            if args.verbose:
                print(f"Grafik kaydedildi: {filename}")
        else:
            plt.show()


        

    if args.verbose:
        # Özet istatistikler
        print("\n" + "="*50)
        print("ÖZET İSTATİSTİKLER - ORİJİNAL REDK")
        print("="*50)
        print(f"Veri Sayısı: {len(df_redk)}")
        print(f"Ortalama: {df_redk['TP_RK_T1_Y'].mean():.4f}")
        print(f"Medyan: {df_redk['TP_RK_T1_Y'].median():.4f}")
        print(f"Standart Sapma: {df_redk['TP_RK_T1_Y'].std():.4f}")
        print(f"Minimum: {df_redk['TP_RK_T1_Y'].min():.4f}")
        print(f"Maksimum: {df_redk['TP_RK_T1_Y'].max():.4f}")

        # Kümülatif çarpım istatistikleri
        valid_results = df_redk["Çarpım Sonucu"].dropna()
        print("\n" + "="*50)
        print("ÖZET İSTATİSTİKLER - ÇARPIM SONUÇLARI")
        print("="*50)
        print(f"Veri Sayısı: {len(valid_results)}")
        print(f"Ortalama: {valid_results.mean():.4f}")
        print(f"Medyan: {valid_results.median():.4f}")
        print(f"Standart Sapma: {valid_results.std():.4f}")
        print(f"Minimum: {valid_results.min():.4f}")
        print(f"Maksimum: {valid_results.max():.4f}")
        print(f"İlk Değer: {valid_results.iloc[0]:.4f}")
        print(f"Son Değer: {valid_results.iloc[-1]:.4f}")

        # Değişim analizi
        if len(valid_results) > 1:
            first_value = valid_results.iloc[0]
            last_value = valid_results.iloc[-1]
            total_change = last_value - first_value
            percent_change = (total_change / first_value) * 100
            
            if args.verbose:
                print(f"\nDEĞİŞİM ANALİZİ - ÇARPIM SONUÇLARI:")
                print(f"Toplam Değişim: {total_change:.4f}")
                print(f"Yüzde Değişim: {percent_change:.2f}%")

        # Big Mac istatistikleri
        if df_bigmac is not None:
            print("\n" + "="*50)
            print("ÖZET İSTATİSTİKLER - BIG MAC DOLAR FİYATLARI")
            print("="*50)
            print(f"Veri Sayısı: {len(df_bigmac)}")
            print(f"Ortalama: ${df_bigmac['dollar_price'].mean():.2f}")
            print(f"Medyan: ${df_bigmac['dollar_price'].median():.2f}")
            print(f"Standart Sapma: ${df_bigmac['dollar_price'].std():.2f}")
            print(f"Minimum: ${df_bigmac['dollar_price'].min():.2f}")
            print(f"Maksimum: ${df_bigmac['dollar_price'].max():.2f}")
            print(f"İlk Değer: ${df_bigmac['dollar_price'].iloc[0]:.2f}")
            print(f"Son Değer: ${df_bigmac['dollar_price'].iloc[-1]:.2f}")
