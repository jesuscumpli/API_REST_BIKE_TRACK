import requests
import os

ORION_HOST = os.getenv('ORION_HOST', 'localhost')
QUANTUMLEAP_HOST = os.getenv('QUANTUMLEAP_HOST', 'localhost')

def get_state_station(id_station):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/' + id_station + '?type=Station'
    response = requests.get(url)
    if response.ok:
        response.encoding = 'utf-8'
        data = response.json()
        state = data["state"]['value']
        return state
    return None

def get_bike_from_station(id_station):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/' + id_station + '?type=Station'
    response = requests.get(url)
    if response.ok:
        response.encoding = 'utf-8'
        data = response.json()
        id_bike = data["id_bike"]['value']
        return id_bike
    return None

def get_bike_from_user_by_id(id_user):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/' + id_user + '?type=User'
    response = requests.get(url)
    if response.ok:
        response.encoding = 'utf-8'
        data = response.json()
        id_bike = data["id_bike"]['value']
        return id_bike
    return None

def get_state_user_by_id(id_user):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/' + id_user + '?type=User'
    response = requests.get(url)
    if response.ok:
        response.encoding = 'utf-8'
        data = response.json()
        state = data["state"]['value']
        return state
    return None

def user_exists(username):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:User:' + username + '?type=User'
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.ok:
        data = response.json()
        if data:
            return True
        else:
            return False
    else:
        return False

def get_password_user(username):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:User:' + username + '?type=User'
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.ok:
        data = response.json()
        password = data["password"]['value']
        return password
    else:
        return None

def get_info_user(username):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:User:' + username + '?type=User'
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.ok:
        data = response.json()
        return data
    else:
        return None

def get_info_station(id_station):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/' + id_station + '?type=Station'
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.ok:
        data = response.json()
        return data
    else:
        return None

def get_all_stations():
    url = 'http://' + ORION_HOST + ':1026/v2/entities?type=Station&limit=100'
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.ok:
        data = response.json()
        return data
    else:
        return None

def get_all_stations_quantumleap():
    url = 'http://' + ORION_HOST + ':8668/v2/entities?type=Station&limit=100'
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.ok:
        data = response.json()
        return data
    else:
        return None

def get_all_bikes():
    url = 'http://' + ORION_HOST + ':1026/v2/entities?type=Bike'
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.ok:
        data = response.json()
        return data
    else:
        return None

def get_info_bike(id_bike):
    url = 'http://' + ORION_HOST + ':1026/v2/entities/' + id_bike + '?type=Bike'
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.ok:
        data = response.json()
        return data
    else:
        return None
