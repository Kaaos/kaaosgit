import urllib.request

weather = {}  # Fill

clouds = {"SKC": "Sky clear",
          "FEW": "Few clouds",
          "SCT": "Scattered clouds",
          "BKN": "Broken clouds",
          "OVC": "Overcast",
          "NSC": "No significant cloud",
          "VV": "Vertical visibility"}


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


def metarstring_to_list(metar):
    return metar.split(" ")


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


def parse_time(timestamp):
    return {"Raw timestamp": timestamp}


def parse_wind(wind):
    if("G" in wind):
        temp = wind.split("G")
        return {"Wind Direction": float(wind[0:3]), "Wind Speed (m/s)": round((float(temp[0][3:]) * 0.514444444), 1), "Gusts (m/s)": round((float(temp[1][:-2]) * 0.514444444), 1)}
    elif("VRB" in wind):
        temp = wind.split("VRB")
        return {"Wind Direction": "Variable", "Wind Speed (m/s)": round((float(wind[3:-2]) * 0.514444444), 1)}
    return {"Wind Direction": float(wind[0:3]), "Wind Speed (m/s)": round((float(wind[3:-2]) * 0.514444444), 1)}  # Return wind in m/s


def parse_temperatures(temp):
    list_temp = temp.split("/")
    obs = list_temp[0]
    dew = list_temp[1]
    obs = obs.replace("M", "-")
    dew = dew.replace("M", "-")
    return {"Temp": float(obs), "Dew point": float(dew)}


def parse_pressure(press):
    return {"Pressure": float(press[1:])}


def parse_cloudcovers(cloud):
    index = 2 if cloud.startswith("VV") else 3
    ret = {}
    try:
        ret[clouds[cloud[:index]]] = round(int(filter(str.isdigit, cloud)) * 100.0 * 0.3048, -2)
    except Exception:
        ret[clouds[cloud[:index]]] = ""
    return ret


def decode_metar(metar):
    metar_list = metarstring_to_list(metar)
    all_clouds = []
    all_vars = {}
    if("METAR" in metar_list[0]):
        for i in metar_list:
            if(i.endswith("Z")):
                all_vars.update(parse_time(i))
            elif(i.endswith("KT")):
                all_vars.update(parse_wind(i))
            elif(is_number(i) or i == "CAVOK"):
                all_vars.update(parse_visibility(i))
            elif("/" in i):
                all_vars.update(parse_temperatures(i))
            elif("Q" in i):
                all_vars.update(parse_pressure(i))
            elif(i.startswith(("SKC", "NSC", "FEW", "SCT", "BKN", "OVC", "VV"))):
                all_clouds.append(parse_cloudcovers(i))
            # elif(i == "BECMG"):
            # becoming = not becoming # not implemented yet --> becoming
            elif(i.startswith("NOSIG")):
                all_vars.update({"Becoming": "No significant changes"})
    else:
        print("Not a METAR message. Exiting.")
        exit()
    return all_vars, all_clouds


#############
#############
#############


metar_message = get_metar_string()
"""
metar_message = "METAR EFHK 161520Z 36010KT 9999 VCSH" \
"FEW045CB VV055 BKN060 BKN160 01/M11 Q1011 BECMG NSC="
"""
print(metar_message, "\n")

all_vars, all_clouds = decode_metar(metar_message)

if(len(all_clouds) > 0):
    print(all_clouds)

for i in all_vars:
    print(i + ":", all_vars[i])
