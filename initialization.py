import hashlib
import random
import uuid

import requests
import json
import os

import queries

ORION_HOST = os.getenv('ORION_HOST', 'localhost')


def create_user(id_user, username, password, tag_rfid):
    try:
        hash_pass = hashlib.sha256(password.encode()).hexdigest()
        json_user = {
            "id": id_user,
            "type": "User",
            "username": {"type": "Text", "value": username},
            "password": {"type": "Text", "value": hash_pass},
            "tag_rfid": {"type": "Text", "value": tag_rfid},
            "state": {"type": "Text", "value": "DISPONIBLE"},  # DISPONIBLE / RESERVADO / OCUPADO
            "id_station": {"type": "Text", "value": None},  # ID ESTACION RESERVADA
            "id_bike": {"type": "Text", "value": None},  # ID BIKE RESERVADA / OCUPADA
        }
        newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
        response = requests.post('http://' + ORION_HOST + ':1026/v2/entities',
                                 data=json.dumps(json_user),
                                 headers=newHeaders)
        print("Status code: ", response.status_code)
        print(response.text)
        if int(response.status_code) >= 400:
            raise Exception(response.text)

        response = {"status": 200, "msg": "User created"}
        return response
    except Exception as e:
        response = {'status': 400, "msg": str(e)}
        return response


def create_station(id, name, latitude, longitude):
    try:
        json_station = {
            "id": id,
            "type": "Station",
            "state": {"type": "Text", "value": "LIBRE"},  # DISPONIBLE / RESERVADO / LIBRE
            "location": {
                "type": "geo:json",
                "value": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                }
            },
            "name": {
                "type": "Text",
                "value": name
            },
            "id_user": {
                "type": "Text",
                "value": None  # ID USUARIO CUANDO ESTA RESERVADO
            },
            "id_bike": {
                "type": "Text",
                "value": None  # ID BICICLETA CUANDO ESTA DISPONIBLE Y RESERVADO
            }
        }
        newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
        response = requests.post('http://' + ORION_HOST + ':1026/v2/entities',
                                 data=json.dumps(json_station),
                                 headers=newHeaders)
        print("Status code: ", response.status_code)
        print(response.text)
        if int(response.status_code) >= 400:
            raise Exception(response.text)
        return {"status": 200, "msg": "Station created!"}
    except Exception as e:
        response = {'status': 400, "msg": str(e)}
        return response


def create_bike(id, price, category, id_station):
    try:
        state_station = queries.get_state_station(id_station)
        if state_station != "LIBRE":
            raise Exception("La estacion no esta libre!")

        json_station_update = {
            "state": {"value": "DISPONIBLE"},
            "id_bike": {"value": id},
        }
        newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
        response = requests.post(
            'http://' + ORION_HOST + ':1026/v2/entities/' + id_station + '/attrs',
            data=json.dumps(json_station_update), headers=newHeaders)
        if int(response.status_code) >= 400:
            raise Exception(response.text)

        json_bike = {
            "id": id,
            "type": "Bike",
            "category": {"type": "Text", "value": category},
            "price": {"type": "Text", "value": price},
            "state": {"type": "Text", "value": "DISPONIBLE"},  # DISPONIBLE / RESERVADO / OCUPADO
            "id_user": {
                "type": "Text",
                "value": None  # ID USUARIO CUANDO ESTA RESERVADO Y OCUPADO
            },
            "id_station": {
                "type": "Text",
                "value": None  # ID ESTACION CUANDO ESTA DISPONIBLE Y RESERVADO
            }
        }
        newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
        response = requests.post('http://' + ORION_HOST + ':1026/v2/entities',
                                 data=json.dumps(json_bike),
                                 headers=newHeaders)

        print("Status code: ", response.status_code)
        print(response.text)
        if int(response.status_code) >= 400:
            raise Exception(response.text)

        return {"status": 200, "msg": "Bike created!"}
    except Exception as e:
        response = {'status': 400, "msg": str(e)}
        return response


def create_subscription_QuantumLeap():
    # Create subscription
    json_dict = {
        "description": "Notify QuantumLeap of all context changes",
        "subject": {
            "entities": [{"idPattern": "^urn:ngsi-ld:Station:[1-100]"}, {"idPattern": "^urn:ngsi-ld:Bike:[1-100]"}, {"idPattern": "^urn:ngsi-ld:User:*"}]
        },
        "notification": {
            "http": {
                "url": "http://quantumleap:8668/v2/notify"
            },
            "attrs": [
                "id_station", "state", "name", "id_user", "id_bike", "location"
            ],
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 1
    }
    newHeaders = {'Content-type': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/subscriptions',
                             data=json.dumps(json_dict),
                             headers=newHeaders)
    print("Status code: ", response.status_code)
    return response


if __name__ == '__main__':
    response = create_subscription_QuantumLeap()

    # CREATE SOME USERS
    username = "jesus"
    id_user = "urn:ngsi-ld:User:" + username
    password = "admin"
    tag_rfid = "TAG1"  # Sustituir por tu tag
    response = create_user(id_user, username, password, tag_rfid)

    username = "ismael"
    id_user = "urn:ngsi-ld:User:" + username
    password = "admin"
    tag_rfid = "TAG2"  # Sustituir por tu tag
    response = create_user(id_user, username, password, tag_rfid)

    username = "admin"
    id_user = "urn:ngsi-ld:User:" + username
    password = "admin"
    tag_rfid = "TAG3"  # Sustituir por tu tag
    response = create_user(id_user, username, password, tag_rfid)

    # Create some stations
    id_stations = []
    for i in range(20):
        id = "urn:ngsi-ld:Station:" + str(i)
        id_stations.append(id)
        name = "Estación: " + str(i)
        latitude = random.random() * 50
        longitude = random.random() * 50
        response = create_station(id, name, latitude, longitude)

    # Create some bikes
    for i in range(30):
        id = "urn:ngsi-ld:Bike:" + str(i)
        price = str(random.random() * 3)
        category = random.choice(["electric", "manual"])
        id_station = random.choice(id_stations)
        response = create_bike(id, price, category, id_station)
        print(response)

    print("success!!")
