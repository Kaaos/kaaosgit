import urllib3
import json
from datetime import datetime

# Get up-to-date NCOV-19 data (Finland). Uses HS open data.
try:
    http = urllib3.PoolManager()
    url = http.request('GET', 'https://w3qa5ydb4l.execute-api.eu-west-1.amazonaws.com/prod/finnishCoronaData/v2/')
    data = json.loads(url.data)
except Exception as e:
    #raise e
    print("Could not get the data.\n")
    exit()

# Parse data:
cases = {}
deaths = {}

try:
    for i in range(len(data['confirmed'])):
        timestamp = datetime.strptime(data['confirmed'][i]['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        district = data['confirmed'][i]['healthCareDistrict']

        if (district in cases.keys()):
            cases[data['confirmed'][i]['healthCareDistrict']] += 1
        else:
            cases[data['confirmed'][i]['healthCareDistrict']] = 1
        

    for i in range(len(data['deaths'])):
        timestamp = datetime.strptime(data['deaths'][i]['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        district = data['deaths'][i]['healthCareDistrict']
        if (data['deaths'][i]['healthCareDistrict'] in deaths.keys()):
            deaths[data['deaths'][i]['healthCareDistrict']] += 1
        else:
            deaths[data['deaths'][i]['healthCareDistrict']] = 1

    caselist  = sorted(cases, key=cases.get)[::-1]
    casecount = sorted(cases.values())[::-1]
    deathlist = sorted(deaths, key=deaths.get)[::-1]
    deathcount = sorted(deaths.values())[::-1]

    # Print results:
    print("\nTartunnat: (N=" + str(sum(casecount)) + ")\n------")
    for i in range(0, len(caselist)):
        print("%-18s %6d" % (caselist[i], casecount[i]))

    if (sum(deathcount) > 0):
        print("\n\nKuolleet: (N=" + str(sum(deathcount)) + ")\n------")
        for i in range(0, len(deathlist)):
            print("%-18s %6d" % (deathlist[i] if deathlist[i] is not None else "-", deathcount[i]))

except Exception as e:
    print("Data parsing error. Check incoming data sample:\n", url.data[:100])
