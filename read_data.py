import datetime

import pandas as pd

# Make sure you initalized the submodule. Using a submodule allows us to get most up to date data more easily!

__TIME_SERIES_PATH = "COVID-19/csse_covid_19_data/csse_covid_19_time_series"
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
    return __get_sanitized_covid_data(__CONFIRMED_GLOBAL_PATH)

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
