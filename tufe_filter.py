import pandas as pd
from datetime import datetime

def filter_tufe_until_august_2020(df_tufe, start_date,verbose=False):
    """
    TÜFE verilerini start_date'ten '01-08-2020' tarihine kadar filtreler
    Eğer start_date '01-08-2020' den küçükse, start_date'ten '01-08-2020' arasındaki verileri döner
    
    Parameters:
    df_tufe: TÜFE verileri içeren DataFrame
    start_date: Kullanıcının girdiği başlangıç tarihi (DD-MM-YYYY formatında)
    
    Returns:
    Filtrelenmiş DataFrame
    """
    
    # Tarihleri datetime formatına çevir
    min_date = datetime.strptime('01-08-2020', '%d-%m-%Y')
    user_date = datetime.strptime(start_date, '%d-%m-%Y')
    
    # Eğer kullanıcının tarihi minimum tarihten küçükse
    if user_date < min_date:
        if verbose:
            print(f"Girilen tarih ({start_date}) minimum tarihten ({min_date.strftime('%d-%m-%Y')}) önce.")
            print(f"Veriler {start_date} ile {min_date.strftime('%d-%m-%Y')} arasından alınacak.")
        
        # Debug: İlk birkaç tarihi göster
        if verbose:
            print(f"Debug: İlk 3 tarih değeri: {df_tufe['Tarih'].head(3).tolist()}")
        
        # DataFrame'in tarih kolonunu datetime formatına çevir (farklı formatları dene)
        try:
            # Önce DD-MM-YYYY formatını dene
            df_tufe['Tarih_dt'] = pd.to_datetime(df_tufe['Tarih'], format='%d-%m-%Y')
            if verbose:
                print("DD-MM-YYYY formatı kullanıldı")
        except ValueError:
            try:
                # YYYY-M formatını dene
                df_tufe['Tarih_dt'] = pd.to_datetime(df_tufe['Tarih'], format='%Y-%m')
                if verbose:
                    print("YYYY-M formatı kullanıldı")
            except ValueError:
                try:
                    # M-YYYY formatını dene
                    df_tufe['Tarih_dt'] = pd.to_datetime(df_tufe['Tarih'], format='%m-%Y')
                    if verbose:
                        print("M-YYYY formatı kullanıldı")
                except ValueError:
                    # Genel format çözümlemesi
                    df_tufe['Tarih_dt'] = pd.to_datetime(df_tufe['Tarih'], infer_datetime_format=True)
                    if verbose:
                        print("Otomatik format çözümlemesi kullanıldı")
        
        # start_date ile '01-09-2020' arasındaki verileri filtrele
        filtered_df = df_tufe[(df_tufe['Tarih_dt'] >= user_date) & (df_tufe['Tarih_dt'] <= min_date)].copy()
        
        # Geçici kolonu kaldır
        filtered_df = filtered_df.drop('Tarih_dt', axis=1)
        
        # TÜFE kolonunu float'a çevir - doğru kolon adını bul
        tufe_col = None
        for col in filtered_df.columns:
            if 'TÜFE' in col or 'TP_FE_OKTG01' in col:
                tufe_col = col
                break
        
        if tufe_col:
            filtered_df[tufe_col] = pd.to_numeric(filtered_df[tufe_col], errors='coerce')
        else:
            # Fallback: İlk numerik kolonu kullan
            for col in filtered_df.columns:
                if col != 'Tarih':
                    filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
                    break
        
        return filtered_df
    else:
        # Kullanıcının tarihi uygunsa, orijinal DataFrame'i döner
        # Debug: İlk birkaç tarihi göster
        if verbose:
            print(f"Debug: İlk 3 tarih değeri: {df_tufe['Tarih'].head(3).tolist()}")
        
        # TÜFE kolonunu float'a çevir - doğru kolon adını bul
        tufe_col = None
        for col in df_tufe.columns:
            if 'TÜFE' in col or 'TP_FE_OKTG01' in col:
                tufe_col = col
                break
        
        if tufe_col:
            df_tufe[tufe_col] = pd.to_numeric(df_tufe[tufe_col], errors='coerce')
        else:
            # Fallback: İlk numerik kolonu kullan
            for col in df_tufe.columns:
                if col != 'Tarih':
                    df_tufe[col] = pd.to_numeric(df_tufe[col], errors='coerce')
                    break
        return df_tufe

# Kullanım örneği:
def create_tufe_array_until_september(df_tufe, start_date):
    """
    start_date'ten '01-09-2020' tarihine kadar TÜFE verilerini içeren pandas array oluşturur
    """
    filtered_df = filter_tufe_until_september_2020(df_tufe, start_date)
    
    # TÜFE değerlerini pandas array olarak döner - doğru kolon adını bul
    tufe_col = None
    for col in filtered_df.columns:
        if 'TÜFE' in col or 'TP_FE_OKTG01' in col:
            tufe_col = col
            break
    
    if tufe_col:
        tufe_array = pd.array(filtered_df[tufe_col])
    else:
        # Fallback: İlk numerik kolonu kullan
        for col in filtered_df.columns:
            if col != 'Tarih':
                tufe_array = pd.array(filtered_df[col])
                break
    
    return tufe_array, filtered_df

# Test fonksiyonu
if __name__ == "__main__":
    # Örnek test - gerçekçi TÜFE değerleri (Haziran 2020 - Kasım 2020)
    sample_data = {
        'Tarih': ['01-06-2020', '01-07-2020', '01-08-2020', '01-09-2020', '01-10-2020', '01-11-2020'],
        'TP_FE_OKTG01': ['98.45', '99.23', '100.45', '101.23', '102.67', '103.89']  # String olarak (API'den gelen gibi)
    }
    sample_df = pd.DataFrame(sample_data)
    
    print("Orijinal veri tipleri:")
    print(sample_df.dtypes)
    print("\nOrijinal veriler:")
    print(sample_df)
    
    # Test 1: Erken tarih (start_date'ten September 2020'ye kadar)
    print("\n" + "="*50)
    print("Test 1: Erken tarih (start_date'ten September 2020'ye kadar)")
    filtered_df = filter_tufe_until_august_2020(sample_df, '01-07-2020')
    print(f"\nFiltered data types: {filtered_df.dtypes}")
    tufe_col = None
    for col in filtered_df.columns:
        if 'TÜFE' in col or 'TP_FE_OKTG01' in col:
            tufe_col = col
            break
    if tufe_col:
        print(f"{tufe_col} dtype: {filtered_df[tufe_col].dtype}")
    print(filtered_df)
    
    # Test 2: Geç tarih (değişiklik yok)
    print("\n" + "="*50)
    print("Test 2: Geç tarih (değişiklik yok)")
    filtered_df = filter_tufe_until_august_2020(sample_df, '01-10-2020')
    print(f"\nFiltered data types: {filtered_df.dtypes}")
    tufe_col = None
    for col in filtered_df.columns:
        if 'TÜFE' in col or 'TP_FE_OKTG01' in col:
            tufe_col = col
            break
    if tufe_col:
        print(f"{tufe_col} dtype: {filtered_df[tufe_col].dtype}")
    print(filtered_df) 