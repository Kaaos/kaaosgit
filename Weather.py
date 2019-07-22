# Python3
# Prints latest weather observations of fmi Kumpula (Helsinki) (closest to me :) or Kaisaniemi weather station each time
# terminal is launched. 
# You need to edit .bash_profile (on mac os) to execute the script on terminal launch


# Imports
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dateutil import tz
import pytz
import fnmatch


# Get urls to fetch the data from
def get_connection_urls():
    utc_zone   = tz.tzutc()
    local_zone = tz.tzlocal()

    time = datetime.utcnow() + timedelta(hours = -1.17)     # Last hour
    time_iso = time.isoformat()                             # To ISO format
    time_obs = time_iso[:-7] + 'Z'                          # Timestamp must be like '2016-09-21T17:30:45Z'

    kumpula_observation    = 'https://opendata.fmi.fi/wfs?request=getFeature&storedquery_id=fmi::observations::weather::timevaluepair&place=kumpula,helsinki&maxlocations=1&starttime='     + time_obs
    kaisaniemi_observation = 'https://opendata.fmi.fi/wfs?request=getFeature&storedquery_id=fmi::observations::weather::timevaluepair&place=kaisaniemi,helsinki&maxlocations=1&starttime='  + time_obs

    return {'Kumpula': kumpula_observation, 'Kaisaniemi': kaisaniemi_observation}


# Try to get the data, if response is slow -> exit and continue with logon
def fetch_data(urls):
    try:
        kumpula = urllib.request.urlopen(urls['Kumpula'], timeout = 1.5)
        kaisaniemi = urllib.request.urlopen(urls['Kaisaniemi'], timeout = 1.5)
    except Exception:
        print('Weather observation timeout, continuing.')
        exit()

    try:
        obs_kumpula = kumpula.read()
        obs_kaisaniemi = kaisaniemi.read()
    except Exception:
        print('Reading weather observation data failed, continuing.')
    finally:
        kumpula.close()     # Close server connections
        kaisaniemi.close()

    # Decide primary observation location based on response length and number of NA's:
    #   The reason behind this is that the Kumpula station seems to be non-functional every now and then
    #   and only returns a few rows of data. Kaisaniemi seems to operate more reliably and constantly.
    #   I still slightly prefer Kumpula due to its location:

    na_kumpula = len(fnmatch.filter(str(obs_kumpula), '*NaN*'))
    na_kaisaniemi = len(fnmatch.filter(str(obs_kaisaniemi), '*NaN*'))

    if(len(obs_kumpula) >= len(obs_kaisaniemi) and na_kumpula <= na_kaisaniemi):
        obs = obs_kumpula
        station = 'Kumpula'
    else:
        obs = obs_kaisaniemi
        station = 'Kaisaniemi'

    return (station, obs)   # Return selected station and its raw gml data


# Parse GML data to a dictionary:
def parse_data(data):
    root = ET.fromstring(data)  # XML/GML parser root
    ret  = {}                   # Empty dictionary for observation variables

    # Get observations:
    variables = root.findall('.//wml2:MeasurementTimeseries', namespaces)
    for i in range(len(variables)):
        observations = variables[i].findall('.//wml2:MeasurementTVP', namespaces)   # Find all time-value pairs
        varname = str(list(variables[i].attrib.values())[0].split('-')[-1])         # Get variable name
        for i in observations:
            if (i[1].text != 'NaN'):                                                # Don't save missing data
                time = datetime.strptime(i[0].text, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo = pytz.UTC)
                time = time.astimezone(tz.tzlocal())
                value = float(i[1].text)
                ret[varname] = [time, value]                                        # Save observation time and value

    #printvars(ret)                                                                 # Debugging call

    # Get latest timestamp of observations:
    timestamps = []
    temp = list(ret.values())   # All observation time-value pairs

    # Put all timestamps in a list (use local time zone)
    for i in range(len(temp)):
        timestamps.append(temp[i][0])
    latest_observation = max(timestamps)    # Find maximum value (= latest observation time)

    return (ret, latest_observation)        # Return data dictionary and latest timestamp


# Function to get older observations timestamps in a preferred form:
def gettime(stamp, latest_observation):
    if (stamp < latest_observation):
        return '(' + stamp.strftime('%H:%M') + ')'
    return ''


# Function for debugging purposes, prints the contents of the data dictionary:
def printvars(variable_dict):
    for x in variable_dict:
        print(x)
        for y in variable_dict[x]:
            print('    ', y)


# Function to print observations on the screen:
def print_observations(vlist, latest, station):
    print('\n%s, Helsinki %s' % (station, latest.strftime('%d/%m/%Y %H:%M')))

    print('Lämpötila: %6s °C %7s  Tuulen nopeus: %5s m/s %7s   Paine: %10s hPa %7s' % 
        ('--' if ('t2m'      not in vlist) else str(vlist['t2m'][1]),      gettime(vlist['t2m'][0], latest)         if 't2m'      in vlist else '',
         '--' if ('ws_10min' not in vlist) else str(vlist['ws_10min'][1]), gettime(vlist['ws_10min'][0], latest)    if 'ws_10min' in vlist else '',
         '--' if ('p_sea'    not in vlist) else str(vlist['p_sea'][1]),    gettime(vlist['p_sea'][0], latest)       if 'p_sea'    in vlist else ''))

    print('Kastepiste: %5s °C %7s   Puuska: %11s m/s %7s   Näkyvyys: %7s km %8s' % 
        ('--' if ('td'       not in vlist) else str(vlist['td'][1]),         gettime(vlist['td'][0], latest)        if 'td'       in vlist else '',
         '--' if ('wg_10min' not in vlist) else str(vlist['wg_10min'][1]),   gettime(vlist['wg_10min'][0], latest)  if 'wg_10min' in vlist else '', 
         '--' if ('vis'      not in vlist) else str(vlist['vis'][1] / 1000), gettime(vlist['vis'][0], latest)       if 'vis'      in vlist else ''))

    print('Kosteus: %8s %% %8s   Tuulen suunta: %4s ° %9s   Pilvisyys: %4s/8 %11s' % 
        ('--' if ('rh'       not in vlist) else str(int(vlist['rh'][1])),       gettime(vlist['rh'][0], latest)         if 'rh'       in vlist else '',
         '--' if ('wd_10min' not in vlist) else str(int(vlist['wd_10min'][1])), gettime(vlist['wd_10min'][0], latest)   if 'wd_10min' in vlist else '',
         '--' if ('n_man'    not in vlist) else str(int(vlist['n_man'][1])),    gettime(vlist['n_man'][0], latest)      if 'n_man'    in vlist else ''))

    # Print precipitation only if precipitation > 0:
    if ('r_1h' in vlist):
        if (vlist['r_1h'][1] > 0.001):
            print('\nEdeltävän tunnin sademäärä: %10.1f mm %s' % (vlist['r_1h'][1], gettime(vlist['r_1h'][0], latest)))

    if ('ri_10min' in vlist):
        if (vlist['ri_10min'][1] > 0.001):
            print('Edeltävän 10 minuutin sademäärä: %5.1f mm %s' % (vlist['ri_10min'][1], gettime(vlist['ri_10min'][0], latest)))

    # Print snow depth only if snow depth > 0:
    if ('snow_aws' in vlist and vlist['snow_aws'][1] > 0):
        print('\nLumen syvyys: %5.1f cm %s' % (vlist['snow_aws'][1], gettime(vlist['snow_aws'][0], latest)))

    # Print weather type:
    if ('wawa' in vlist):
        print('\n%s %7s\n' % (weather[int(vlist['wawa'][1])], gettime(vlist['wawa'][0], latest)))
    else:
        print('\nSäätyyppiä ei voitu määrittää (tieto puuttuu)\n')



# # # # # # # # # # #
#       Main:       #
# # # # # # # # # # #

# Define XML/GML namespaces:
namespaces = {'wfs'     : 'http://www.opengis.net/wfs/2.0',
              'xsi'     : 'http://www.w3.org/2001/XMLSchema-instance',
              'xlink'   : 'http://www.w3.org/1999/xlink',
              'om'      : 'http://www.opengis.net/om/2.0',
              'ompr'    : 'http://inspire.ec.europa.eu/schemas/ompr/3.0',
              'omso'    : 'http://inspire.ec.europa.eu/schemas/omso/3.0',
              'gml'     : 'http://www.opengis.net/gml/3.2',
              'gmd'     : 'http://www.isotc211.org/2005/gmd',
              'gco'     : 'http://www.isotc211.org/2005/gco',
              'swe'     : 'http://www.opengis.net/swe/2.0',
              'gmlcov'  : 'http://www.opengis.net/gmlcov/1.0',
              'sam'     : 'http://www.opengis.net/sampling/2.0',
              'sams'    : 'http://www.opengis.net/samplingSpatial/2.0',
              'wml2'    : 'http://www.opengis.net/waterml/2.0',
              'target'  : 'http://xml.fmi.fi/namespace/om/atmosphericfeatures/1.0'}

# Define weather types (wawa):
weather = {0:  'Ei merkittäviä sääilmiöitä',
           4:  'Auerta, savua tai ilmassa leijuvaa pölyä ja näkyvyys vähintään 1 km',
           5:  'Auerta, savua tai ilmassa leijuvaa pölyä ja näkyvyys alle 1 km',
           10: 'Utua',

           # Koodeja 20-25 käytetään, kun on ollut sadetta tai sumua edellisen tunnin aikana mutta ei enää havaintohetkellä:
           20: 'Sumua viimeisen tunnin aikana',
           21: 'Sadetta viimeisen tunnin aikana',
           22: 'Tihkusadetta tai lumijyväsiä viimeisen tunnin aikana',
           23: 'Vesisadetta viimeisen tunnin aikana',
           24: 'Lumisadetta viimeisen tunnin aikana',
           25: 'Jäätävää vesisadetta tai jäätävää tihkua viimeisen tunnin aikana',

           # Seuraavia koodeja käytetään, kun sadetta tai sumua on havaittu havaintohetkellä:
           30: 'Sumua',
           31: 'Sumua tai jääsumua erillisinä hattaroina',
           32: 'Sumua tai jääsumua, joka on ohentunut edellisen tunnin aikana',
           33: 'Sumua tai jääsumua, jonka tiheydessä ei ole tapahtunut merkittäviä muutoksia edellisen tunnin aikana',
           34: 'Sumua tai jääsumua, joka on muodostunut tai tullut sakeammaksi edellisen tunnin aikana',
           40: 'Sadetta (olomuoto määrittelemätön)',
           41: 'Heikkoa tai kohtalaista sadetta (olomuoto määrittelemätön)',
           42: 'Kovaa sadetta (olomuoto määrittelemätön)',
           50: 'Tihkusadetta',
           51: 'Heikkoa tihkua, joka ei ole jäätävää',
           52: 'Kohtalaista tihkua, joka ei ole jäätävää',
           53: 'Kovaa tihkua, joka ei ole jäätävää',
           54: 'Jäätävää heikkoa tihkua',
           55: 'Jäätävää kohtalaista tihkua',
           56: 'Jäätävää kovaa tihkua',
           60: 'Vesisadetta',
           61: 'Heikkoa vesisadetta, joka ei ole jäätävää',
           62: 'Kohtalaista vesisadetta, joka ei ole jäätävää',
           63: 'Kovaa vesisadetta, joka ei ole jäätävää',
           64: 'Jäätävää heikkoa vesisadetta',
           65: 'Jäätävää kohtalaista vesisadetta',
           66: 'Jäätävää kovaa vesisadetta',
           67: 'Heikkoa lumensekaista vesisadetta tai tihkua (räntää)',
           68: 'Kohtalaista tai kovaa lumensekaista vesisadetta tai tihkua (räntää)',
           70: 'Lumisadetta',
           71: 'Heikkoa lumisadetta',
           72: 'Kohtalaista lumisadetta',
           73: 'Tiheää lumisadetta',
           74: 'Heikkoa jääjyvässadetta',
           75: 'Kohtalaista jääjyväsadetta',
           76: 'Kovaa jääjyväsadetta',
           77: 'Lumijyväsiä',
           78: 'Jääkiteitä',
           80: 'Kuuroja tai ajoittaista vesisadetta',
           81: 'Heikkoja vesikuuroja',
           82: 'Kohtalaisia vesikuuroja',
           83: 'Kovia vesikuuroja',
           84: 'Ankaria vesikuuroja (>32 mm/h)',
           85: 'Heikkoja lumikuuroja',
           86: 'Kohtalaisia lumikuuroja',
           87: 'Kovia lumikuuroja',
           89: 'Raekuuroja mahdollisesti yhdessä vesi- tai räntäsateen kanssa'}

urls          = get_connection_urls()
station, data = fetch_data(urls)
vlist, latest = parse_data(data)
print_observations(vlist, latest, station)
