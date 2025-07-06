from evds import evdsAPI
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import numpy as np
from enag import enag_kumulatif_yuzde
from tufe_filter import filter_tufe_until_august_2020
from datetime import datetime


# EVDS API Key
API_KEY = 'kk11ju7Bis'
evds = evdsAPI(API_KEY)

def check_time_range(start_date, end_date):
    start_date_obj = None
    september_2020 = datetime.strptime('01-09-2020', '%d-%m-%Y')
    try:
        start_date_obj = datetime.strptime(start_date, '%d-%m-%Y')
        if start_date_obj < september_2020:
            print(f"Uyarı: Girilen başlangıç tarihi ({start_date}) Eylül 2020'den önce.")
        return start_date_obj,september_2020
    except ValueError:
        print(f"Uyarı: Tarih formatı hatalı olabilir: {start_date}")
        return None,None

def get_evds_data(series, start_date, end_date, frequency, formulas=None):
    if formulas is not None:
        df = evds.get_data(
            series=series,
            startdate=start_date,
            enddate=end_date,
            frequency=frequency,
            formulas=formulas
        )
    else:
        df = evds.get_data(
            series=series,
            startdate=start_date,
            enddate=end_date,
            frequency=frequency,
        )
    return df

def get_evds_data_and_normalize(series, start_date, end_date, frequency,formulas=None, keep_raw=False, normalize=False):
    df = get_evds_data(series, start_date, end_date, frequency,formulas)
    df = df.sort_index()
    
    # series listesinden ilk elementi al
    series_name = series[0]
    
    # Kolon adını düzelt (nokta yerine alt çizgi olabilir)
    actual_column = None
    for col in df.columns:
        if col.replace('_', '.') == series_name or col == series_name:
            actual_column = col
            break
    
    if actual_column is None:
        print(f"Hata: {series_name} kolonu bulunamadı. Mevcut kolonlar: {df.columns.tolist()}")
        return df, None
    
    df[actual_column] = pd.to_numeric(df[actual_column], errors="coerce")
    
    # Ham değeri sakla (eğer istenirse)
    if keep_raw:
        df[actual_column + "_HAM"] = df[actual_column].copy()
    
    # Normalize et
    if normalize:
        df[actual_column] = df[actual_column] * (100 / df[actual_column].iloc[0])
    return df, actual_column

def enag_calculation(df_tufe,tufe_column, start_date, start_date_obj,september_2020, end_date, args):
    combined_data = None  # Initialize combined_data
    if start_date_obj is not None and start_date_obj < september_2020:
        filtered_tufe_df = filter_tufe_until_august_2020(df_tufe, start_date,args.verbose)
        # Normalizasyon sonrası kolon adını kullan
        if args.normalize:
            tufe_col_name = 'TÜFE Endeksi (Başlangıç = 100)' if 'TÜFE Endeksi (Başlangıç = 100)' in filtered_tufe_df.columns else tufe_column
        else:
            tufe_col_name = 'TÜFE Endeksi' if 'TÜFE Endeksi' in filtered_tufe_df.columns else tufe_column
        filtered_tufe_values = filtered_tufe_df[tufe_col_name]
        if args.normalize:
            normalized_filtered_tufe = filtered_tufe_values * 100 / filtered_tufe_values.iloc[0]
        else:
            normalized_filtered_tufe = filtered_tufe_values
        print("Filtered TÜFE Data (normalized to 100):")
        
        start_date_enag = '09-2020'
        enag_list = enag_kumulatif_yuzde(normalized_filtered_tufe.iloc[-1], start_date_enag, args.verbose)
        normalized_filtered_tufe = normalized_filtered_tufe.iloc[:-1]
        
        # Combine filtered TÜFE and ENAG data
        combined_data = list(normalized_filtered_tufe) + enag_list
        print(f"Combined data length: {len(combined_data)}")
        print(f"Filtered TÜFE length: {len(normalized_filtered_tufe)}")
        print(f"ENAG list length: {len(enag_list)}")
        
        #print(normalized_filtered_tufe)
        #print(enag_list)
        #print(combined_data)
    else:
        start_date_enag = args.start_date.split('-')[1] + '-' + args.start_date.split('-')[2]
        if args.normalize:
            enag_list = enag_kumulatif_yuzde(100, start_date_enag, args.verbose)
        else:
            enag_list = enag_kumulatif_yuzde(df_tufe["TÜFE Endeksi"].iloc[0], start_date_enag, args.verbose)
    
    # Truncate ENAG data to match TÜFE data length
    tufe_length = len(df_tufe["Tarih"])
    
    # Use combined data if start date is before September 2020, otherwise use enag_list
    if combined_data is not None:
        enag_list_truncated = combined_data[:tufe_length]
    else:
        enag_list_truncated = enag_list[:tufe_length]
    
    # ENAG average hesapla (ENAG ve USD/TRY ortalması)
    if args.normalize:
        tufe_values = df_tufe["TÜFE Endeksi (Başlangıç = 100)"][:tufe_length]
    else:
        tufe_values = df_tufe["TÜFE Endeksi"][:tufe_length]

    enag_average = [(enag_val + tufe_val) / 2 for enag_val, tufe_val in zip(enag_list_truncated, tufe_values)]
    
    if args.normalize:
        enag_data = pd.DataFrame({
            'ENAG Endeksi (Başlangıç = 100)': enag_list_truncated,
            'ENAG Ortalama (12 Ay)': enag_average
        }, index=df_tufe["Tarih"])
    else:
        enag_data = pd.DataFrame({
            'ENAG Endeksi': enag_list_truncated,
            'ENAG Ortalama (12 Ay)': enag_average
        }, index=df_tufe["Tarih"])
    return enag_data

def combine_dataframes(df_tufe, df_usd, enag_data=None, normalize=False):
    """
    İki veya daha fazla dataframe'i birleştirir ve standart kolon adları atar.
    
    Args:
        df_tufe: TÜFE verilerini içeren dataframe
        df_usd: USD/TRY verilerini içeren dataframe
        enag_data: ENAG verilerini içeren dataframe (opsiyonel)
        normalize: Normalize edilmiş veriler kullanılıyorsa True
        
    Returns:
        combined_df: Birleştirilmiş dataframe
    """
    # Her iki dataframe'in indexini eşitle
    df_tufe.index = df_tufe["Tarih"]
    df_usd.index = df_usd["Tarih"]

    # Doğru kolon adlarını bul
    tufe_endeks_col = None
    usd_endeks_col = None
    usd_ham_col = None

    for col in df_tufe.columns:
        if 'TÜFE' in col and 'Endeks' in col:
            tufe_endeks_col = col
            break

    for col in df_usd.columns:
        if 'USD' in col and 'Endeks' in col:
            usd_endeks_col = col
        elif 'USD' in col and 'Ham' in col:
            usd_ham_col = col

    # Birleştir ve çiz
    if tufe_endeks_col and usd_endeks_col and usd_ham_col:
        combined_df = pd.merge(
            df_tufe[[tufe_endeks_col]],
            df_usd[[usd_endeks_col, usd_ham_col]],
            left_index=True,
            right_index=True,
            how="inner"
        )
        # Kolon adlarını standartlaştır
        if normalize:
            combined_df.rename(columns={
                tufe_endeks_col: "TÜFE Endeksi (Başlangıç = 100)",
                usd_endeks_col: "USD Endeksi (Başlangıç = 100)",
                usd_ham_col: "USD Ham Değer"
            }, inplace=True)
        else:
            combined_df.rename(columns={
                tufe_endeks_col: "TÜFE Endeksi",
                usd_endeks_col: "USD Endeksi",
                usd_ham_col: "USD Ham Değer"
            }, inplace=True)
    else:
        raise ValueError("Hata: Gerekli kolonlar bulunamadı!")

    if enag_data is not None:
        # Merge ENAG data with existing data
        combined_df = pd.merge(
            combined_df,
            enag_data,
            left_index=True,
            right_index=True,
            how="inner"
        )
    
    return combined_df

def analyze_economic_data(start_date='01-09-2020', end_date='01-07-2025', include_enag=False, 
                         verbose=False, normalize=False):
    """
    TÜFE ve USD/TRY verilerini analiz eder ve birleştirilmiş dataframe döndürür.
    
    Args:
        start_date: Başlangıç tarihi (DD-MM-YYYY formatında)
        end_date: Bitiş tarihi (DD-MM-YYYY formatında)
        include_enag: ENAG verilerini dahil et
        verbose: Detaylı çıktı göster
        normalize: Verileri normalize et
        
    Returns:
        combined_df: Birleştirilmiş dataframe
    """
    start_date_obj, september_2020 = check_time_range(start_date, end_date)

    print(f"Veri çekiliyor: {start_date} - {end_date}")

    df_tufe, tufe_column = get_evds_data_and_normalize(["TP.FE.OKTG01"], start_date, end_date, 5, normalize=normalize)
    if tufe_column:
        if normalize:
            df_tufe.rename(columns={tufe_column: "TÜFE Endeksi (Başlangıç = 100)"}, inplace=True)
        else:
            df_tufe.rename(columns={tufe_column: "TÜFE Endeksi"}, inplace=True)

    df_usd, usd_column = get_evds_data_and_normalize(["TP.DK.USD.S.YTL"], start_date, end_date, 5, keep_raw=True, normalize=normalize)
    if usd_column:
        # Ham USD değerlerini doğru şekilde al
        df_usd["USD Ham Değer"] = df_usd[usd_column + "_HAM"]
        if normalize:
            df_usd.rename(columns={usd_column: "USD Endeksi (Başlangıç = 100)"}, inplace=True)
        else:
            df_usd.rename(columns={usd_column: "USD Endeksi"}, inplace=True)

    # ENAG verilerini hazırla
    enag_data = None
    if include_enag:
        # Argparse args nesnesini taklit et
        class Args:
            def __init__(self):
                self.normalize = normalize
                self.verbose = verbose
                self.start_date = start_date
                
        args = Args()
        enag_data = enag_calculation(df_tufe, tufe_column, start_date, start_date_obj, september_2020, end_date, args)

    try:
        # Dataframe'leri birleştir
        combined_df = combine_dataframes(df_tufe, df_usd, enag_data, normalize)
        return combined_df
    except ValueError as e:
        print(e)
        return None

def plot_economic_data(df, include_enag=False, normalize=False, save_path=None):
    """
    Ekonomik verileri grafikle gösterir.
    
    Args:
        df: Çizilecek veri içeren dataframe
        include_enag: ENAG verilerini dahil et
        normalize: Normalize edilmiş veriler kullanılıyorsa True
        save_path: Grafiğin kaydedileceği dosya yolu (None ise kaydetmez)
    """
    # Grafik
    plt.figure(figsize=(16, 8))
    if normalize:
        plt.plot(df.index, df["TÜFE Endeksi (Başlangıç = 100)"], label="TÜFE Endeksi", linewidth=2)
        plt.plot(df.index, df["USD Endeksi (Başlangıç = 100)"], label="USD/TRY Endeksi", linewidth=2)
    else:
        plt.plot(df.index, df["TÜFE Endeksi"], label="TÜFE Endeksi", linewidth=2)
        plt.plot(df.index, df["USD Endeksi"], label="USD/TRY Endeksi", linewidth=2)
    plt.plot(df.index, df["USD Ham Değer"], label="USD/TRY Ham Değer", linewidth=2, linestyle='--')

    if include_enag:
        if normalize:
            plt.plot(df.index, df["ENAG Endeksi (Başlangıç = 100)"], label="ENAG Endeksi", linewidth=2)
            plt.plot(df.index, df["ENAG Ortalama (12 Ay)"], label="ENAG Ortalama", linewidth=2, linestyle=':', alpha=0.8)
        else:
            plt.plot(df.index, df["ENAG Endeksi"], label="ENAG Endeksi", linewidth=2)
            plt.plot(df.index, df["ENAG Ortalama (12 Ay)"], label="ENAG Ortalama", linewidth=2, linestyle=':', alpha=0.8)

    title = "TÜFE ve USD/TRY Endeksi Karşılaştırması"
    if include_enag:
        title += " (ENAG ile)"
    if normalize:
        title += " (Başlangıç Tarihi = 100)"

    plt.title(title)
    plt.xlabel("Tarih")
    plt.ylabel("Endeks")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Her 5 datada bir değer göster
    for i in range(0, len(df), 5):
        date = df.index[i]
        if normalize:
            tufe_val = df["TÜFE Endeksi (Başlangıç = 100)"].iloc[i]
            usd_val = df["USD Endeksi (Başlangıç = 100)"].iloc[i]
        else:
            tufe_val = df["TÜFE Endeksi"].iloc[i]
            usd_val = df["USD Endeksi"].iloc[i]
        usd_raw_val = df["USD Ham Değer"].iloc[i]
        
        # Check for finite values before displaying
        if pd.notna(tufe_val) and np.isfinite(tufe_val):
            plt.text(date, tufe_val + 10, f'{tufe_val:.0f}', ha='center', va='bottom', fontsize=8, color='blue')
        if pd.notna(usd_val) and np.isfinite(usd_val):
            plt.text(date, usd_val - 20, f'{usd_val:.0f}', ha='center', va='top', fontsize=8, color='orange')
        if pd.notna(usd_raw_val) and np.isfinite(usd_raw_val):
            plt.text(date, usd_raw_val - 40, f'{usd_raw_val:.1f}', ha='center', va='top', fontsize=8, color='red')
        
        if include_enag:
            if normalize:
                enag_val = df["ENAG Endeksi (Başlangıç = 100)"].iloc[i]
                enag_avg_val = df["ENAG Ortalama (12 Ay)"].iloc[i]
            else:
                enag_val = df["ENAG Endeksi"].iloc[i]
                enag_avg_val = df["ENAG Ortalama (12 Ay)"].iloc[i]
            if pd.notna(enag_val) and np.isfinite(enag_val):
                plt.text(date, enag_val + 30, f'{enag_val:.0f}', ha='center', va='bottom', fontsize=8, color='green')
            if pd.notna(enag_avg_val) and np.isfinite(enag_avg_val):
                plt.text(date, enag_avg_val + 50, f'{enag_avg_val:.0f}', ha='center', va='bottom', fontsize=8, color='purple')

    # En son dataya da ekle
    last_index = len(df) - 1
    if last_index % 5 != 0:  # Eğer en son data zaten 5'in katıysa ekleme
        last_date = df.index[last_index]
        if normalize:
            last_tufe_val = df["TÜFE Endeksi (Başlangıç = 100)"].iloc[last_index]
            last_usd_val = df["USD Endeksi (Başlangıç = 100)"].iloc[last_index]
        else:
            last_tufe_val = df["TÜFE Endeksi"].iloc[last_index]
            last_usd_val = df["USD Endeksi"].iloc[last_index]
        last_usd_raw_val = df["USD Ham Değer"].iloc[last_index]
        
        # Check for finite values before displaying
        if pd.notna(last_tufe_val) and np.isfinite(last_tufe_val):
            plt.text(last_date, last_tufe_val + 10, f'{last_tufe_val:.0f}', ha='center', va='bottom', fontsize=8, color='blue')
        if pd.notna(last_usd_val) and np.isfinite(last_usd_val):
            plt.text(last_date, last_usd_val - 20, f'{last_usd_val:.0f}', ha='center', va='top', fontsize=8, color='orange')
        if pd.notna(last_usd_raw_val) and np.isfinite(last_usd_raw_val):
            plt.text(last_date, last_usd_raw_val - 40, f'{last_usd_raw_val:.1f}', ha='center', va='top', fontsize=8, color='red')
        
        if include_enag:
            if normalize:
                last_enag_val = df["ENAG Endeksi (Başlangıç = 100)"].iloc[last_index]
                last_enag_avg_val = df["ENAG Ortalama (12 Ay)"].iloc[last_index]
            else:
                last_enag_val = df["ENAG Endeksi"].iloc[last_index]
                last_enag_avg_val = df["ENAG Ortalama (12 Ay)"].iloc[last_index]
            if pd.notna(last_enag_val) and np.isfinite(last_enag_val):
                plt.text(last_date, last_enag_val + 30, f'{last_enag_val:.0f}', ha='center', va='bottom', fontsize=8, color='green')
            if pd.notna(last_enag_avg_val) and np.isfinite(last_enag_avg_val):
                plt.text(last_date, last_enag_avg_val + 50, f'{last_enag_avg_val:.0f}', ha='center', va='bottom', fontsize=8, color='purple')

    plt.xticks(rotation=45)
    plt.tight_layout()

    # Grafik kaydetme
    if save_path:
        try:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Grafik kaydedildi: {save_path}")
        except Exception as e:
            print(f"Grafik kaydedilirken hata oluştu: {e}")

    plt.show()

def analyze_and_plot_data(start_date='01-09-2020', end_date='01-07-2025', include_enag=False, 
                         verbose=False, normalize=False, save=False):
    """
    TÜFE ve USD/TRY verilerini analiz eder ve grafikle gösterir.
    
    Args:
        start_date: Başlangıç tarihi (DD-MM-YYYY formatında)
        end_date: Bitiş tarihi (DD-MM-YYYY formatında)
        include_enag: ENAG verilerini dahil et
        verbose: Detaylı çıktı göster
        normalize: Verileri normalize et
        save: Grafiği dosya olarak kaydet
        
    Returns:
        combined_df: Birleştirilmiş dataframe
    """
    # Veri analizi
    combined_df = analyze_economic_data(
        start_date=start_date,
        end_date=end_date,
        include_enag=include_enag,
        verbose=verbose,
        normalize=normalize
    )
    
    if combined_df is None:
        return None
        
    # Grafik çizimi
    if save:
        filename_parts = [
            f"{start_date.replace('-', '_')}_{end_date.replace('-', '_')}",
            "TUFE_USD"
        ]
        
        if include_enag:
            filename_parts.append("ENAG")
        
        filename = "_".join(filename_parts) + ".png"
    else:
        filename = None
        
    # Grafik çiz
    plot_economic_data(combined_df, include_enag=include_enag, normalize=normalize, save_path=filename)
    
    return combined_df

if __name__ == "__main__":
    # Argparse setup
    parser = argparse.ArgumentParser(description='TÜFE ve USD/TRY endeksi karşılaştırma scripti')
    parser.add_argument('--start_date', '-s', 
                        default='01-09-2020', 
                        help='Başlangıç tarihi (DD-MM-YYYY formatında, default: 01-01-2020)')
    parser.add_argument('--end_date', '-e', 
                        default='01-07-2025', 
                        help='Bitiş tarihi (DD-MM-YYYY formatında, default: 01-07-2025)')
    parser.add_argument('--enag', action='store_true', help='ENAG verisini dahil et')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose mod')
    parser.add_argument('--normalize', action='store_true', help='Normalize et')
    parser.add_argument('--save', action='store_true', help='Grafiği dosya olarak kaydet')
    parser.add_argument('--analyze_only', action='store_true', help='Sadece veri analizi yap, grafik çizme')

    args = parser.parse_args()

    # Veri analizi
    data = analyze_economic_data(
        start_date=args.start_date,
        end_date=args.end_date,
        include_enag=args.enag,
        verbose=args.verbose,
        normalize=args.normalize
    )
    
    # Grafik çizimi (eğer sadece analiz istenmemişse)
    if not args.analyze_only and data is not None:
        # Dosya adı oluştur
        if args.save:
            filename_parts = [
                f"{args.start_date.replace('-', '_')}_{args.end_date.replace('-', '_')}",
                "TUFE_USD"
            ]
            
            if args.enag:
                filename_parts.append("ENAG")
            
            filename = "_".join(filename_parts) + ".png"
        else:
            filename = None
            
        # Grafik çiz
        plot_economic_data(data, include_enag=args.enag, normalize=args.normalize, save_path=filename)
