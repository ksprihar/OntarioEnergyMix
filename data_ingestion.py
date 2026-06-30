"""
data_ingestion.py
-----------------
Fetches Ontario electricity data from the IESO public report portal and writes
two CSV files used by the SQL setup scripts:

  csv_data/generation_data.csv  — monthly generation output (GWh) by fuel type, 2015–present
  csv_data/demand_data.csv      — monthly total demand (GWh) and peak demand (GW), 2015–present

Data sources:
  Generation : https://reports-public.ieso.ca/public/GenOutputbyFuelMonthly/
  Demand     : https://reports-public.ieso.ca/public/Demand/

Run from the project root directory:
    python data_ingestion.py
"""

import requests
import pandas as pd
import xml.etree.ElementTree as ET


def extract_generation_data(start_year, end_year):
    """
    Fetch monthly generation output by fuel type from IESO XML reports and
    write the combined result to csv_data/generation_data.csv.

    The IESO publishes one XML file per calendar year. Each file contains
    monthly totals broken down by fuel type (Nuclear, Gas, Hydro, Wind, etc.).

    Parameters
    ----------
    start_year : int
        First year to fetch (inclusive). IESO data is available from 2015.
    end_year : int
        Last year to fetch (inclusive). Passing the current year will include
        whatever months have been published so far.
    """
    fuel_url = "https://reports-public.ieso.ca/public/GenOutputbyFuelMonthly/PUB_GenOutputbyFuelMonthly_{}.xml"

    # The IESO XML files use a custom namespace — required for all .find() calls
    ns = {'ieso': 'http://www.ieso.ca/schema'}

    df_list = []

    for year in range(start_year, end_year + 1):

        url = fuel_url.format(year)
        response = requests.get(url)

        if response.status_code == 200:
            root = ET.fromstring(response.content)
        else:
            raise Exception(f'Error while fetching Generation data for year {year}.')

        # Each <MonthData> node holds one month; within it, <FuelTotal> nodes
        # hold the per-fuel breakdowns we want
        data_list = []
        for item in root.findall('.//ieso:MonthData', ns):
            month_str = item.find('ieso:Month', ns).text   # e.g. "January"
            for fuel in item.findall('ieso:FuelTotal', ns):
                data_list.append({
                    'month':      month_str,
                    'fuel':       fuel.find('ieso:Fuel', ns).text,
                    'output_gwh': float(fuel.find('ieso:EnergyGW', ns).text),
                })

        df = pd.DataFrame(data_list)

        if not df.empty:
            # Combine the year integer with the month name so pandas can parse
            # the date — e.g. "2022" + "January" → "2022-January" → 2022-01-01
            df['month'] = str(year) + '-' + df['month']
            df_list.append(df)
        else:
            raise Exception(
                f"Warning: No data found in the Generation XML for year {year}. "
                f"Please check the year range supplied to '{extract_generation_data.__name__}'."
            )

    fuel_df = pd.concat(df_list, ignore_index=True)
    fuel_df['month'] = pd.to_datetime(fuel_df['month'], format='%Y-%B')
    fuel_df.to_csv('csv_data/generation_data.csv', index=False)
    print('Generation data saved to csv_data/generation_data.csv')


def extract_demand_data(start_year, end_year):
    """
    Fetch hourly Ontario demand data from IESO CSV reports, aggregate to
    monthly totals and peaks, and write the result to csv_data/demand_data.csv.

    The IESO publishes one CSV per calendar year with hourly demand readings
    in MW. This function converts to GW, then resamples to monthly frequency,
    producing:
      - total_demand_gwh : sum of all hourly readings for the month (GWh)
      - peak_demand_gw   : single highest hourly reading in the month (GW)

    Parameters
    ----------
    start_year : int
        First year to fetch (inclusive).
    end_year : int
        Last year to fetch (inclusive). The current year will have partial data for the current month;
        The demand data is more up to date than generation data;
        the downstream SQL views account for these.
    """
    demand_url = "https://reports-public.ieso.ca/public/Demand/PUB_Demand_{}.csv"

    df_list = []

    for year in range(start_year, end_year + 1):
        url = demand_url.format(year)

        try:
            # IESO demand CSVs have 3 header rows of metadata before the column names
            df = pd.read_csv(url, skiprows=3)
        except Exception as e:
            raise Exception(f'Error while fetching Demand data for year {year}.\nDetails: {e}')

        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            df['ontario_demand_gw'] = df['Ontario Demand'] / 1000  # Convert MW → GW

            # Resample hourly rows to month-start frequency:
            #   total_demand_gwh sums all hourly GW readings → approximates GWh
            #   peak_demand_gw   takes the single-hour maximum for the month
            df.rename(columns={'Date': 'month'}, inplace=True)
            df = df.resample('MS', on='month').agg(
                total_demand_gwh=('ontario_demand_gw', 'sum'),
                peak_demand_gw=('ontario_demand_gw', 'max'),
            ).reset_index()

            df_list.append(df)
        else:
            raise Exception(
                f"Warning: No data found in the Demand CSV for year {year}. "
                f"Please check the year range supplied to '{extract_demand_data.__name__}'."
            )

    demand_df = pd.concat(df_list, ignore_index=True)
    demand_df.to_csv('csv_data/demand_data.csv', index=False)
    print('Demand data saved to csv_data/demand_data.csv')


if __name__ == '__main__':
    print('Starting ingestion pipeline...')
    extract_generation_data(2015, 2026)
    extract_demand_data(2015, 2026)
    print('All data extracted and ready for SQL.')
