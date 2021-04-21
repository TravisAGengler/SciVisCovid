import datetime
import countries
import os

import pandas as pd

from cartopy.io.shapereader import Reader

# Make sure you initalized the submodule. Using a submodule allows us to get most up to date data more easily!

__TIME_SERIES_PATH = "COVID-19/csse_covid_19_data/csse_covid_19_time_series"
__DAILY_REPORT_PATH = "COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"
__CONFIRMED_GLOBAL_PATH = f"{__TIME_SERIES_PATH}/time_series_covid19_confirmed_global.csv"
__CONFIRMED_US_PATH = f"{__TIME_SERIES_PATH}/time_series_covid19_confirmed_US.csv"
__DEATHS_GLOBAL_PATH = f"{__TIME_SERIES_PATH}/time_series_covid19_deaths_global.csv"
__DEATHS_US_PATH = f"{__TIME_SERIES_PATH}/time_series_covid19_deaths_US.csv"
__RECOVERED_GLOBAL_PATH = f"{__TIME_SERIES_PATH}/time_series_covid19_recovered_global.csv"

def get_covid_confirmed_global():
    """
    Reads the global confirmed cases dataset into a pandas dataframe.
    
    Returns a pandas dataframe containing the sanitized data and timestep metadata
    """
    return __get_sanitized_covid_data(__CONFIRMED_GLOBAL_PATH)

def get_covid_deaths_global():
    """
    Reads the global deaths dataset into a pandas dataframe.
    
    Returns a pandas dataframe containing the sanitized data and timestep metadata
    """
    return __get_sanitized_covid_data(__DEATHS_GLOBAL_PATH)

def get_covid_confirmed_US():
    """
    Reads the US deaths confirmed cases dataset into a pandas dataframe.
    
    Returns a pandas dataframe containing the sanitized data and timestep metadata
    """
    return __get_sanitized_covid_data(__CONFIRMED_US_PATH)

def get_covid_deaths_US():
    """
    Reads the US deaths confirmed cases dataset into a pandas dataframe.
    
    Returns a pandas dataframe containing the sanitized data and timestep metadata
    """
    return __get_sanitized_covid_data(__DEATHS_US_PATH)

def get_covid_recovered_global():
    """
    Reads the global recovered cases dataset into a pandas dataframe.
    
    Returns a pandas dataframe containing the sanitized data and timestep metadata
    """
    return __get_sanitized_covid_data(__RECOVERED_GLOBAL_PATH)

def get_derived_covid_active_global():
    """
    Reads the global active cases dataset into a pandas dataframe.
    
    This is a derivative dataset. It is synthesized from confirmed and recovered cases.
    Lat/Lon is converted into ISO country codes and shape data for easier country identification
    
    Returns a pandas dataframe containing the sanitized data and timestep metadata
    """

    cc = countries.CountryChecker('TM_WORLD_BORDERS-0.3.shp')
    shapes = Reader('ne_50m_admin_0_countries.shp')

    confirmed, timesteps_confirmed = get_covid_confirmed_global()
    shape_data_confirmed = transform_to_shape_data(confirmed, timesteps_confirmed, cc, shapes)

    recovered, timesteps_recovered = get_covid_recovered_global()
    shape_data_recovered = transform_to_shape_data(recovered, timesteps_recovered, cc, shapes)
    
    deaths, timesteps_deaths = get_covid_deaths_global()
    shape_data_deaths = transform_to_shape_data(deaths, timesteps_deaths, cc, shapes)

    shape_data_confirmed_count = shape_data_confirmed[[*timesteps_confirmed]]
    shape_data_recovered_count = shape_data_recovered[[*timesteps_recovered]]
    shape_data_deaths_count = shape_data_deaths[[*timesteps_deaths]]
    shape_data_con_min_rec = shape_data_confirmed_count.subtract(shape_data_recovered_count)
    shape_data_active_count = shape_data_con_min_rec.subtract(shape_data_deaths_count)
    shape_data_active_countries = shape_data_confirmed[['iso', 'shape']]
    shape_data_active = pd.concat([shape_data_active_countries, shape_data_active_count], axis=1)
    
    return shape_data_active, timesteps_confirmed

def get_derived_covid_active_change_global():
    """
    Reads the global active cases change dataset into a pandas dataframe.
    
    This is a derivative dataset. It is synthesized from confirmed and recovered cases.
    Lat/Lon is converted into ISO country codes and shape data for easier country identification.
    Changes are calculated based on previous day active cases
    
    Returns a pandas dataframe containing the sanitized data and timestep metadata
    """
    
    data, timesteps = get_derived_covid_active_global()
    
    delta = data.iloc[0:0,:].copy()
    for index, row in data.iterrows():
        orig = row[[*timesteps]].values
        delt = []
        for day in range(len(orig)):
            prev = orig[day-1] if day != 0 else 0
            cur = orig[day]
            new = cur-prev
            delt.append(new)
        delt.insert(0, row['shape'])
        delt.insert(0, row['iso'])
        delt_row = pd.DataFrame([delt], columns = list(data.columns.values))
        delta = delta.append(delt_row, ignore_index=True)

    return delta, timesteps

def get_daily_data():
    """
    Reads the daily data from the COVID repo. Does some regularization and calculation of Active cases where needed
    
    Returns a dictionary of timestamps to dataframes and the timestamps in chronological order.
    
    The column names are 'province', 'country', 'lat', 'lon', 'confirmed', 'deaths' recovered', 'active'
    
    Any days for which there is no lat-lon data are skipped in the dataset. Effectively, this means we start at 03-01-2020
    """
 
    # 39 (03-01-2020) is the first daily report that contains latitude and longitude
    # 60 (03-22-2020) is the first daily report that contains active cases
    
    days_csv = [os.path.splitext(f)[0] for f in os.listdir(__DAILY_REPORT_PATH) if os.path.splitext(f)[1] == '.csv']
    timestamps = sorted(days_csv, key=lambda x: datetime.datetime.strptime(x, '%m-%d-%Y'))
        
    new_data_all = {}
    kept_timestamps = []
    for timestamp in timestamps:
        csv_path = os.path.join(__DAILY_REPORT_PATH, timestamp) + '.csv'
        data = pd.read_csv(csv_path)

        province_key = 'Province/State'
        if 'Province_State' in data:
            province_key = 'Province_State'

        country_key = 'Country/Region'
        if 'Country_Region' in data:
            country_key = 'Country_Region'
            
        lat_key = 'Latitude'
        if 'Lat' in data:
            lat_key = 'Lat'
            
        lon_key = 'Longitude'
        if 'Long_' in data:
            lon_key = 'Long_'

        needed_keys = [province_key, country_key, lat_key, lon_key, 'Confirmed', 'Deaths', 'Recovered']

        new_keys = {province_key: 'province', 
                    country_key:'country', 
                    lat_key: 'lat', 
                    lon_key: 'lon', 
                    'Confirmed': 'confirmed', 
                    'Deaths': 'deaths', 
                    'Recovered': 'recovered',
                    'Active': 'active'}

        must_skip = False
        for key in needed_keys:
            if not key in data:
                # print(f"{csv_path} lacks required field {key}")
                must_skip = True
                break
        if must_skip:
            continue
        kept_timestamps.append(timestamp)

        needed_data = data[needed_keys]

        if 'Active' in data:
            optional_data = data[['Active']]
            active_cases = optional_data['Active'].fillna(0)
        else:
            # Active = confirmed - deaths - recovered
            confirm_min_death = needed_data['Confirmed'].subtract(needed_data['Deaths'])
            active = confirm_min_death.subtract(needed_data['Recovered'])
            active_cases = active

        new_data = pd.concat([needed_data, active_cases], axis=1)
        new_data.rename(columns={0:'Active'}, inplace=True)
        new_data.rename(columns=new_keys, inplace=True)
        
        new_data_all[timestamp] = new_data
        
    return new_data_all, kept_timestamps

def __sanitize_data(data):
    """
    Removes invalid lat-lon data from the dataset and the associated rows.
    
    Returns a new, sanitized dataframe
    """
    
    # TRICKY: For WHATEVER reason, Long in the US Deaths dataset has a col_name of "Long_". Rename it
    data.rename(columns={"Long_": "Long"}, inplace=True)
    
    # Remove lat-lon of 0. These are cruise ships
    data.drop(data[(data['Lat'] == 0.0) & (data['Long'] == 0.0)].index, inplace=True)
    
    # Remove empty lat-lon. These are repatriated travelers
    data.dropna(subset=['Lat'], inplace=True)
    
    return data

def __get_sanitized_covid_data(data_path):
    data = pd.read_csv(data_path)
    sanitized_data = __sanitize_data(data)
    timesteps = __get_timesteps(sanitized_data)
    return sanitized_data, timesteps

def __is_valid_date(datestring):
    try:
        datetime.datetime.strptime(datestring, '%m/%d/%y')
        return True
    except ValueError:
        return False

def __get_timesteps(data):
    date_cols = []
    for col in data.keys().tolist():
        if __is_valid_date(col):
            date_cols.append(col)
    return date_cols

def __get_entries_iso(country_entries, cc):
    iso = ""
    if country_entries.shape[0] > 1:
        lats = country_entries['Lat'].values
        lons = country_entries['Long'].values
        for i in range(0, len(lats)):
            lat = lats[i]
            lon = lons[i]
            c = cc.getCountry(countries.Point(lat, lon))
            if c:
                iso = c.iso
                break
    else:
        lat = country_entries['Lat'].values[0]
        lon = country_entries['Long'].values[0]
        c = cc.getCountry(countries.Point(lat, lon))
        if c:
            iso = c.iso
    return None if iso == "" else iso

def __get_iso_shape(iso, shapes):
    # TRICKY: We need to use the geometries from THIS, not from TM_WORLD_BORDERS-0.3.shp
    # There are also some large regions that we cannot look up from the ISO_A2 code
    # https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-details/
    # TODO: Handle the exceptions (France, Norway, etc.)
    if iso == None:
        return None
    shp = [s for s in shapes.records() if iso in s.attributes['ISO_A2']]
    return None if len(shp) < 1 else shp[0].geometry

def __get_cumulative_vals(country_entries, timesteps):
    sum_val = [0]*len(timesteps)
    if country_entries.shape[0] > 1:
        vals = country_entries[[*timesteps]].values
        for val in vals:
            sum_val = [sum(x) for x in zip(sum_val, val)]
    else:
        sum_val = country_entries[[*timesteps]].values[0]
    return sum_val

def transform_to_shape_data(data, timesteps, cc, shapes):
    """
    Transforms a dataset into a best-guess shape dataset for countries
    """
    country_data = []
    for country in data['Country/Region'].unique():
        country_entries = data[data['Country/Region'] == country]
        iso = __get_entries_iso(country_entries, cc)
        shape = __get_iso_shape(iso, shapes)
        cumulative_values = __get_cumulative_vals(country_entries, timesteps)
        country_data.append([iso, shape, *cumulative_values])
    shape_data = pd.DataFrame(country_data, columns = ['iso', 'shape', *data[timesteps]])
    return shape_data
