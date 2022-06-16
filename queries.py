import requests
import os

ORION_HOST = os.getenv('ORION_HOST', 'localhost')
QUANTUMLEAP_HOST = os.getenv('QUANTUMLEAP_HOST', 'localhost')

def get_state_station(id_station):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:Station:'+id_station+'?type=Station'
    response = requests.get(url)
    response.encoding = 'utf-8'
    data = response.json()
    state = data["state"]
    return state

def get_bike_from_station(id_station):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:Station:' + id_station + '?type=Station'
    response = requests.get(url)
    response.encoding = 'utf-8'
    data = response.json()
    id_bike = data["id_bike"]
    return id_bike

def get_bike_from_user(id_user):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:User:' + id_user + '?type=Station'
    response = requests.get(url)
    response.encoding = 'utf-8'
    data = response.json()
    id_bike = data["id_bike"]
    return id_bike

def get_state_user(id_user):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:User:' + id_user + '?type=Station'
    response = requests.get(url)
    response.encoding = 'utf-8'
    data = response.json()
    state = data["state"]
    return state