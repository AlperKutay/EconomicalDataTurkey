enag_aylik_yuzde = [
    3.61, 2.56, 3.43, 4.08, 2.99, 1.84, 3.36, 2.62, 3.94, 3.28, 4.89, 4.06,
    2.89, 6.90, 9.91, 19.35, 15.52, 5.44, 11.93, 8.68, 5.46, 8.31, 5.03, 5.86,
    5.30, 7.18, 4.24, 5.18, 9.26, 7.21, 3.91, 4.86, 3.66, 8.54, 13.18, 8.59,
    6.24, 5.09, 5.58, 4.12, 9.38, 4.32, 5.68, 5.02, 5.66, 4.27, 5.91, 3.47,
    5.34, 5.57, 4.06, 2.34, 8.22, 3.37, 3.91, 4.46, 3.66, 3.05
]
enag_tarihler = [
    '09-2020', '10-2020', '11-2020', '12-2020', '01-2021', '02-2021', '03-2021', 
    '04-2021', '05-2021', '06-2021', '07-2021', '08-2021', '09-2021', '10-2021', 
    '11-2021', '12-2021', '01-2022', '02-2022', '03-2022', '04-2022', '05-2022', 
    '06-2022', '07-2022', '08-2022', '09-2022', '10-2022', '11-2022', '12-2022', 
    '01-2023', '02-2023', '03-2023', '04-2023', '05-2023', '06-2023', '07-2023', 
    '08-2023', '09-2023', '10-2023', '11-2023', '12-2023', '01-2024', '02-2024', 
    '03-2024', '04-2024', '05-2024', '06-2024', '07-2024', '08-2024', '09-2024', 
    '10-2024', '11-2024', '12-2024', '01-2025', '02-2025', '03-2025', '04-2025', 
    '05-2025', '06-2025'
]
def enag_kumulatif_yuzde(first_data, start_date,verbose=False):
    if start_date in enag_tarihler:
        start_index = enag_tarihler.index(start_date)
        enag_kumulatif_yuzde = [first_data]
        if verbose:
            print(f" {-1} {enag_tarihler[start_index]} : {enag_kumulatif_yuzde[0]}")
        for i in range(start_index, len(enag_aylik_yuzde)):
            enag_kumulatif_yuzde.append(enag_kumulatif_yuzde[i-start_index] * (1 + enag_aylik_yuzde[i] / 100))
            if verbose:
                print(f" {i-start_index} {enag_tarihler[i]} : {enag_kumulatif_yuzde[i-start_index]} * (1 + {enag_aylik_yuzde[i]} / 100)")
        
        return enag_kumulatif_yuzde
    else:
        if verbose:
            print(f"Date {start_date} not found in available dates")
        return [first_data]

