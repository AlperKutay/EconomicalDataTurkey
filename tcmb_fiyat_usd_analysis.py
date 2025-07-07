#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ev Fiyat Endeksi USD Bazlı Analiz
Ev fiyat endeksi (varsayılan: TP.KFE.TR) / USD/TRY ile USD bazında ev fiyat endeksi hesaplar
"""

from evds import evdsAPI
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
import argparse
from enf import get_evds_data, get_evds_data_and_normalize

# Matplotlib için Türkçe karakter desteği
plt.rcParams['font.family'] = ['DejaVu Sans', 'Tahoma', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# EVDS API Key
API_KEY = 'kk11ju7Bis'

def fetch_house_price_data(start_date, end_date, series_name="TP.KFE.TR", api_key=API_KEY, verbose=False):
    """
    TCMB'den ev fiyat endeksi ve USD/TRY verilerini çeker
    
    Args:
        start_date: Başlangıç tarihi (DD-MM-YYYY formatında)
        end_date: Bitiş tarihi (DD-MM-YYYY formatında)
        series_name: Ev fiyat endeksi serisi kodu (varsayılan: TP.KFE.TR)
        api_key: EVDS API anahtarı
        verbose: Detaylı çıktı göster
        
    Returns:
        combined_df: Birleştirilmiş veri içeren dataframe
    """
    evds = evdsAPI(api_key)
    
    try:
        print(f"Ev fiyat endeksi ({series_name}) ve USD/TRY verileri çekiliyor: {start_date} - {end_date}")
        
        # Ev fiyat endeksi verisi - çeyreklik
        df_house, house_column = get_evds_data_and_normalize(
            [series_name], 
            start_date, 
            end_date, 
            frequency=5,  # Aylık
            normalize=False
        )
        
        # USD/TRY verisi - çeyreklik
        df_usd, usd_column = get_evds_data_and_normalize(
            ["TP.DK.USD.A"], 
            start_date, 
            end_date, 
            frequency=5,  # Aylık
            normalize=False
        )
        
        if not house_column or not usd_column:
            print("Hata: Gerekli veri kolonları bulunamadı!")
            return None
            
        # Tarih sütunlarını datetime formatına çevir
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df_house["Tarih"] = pd.to_datetime(df_house["Tarih"], errors='coerce')
            df_usd["Tarih"] = pd.to_datetime(df_usd["Tarih"], errors='coerce')
        
        # Index'leri eşitle
        df_house.index = df_house["Tarih"]
        df_usd.index = df_usd["Tarih"]
        
        # Dataframe'leri birleştir
        combined_df = pd.merge(
            df_house[[house_column]],
            df_usd[[usd_column]],
            left_index=True,
            right_index=True,
            how="inner"
        )
        
        # Kolon adlarını standartlaştır
        combined_df.rename(columns={
            house_column: "Ev_Fiyat_TL",
            usd_column: "USD_TRY"
        }, inplace=True)
        
        # Eksik değerleri temizle
        combined_df = combined_df.dropna()
        
        if combined_df.empty:
            print("Temizleme sonrası veri kalmadı!")
            return None
        
        # USD bazında ev fiyat endeksi hesapla
        combined_df['Ev_Fiyat_USD'] = combined_df['Ev_Fiyat_TL'] / combined_df['USD_TRY']
        
        # Tarih formatını düzenle
        combined_df["Ay-Yıl"] = combined_df.index.strftime("%m-%Y")
        
        if verbose:
            print(f"Veri boyutu: {combined_df.shape}")
            print(f"Kolonlar: {combined_df.columns.tolist()}")
            print(f"İlk 3 satır:\n{combined_df.head(3)}")
            print(f"TL Ev Fiyat Endeksi - Min: {combined_df['Ev_Fiyat_TL'].min():.1f}, Max: {combined_df['Ev_Fiyat_TL'].max():.1f}")
            print(f"USD/TRY - Min: {combined_df['USD_TRY'].min():.2f}, Max: {combined_df['USD_TRY'].max():.2f}")
            print(f"USD Ev Fiyat Endeksi - Min: {combined_df['Ev_Fiyat_USD'].min():.2f}, Max: {combined_df['Ev_Fiyat_USD'].max():.2f}")
        
        print(f"Toplam {len(combined_df)} veri noktası işlendi")
        return combined_df
        
    except Exception as e:
        print(f"Veri çekme hatası: {e}")
        return None

def calculate_house_price_statistics(df, column='Ev_Fiyat_USD', verbose=False):
    """
    Ev fiyat veriler için istatistik hesaplar
    
    Args:
        df: Veri içeren dataframe
        column: İstatistik hesaplanacak kolon
        verbose: Detaylı çıktı göster
        
    Returns:
        stats: İstatistik sözlüğü
    """
    if df is None or df.empty or column not in df.columns:
        return None
        
    stats = {
        'min': df[column].min(),
        'max': df[column].max(),
        'mean': df[column].mean(),
        'median': df[column].median(),
        'std': df[column].std(),
        'current': df[column].iloc[-1],
        'start': df[column].iloc[0],
        'count': len(df)
    }
    
    # Değişim hesapla
    stats['total_change'] = ((stats['current'] - stats['start']) / stats['start']) * 100
    
    # Yıllık değişim hesapla
    date_range = (df.index[-1] - df.index[0]).days
    if date_range > 0:
        years = date_range / 365.25
        stats['annual_change'] = stats['total_change'] / years
    else:
        stats['annual_change'] = 0
    
    if verbose:
        print(f"\n=== {column} İSTATİSTİKLERİ ===")
        print(f"Veri Sayısı: {stats['count']}")
        print(f"Minimum: {stats['min']:.3f}")
        print(f"Maksimum: {stats['max']:.3f}")
        print(f"Ortalama: {stats['mean']:.3f}")
        print(f"Medyan: {stats['median']:.3f}")
        print(f"Standart Sapma: {stats['std']:.3f}")
        print(f"İlk Değer: {stats['start']:.3f}")
        print(f"Son Değer: {stats['current']:.3f}")
        print(f"Toplam Değişim: {stats['total_change']:.2f}%")
        print(f"Yıllık Ortalama Değişim: {stats['annual_change']:.2f}%")
        
    return stats

def plot_house_price_comparison(df, save=False, save_name=None, start_date=None, end_date=None, verbose=False):
    """
    TL ve USD bazında ev fiyat endekslerini 3 panelde karşılaştırır
    
    Args:
        df: Veri içeren dataframe
        save: Grafiği kaydet
        save_name: Özel dosya adı
        start_date: Başlangıç tarihi (dosya adı için)
        end_date: Bitiş tarihi (dosya adı için)
        verbose: Detaylı çıktı göster
        
    Returns:
        stats_dict: İstatistik sonuçları sözlüğü
    """
    if df is None or df.empty:
        print("Grafik için veri yok!")
        return None
        
    # İstatistikleri hesapla
    stats_tl = calculate_house_price_statistics(df, 'Ev_Fiyat_TL', verbose=verbose)
    stats_usd = calculate_house_price_statistics(df, 'Ev_Fiyat_USD', verbose=verbose)
    stats_usdtry = calculate_house_price_statistics(df, 'USD_TRY', verbose=verbose)
    
    # Üç alt grafik oluştur
    plt.figure(figsize=(16, 15))
    
    # 1. TL Bazında Ev Fiyat Endeksi
    plt.subplot(3, 1, 1)
    plt.plot(df.index, df['Ev_Fiyat_TL'], 
            color='#2c3e50', linewidth=2, label='Ev Fiyat Endeksi (TL)')
    
    # Min/Max/Son değerleri vurgula
    min_idx_tl = df['Ev_Fiyat_TL'].idxmin()
    max_idx_tl = df['Ev_Fiyat_TL'].idxmax()
    
    plt.plot(min_idx_tl, df.loc[min_idx_tl, 'Ev_Fiyat_TL'], 
            'go', markersize=8, label=f'Min: {stats_tl["min"]:.1f}')
    plt.plot(max_idx_tl, df.loc[max_idx_tl, 'Ev_Fiyat_TL'], 
            'ro', markersize=8, label=f'Max: {stats_tl["max"]:.1f}')
    plt.plot(df.index[-1], df['Ev_Fiyat_TL'].iloc[-1], 
            'bo', markersize=10, label=f'Son: {stats_tl["current"]:.1f}')
    
    plt.title('Ev Fiyat Endeksi (TL Bazında)', fontsize=14, fontweight='bold')
    plt.ylabel('Endeks Değeri (TL)', fontsize=11, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper left')
    
    # X ekseni formatını ayarla - 6 ayda bir
    ax1 = plt.gca()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Her 5 datada bir değer göster
    step = max(1, len(df) // 10)
    for i in range(0, len(df), step):
        date = df.index[i]
        value = df['Ev_Fiyat_TL'].iloc[i]
        if pd.notna(value) and np.isfinite(value):
            plt.text(date, value, f'{value:.0f}', 
                    ha='center', va='bottom', fontsize=8, color='#2c3e50')
    
    # 2. USD Bazında Ev Fiyat Endeksi
    plt.subplot(3, 1, 2)
    plt.plot(df.index, df['Ev_Fiyat_USD'], 
            color='#27ae60', linewidth=2, label='Ev Fiyat Endeksi (USD)')
    
    # Min/Max/Son değerleri vurgula
    min_idx_usd = df['Ev_Fiyat_USD'].idxmin()
    max_idx_usd = df['Ev_Fiyat_USD'].idxmax()
    
    plt.plot(min_idx_usd, df.loc[min_idx_usd, 'Ev_Fiyat_USD'], 
            'go', markersize=8, label=f'Min: {stats_usd["min"]:.1f}')
    plt.plot(max_idx_usd, df.loc[max_idx_usd, 'Ev_Fiyat_USD'], 
            'ro', markersize=8, label=f'Max: {stats_usd["max"]:.1f}')
    plt.plot(df.index[-1], df['Ev_Fiyat_USD'].iloc[-1], 
            'bo', markersize=10, label=f'Son: {stats_usd["current"]:.1f}')
    
    plt.title('Ev Fiyat Endeksi (USD Bazında)', fontsize=14, fontweight='bold')
    plt.ylabel('Endeks Değeri (USD)', fontsize=11, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper left')
    
    # X ekseni formatını ayarla - 6 ayda bir
    ax2 = plt.gca()
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # Her 5 datada bir değer göster
    for i in range(0, len(df), step):
        date = df.index[i]
        value = df['Ev_Fiyat_USD'].iloc[i]
        if pd.notna(value) and np.isfinite(value):
            plt.text(date, value, f'{value:.0f}', 
                    ha='center', va='bottom', fontsize=8, color='#27ae60')
    
    # 3. USD/TRY Kuru (Referans)
    plt.subplot(3, 1, 3)
    plt.plot(df.index, df['USD_TRY'], 
            color='#e74c3c', linewidth=2, label='USD/TRY')
    
    # Min/Max/Son değerleri vurgula
    min_idx_fx = df['USD_TRY'].idxmin()
    max_idx_fx = df['USD_TRY'].idxmax()
    
    plt.plot(min_idx_fx, df.loc[min_idx_fx, 'USD_TRY'], 
            'go', markersize=8, label=f'Min: {stats_usdtry["min"]:.2f}')
    plt.plot(max_idx_fx, df.loc[max_idx_fx, 'USD_TRY'], 
            'ro', markersize=8, label=f'Max: {stats_usdtry["max"]:.2f}')
    plt.plot(df.index[-1], df['USD_TRY'].iloc[-1], 
            'bo', markersize=10, label=f'Son: {stats_usdtry["current"]:.2f}')
    
    plt.title('USD/TRY Döviz Kuru (Referans)', fontsize=14, fontweight='bold')
    plt.ylabel('USD/TRY', fontsize=11, fontweight='bold')
    plt.xlabel('Tarih', fontsize=11, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper left')
    
    # X ekseni formatını ayarla - 6 ayda bir
    ax3 = plt.gca()
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # Her 5 datada bir değer göster
    for i in range(0, len(df), step):
        date = df.index[i]
        value = df['USD_TRY'].iloc[i]
        if pd.notna(value) and np.isfinite(value):
            plt.text(date, value, f'{value:.1f}', 
                    ha='center', va='bottom', fontsize=8, color='#e74c3c')
    
    # Ana başlık
    plt.suptitle('Ev Fiyat Endeksi: TL vs USD Bazlı Karşılaştırma', 
                fontsize=16, fontweight='bold', y=0.98)
    
    # İstatistik kutusu (sağ üstte)
    stats_text = f'''USD Bazlı Ev Fiyat Endeksi:
Min: {stats_usd["min"]:.2f}
Max: {stats_usd["max"]:.2f}
Ortalama: {stats_usd["mean"]:.2f}
Son: {stats_usd["current"]:.2f}
Toplam Değişim: {stats_usd["total_change"]:.1f}%
Yıllık Ort.: {stats_usd["annual_change"]:.1f}%

TL Bazlı Ev Fiyat Endeksi:
Toplam Değişim: {stats_tl["total_change"]:.1f}%
Yıllık Ort.: {stats_tl["annual_change"]:.1f}%'''
    
    plt.figtext(0.98, 0.85, stats_text, 
               verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8), 
               fontsize=9)
    
    # Layout ayarla
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, right=0.78)
    
    # Kaydet
    if save:
        if save_name:
            filename = save_name
        else:
            start_str = start_date.replace('-', '_') if start_date else df.index[0].strftime('%d_%m_%Y')
            end_str = end_date.replace('-', '_') if end_date else df.index[-1].strftime('%d_%m_%Y')
            filename = f"EvFiyat_TL_USD_Karsilastirma_{start_str}_{end_str}.png"
        
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Grafik kaydedildi: {filename}")
    
    plt.show()
    
    return {
        'tl_stats': stats_tl,
        'usd_stats': stats_usd,
        'usdtry_stats': stats_usdtry
    }

def plot_usd_house_price_only(df, save=False, save_name=None, start_date=None, end_date=None, verbose=False):
    """
    Sadece USD bazında ev fiyat endeksini tek grafikte gösterir
    
    Args:
        df: Veri içeren dataframe
        save: Grafiği kaydet
        save_name: Özel dosya adı
        start_date: Başlangıç tarihi (dosya adı için)
        end_date: Bitiş tarihi (dosya adı için)
        verbose: Detaylı çıktı göster
        
    Returns:
        stats: İstatistik sonuçları
    """
    if df is None or df.empty:
        print("Grafik için veri yok!")
        return None
        
    # İstatistikleri hesapla
    stats = calculate_house_price_statistics(df, 'Ev_Fiyat_USD', verbose=verbose)
    
    # Grafik oluştur
    plt.figure(figsize=(16, 8))
    
    # Ana çizgi grafiği
    plt.plot(df.index, df['Ev_Fiyat_USD'], 
           color='#27ae60', linewidth=2.5, label='Ev Fiyat Endeksi (USD)')
    
    # Minimum ve maksimum noktaları vurgula
    min_idx = df['Ev_Fiyat_USD'].idxmin()
    max_idx = df['Ev_Fiyat_USD'].idxmax()
    
    plt.plot(min_idx, df.loc[min_idx, 'Ev_Fiyat_USD'], 
           'go', markersize=10, label=f'Min: {stats["min"]:.2f}')
    plt.plot(max_idx, df.loc[max_idx, 'Ev_Fiyat_USD'], 
           'ro', markersize=10, label=f'Max: {stats["max"]:.2f}')
    
    # Son değeri vurgula
    plt.plot(df.index[-1], df['Ev_Fiyat_USD'].iloc[-1], 
           'bo', markersize=12, label=f'Son: {stats["current"]:.2f}')
    
    # Trend çizgisi ekle
    x_numeric = np.arange(len(df))
    z = np.polyfit(x_numeric, df['Ev_Fiyat_USD'], 1)
    p = np.poly1d(z)
    plt.plot(df.index, p(x_numeric), "--", alpha=0.7, color='gray', 
           label=f'Trend (Eğim: {z[0]:.3f})')
    
    # X ekseni formatı (6 aylık)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45)
    
    # Grid ve stil
    plt.grid(True, alpha=0.3)
    plt.xlabel('Tarih', fontsize=12, fontweight='bold')
    plt.ylabel('Ev Fiyat Endeksi (USD Bazında)', fontsize=12, fontweight='bold')
    plt.title('Türkiye Ev Fiyat Endeksi (USD Bazında)', fontsize=16, fontweight='bold', pad=20)
    
    # Legend
    plt.legend(loc='upper left', framealpha=0.9)
    
    # İstatistik kutusu
    if verbose:
        stats_text = f'''İstatistikler:
        Min: {stats["min"]:.3f}
        Max: {stats["max"]:.3f}
        Ortalama: {stats["mean"]:.3f}
        Medyan: {stats["median"]:.3f}
        Std. Sapma: {stats["std"]:.3f}
        Son Değer: {stats["current"]:.3f}
        Toplam Değişim: {stats["total_change"]:.1f}%
        Yıllık Ort. Değişim: {stats["annual_change"]:.1f}%
        Veri Sayısı: {stats["count"]}'''
    else:
        stats_text = None
        
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', 
           facecolor='lightgreen', alpha=0.8), fontsize=10)
    
    # Her 5 datada bir değer göster
    step = max(1, len(df) // 10)
    for i in range(0, len(df), step):
        date = df.index[i]
        value = df['Ev_Fiyat_USD'].iloc[i]
        if pd.notna(value) and np.isfinite(value):
            plt.text(date, value, f'{value:.0f}', 
                    ha='center', va='bottom', fontsize=8, color='#27ae60')
    
    # Layout ayarla
    plt.tight_layout()
    
    # Kaydet
    if save:
        if save_name:
            filename = save_name
        else:
            start_str = start_date.replace('-', '_') if start_date else df.index[0].strftime('%d_%m_%Y')
            end_str = end_date.replace('-', '_') if end_date else df.index[-1].strftime('%d_%m_%Y')
            filename = f"EvFiyat_USD_Endeksi_{start_str}_{end_str}.png"
        
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Grafik kaydedildi: {filename}")
    
    plt.show()
    
    return stats

def plot_multiple_series(series_names, start_date, end_date, comparison, usd_only, verbose, save, save_name):
    """
    Birden fazla seriyi alt alta plotlar
    
    Args:
        series_names: Seri kodları listesi
        start_date: Başlangıç tarihi
        end_date: Bitiş tarihi
        comparison: Karşılaştırmalı mod
        usd_only: Sadece USD modu
        verbose: Detaylı çıktı
        save: Kaydet
        save_name: Dosya adı
        
    Returns:
        results_dict: Her seri için sonuçlar
    """
    results_dict = {}
    all_data = {}
    
    # Önce tüm serilerin verilerini çek
    for series in series_names:
        if verbose:
            print(f"\n{series} serisi işleniyor...")
        
        df = fetch_house_price_data(start_date, end_date, series, verbose=verbose)
        if df is not None:
            all_data[series] = df
            # İstatistikleri hesapla
            stats = calculate_house_price_statistics(df, 'Ev_Fiyat_USD', verbose=verbose)
            results_dict[series] = {'usd_stats': stats}
        else:
            print(f"Uyarı: {series} serisi için veri alınamadı!")
    
    if not all_data:
        print("Hiçbir seri için veri alınamadı!")
        return None
    
    # Grafik oluştur
    if comparison:
        plot_multiple_series_comparison(all_data, start_date, end_date, save, save_name, verbose)
    elif usd_only:
        plot_multiple_series_usd_only(all_data, start_date, end_date, save, save_name, verbose)
    else:
        # Varsayılan olarak USD only
        plot_multiple_series_usd_only(all_data, start_date, end_date, save, save_name, verbose)
    
    return results_dict

def plot_multiple_series_comparison(all_data, start_date, end_date, save, save_name, verbose):
    """Birden fazla seri için karşılaştırmalı grafik (3 panel her seri için)"""
    num_series = len(all_data)
    
    # Her seri için 3 panel, toplamda 3*num_series panel
    fig, axes = plt.subplots(num_series, 3, figsize=(20, 6*num_series))
    
    if num_series == 1:
        axes = axes.reshape(1, -1)
    
    colors = ['#2c3e50', '#27ae60', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
    
    for i, (series_name, df) in enumerate(all_data.items()):
        color = colors[i % len(colors)]
        
        # TL Panel
        ax1 = axes[i, 0]
        ax1.plot(df.index, df['Ev_Fiyat_TL'], color=color, linewidth=2, label=f'{series_name} (TL)')
        ax1.set_title(f'{series_name} - TL Bazında', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Endeks Değeri (TL)', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # USD Panel
        ax2 = axes[i, 1]
        ax2.plot(df.index, df['Ev_Fiyat_USD'], color=color, linewidth=2, label=f'{series_name} (USD)')
        ax2.set_title(f'{series_name} - USD Bazında', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Endeks Değeri (USD)', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # USD/TRY Panel
        ax3 = axes[i, 2]
        ax3.plot(df.index, df['USD_TRY'], color='#e74c3c', linewidth=2, label='USD/TRY')
        ax3.set_title('USD/TRY Kuru (Referans)', fontsize=12, fontweight='bold')
        ax3.set_ylabel('USD/TRY', fontsize=10)
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # X ekseni formatı - sadece son satır için
        if i == num_series - 1:
            for ax in [ax1, ax2, ax3]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                ax.set_xlabel('Tarih', fontsize=10)
        else:
            for ax in [ax1, ax2, ax3]:
                ax.set_xticklabels([])
    
    plt.suptitle('Ev Fiyat Endeksleri Karşılaştırması (Çoklu Seri)', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    # Kaydet
    if save:
        if save_name:
            filename = save_name
        else:
            start_str = start_date.replace('-', '_')
            end_str = end_date.replace('-', '_')
            filename = f"EvFiyat_Coklu_Karsilastirma_{start_str}_{end_str}.png"
        
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Grafik kaydedildi: {filename}")
    
    plt.show()

def plot_multiple_series_usd_only(all_data, start_date, end_date, save, save_name, verbose):
    """Birden fazla seri için sadece USD bazlı grafikler"""
    num_series = len(all_data)
    
    fig, axes = plt.subplots(num_series, 1, figsize=(16, 5*num_series))
    
    if num_series == 1:
        axes = [axes]
    
    colors = ['#27ae60', '#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
    
    for i, (series_name, df) in enumerate(all_data.items()):
        ax = axes[i]
        color = colors[i % len(colors)]
        
        # Ana çizgi
        ax.plot(df.index, df['Ev_Fiyat_USD'], color=color, linewidth=2.5, label=f'{series_name} (USD)')
        
        # İstatistikler
        stats = calculate_house_price_statistics(df, 'Ev_Fiyat_USD', verbose=False)
        
        if stats:
            # Min/Max/Son değerler
            min_idx = df['Ev_Fiyat_USD'].idxmin()
            max_idx = df['Ev_Fiyat_USD'].idxmax()
            
            ax.plot(min_idx, df.loc[min_idx, 'Ev_Fiyat_USD'], 'go', markersize=8, label=f'Min: {stats["min"]:.1f}')
            ax.plot(max_idx, df.loc[max_idx, 'Ev_Fiyat_USD'], 'ro', markersize=8, label=f'Max: {stats["max"]:.1f}')
            ax.plot(df.index[-1], df['Ev_Fiyat_USD'].iloc[-1], 'bo', markersize=10, label=f'Son: {stats["current"]:.1f}')
            
            # Trend çizgisi
            x_numeric = np.arange(len(df))
            z = np.polyfit(x_numeric, df['Ev_Fiyat_USD'], 1)
            p = np.poly1d(z)
            ax.plot(df.index, p(x_numeric), "--", alpha=0.7, color='gray', label=f'Trend')
        
        ax.set_title(f'{series_name} - USD Bazında Ev Fiyat Endeksi', fontsize=14, fontweight='bold')
        ax.set_ylabel('USD Endeks Değeri', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
        # X ekseni formatı - sadece son grafik için
        if i == num_series - 1:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            ax.set_xlabel('Tarih', fontsize=11)
        else:
            ax.set_xticklabels([])
    
    plt.suptitle('Ev Fiyat Endeksleri USD Bazlı Analiz (Çoklu Seri)', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    # Kaydet
    if save:
        if save_name:
            filename = save_name
        else:
            start_str = start_date.replace('-', '_')
            end_str = end_date.replace('-', '_')
            filename = f"EvFiyat_Coklu_USD_{start_str}_{end_str}.png"
        
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Grafik kaydedildi: {filename}")
    
    plt.show()

def parse_date(date_str):
    """Tarih string'ini datetime objesine çevirir"""
    try:
        return datetime.strptime(date_str, '%d-%m-%Y')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Geçersiz tarih formatı: {date_str}. DD-MM-YYYY formatında olmalı.")

def analyze_house_price_usd(start_date='01-01-2010', end_date=None, series_name=["TP.KFE.TR"], 
                           comparison=True, usd_only=False, verbose=False, save=False, save_name=None):
    """
    Ev fiyat endeksi USD analizi yapan ana fonksiyon
    
    Args:
        start_date: Başlangıç tarihi (DD-MM-YYYY formatında)
        end_date: Bitiş tarihi (DD-MM-YYYY formatında, None ise bugün)
        series_name: Ev fiyat endeksi serisi kodu(ları) listesi (varsayılan: ["TP.KFE.TR"])
        comparison: Karşılaştırmalı grafik çiz
        usd_only: Sadece USD bazlı grafik çiz
        verbose: Detaylı çıktı göster
        save: Grafiği kaydet
        save_name: Özel dosya adı
        
    Returns:
        results_dict: Her seri için analiz sonuçları içeren sözlük
    """
    # Bitiş tarihi varsayılan olarak bugün
    if end_date is None:
        end_date = datetime.now().strftime('%d-%m-%Y')
    
    # Eğer tek string gelirse listeye çevir
    if isinstance(series_name, str):
        series_name = [series_name]
    
    if verbose:
        print(f"Analiz edilecek seriler: {', '.join(series_name)}")
        print(f"Tarih aralığı: {start_date} - {end_date}")
    
    # Birden fazla seri varsa alt alta plot yap
    if len(series_name) > 1:
        return plot_multiple_series(series_name, start_date, end_date, comparison, usd_only, verbose, save, save_name)
    
    # Tek seri için eski fonksiyonları kullan
    single_series = series_name[0]
    if verbose:
        print(f"{single_series} Fiyat endeksi (USD) analizi başlatılıyor...")
    
    # Veri çek
    df = fetch_house_price_data(start_date, end_date, single_series, verbose=verbose)
    
    if df is None:
        print("Veri çekilemedi, program sonlandırılıyor.")
        return None
    
    results = None
    
    # Grafik türüne göre görselleştir
    if comparison:
        if verbose:
            print("Karşılaştırmalı grafik çiziliyor...")
        
        results = plot_house_price_comparison(
            df, 
            save=save, 
            save_name=save_name,
            start_date=start_date,
            end_date=end_date,
            verbose=verbose
        )
    
    elif usd_only:
        if verbose:
            print("USD bazlı tek grafik çiziliyor...")
        
        stats = plot_usd_house_price_only(
            df, 
            save=save, 
            save_name=save_name,
            start_date=start_date,
            end_date=end_date,
            verbose=verbose
        )
        results = {'usd_stats': stats}
    
    return {single_series: results}

if __name__ == "__main__":
    # Argparse setup
    parser = argparse.ArgumentParser(description='Ev Fiyat Endeksi USD Bazlı Analiz')
    parser.add_argument('--start_date', '-s', type=str, default='01-01-2010',
                       help='Başlangıç tarihi (DD-MM-YYYY formatında, varsayılan: 01-01-2010)')
    parser.add_argument('--end_date', '-e', type=str, default=None,
                       help='Bitiş tarihi (DD-MM-YYYY formatında, varsayılan: bugün)')
    parser.add_argument('--series_name', type=str, nargs='+', default=['TP.KFE.TR'],
                       help='Ev fiyat endeksi serisi kodu(ları) (varsayılan: TP.KFE.TR). Birden fazla seri için boşlukla ayırın')
    parser.add_argument('--save', action='store_true',
                       help='Grafiği PNG dosyası olarak kaydet')
    parser.add_argument('--save_name', type=str,
                       help='Özel dosya adı (PNG uzantısı ile)')
    parser.add_argument('--comparison', action='store_true',
                       help='TL ve USD karşılaştırmalı grafik (3 panel)')
    parser.add_argument('--usd_only', action='store_true',
                       help='Sadece USD bazında tek grafik')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Detaylı çıktı göster')
    parser.add_argument('--api_key', type=str,
                       help='TCMB EVDS API anahtarı (kullanılmıyor, uyumluluk için)')
    
    args = parser.parse_args()
    
    # Eğer hiçbir grafik türü seçilmemişse varsayılan olarak karşılaştırma
    if not args.comparison and not args.usd_only:
        args.comparison = True
    
    # Tarih doğrulama
    try:
        start_dt = parse_date(args.start_date)
        if args.end_date:
            end_dt = parse_date(args.end_date)
            if start_dt >= end_dt:
                print("Hata: Başlangıç tarihi bitiş tarihinden önce olmalı!")
                exit(1)
    except argparse.ArgumentTypeError as e:
        print(f"Tarih hatası: {e}")
        exit(1)
    
    # Analiz yap
    results_dict = analyze_house_price_usd(
        start_date=args.start_date,
        end_date=args.end_date,
        series_name=args.series_name,
        comparison=args.comparison,
        usd_only=args.usd_only,
        verbose=args.verbose,
        save=args.save,
        save_name=args.save_name
    )
    
    # Sonuçları yazdır
    if args.verbose and results_dict:
        print("\n" + "="*50)
        print("ÖZET İSTATİSTİKLER")
        print("="*50)
        
        for series_name, results in results_dict.items():
            print(f"\n>>> {series_name} <<<")
            
            if results and 'usd_stats' in results:
                usd_stats = results['usd_stats']
                print(f"USD Bazlı Ev Fiyat Endeksi:")
                print(f"  Veri Sayısı: {usd_stats['count']}")
                print(f"  Ortalama: {usd_stats['mean']:.3f}")
                print(f"  Medyan: {usd_stats['median']:.3f}")
                print(f"  Standart Sapma: {usd_stats['std']:.3f}")
                print(f"  Minimum: {usd_stats['min']:.3f}")
                print(f"  Maksimum: {usd_stats['max']:.3f}")
                print(f"  İlk Değer: {usd_stats['start']:.3f}")
                print(f"  Son Değer: {usd_stats['current']:.3f}")
                print(f"  Toplam Değişim: {usd_stats['total_change']:.2f}%")
                print(f"  Yıllık Ortalama Değişim: {usd_stats['annual_change']:.2f}%")
            
            if results and 'tl_stats' in results:
                tl_stats = results['tl_stats']
                print(f"\nTL Bazlı Ev Fiyat Endeksi:")
                print(f"  Toplam Değişim: {tl_stats['total_change']:.2f}%")
                print(f"  Yıllık Ortalama Değişim: {tl_stats['annual_change']:.2f}%")
                
            if results and 'usdtry_stats' in results:
                fx_stats = results['usdtry_stats']
                print(f"\nUSD/TRY Döviz Kuru:")
                print(f"  Toplam Değişim: {fx_stats['total_change']:.2f}%")
                print(f"  Yıllık Ortalama Değişim: {fx_stats['annual_change']:.2f}%") 