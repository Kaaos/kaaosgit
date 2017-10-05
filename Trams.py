# -*- coding: utf-8 -*-

# Gets realtime data for nearby tram stops

import requests


# Define function to parse times to human understandable form:
def parse_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)  # Return time in hh:mm:ss


###############
#  Get data:  #
###############

# Predefined GraphQL query to get data from desired stops and alerts:
query = '{                                                                                                      \
    routes(ids: ["HSL:1001", "HSL:1006", "HSL:1006T", "HSL:1007", "HSL:1008"]) {                                \
        shortName                                                                                               \
        alerts {                                                                                                \
            alertDescriptionText                                                                                \
        }                                                                                                       \
    }                                                                                                           \
    stops(ids: ["HSL:1220411", "HSL:1220410", "HSL:1220417", "HSL:1220416"]) {                                  \
        name                                                                                                    \
        code                                                                                                    \
        stoptimesWithoutPatterns {                                                                              \
            realtimeArrival                                                                                     \
            arrivalDelay                                                                                        \
            realtime                                                                                            \
            headsign                                                                                            \
            trip {                                                                                              \
                route {                                                                                         \
                    shortName                                                                                   \
                }                                                                                               \
            }                                                                                                   \
        }                                                                                                       \
    }                                                                                                           \
}'


# Get data:
limit = 5  # Retry limit
loops = 0  # Retry count

# Try to get the data, retry if need be (up to the retry limit). Continue only with valid response:
while True:
    try:
        res = requests.post("https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql", data=query)
    except Exception:
        loops += 1
    if(loops >= limit):
        print("Data request failed. Exiting.")
        exit()
        continue
    if(res.status_code == requests.codes.ok):
        data = res.json()
        break


####################
#  Print results:  #
####################

# Define directions of travel:
stop_directions = {"0266": "Keskustaan", "0320": "Keskustaan", "0319": "Arabiaan", "0265": "Pasilaan / Käpylään"}

# Print to terminal:
print('Seuraavat sporat lähipysäkeiltä:')

for i in [0, 2]:  # 0 & 2 = Stop group indexes, indexes to start a new print group
    # Print stop information:
    print()
    print('%s' % (data['data']['stops'][i]['name']))
    print('%s:%51s%s:' % (stop_directions[data['data']['stops'][i]['code']], ' ', stop_directions[data['data']['stops'][i + 1]['code']]))

    # Print times:
    for j in range(len(data['data']['stops'][i]['stoptimesWithoutPatterns'])):
        time_1 = parse_time(data['data']['stops'][i]['stoptimesWithoutPatterns'][j]['realtimeArrival'])
        time_2 = parse_time(data['data']['stops'][i + 1]['stoptimesWithoutPatterns'][j]['realtimeArrival'])
        line_1 = data['data']['stops'][i]['stoptimesWithoutPatterns'][j]['trip']['route']['shortName']
        line_2 = data['data']['stops'][i + 1]['stoptimesWithoutPatterns'][j]['trip']['route']['shortName']
        sign_1 = data['data']['stops'][i]['stoptimesWithoutPatterns'][j]['headsign']
        sign_2 = data['data']['stops'][i + 1]['stoptimesWithoutPatterns'][j]['headsign']
        print('%-12s%-6s%-30s  %10s  %-12s%-6s%-30s' % (time_1, line_1, ('-' if sign_1 is None else sign_1), ' ', time_2, line_2, ('-' if sign_2 is None else sign_2)))

print()

# Print possible alerts for routes above:
for i in range(len(data['data']['routes'])):
    for j in data['data']['routes'][i]['alerts']:
        print('%s%2s%s%s' % ('Linja ', data['data']['routes'][i]['shortName'], ':\n', j['alertDescriptionText']))
