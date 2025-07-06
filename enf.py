from evds import evdsAPI
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import numpy as np
from enag import enag_kumulatif_yuzde
from tufe_filter import filter_tufe_until_august_2020
from datetime import datetime
# Argparse setup
parser = argparse.ArgumentParser(description='TÜFE ve USD/TRY endeksi karşılaştırma scripti')
parser.add_argument('--start_date', '-s', 
                    default='01-09-2018', 
                    help='Başlangıç tarihi (DD-MM-YYYY formatında, default: 01-01-2020)')
parser.add_argument('--end_date', '-e', 
                    default='01-07-2025', 
                    help='Bitiş tarihi (DD-MM-YYYY formatında, default: 01-07-2025)')
parser.add_argument('--enag', action='store_true', help='ENAG verisini dahil et')
parser.add_argument('--verbose', '-v', action='store_true', help='Verbose mod')

args = parser.parse_args()


start_date = args.start_date
end_date = args.end_date

# Check if start date is before September 2020
start_date_obj = None
september_2020 = datetime.strptime('01-09-2020', '%d-%m-%Y')
try:
    start_date_obj = datetime.strptime(start_date, '%d-%m-%Y')
    
    if start_date_obj < september_2020:
        print(f"Uyarı: Girilen başlangıç tarihi ({start_date}) Eylül 2020'den önce.")
        print(f"Veriler {start_date} tarihinden itibaren işlenecektir.")
except ValueError:
    print(f"Uyarı: Tarih formatı hatalı olabilir: {start_date}")

print(f"Veri çekiliyor: {start_date} - {end_date}")

# EVDS API Key
API_KEY = 'API_KEY'
evds = evdsAPI(API_KEY)

df_tufe = evds.get_data(
    series=["TP.FE.OKTG01"],
    startdate=start_date,
    enddate=end_date,
    frequency=5
)


#print(df_tufe["TP_FE_OKTG01"])
df_tufe = df_tufe.sort_index()

df_tufe["TP_FE_OKTG01"] = pd.to_numeric(df_tufe["TP_FE_OKTG01"], errors="coerce")

# Normalize et (başlangıç tarihi = 100)
tufe_base = df_tufe["TP_FE_OKTG01"].iloc[0]
df_tufe["TÜFE Endeksi (Başlangıç = 100)"] = df_tufe["TP_FE_OKTG01"] * (100 / tufe_base)

# USD/TRY verisini çek ve normalize et
df_usd = evds.get_data(
    series=["TP.DK.USD.S.YTL"],
    startdate=start_date,
    enddate=end_date,
    frequency=5
)
df_usd = df_usd.sort_index()
df_usd["TP_DK_USD_S_YTL"] = pd.to_numeric(df_usd["TP_DK_USD_S_YTL"], errors="coerce")
df_usd["USD Endeksi (Başlangıç = 100)"] = df_usd["TP_DK_USD_S_YTL"] * (100 / df_usd["TP_DK_USD_S_YTL"].iloc[0])



if args.enag:
    combined_data = None  # Initialize combined_data
    
    if start_date_obj is not None and start_date_obj < september_2020:
        filtered_tufe_df = filter_tufe_until_august_2020(df_tufe, start_date,args.verbose)
        filtered_tufe_values = filtered_tufe_df['TP_FE_OKTG01']
        normalized_filtered_tufe = filtered_tufe_values * 100 / filtered_tufe_values.iloc[0]
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
        enag_list = enag_kumulatif_yuzde(100, start_date_enag, args.verbose)
    
    # Truncate ENAG data to match TÜFE data length
    tufe_length = len(df_tufe["Tarih"])
    
    # Use combined data if start date is before September 2020, otherwise use enag_list
    if combined_data is not None:
        enag_list_truncated = combined_data[:tufe_length]
    else:
        enag_list_truncated = enag_list[:tufe_length]
    
    # ENAG average hesapla (ENAG ve USD/TRY ortalması)
    usd_values = df_usd["TP_DK_USD_S_YTL"][:tufe_length]
    enag_average = [(enag_val + usd_val) / 2 for enag_val, usd_val in zip(enag_list_truncated, usd_values)]
    
    enag_data = pd.DataFrame({
        'ENAG Endeksi (Başlangıç = 100)': enag_list_truncated,
        'ENAG Ortalama (12 Ay)': enag_average
    }, index=df_tufe["Tarih"])
    

# Her iki dataframe'in indexini eşitle
df_tufe.index = df_tufe["Tarih"]
df_usd.index = df_usd["Tarih"]

# Birleştir ve çiz
combined_df = pd.merge(
    df_tufe[["TÜFE Endeksi (Başlangıç = 100)"]],
    df_usd[["USD Endeksi (Başlangıç = 100)", "TP_DK_USD_S_YTL"]],
    left_index=True,
    right_index=True,
    how="inner"
)

if args.enag:
    # Merge ENAG data with existing data
    combined_df = pd.merge(
        combined_df,
        enag_data,
        left_index=True,
        right_index=True,
        how="inner"
    )
# Grafik
plt.figure(figsize=(16, 8))
plt.plot(combined_df.index, combined_df["TÜFE Endeksi (Başlangıç = 100)"], label="TÜFE Endeksi", linewidth=2)
plt.plot(combined_df.index, combined_df["USD Endeksi (Başlangıç = 100)"], label="USD/TRY Endeksi", linewidth=2)
plt.plot(combined_df.index, combined_df["TP_DK_USD_S_YTL"], label="USD/TRY Ham Değer", linewidth=2, linestyle='--')

if args.enag:
    plt.plot(combined_df.index, combined_df["ENAG Endeksi (Başlangıç = 100)"], label="ENAG Endeksi", linewidth=2)
    plt.plot(combined_df.index, combined_df["ENAG Ortalama (12 Ay)"], label="ENAG Ortalama", linewidth=2, linestyle=':', alpha=0.8)

title = "TÜFE ve USD/TRY Endeksi Karşılaştırması"
if args.enag:
    title += " (ENAG ile)"
title += " (Başlangıç Tarihi = 100)"

plt.title(title)
plt.xlabel("Tarih")
plt.ylabel("Endeks")
plt.legend()
plt.grid(True, alpha=0.3)

# Her 5 datada bir değer göster
for i in range(0, len(combined_df), 5):
    date = combined_df.index[i]
    tufe_val = combined_df["TÜFE Endeksi (Başlangıç = 100)"].iloc[i]
    usd_val = combined_df["USD Endeksi (Başlangıç = 100)"].iloc[i]
    usd_raw_val = combined_df["TP_DK_USD_S_YTL"].iloc[i]
    
    # Check for finite values before displaying
    if pd.notna(tufe_val) and np.isfinite(tufe_val):
        plt.text(date, tufe_val + 10, f'{tufe_val:.0f}', ha='center', va='bottom', fontsize=8, color='blue')
    if pd.notna(usd_val) and np.isfinite(usd_val):
        plt.text(date, usd_val - 20, f'{usd_val:.0f}', ha='center', va='top', fontsize=8, color='orange')
    if pd.notna(usd_raw_val) and np.isfinite(usd_raw_val):
        plt.text(date, usd_raw_val - 40, f'{usd_raw_val:.1f}', ha='center', va='top', fontsize=8, color='red')
    
    if args.enag:
        enag_val = combined_df["ENAG Endeksi (Başlangıç = 100)"].iloc[i]
        enag_avg_val = combined_df["ENAG Ortalama (12 Ay)"].iloc[i]
        if pd.notna(enag_val) and np.isfinite(enag_val):
            plt.text(date, enag_val + 30, f'{enag_val:.0f}', ha='center', va='bottom', fontsize=8, color='green')
        if pd.notna(enag_avg_val) and np.isfinite(enag_avg_val):
            plt.text(date, enag_avg_val + 50, f'{enag_avg_val:.0f}', ha='center', va='bottom', fontsize=8, color='purple')

# En son dataya da ekle
last_index = len(combined_df) - 1
if last_index % 5 != 0:  # Eğer en son data zaten 5'in katıysa ekleme
    last_date = combined_df.index[last_index]
    last_tufe_val = combined_df["TÜFE Endeksi (Başlangıç = 100)"].iloc[last_index]
    last_usd_val = combined_df["USD Endeksi (Başlangıç = 100)"].iloc[last_index]
    last_usd_raw_val = combined_df["TP_DK_USD_S_YTL"].iloc[last_index]
    
    # Check for finite values before displaying
    if pd.notna(last_tufe_val) and np.isfinite(last_tufe_val):
        plt.text(last_date, last_tufe_val + 10, f'{last_tufe_val:.0f}', ha='center', va='bottom', fontsize=8, color='blue')
    if pd.notna(last_usd_val) and np.isfinite(last_usd_val):
        plt.text(last_date, last_usd_val - 20, f'{last_usd_val:.0f}', ha='center', va='top', fontsize=8, color='orange')
    if pd.notna(last_usd_raw_val) and np.isfinite(last_usd_raw_val):
        plt.text(last_date, last_usd_raw_val - 40, f'{last_usd_raw_val:.1f}', ha='center', va='top', fontsize=8, color='red')
    
    if args.enag:
        last_enag_val = combined_df["ENAG Endeksi (Başlangıç = 100)"].iloc[last_index]
        last_enag_avg_val = combined_df["ENAG Ortalama (12 Ay)"].iloc[last_index]
        if pd.notna(last_enag_val) and np.isfinite(last_enag_val):
            plt.text(last_date, last_enag_val + 30, f'{last_enag_val:.0f}', ha='center', va='bottom', fontsize=8, color='green')
        if pd.notna(last_enag_avg_val) and np.isfinite(last_enag_avg_val):
            plt.text(last_date, last_enag_avg_val + 50, f'{last_enag_avg_val:.0f}', ha='center', va='bottom', fontsize=8, color='purple')

plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
