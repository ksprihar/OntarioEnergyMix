import requests
import pandas as pd
import xml.etree.ElementTree as ET

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
            raise Exception(f'Error while fetching Generation data for year {year}.')

        data_list = []
        for item in root.findall('.//ieso:MonthData', ns):
            for fuel in item.findall('ieso:FuelTotal', ns):
                data_dict = {}
                data_dict['month'] = item.find('ieso:Month', ns).text
                data_dict['fuel'] = fuel.find('ieso:Fuel', ns).text
                data_dict['output_gwh'] = float(fuel.find('ieso:EnergyGW', ns).text)

                data_list.append(data_dict)

        df = pd.DataFrame(data_list)

        if not df.empty:
            df['month'] = str(year) + '-' + df['month']
            df_list.append(df)
        else:
            raise Exception(f"Warning: No data found in the Generation xml for year {year}. Please check the year range supplied to the '{extract_generation_data.__name__}' function.")

    fuel_df = pd.concat(df_list, ignore_index=True)
    fuel_df['month'] = pd.to_datetime(fuel_df['month'], format='%Y-%B')
    fuel_df.to_csv('csv_data/generation_data.csv', index=False)
    print('Generation data saved to data/generation_data.csv')

def extract_demand_data(start_year, end_year):
    year_range = range(start_year, end_year + 1)
    demand_url = "https://reports-public.ieso.ca/public/Demand/PUB_Demand_{}.csv"

    df_list = []

    for year in year_range:
        url = demand_url.format(year)

        try:
            df = pd.read_csv(url, skiprows=3)
        except Exception as e:
            raise Exception(f'Error while fetching Demand data for year {year}.\nDetails: {e}')

        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            df['ontario_demand_gw'] = df['Ontario Demand'] / 1000  # Converting MW to GW
            df.rename(columns={'Date': 'month'}, inplace=True)
            df = df.resample('MS', on='month').agg(
                total_demand_gwh=('ontario_demand_gw', 'sum'), # Total energy consumption for the month in GWh
                avg_demand_gw=('ontario_demand_gw', 'mean'), # Average Power demand in GW
                peak_demand_gw=('ontario_demand_gw', 'max'), # Maximum Power demand over a single hour in the month in GW
            ).reset_index()

            df_list.append(df)
        else:
            raise Exception(f"Warning: No data found in the Demand csv for year {year}. Please check the year range supplied to the '{extract_demand_data.__name__}' function.")

    demand_df = pd.concat(df_list, ignore_index=True)
    demand_df.to_csv('csv_data/demand_data.csv', index=False)
    print('Demand data saved to data/demand_data.csv')

if __name__ == '__main__':
    print('Starting ingestion pipeline...')
    extract_generation_data(2015, 2026)
    extract_demand_data(2015, 2026)
    print('All data extracted and ready for SQL.')
