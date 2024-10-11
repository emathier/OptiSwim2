# pip install requests-cache retry-requests openmeteo-requests
# Fetches weather forecast for next 7 days
import argparse
import requests_cache
import pandas as pd
from retry_requests import retry
import openmeteo_requests
from sympy import false
import tqdm

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 47.3667,
	"longitude": 8.55,
	"minutely_15": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "wind_speed_10m", "is_day", "shortwave_radiation"],
	"hourly": "cloud_cover",
    "forecast_days": 7
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# Process minutely_15 data. The order of variables needs to be the same as requested.
minutely_15 = response.Minutely15()
minutely_15_temperature_2m = minutely_15.Variables(0).ValuesAsNumpy()
minutely_15_relative_humidity_2m = minutely_15.Variables(1).ValuesAsNumpy()
minutely_15_apparent_temperature = minutely_15.Variables(2).ValuesAsNumpy()
minutely_15_precipitation = minutely_15.Variables(3).ValuesAsNumpy()
minutely_15_wind_speed_10m = minutely_15.Variables(4).ValuesAsNumpy()
minutely_15_is_day = minutely_15.Variables(5).ValuesAsNumpy()
minutely_15_shortwave_radiation = minutely_15.Variables(6).ValuesAsNumpy()

minutely_15_data = {"date": pd.date_range(
	start = pd.to_datetime(minutely_15.Time(), unit = "s", utc = True),
	end = pd.to_datetime(minutely_15.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = minutely_15.Interval()),
	inclusive = "left"
)}
minutely_15_data["temperature_2m"] = minutely_15_temperature_2m
minutely_15_data["relative_humidity_2m"] = minutely_15_relative_humidity_2m
minutely_15_data["apparent_temperature"] = minutely_15_apparent_temperature
minutely_15_data["precipitation"] = minutely_15_precipitation
minutely_15_data["wind_speed_10m"] = minutely_15_wind_speed_10m
minutely_15_data["is_day"] = minutely_15_is_day
minutely_15_data["shortwave_radiation"] = minutely_15_shortwave_radiation

minForecast = pd.DataFrame(data = minutely_15_data)
minForecast.to_csv("APIs/minForecast.csv", index=False)

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_cloud_cover = hourly.Variables(0).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}
hourly_data["cloud_cover"] = hourly_cloud_cover

hourly = pd.DataFrame(data = hourly_data)
hourly.to_csv("APIs/hourlyForecast.csv", index = False)

# Weather forecast is hourly. However our data is in 30s intervals. We use linear interpolation to achive this.

    

