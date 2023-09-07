import os
import sys
import time
import requests
import csv
import RPi.GPIO as GPIO
from enum import Enum
from datetime import datetime, timedelta
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic

class Location(Enum):
    INCOGNITO = 0
    UNKNOWN = 1
    MOVING = 2
    HOME = 3
    WORK = 4
    SCHOOL = 5

class Person(Enum):
    PERSON1 = "person1"
    PERSON2 = "person2"
    PERSON3 = "person3"
    PERSON4 = "person4"

# Note these are the GPIO pin numbers, not the
# pysical pin numbers.
gpio_pin_assignments = {Person.PERSON2: [7,8,25,24],
                        Person.PERSON1: [9,10,22,27],
                        Person.PERSON3: [14,15,18,23],
                        Person.PERSON4: [2,3,4,17]}
# Sequence the stepper motor coils
# need to be activated in for the
# motor to turn.
coil_seq = [[1,0,0,1],
            [1,0,0,0],
            [1,1,0,0],
            [0,1,0,0],
            [0,1,1,0],
            [0,0,1,0],
            [0,0,1,1],
            [0,0,0,1]]

# Define the lat/lng polygons for each semnatic location.
known_locations = {
    Person.PERSON1: {  Location.HOME: [(-18.196234173438185, 19.0628987963763),
                                    (-17.594046844569828, 29.013219330591376),
                                    (-26.540447945397897, 29.14414460077842),
                                    (-26.774464793381775, 19.84845041749854)],
                                 },
    Person.PERSON2: { Location.HOME:  [(-18.196234173438185, 19.0628987963763),
                                    (-17.594046844569828, 29.013219330591376),
                                    (-26.540447945397897, 29.14414460077842),
                                    (-26.774464793381775, 19.84845041749854)],
                                 },
    # etc...

}

# number of iterations in a full rotation of the
# stepper motor. There are 8 coil activations per
# step of the motor, and 512 steps in a 360 deg rotation.
full_rotation_iterations = 512 * 8

# Helper function to parse timestamps
def parse_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")

def get_current_semantic_locations():
    # HTTP GET request to the API endpoint
    url = "https://api.thinkkappi.com/get_locations"
    secret_token = os.environ.get("WEASLEY_CLOCK_ENDPOINT_SECRET")
    if secret_token is None:
        print("Error: SECRET_TOKEN environment variable not set.")
        exit(1)
    headers = {
    "Authorization": secret_token
    }
    response = requests.get(url)
    data = response.json()

    # Current time
    current_time = datetime.utcnow()

    # Define the threshold time intervals
    moving_threshold = timedelta(minutes=30)

    # Dictionary to store the most recent locations for each name
    recent_locations = {}

    # Initialize the output dictionary with names and "incognito"
    output_dict = {name: Location.INCOGNITO for name in Person}

    # Get the most recent location for each person.
    for entry in data:
        name = Person(entry["name"])
        timestamp = parse_timestamp(entry["timestamp"])
        coordinates = (entry["coordinates"]["x"], entry["coordinates"]["y"])
       
        # Update the recent location if necessary
        if name not in recent_locations or timestamp > recent_locations[name]["timestamp"]:
            recent_locations[name] = {"timestamp": timestamp, "coordinates": coordinates}

    # See if people are in a known location.
    for name, recent_location in recent_locations.items():
        coordinates = recent_location["coordinates"]
        point = Point(coordinates)
       
        # Check if the coordinates fall inside any of the stored polygons
        location = Location.UNKNOWN
        for location_name, poly_coords in known_locations[name].items():
            polygon = Polygon(poly_coords)
            if polygon.contains(point):
                location = location_name
                break
        output_dict[name] = location

    # For any unknown locations, see if the person is actively moving.
    for name, location in output_dict.items():
        if location == Location.UNKNOWN:
            moving_entries = [entry for entry in data if Person(entry["name"]) == name and
                              current_time - parse_timestamp(entry["timestamp"]) <= moving_threshold]
            if len(moving_entries) >= 2:
                previous_coordinates = None
                is_moving = False
               
                for entry in moving_entries:
                    entry_coordinates = (entry["coordinates"]["x"], entry["coordinates"]["y"])
                    if previous_coordinates:
                        distance = geodesic(previous_coordinates, entry_coordinates).meters
                        if distance > 50:
                            is_moving = True
                            break
                   
                    previous_coordinates = entry_coordinates
               
                if is_moving:
                    output_dict[name] = Location.MOVING
    return output_dict

# Function to get previous clock locations from CSV
def get_stored_clock_locations():
    previous_locations = {}
    try:
        with open("clock_locations.csv", "r") as file:
            reader = csv.reader(file)
            for row in reader:
                name = row[0]
                location = row[1]
                previous_locations[Person(name)] = float(location)
    return previous_locations

def write_stored_clock_locations(locations_dict):
    with open("clock_locations.csv", "w", newline="") as file:
        writer = csv.writer(file)
        for name, location in locations_dict.items():
            writer.writerow([name, location])

def semantic_location_to_clock_position(semantic_location: Location):
    segment_size = (full_rotation_iterations / len(Location.__members__))
    # Adjust to be a multiple of 8 so we do full steps of the motor.
    segment_size = segment_size - (segment_size % 8)
    return semantic_location.value * segment_size

def clockwise_loops_delta(start_position, finish_position):
    if finish_position >= start_position:
        return finish_position - start_position
    return start_position + (full_rotation_iterations - finish_position)

def move_hand(person, delta):
    motor_pins = gpio_pin_assignments[person]
    wait_time = 5/float(1000) # 5 milliseconds
    loop_counter = 0
    seq_reset = len(coil_seq)
    seq_counter = 0
    while loop_counter < delta:
        for pin in range(0, 4):
            xpin = motor_pins[pin]
            if coil_seq[seq_counter][pin]!=0:
                GPIO.output(xpin, True)
            else:
                GPIO.output(xpin, False)

        seq_counter += 1
        # If we reach the end of the sequence
        # start again
        if (seq_counter >= seq_reset):
            seq_counter = 0

        # Wait before moving on
        time.sleep(wait_time)
        loop_counter += 1

# Run the main loop.
current_semantic_locations = get_current_semantic_locations()
stored_locations = get_stored_clock_locations()
new_clock_positions = {}
for person, location in current_semantic_locations.items():
    new_clock_position = semantic_location_to_clock_position(location)
    new_clock_positions[person.name] = new_clock_position
    delta = clockwise_loops_delta(stored_locations[person], new_clock_position)
    move_hand(person, delta)

write_stored_clock_locations(new_clock_positions)
