# Turkish Economic Data Analysis Tool

This project analyzes and visualizes Turkish economic indicators, specifically comparing the Turkish Consumer Price Index (TÜFE) with USD/TRY exchange rates and optionally including ENAG (Alternative Inflation Index) data.

![Example Output](Figure_1.png)

## Features

- **TÜFE Analysis**: Fetches and normalizes Turkish Consumer Price Index data from EVDS API
- **USD/TRY Exchange Rate**: Compares inflation with currency devaluation
- **ENAG Integration**: Optional inclusion of alternative inflation index data
- **Interactive Visualization**: Generates comprehensive charts with multiple indicators
- **Flexible Date Ranges**: Customizable start and end dates for analysis
- **Data Normalization**: All indices normalized to base 100 for easy comparison

## Installation

### Prerequisites

- Python 3.7+
- EVDS API access (Turkish Central Bank data service)

### Required Packages

```bash
pip install evds pandas matplotlib numpy argparse
```

## Usage

### Basic Usage

```bash
python enf.py
```

### With Custom Date Range

```bash
python enf.py --start_date 01-01-2020 --end_date 01-12-2024
```

### Including ENAG Data

```bash
python enf.py --enag --start_date 01-09-2018 --end_date 01-07-2025
```

### Command Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--start_date` | `-s` | Start date in DD-MM-YYYY format | 01-09-2018 |
| `--end_date` | `-e` | End date in DD-MM-YYYY format | 01-07-2025 |
| `--enag` | - | Include ENAG data in analysis | False |
| `--verbose` | `-v` | Enable verbose output | False |

## Data Sources

- **TÜFE**: Turkish Consumer Price Index from EVDS API (Series: TP.FE.OKTG01)
- **USD/TRY**: USD to Turkish Lira exchange rate from EVDS API (Series: TP.DK.USD.S.YTL)
- **ENAG**: Alternative inflation index with monthly data from September 2020 onwards

## Output

The tool generates a comprehensive visualization showing:

1. **TÜFE Index**: Consumer price index normalized to starting value
2. **USD/TRY Index**: Exchange rate normalized to starting value
3. **USD/TRY Raw Values**: Actual exchange rate values
4. **ENAG Index** (optional): Alternative inflation index
5. **ENAG Average** (optional): 12-month average of ENAG and USD/TRY

All normalized indices start at 100 on the specified start date for easy comparison.

## File Structure

```
testo/
├── enf.py              # Main analysis script
├── enag.py             # ENAG data processing module
├── tufe_filter.py      # TÜFE data filtering utilities
├── Figure_1.png        # Example output visualization
└── README.md          # This file
```

## Module Details

### enf.py
Main script that:
- Fetches data from EVDS API
- Processes and normalizes data
- Generates comparative visualizations
- Handles command line arguments

### enag.py
Contains:
- Monthly ENAG percentage data from September 2020
- Cumulative percentage calculation functions
- Date range validation

### tufe_filter.py
Utility functions for:
- Filtering TÜFE data by date ranges
- Data type conversion and validation
- Handling pre-September 2020 data

## Special Features

### Historical Data Handling
For start dates before September 2020, the tool:
- Filters TÜFE data until August 2020
- Combines with ENAG data from September 2020 onwards
- Maintains data continuity and normalization

### Data Visualization
- Displays values at regular intervals on the chart
- Uses different colors and styles for each indicator
- Includes both normalized indices and raw values
- Automatic chart scaling and formatting

## API Configuration

The script uses the EVDS API with a predefined API key. For production use, consider:
- Using environment variables for API keys
- Implementing proper error handling for API failures
- Adding rate limiting for API requests

## Examples

### Basic Analysis
```bash
python enf.py --start_date 01-01-2020 --end_date 01-12-2023
```

### Comprehensive Analysis with ENAG
```bash
python enf.py --enag --start_date 01-09-2018 --end_date 01-07-2025 --verbose
```

### Short-term Analysis
```bash
python enf.py --start_date 01-01-2023 --end_date 01-06-2023
```

## Notes

- Start dates before September 2020 will trigger special handling for ENAG data
- The tool automatically warns about data availability for early dates
- All financial data is sourced from official Turkish economic institutions
- Visualizations include both trend analysis and specific data point values

## License

This project is for educational and research purposes. Please ensure compliance with EVDS API terms of service when using this tool. 