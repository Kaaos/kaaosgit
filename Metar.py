import urllib.request

weather = {}  # Fill

clouds = {"SKC": "Sky clear",
          "FEW": "Few clouds",
          "SCT": "Scattered clouds",
          "BKN": "Broken clouds",
          "OVC": "Overcast",
          "NSC": "No significant cloud",
          "VV" : "Vertical visibility",
          "NCD": "Nil cloud detected"}

precip = {'DZ': 'Drizzle', 
          'GR': 'Hail', 
          'GS': 'Snow pellets (granules)', 
          'IC': 'Ice crystals', 
          'PL': 'Pellets of ice',
          'RA': 'Rain', 
          'SG': 'Snow grains', 
          'SN': 'Snow',
          'UP': 'Unknown precipitation'}

obscur = {'FG': 'Fog',
          'BR': 'Mist',
          'DU': 'Dust',
          'SA': 'Sand',
          'VA': 'Volcanic ash',
          'HZ': 'Haze',
          'FU': 'Smoke',
          'PY': 'Spray'}

desc = {'MI': 'Shallow',
        'BC': 'Patches',
        'BL': 'Blowing',
        'TS': 'Thunderstorm',
        'PR': 'Partial',
        'DR': 'Low drifting',
        'SH': 'Showers:',
        'FZ': 'Freezing',
        'VC': 'In the vicinity'}

other = {'SQ': 'Squall',
         'DS': 'Dust storm',
         'FC': 'Funnel cloud',
         'PO': 'Dust or sand whirls',
         'SS': 'Sandstorm'}


def get_intensity(input_str):
    if ('-' in input_str):
        return ' (light)'
    elif ('+' in input_str):
        return ' (heavy)'
    else:
        return ''


def get_metar_string():
    get_metar = "https://opendata.fmi.fi/wfs?request=getFeature&storedquery_id=fmi::avi::observations::latest::iwxxm&icaocode=EFHK"
    try:
        metar = urllib.request.urlopen(get_metar, timeout = 1)
        metar_hel = metar.read()
        metar.close()
    except urllib2.URLError:
        print("Metar observation timeout, continuing.")
        exit()
    metar_hel = str(metar_hel)
    return metar_hel.split("avi:input")[1][1:-2]


def is_number(inp):
    try:
        float(inp)
        return True
    except ValueError:
        return False


def parse_visibility(vis):
    ret = {}
    if(vis == "CAVOK"):
        ret["Visibility"] = "Ceiling and visibility ok"
    elif(int(vis) < 9999):
        ret["Visibility"] = int(vis)
    else:
        ret["Visibility"] = "10 km or more"
    return ret


def parse_wind(wind):
    # Lisää MPS - arvot suoraan m/s
    if("G" in wind):
        temp = wind.split("G")
        return {"Wind Direction": float(wind[0:3]), "Wind Speed (m/s)": round((float(temp[0][3:]) * 0.514444444), 1), "Gusts (m/s)": round((float(temp[1][:-2]) * 0.514444444), 1)}
    elif("VRB" in wind):
        temp = wind.split("VRB")
        return {"Wind Direction": "Variable", "Wind Speed (m/s)": round((float(wind[3:-2]) * 0.514444444), 1)}
    elif("V" in wind):
        return {"Wind Direction": "Variable"}
    return {"Wind Direction": float(wind[0:3]), "Wind Speed (m/s)": round((float(wind[3:-2]) * 0.514444444), 1)}  # Return wind in m/s


def parse_temperatures(temp):
    list_temp = temp.split("/")
    obs = list_temp[0]
    dew = list_temp[1]
    obs = obs.replace("M", "-")
    dew = dew.replace("M", "-")
    return {"Temp": float(obs), "Dew point": float(dew)}


def parse_pressure(press):
    if ('=' in press):
        press = press[:-1]
    return {"Pressure": press[1:] + ' hPa'}


def parse_cloudcovers(cloud):
    index = 2 if cloud.startswith("VV") else 3
    ret = {}
    try:
        ret[clouds[cloud[:index]]] = round(int(filter(str.isdigit, cloud)) * 100.0 * 0.3048, -2)
    except Exception:
        ret[clouds[cloud[:index]]] = ""
    return ret


def decode_metar(metar):
    metar_list = metar.split(' ')

    all_clouds = []
    all_vars = {}


    if("METAR" in metar_list and metar_list[-1].endswith('=')):
        all_vars['Site'] = metar_list[1]
        all_vars['Date'] = metar_list[2][:2]
        all_vars['Time'] = metar_list[2][2:][:2] + ':' + metar_list[2][2:][2:-1] + ' (UTC)'
        all_vars.update(parse_wind(metar_list[3]))
        #all_vars.update(parse_visibility(metar_list[4]))


        precipitation = [] 
        obscurations = []

        intensity = ''

        for i in range(5, len(metar_list)):
            intensity = ''

            if (metar_list[i].startswith('-') or metar_list[i].startswith('+')):
                intensity = get_intensity(metar_list[i])
                metar_list[i] = metar_list[i][1:]
                
            if("/" in metar_list[i]):                                 # OK
                all_vars.update(parse_temperatures(metar_list[i]))

            elif(metar_list[i].startswith('Q')):                        # OK
                all_vars.update(parse_pressure(metar_list[i]))

            elif("G" in metar_list[i] or "VRB" in metar_list[i] or "V" in metar_list[i]):
                parse_wind(metar_list[i])

            elif(metar_list[i][:3] in (list(clouds.keys())) or metar_list[i][:2] in (list(clouds.keys()))):
                all_clouds.append(parse_cloudcovers(metar_list[i]))

            elif(metar_list[i] in (list(obscur.keys()))):
                all_vars['Obscurations'] = obscur[metar_list[i]] + intensity

            elif(metar_list[i] in (list(precip.keys()))):
                all_vars['Precipitation'] = precip[metar_list[i]] + intensity

            elif(metar_list[i][:2] in (list(desc.keys())) and metar_list[i][2:4] in (list(precip.keys()))):
                all_vars['Precipitation'] = desc[metar_list[i][:2]] + ' ' + precip[metar_list[i][2:4]]

            elif("V" in metar_list[i]):
                all_vars['Wind direction'] = "Variable: " + str(metar_list[i].split("V")[0] + " - " + str(metar_list[i].split("V")[-1]))


            # elif(i == "BECMG"):
            # becoming = not becoming # not implemented yet --> becoming
            elif(metar_list[i].startswith("NOSIG")):
                all_vars.update({"Becoming": "No significant changes"})
    else:
        print("Input is not a valid METAR message: \t%s \nExiting." % metar)
        exit()

    '''
    if("METAR" in metar_list[0]):
        for i in metar_list:
            if(i.endswith("KT")):
                all_vars.update(parse_wind(i))
            elif(is_number(i) or i == "CAVOK"):
                all_vars.update(parse_visibility(i))
            elif("/" in i):
                all_vars.update(parse_temperatures(i))
            elif("Q" in i):
                all_vars.update(parse_pressure(i))
            elif(i[:3] in (list(clouds.keys())) or i[:2] in (list(clouds.keys()))):
                all_clouds.append(parse_cloudcovers(i))
            # elif(i == "BECMG"):
            # becoming = not becoming # not implemented yet --> becoming
            elif(i.startswith("NOSIG")):
                all_vars.update({"Becoming": "No significant changes"})
    else:
        print("Not a METAR message. Exiting.")
        exit()
    '''

    return all_vars, all_clouds


#############
#############
#############





metar_message = get_metar_string()
#metar_message = "METAR EFHK 161520Z 36010KT 9999 VCSH " \
#"FEW045CB VV055 -RA +SN BKN060 BKN160 01/M11 Q1011 BECMG NSC="
print('METAR:\n\t', metar_message, "\n")

all_vars, all_clouds = decode_metar(metar_message)

if(len(all_clouds) > 0):
    print(all_clouds)

for i in all_vars:
    print(i + ":", all_vars[i])
