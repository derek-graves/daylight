import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime

BASE_URL = "https://gml.noaa.gov/grad/solcalc/table.php?"
YEAR = datetime.datetime.now().year

def create_plot(df):
    """
    plots daylight hours for each day in df

    assumes df has been created by the get_clean_data function
    """

    #preprocess time deltas for graphing
    df["Sunrise_Time"] = df["Sunrise_Time"] / pd.Timedelta(1, "h")
    df["Sunset_Time"] = df["Sunset_Time"] / pd.Timedelta(1, "h")

    #plot with two y-axes: one for daylight hours, the other for sunrise and sunset times
    ax = df.plot(x = "Date", y = "Daylight_Hours")
    plt.xlabel("Date")
    plt.ylabel("Hours", labelpad = 15)
    df.plot(x = "Date", y = ["Sunset_Time", "Sunrise_Time"], secondary_y = True, ax = ax)
    plt.ylabel("Time of Day", rotation = 270, labelpad = 15)
    plt.yticks(np.arange(25, step = 2), [str(i) + ":00" for i in range(0, 24, 2)] + ["0:00"])
    plt.show(block=True)


def get_clean_data(url):
    """
    returns cleaned pandas df of sunrise times, sunset times, and daylight hours for each day of the year

    assumes url contains geographic coordinates of desired location
    """

    #graph html tables
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    data_tables = soup.find_all("table")[:2] #only want sunrise and sunset, not solar noon

    #extract sunrise and sunset times as Timedeltas
    sunrise_deltas = extract_deltas(format_time_data(pd.read_html(str(data_tables))[0]))
    sunset_deltas = extract_deltas(format_time_data(pd.read_html(str(data_tables))[1]))

    #calculate daylight hours as a Timedelta
    daylight_hours = [(sunset_deltas[i] - sunrise_deltas[i]) / pd.Timedelta(hours = 1) for i in range(len(sunrise_deltas))]
    dates = pd.date_range(str(YEAR) + "-01-01", periods = len(sunrise_deltas), freq = "D")

    all_data = {"Date" : dates, "Sunrise_Time" : sunrise_deltas, "Sunset_Time" : sunset_deltas, "Daylight_Hours" : daylight_hours}
    all_df = pd.DataFrame(data = all_data)

    return all_df


def extract_deltas(df):
    """
    extracts timedeltas from pandas dataframe of times

    assumes first column does not contain times
    """

    #create list of Timedeltas from the string containing time of day
    #iterate over each entry in the dataframe
    extraction = [pd.to_timedelta(df.at[i, name].strftime("%H:%M:%S")) for name in list(df.columns)[1:] for i in df.index if pd.notnull(df.at[i, name])]

    return extraction


def format_time_data(df):
    """
    converts all datetime-containing cells in df to correct dtype and correct date
    """

    for name in list(df.columns)[1:]: #first column is day number
        df[name] = df[name].astype("datetime64[ns]") #could use to_datetime

        #ensure each entry has correct date
        for i in df.index:
            df.at[i,name] = df.at[i,name].replace(year = YEAR, month = list(df.columns).index(name), day = df.at[i,"Day"])

    return df


def create_url(lat,lon):
    """
    generate sunrise/sunset data url for given latitude and longitude

    uses NOAA's GML sunrise and sunset table web pages
    """

    curr_year = datetime.date.today().year
    desired_url = f"{BASE_URL}lat={lat}&lon={lon}&year={curr_year}"

    return desired_url


def validate_float(message):
    """
    ensures that the input returned is a valid float.
    """

    value = input(message)
    correct_input = False
    while not correct_input:
        try:
            float(value)
            correct_input = True
        except ValueError:
            print("That is not a valid float. Please enter a float or an integer.\n")
            value = input(message)

    return float(value)


def valid_lat(message):
    """
    ensures that the input returned is a valid latitude float.
    """

    value = validate_float(message)
    while not (-90.0 <= value <= 90.0):
        print("Latitutdes must be between -90 and 90. Please try again.\n")
        value = validate_float(message)

    return value


def valid_lon(message):
    """
    ensures that the input returned is a valid longitude float.
    """

    value = validate_float(message)
    while not (-180.0 <= value <= 180.0):
        print("Longitudes must be between -180 and 180. Please try again.\n")
        value = validate_float(message)

    return value


def main():
    latitude = valid_lat("What is the latitude of your desired location? ")
    longitude = valid_lon("What is the longitude of your desired location? ")
    location_url = create_url(latitude,longitude)
    clean_df = get_clean_data(location_url)
    create_plot(clean_df)


if __name__ == "__main__":
    main()
