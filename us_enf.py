import requests
import argparse
from datetime import datetime, timedelta

# Replace with your FRED API key
FRED_API_KEY = 'a963277ac5a2ba645e11bdee8132c0a6'

def get_cpi(series_id, date=None, return_data=False):
    """
    Get CPI data from FRED API
    
    Args:
        series_id (str): FRED series ID
        date (str, optional): Date in YYYY-MM-DD format. If None, gets latest data.
        return_data (bool): If True, returns data instead of printing
    
    Returns:
        dict or None: If return_data=True, returns {'date': str, 'value': float} or None
    """
    url = f'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json'
    }
    
    if date:
        # Get data around the requested date to find the closest match
        target_date = datetime.strptime(date, '%Y-%m-%d')
        
        # Get data from 6 months before to 6 months after the target date
        start_date = (target_date - timedelta(days=180)).strftime('%Y-%m-%d')
        end_date = (target_date + timedelta(days=180)).strftime('%Y-%m-%d')
        
        params.update({
            'start_date': start_date,
            'end_date': end_date,
            'sort_order': 'asc'
        })
    else:
        # Get latest data
        params.update({
            'sort_order': 'desc',
            'limit': 1
        })
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        observations = data['observations']
        
        # Filter out observations with missing values
        valid_observations = [obs for obs in observations if obs['value'] != '.']
        
        if valid_observations:
            if date:
                # Find the observation closest to the target date
                target_date = datetime.strptime(date, '%Y-%m-%d')
                closest_obs = None
                min_diff = float('inf')
                
                for obs in valid_observations:
                    obs_date = datetime.strptime(obs['date'], '%Y-%m-%d')
                    diff = abs((obs_date - target_date).days)
                    if diff < min_diff:
                        min_diff = diff
                        closest_obs = obs
                
                if closest_obs:
                    if return_data:
                        return {'date': closest_obs['date'], 'value': float(closest_obs['value'])}
                    
                    if min_diff == 0:
                        print(f"Series ID: {series_id}")
                        print(f"Date: {closest_obs['date']}, CPI: {closest_obs['value']}")
                    else:
                        print(f"Series ID: {series_id}")
                        print(f"Requested date: {date}")
                        print(f"Closest available date: {closest_obs['date']} (difference: {min_diff} days)")
                        print(f"CPI: {closest_obs['value']}")
                else:
                    if return_data:
                        return None
                    print(f"No data found near date {date} in series {series_id}")
            else:
                # Latest data
                obs = valid_observations[0]
                if return_data:
                    return {'date': obs['date'], 'value': float(obs['value'])}
                
                print(f"Series ID: {series_id}")
                print(f"Date: {obs['date']}, CPI: {obs['value']}")
        else:
            if return_data:
                return None
            if date:
                print(f"No data found for date {date} in series {series_id}")
            else:
                print(f"No data found for series {series_id}")
    else:
        if return_data:
            return None
        print("Failed to fetch data:", response.status_code, response.text)

def get_cpi_range(series_id, start_date, end_date):
    """
    Get CPI data for a date range from FRED API
    
    Args:
        series_id (str): FRED series ID
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
    
    Returns:
        list: List of {'date': str, 'value': float} dictionaries
    """
    url = f'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'start_date': start_date,
        'end_date': end_date,
        'sort_order': 'asc'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        observations = data['observations']
        
        # Filter out observations with missing values and convert to proper format
        valid_observations = []
        for obs in observations:
            if obs['value'] != '.':
                valid_observations.append({
                    'date': obs['date'],
                    'value': float(obs['value'])
                })
        
        return valid_observations
    else:
        print(f"Failed to fetch CPI range data: {response.status_code}, {response.text}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Get CPI data from FRED API')
    parser.add_argument('--series_id', 
                       default='CPIAUCSL',
                       help='FRED series ID (default: CPIAUCSL - Consumer Price Index for All Urban Consumers: All Items)')
    parser.add_argument('--date',
                       help='Date in YYYY-MM-DD format (e.g., 2023-01-01). If not provided, gets latest data')
    
    args = parser.parse_args()
    
    # Validate date format if provided
    if args.date:
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print("Error: Date must be in YYYY-MM-DD format (e.g., 2023-01-01)")
            return
    
    get_cpi(args.series_id, args.date)

if __name__ == "__main__":
    main()
