import hashlib

from flask import Flask, request
import requests
import json
import os
import queries

ORION_HOST = os.getenv('ORION_HOST', 'localhost')
app = Flask(__name__)


@app.route('/api/entities/user', methods="POST")
def create_user():
    data = request.get_json()
    try:
        username = data["username"]
        password = data["username"]
        tag_rfid = data["tag_rfid"]
        hash_pass = hashlib.sha256(password.encode()).hexdigest()
        json_user = {
            "id": "urn:ngsi-ld:User:" + username,
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

        return {"status": 200, "msg": "User created"}
    except Exception as e:
        return {'status': 400, "msg": str(e)}


@app.route('/api/entities/station', methods="POST")
def create_station():
    data = request.get_json()
    try:
        id = data["id"]
        name = data["name"]
        latitude = data["latitude"]
        longitude = data["longitude"]
        json_station = {
            "id": "urn:ngsi-ld:Station:" + id,
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
        return {"status": 400, "msg": str(e)}


@app.route('/api/entities/bike', methods="POST")
def create_bike():
    data = request.get_json()
    try:
        id = data["id"]
        price = data["price"]
        category = data["category"]
        id_station = data["id_station"]

        state_station = queries.get_state_station(id_station)
        if state_station != "LIBRE":
            raise Exception("La estacion no esta libre!")

        json_station_update = {
            "state": {"value": "DISPONIBLE"},
            "id_bike": {"value": id},
        }
        newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
        response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:Station:'+id_station+'/attrs',
                                 data=json.dumps(json_station_update), headers=newHeaders)
        if int(response.status_code) >= 400:
            raise Exception(response.text)

        json_bike = {
            "id": "urn:ngsi-ld:Bike:" + id,
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
        return {"status": 400, "msg": str(e)}


@app.route('/user_lock_station', methods="POST")
def user_lock_station():
    try:
        data = request.get_json()
        id_user = data["id_user"]
        id_station = data["id_station"]

        # Check user is OCUPADO
        state_user = queries.get_state_user(id_user)
        if state_user != "OCUPADO":
            raise Exception("Usuario no esta Ocupado!")
        # Check station is LIBRE
        state_station = queries.get_state_station(id_station)
        if state_station != "LIBRE":
            raise Exception("La estacion no esta Libre!")

        # Get id_bike
        id_bike = queries.get_bike_from_user(id_user)

        response = lock_user(id_user)
        if int(response.status_code) >= 400:
            raise Exception(response.text)
        response = lock_station(id_station, id_bike)
        if int(response.status_code) >= 400:
            raise Exception(response.text)
        response = lock_bike(id_bike, id_station)
        if int(response.status_code) >= 400:
            raise Exception(response.text)

        return {"status": "200", "msg": "Bloqueado con éxito!"}
    except Exception as e:
        return {"status": "400", "msg": str(e)}

@app.route('/user_book_station', methods="POST")
def user_book_station():
    try:
        data = request.get_json()
        id_user = data["id_user"]
        id_station = data["id_station"]

        # Check user is DISPONIBLE
        state_user = queries.get_state_user(id_user)
        if state_user != "DISPONIBLE":
            raise Exception("Usuario no esta Disponible!")
        # Check station is DISPONIBLE
        state_station = queries.get_state_station(id_station)
        if state_station != "DISPONIBLE":
            raise Exception("La estacion no esta Disponible!")

        # Get id_bike
        id_bike = queries.get_bike_from_station(id_station)

        response = book_user(id_user, id_station, id_bike)
        if int(response.status_code) >= 400:
            raise Exception(response.text)
        response = book_station(id_station, id_user)
        if int(response.status_code) >= 400:
            raise Exception(response.text)
        response = book_bike(id_bike, id_user)
        if int(response.status_code) >= 400:
            raise Exception(response.text)

        return {"status": "200", "msg": "Reservado con éxito!"}
    except Exception as e:
        return {"status": "400", "msg": str(e)}

@app.route('/user_unlock_station', methods="POST")
def user_unlock_station():
    try:
        data = request.get_json()
        id_user = data["id_user"]
        id_station = data["id_station"]

        # Check user is RESERVADO
        state_user = queries.get_state_user(id_user)
        if state_user != "RESERVADO":
            raise Exception("Usuario no esta Reservado!")
        # Check station is RESERVADO
        state_station = queries.get_state_station(id_station)
        if state_station != "RESERVADO":
            raise Exception("La estacion no esta Reservada!")

        # Get id_bike
        id_bike = queries.get_bike_from_station(id_station)

        response = unlock_user(id_user)
        if int(response.status_code) >= 400:
            raise Exception(response.text)
        response = unlock_station(id_station)
        if int(response.status_code) >= 400:
            raise Exception(response.text)
        response = unlock_bike(id_bike)
        if int(response.status_code) >= 400:
            raise Exception(response.text)

        return {"status": "200", "msg": "Desbloqueado con éxito!"}
    except Exception as e:
        return {"status": "400", "msg": str(e)}






# METODOS PRIVADOS
##########################################################################


def lock_station(id_station, id_bike):
    json_station_update = {
        "state": {"value": "DISPONIBLE"},
        "id_bike": {"value": id_bike},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:Station:' + id_station + '/attrs',
                             data=json.dumps(json_station_update), headers=newHeaders)
    return response

def lock_bike(id_bike, id_station):
    json_bike_update = {
        "state": {"value": "DISPONIBLE"},
        "id_station": {"value": id_station},
        "id_user": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:Bike:' + id_bike + '/attrs',
                             data=json.dumps(json_bike_update), headers=newHeaders)
    return response

def lock_user(id_user):
    json_user_update = {
        "state": {"value": "DISPONIBLE"},
        "id_bike": {"value": None},
        "id_station": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:User:' + id_user + '/attrs',
                             data=json.dumps(json_user_update), headers=newHeaders)
    return response


def book_station(id_station, id_user):
    json_station_update = {
        "state": {"value": "RESERVADO"},
        "id_user": {"value": id_user},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:Station:' + id_station + '/attrs',
                             data=json.dumps(json_station_update), headers=newHeaders)
    return response

def book_bike(id_bike, id_user):
    json_bike_update = {
        "state": {"value": "RESERVADO"},
        "id_user": {"value": id_user},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:Bike:' + id_bike + '/attrs',
                             data=json.dumps(json_bike_update), headers=newHeaders)
    return response

def book_user(id_user, id_station, id_bike):
    json_user_update = {
        "state": {"value": "RESERVADO"},
        "id_station": {"value": id_station},
        "id_bike": {"value": id_bike},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:User:' + id_user + '/attrs',
                             data=json.dumps(json_user_update), headers=newHeaders)
    return response

def unlock_station(id_station):
    json_station_update = {
        "state": {"value": "LIBRE"},
        "id_bike": {"value": None},
        "id_user": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:Station:' + id_station + '/attrs',
                             data=json.dumps(json_station_update), headers=newHeaders)
    return response

def unlock_bike(id_bike):
    json_bike_update = {
        "state": {"value": "OCUPADO"},
        "id_station": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:Bike:' + id_bike + '/attrs',
                             data=json.dumps(json_bike_update), headers=newHeaders)
    return response

def unlock_user(id_user):
    json_user_update = {
        "state": {"value": "OCUPADO"},
        "id_station": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/urn:ngsi-ld:User:' + id_user + '/attrs',
                             data=json.dumps(json_user_update), headers=newHeaders)
    return response


if __name__ == '__main__':
    app.run()
