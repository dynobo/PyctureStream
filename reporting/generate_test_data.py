"""Used to generate some dummy events."""

import datetime as dt
from numpy.random import choice
import json


#--------------------------------
# Configure Dummy Data here!
#--------------------------------

# Output Filename
filename = 'events.json'

# Define Range of Timestamp
startdate = (2018,1,1)
number_events = 1000

# Define Values + Distribution for events
# [(Value1,Value2,..) (Probability1, Probability2,...)]
# Sum of probabilities has to be 1
camera_ids = [('webcam_1','webcam_2','webcam_3'),(0.4, 0.3, 0.3)]
event_types = [('frame','movement','face'),(0.9, 0.05, 0.05)]
diff_seconds = [(1, 3, 4, 5, 7),(0.1, 0.2, 0.3, 0.3, 0.1)]


#--------------------------------
# Code for generating Dummy Data
#--------------------------------

def random_value(val_list):
    """Get random value, based on distribution."""
    draw = choice(val_list[0], 1, p=val_list[1])
    return draw[0]


# Startdate for the events
starttime = dt.datetime(*startdate)
events = []
for i in range(number_events):
    time_diff = int(random_value(diff_seconds))
    starttime = starttime + dt.timedelta(seconds=time_diff)
    event = {
            'event_type': random_value(event_types),
            'timestamp': starttime.isoformat(),
            'camera_id': random_value(camera_ids)
    }
    events.append(event)

# Output first and last 3 events for debugging
for i in events[:3]:
    print(i)
print('...')
for i in events[-3:]:
    print(i)

# Store in file
with open(filename, 'w') as f:
    json.dump(events, f, indent=4)
