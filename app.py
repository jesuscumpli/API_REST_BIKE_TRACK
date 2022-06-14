from flask import Flask
import requests
import json
import os

ORION_HOST = os.getenv('ORION_HOST', 'localhost')
app = Flask(__name__)


@app.route('/api/entities/user', methods="POST")
def create_user():
    json_user = {
        "id": "urn:ngsi-ld:User:001",
        "type": "User",
        "username": {"type": "Text", "value": "Username1"},
        "password": {"type": "Text", "value": "Password1"},
        "tag_rfid": {"type": "Text", "value": "TAG1"},
        "state": {"type": "Text", "value": "DESCONOCIDO"},  # DESCONOCIDO / DISPONIBLE / RESERVADO / OCUPADO
        "id_station": {"type": "Text", "value": None},  # ID ESTACION RESERVADA
        "id_bike": {"type": "Text", "value": None},  # ID BIKE RESERVADA / OCUPADA
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities',
                             data=json.dumps(json_user),
                             headers=newHeaders)
    print("Status code: ", response.status_code)
    print(response.text)
    return 'Hello World!'


@app.route('/api/entities/station', methods="POST")
def create_station():
    json_station = {
        "id": "urn:ngsi-ld:Station:001",
        "type": "Station",
        "state": {"type": "Text", "value": "DESCONOCIDO"},  # DESCONOCIDO / DISPONIBLE / RESERVADO / LIBRE
        "location": {
            "type": "geo:json",
            "value": {
                "type": "Point",
                "coordinates": [13.3986, 52.5547]
            }
        },
        "name": {
            "type": "Text",
            "value": "Estacion 1"
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
    return 'Hello World!'


@app.route('/api/entities/bike', methods="POST")
def create_bike():
    json_bike = {
        "id": "urn:ngsi-ld:Bike:001",
        "type": "Bike",
        "category": {"type": "Text", "value": "electric"},
        "price": {"type": "Text", "value": "1.5 euros per hour"},
        "state": {"type": "Text", "value": "DESCONOCIDO"},  # DESCONOCIDO / DISPONIBLE / RESERVADO / OCUPADO
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
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
