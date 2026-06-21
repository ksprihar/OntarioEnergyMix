import requests
import pandas as pd
import xml.etree.ElementTree as ET
from io import StringIO

def extract_generation_data(start_year, end_year):
    year_range = range(start_year, end_year + 1)
    fuel_url = "https://reports-public.ieso.ca/public/GenOutputbyFuelMonthly/PUB_GenOutputbyFuelMonthly_{}.xml"
    ns = {'ieso': 'http://www.ieso.ca/schema'}

    df_list = []

    for year in year_range:

        url = fuel_url.format(year)
        response = requests.get(url)
        if response.status_code == 200:
            xml_string = response.content
            root = ET.fromstring(xml_string)
        else:
            raise Exception(f'Error while fetching generation data for year {year}.')

        data_list = []
        for item in root.findall('.//ieso:MonthData', ns):
            for fuel in item.findall('ieso:FuelTotal', ns):
                data_dict = {}
                data_dict['month'] = item.find('ieso:Month', ns).text
                data_dict['fuel'] = fuel.find('ieso:Fuel', ns).text
                data_dict['energy_gw'] = float(fuel.find('ieso:EnergyGW', ns).text)

                data_list.append(data_dict)

        df = pd.DataFrame(data_list)
        df.insert(0, 'year', year)
        df_list.append(df)

    fuel_df = pd.concat(df_list, ignore_index=True)
    fuel_df.to_csv('data/generation_data.csv', index=False)
    print('Generation data saved to data/generation_data.csv')

def extract_demand_data(start_year, end_year):
    year_range = range(start_year, end_year + 1)
    demand_url = "https://reports-public.ieso.ca/public/Demand/PUB_Demand_{}.csv"

    df_list = []

    for year in year_range:
        url = demand_url.format(year)
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text), skiprows=3)
        else:
            raise Exception(f'Error while fetching demand data for year {year}.')

        df['Date'] = pd.to_datetime(df['Date'])
        df.rename(columns={'Date': 'month'}, inplace=True)
        df = df.resample('MS', on='month').agg(
            total_demand=('Ontario Demand', 'sum'),
            avg_demand=('Ontario Demand', 'mean'),
            peak_demand=('Ontario Demand', 'max'),
        )

        df_list.append(df)

    demand_df = pd.concat(df_list)
    demand_df.to_csv('data/demand_data.csv')
    print('Demand data saved to data/demand_data.csv')

if __name__ == '__main__':
    print('Starting ingestion pipeline...')
    extract_generation_data(2015, 2026)
    extract_demand_data(2015, 2026)
    print('All data extracted and ready for SQL.')
