# -*- coding: utf-8 -*-

# Prints latest weather observations of fmi Kumpula (Helsinki) (closest to me :) or Kaisaniemi weather station each time
# terminal is launched. Get your fmi api key here: https://ilmatieteenlaitos.fi/rekisteroityminen-avoimen-datan-kayttajaksi
# You also need to edit .bash_profile (on mac os x) to execute the script on terminal launch

import urllib2
from datetime import datetime, timedelta
from dateutil import tz
import fnmatch
import socket


# Define time zones - UTC & local:
utc_zone = tz.tzutc()
local_zone = tz.tzlocal()

# Time formatting for data requests:
time = datetime.utcnow() + timedelta(hours=-1.17)  # Last hour
time_iso = time.isoformat()  # To ISO format
time_obs = time_iso[:-7] + "Z"  # Timestamp must be like "2016-09-21T17:30:45Z"


# Create links to fetch datasets from server:
kumpula_observation = "https://opendata.fmi.fi/wfs?request=getFeature&storedquery_id=fmi::observations::weather::timevaluepair&place=kumpula,helsinki&maxlocations=1&starttime=" + time_obs
kaisaniemi_observation = "https://opendata.fmi.fi/wfs?request=getFeature&storedquery_id=fmi::observations::weather::timevaluepair&place=kaisaniemi,helsinki&maxlocations=1&starttime=" + time_obs


# Try to get the data, if response is slow -> exit and continue with logon
try:
    observation_kumpula = urllib2.urlopen(kumpula_observation, timeout = 1.5)
    observation_kaisaniemi = urllib2.urlopen(kaisaniemi_observation, timeout = 1.5)
except Exception:
    print "Weather observation timeout, continuing."
    exit()


# Special case handling - If all observations from last hour are 'nan':
# Set base 'naive' timestamp to all variables to avoid errors from undefined variables.
# If no observations from last hour (all "NaN"), program will print out 'nan' and no timestamp.
utctime = datetime.strptime(time_obs, '%Y-%m-%dT%H:%M:%SZ')
utctime = utctime.replace(tzinfo=utc_zone)
naive_time = r_1h_time = t2m_time = ws_10min_time = wg_10min_time = wd_10min_time = rh_time = td_time = ri_10min_time = snow_time = pressure_sealevel_time = visibility_time = cloudcov_time = wawa_time = utctime.astimezone(local_zone) + timedelta(hours=1)

# Assign NA's to variables - if parsing is not successful, prints out 'nan'.
t2m = ws_10min = wg_10min = wd_10min = rh = td = r_1h = ri_10min = snow = pressure_sealevel = visibility = cloudcov = wawa = float("NaN")


# Define weather types (wawa):
weather = {00: "Ei merkittäviä sääilmiöitä",
           04: "Auerta, savua tai ilmassa leijuvaa pölyä ja näkyvyys vähintään 1 km",
           05: "Auerta, savua tai ilmassa leijuvaa pölyä ja näkyvyys alle 1 km",
           10: "Utua",

           # Koodeja 20-25 käytetään, kun on ollut sadetta tai sumua edellisen tunnin aikana mutta ei enää havaintohetkellä:
           20: "Sumua viimeisen tunnin aikana",
           21: "Sadetta viimeisen tunnin aikana",
           22: "Tihkusadetta tai lumijyväsiä viimeisen tunnin aikana",
           23: "Vesisadetta viimeisen tunnin aikana",
           24: "Lumisadetta viimeisen tunnin aikana",
           25: "Jäätävää vesisadetta tai jäätävää tihkua viimeisen tunnin aikana",

           # Seuraavia koodeja käytetään, kun sadetta tai sumua on havaittu havaintohetkellä:
           30: "Sumua",
           31: "Sumua tai jääsumua erillisinä hattaroina",
           32: "Sumua tai jääsumua, joka on ohentunut edellisen tunnin aikana",
           33: "Sumua tai jääsumua, jonka tiheydessä ei ole tapahtunut merkittäviä muutoksia edellisen tunnin aikana",
           34: "Sumua tai jääsumua, joka on muodostunut tai tullut sakeammaksi edellisen tunnin aikana",

           40: "Sadetta (olomuoto määrittelemätön)",
           41: "Heikkoa tai kohtalaista sadetta (olomuoto määrittelemätön)",
           42: "Kovaa sadetta (olomuoto määrittelemätön)",

           50: "Tihkusadetta",
           51: "Heikkoa tihkua, joka ei ole jäätävää",
           52: "Kohtalaista tihkua, joka ei ole jäätävää",
           53: "Kovaa tihkua, joka ei ole jäätävää",
           54: "Jäätävää heikkoa tihkua",
           55: "Jäätävää kohtalaista tihkua",
           56: "Jäätävää kovaa tihkua",

           60: "Vesisadetta",
           61: "Heikkoa vesisadetta, joka ei ole jäätävää",
           62: "Kohtalaista vesisadetta, joka ei ole jäätävää",
           63: "Kovaa vesisadetta, joka ei ole jäätävää",
           64: "Jäätävää heikkoa vesisadetta",
           65: "Jäätävää kohtalaista vesisadetta",
           66: "Jäätävää kovaa vesisadetta",
           67: "Heikkoa lumensekaista vesisadetta tai tihkua (räntää)",
           68: "Kohtalaista tai kovaa lumensekaista vesisadetta tai tihkua (räntää)",

           70: "Lumisadetta",
           71: "Heikkoa lumisadetta",
           72: "Kohtalaista lumisadetta",
           73: "Tiheää lumisadetta",
           74: "Heikkoa jääjyvässadetta",
           75: "Kohtalaista jääjyväsadetta",
           76: "Kovaa jääjyväsadetta",
           77: "Lumijyväsiä",
           78: "Jääkiteitä",

           80: "Kuuroja tai ajoittaista vesisadetta",
           81: "Heikkoja vesikuuroja",
           82: "Kohtalaisia vesikuuroja",
           83: "Kovia vesikuuroja",
           84: "Ankaria vesikuuroja (>32 mm/h)",
           85: "Heikkoja lumikuuroja",
           86: "Kohtalaisia lumikuuroja",
           87: "Kovia lumikuuroja",
           89: "Raekuuroja mahdollisesti yhdessä vesi- tai räntäsateen kanssa"}


# Read observation datasets to string arrays:
try:
    obs_kumpula = observation_kumpula.read().splitlines()
    obs_kaisaniemi = observation_kaisaniemi.read().splitlines()
except Exception:
    print "Error reading weather observations, continuing."
    exit()

# Close server connections:
observation_kumpula.close()
observation_kaisaniemi.close()


# Count NA's of observation sites:
na_kumpula = len(fnmatch.filter(obs_kumpula, '*NaN*'))
na_kaisaniemi = len(fnmatch.filter(obs_kaisaniemi, '*NaN*'))

# Decide primary observation location based on response length and number of NA's:
#   The reason behind this is that the Kumpula station seems to be non-functional every now and then
#   and only returns a few rows of data. Kaisaniemi seems to operate more reliably and constantly.
#   I still slightly prefer Kumpula, due to its location:
if(len(obs_kumpula) >= len(obs_kaisaniemi) and na_kumpula <= na_kaisaniemi):
    obs = obs_kumpula
    station = "Kumpula"
else:
    obs = obs_kaisaniemi
    station = "Kaisaniemi"


# Get latest observations from the data:
#   Loop trough the data (once -> efficient):
i = 0  # Index

while(i < len(obs)):

    # Skip rows with no relevant information:
    if("MeasurementTimeseries" not in obs[i]):
        i += 1
        continue

    # Temperature at 2m level:
    if("t2m" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    t2m = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    t2m_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Wind speed (10 min average):
    elif("ws_10min" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    ws_10min = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    ws_10min_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Wind speed, gusts (10 min):
    elif("wg_10min" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    wg_10min = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    wg_10min_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Wind direction (10 min mean):
    elif("wd_10min" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    wd_10min = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    wd_10min_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Relative humidity:
    elif("rh" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    rh = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    rh_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Dew point:
    elif("td" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    td = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    td_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Total precipitation (last hour):
    elif("r_1h" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    r_1h = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    r_1h_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Rain intensity (last 10 minutes):
    elif("ri_10min" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    ri_10min = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    ri_10min_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Snow depth:
    elif("snow_aws" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    snow = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    snow_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Pressure (at sea level):
    elif("p_sea" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    pressure_sealevel = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    pressure_sealevel_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Visibility:
    elif("vis" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0]
                if(ret != "NaN"):
                    visibility = float(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    visibility_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # Cloud cover:
    elif("n_man" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0].split('.')[0]
                if(ret != "NaN"):
                    cloudcov = int(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    cloudcov_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    # WAWA (weather type):
    elif("wawa" in obs[i]):
        while(True):
            i += 1
            if("value" in obs[i]):
                ret = obs[i].split('>')[1].split('<')[0].split('.')[0]
                if(ret != "NaN"):
                    wawa = int(ret)
                    ret_time = obs[i - 1].split('>')[1].split('<')[0]
                    utctime = datetime.strptime(ret_time, '%Y-%m-%dT%H:%M:%SZ')
                    utc = utctime.replace(tzinfo=utc_zone)
                    wawa_time = utc.astimezone(local_zone)
            elif("MeasurementTimeseries" in obs[i]):
                break

    i += 1  # Update index


# Get timestamp of newest observation:
newest = max(t2m_time, ws_10min_time, wg_10min_time, wd_10min_time, rh_time, td_time, ri_10min_time, snow_time,
             pressure_sealevel_time, visibility_time, cloudcov_time, wawa_time, r_1h_time)


# Define function to return the timestamps of older observations:
def gettime(timevar):
    if(timevar == naive_time):  # No observations in the last hour
        return ''
    elif(timevar != newest):  # Older observation
        return '(' + timevar.strftime('%H:%M') + ')'
    return ''


# Print observations on the screen:
print "\n%s, Helsinki  %s" % (station, newest.strftime("%d/%m/%Y  %H:%M"))
print "Lämpötila: %6.1f °C %8s  Tuulen nopeus: %4.1f m/s %7s   Paine: %10.1f hPa %3s%7s" % (t2m, gettime(t2m_time), ws_10min, gettime(ws_10min_time), pressure_sealevel, "(K)" if pressure_sealevel > 1013.25 else "(M)", gettime(pressure_sealevel_time))
print "Kastepiste: %5.1f °C %7s   Puuska: %11.1f m/s %7s   Näkyvyys: %7.1f km %8s" % (td, gettime(td_time), wg_10min, gettime(wg_10min_time), (visibility / 1000), gettime(visibility_time))
print "Kosteus: %8d %% %8s   Tuulen suunta: %4d ° %9s   Pilvisyys: %4d/8 %11s" % (rh, gettime(rh_time), wd_10min, gettime(wd_10min_time), cloudcov, gettime(cloudcov_time))

# Print precipitation only if precipitation > 0:
if(r_1h > 0.001 or ri_10min > 0.001):
    print "\nEdeltävän tunnin sademäärä: %10.1f mm %s" % (r_1h, gettime(r_1h_time))
    print "Edeltävän 10 minuutin sademäärä: %5.1f mm %s" % (ri_10min, gettime(ri_10min_time))

# Print snow depth only if snow depth > 0:
if(snow > 0):
    print "\nLumen syvyys: %5.1f cm %s" % (snow, gettime(snow_time))

# Print weather type:
if(wawa in weather):
    print "\n%s %7s\n" % (weather[wawa], gettime(wawa_time))
else:
    print "\nSäätyyppiä ei voitu määrittää (tieto puuttuu)\n"
