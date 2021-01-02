import argparse
import requests
import json
from datetime import datetime
from zoautil_py import MVSCmd, Datasets
from zoautil_py.types import DDStatement
 
def converttodate(timestamp):
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")

#Setup Parser
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--From", help = "From where do you need to leave(e.g. Zurich)")
parser.add_argument("-t", "--To", help = "Where do you need to go(e.g. Geneva)")
parser.add_argument("-a", "--ArrivalTime", help = "When do you need to arrive at your destination(e.g. 17:00)")

args = parser.parse_args()

fromStation = args.From
toStation = args.To
arrivalTime = args.ArrivalTime

print("calculating your journey please wait :)")
#creating member for the journey output
output_dataset="Z06403.OUTPUT.JOURNEY"
if Datasets.exists(output_dataset):
    Datasets.delete(output_dataset)

Datasets.create(output_dataset,"SEQ")

#get the json structure from opendata switzerland
response = requests.get(
    'http://transport.opendata.ch/v1/connections',
    params={'from': fromStation,
            'to': toStation,
            'time': arrivalTime,
            'isArrivalTime': '1'},
)
journeys = json.loads(response.text)
sections = []
lines = []
try:
    sections = journeys["connections"][3]["sections"]
except IndexError:
    print("the stations you entered do not exist")
    quit(1)
    
# Write header information
lines.append("==============================================================================")
lines.append(journeys["connections"][3]["from"]["station"]["name"] + " -> " +
             journeys["connections"][3]["to"]["station"]["name"])
lines.append("Departure time: " + converttodate(sections[0]["departure"]["departure"]).strftime(
    "%H:%M:%S") + " CET | Arrival time: " + journeys["connections"][3]["to"]["arrival"][11:19] + " CET")
lines.append("Duration: " + journeys["connections"][3]["duration"][3:] + "    ")

lines.append("==============================================================================")

# iterate over all sections of the journey
for section in sections:
    if section["journey"] is None:
        continue
    else:
        formattedDeparture = converttodate(section["departure"]["departure"])
        formattedArrival = converttodate(section["arrival"]["arrival"])
        platform = ""
        if section["departure"]["platform"] is not None:
            platform = section["departure"]["platform"]

        lines.append(
            formattedDeparture.strftime("%H:%M:%S") + " * "
            + section["departure"]["station"]["name"]
            + " (platform:" +
            platform + ")")
        lines.append("         | ")
        lines.append("         | " + section["journey"]["category"] + section["journey"]["number"] + " to " +
                     section["journey"]["to"])
        lines.append("         | ")
        lines.append(
            formattedArrival.strftime("%H:%M:%S") + " * "
            + section["arrival"]["station"]["name"])
lines.append("==============================================================================")

# replace special chars to prevent encoding issues
lines = [w.replace(chr(252), 'u').replace(chr(232), 'e') for w in lines]

connectionOutput = '\n'.join(lines)
# give the user feedback about the journey
print(connectionOutput)
print("saving the connection...")
Datasets.write(output_dataset,connectionOutput)
print("all done!")