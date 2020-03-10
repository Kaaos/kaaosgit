import urllib3
import json
from datetime import datetime

# Get up-to-date NCOV-19 data (Finland). Uses HS open data.
http = urllib3.PoolManager()
url = http.request('GET', 'https://w3qa5ydb4l.execute-api.eu-west-1.amazonaws.com/prod/finnishCoronaData')
data = json.loads(url.data)

# Parse data:
cases = {}
deaths = {}
latest_infection = [None, None]
latest_death = [None, None]

for i in range(len(data['confirmed'])):
    timestamp = datetime.strptime(data['confirmed'][i]['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
    district = data['confirmed'][i]['healthCareDistrict']

    if (district in cases.keys()):
        cases[data['confirmed'][i]['healthCareDistrict']] += 1
    else:
        cases[data['confirmed'][i]['healthCareDistrict']] = 1
    
    if (latest_infection[0] is None):
        latest_infection[0] = timestamp
        latest_infection[1] = district
    elif (latest_infection[0] < timestamp):
        latest_infection[0] = timestamp
        latest_infection[1] = district

for i in range(len(data['deaths'])):
    timestamp = datetime.strptime(data['deaths'][i]['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
    district = data['deaths'][i]['healthCareDistrict']
    if (data['deaths'][i]['healthCareDistrict'] in deaths.keys()):
        deaths[data['deaths'][i]['healthCareDistrict']] += 1
    else:
        deaths[data['deaths'][i]['healthCareDistrict']] = 1

    if (latest_death[0] is None):
        latest_death[0] = timestamp
        latest_death[1] = district
    if (latest_death[0] < timestamp):
        latest_death[0] = timestamp
        latest_death[1] = district

caselist  = sorted(cases, key=cases.get)[::-1]
casecount = sorted(cases.values())[::-1]
deathlist = sorted(deaths, key=deaths.get)[::-1]
deathcount = sorted(deaths.values())[::-1]

# Print results:
print("\nTartunnat: (N=" + str(sum(casecount)) + ")\n------")
for i in range(0, len(caselist)):
    print("%-18s %6d" % (caselist[i], casecount[i]))
print("\n\tUusin vahvistettu tartunta:", latest_infection[0].strftime("%d.%m.%Y %H:%M:%S UTC") + ", " + latest_infection[1])

if (sum(deathcount) > 0):
    print("\n\nKuolleet: (N=" + str(sum(deathcount)) + ")\n------")
    for i in range(0, len(deathlist)):
        print("%-18s %6d" % (deathlist[i], deathcount[i]))
    print("\n\tTuorein vahvistettu kuolemantapaus:", latest_death[0].strftime("%d.%m.%Y %H:%M:%S UTC") + ", " + latest_death[1])
