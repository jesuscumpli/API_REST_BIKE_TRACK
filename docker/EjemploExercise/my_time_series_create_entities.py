import requests
import json
import os

ORION_HOST = os.getenv('ORION_HOST', 'localhost')

# Create entity
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

newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json', 'fiware-service': 'openiot',
              'fiware-servicepath': '/'}
response = requests.post('http://' + ORION_HOST + ':1026/v2/entities',
                         data=json.dumps(json_station),
                         headers=newHeaders)
print("Status code: ", response.status_code)

# Create entity
json_station = {
    "id": "urn:ngsi-ld:Station:002",
    "type": "Station",
    "state": {"type": "Text", "value": "DESCONOCIDO"},  # DESCONOCIDO / DISPONIBLE / RESERVADO / LIBRE
    "location": {
        "type": "geo:json",
        "value": {
            "type": "Point",
            "coordinates": [13.3916, 52.5237]
        }
    },
    "name": {
        "type": "Text",
        "value": "Estacion 2"
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
newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json', 'fiware-service': 'openiot',
              'fiware-servicepath': '/'}
response = requests.post('http://' + ORION_HOST + ':1026/v2/entities',
                         data=json.dumps(json_station),
                         headers=newHeaders)
print("Status code: ", response.status_code)


# Create subscription
json_dict = {
    "description": "Notify QuantumLeap of all context changes",
    "subject": {
        "entities": [{"idPattern": "^urn:ngsi-ld:Station:00[1-50]"}]
    },
    "notification": {
        "http": {
            "url": "http://quantumleap:8668/v2/notify"
        },
        "attrs": [
            "state", "name", "id_user", "id_bike", "location"
        ],
        "metadata": ["dateCreated", "dateModified"]
    },
    "throttling": 1
}

newHeaders = {'Content-type': 'application/json', 'fiware-service': 'openiot', 'fiware-servicepath': '/'}
response = requests.post('http://' + ORION_HOST + ':1026/v2/subscriptions',
                         data=json.dumps(json_dict),
                         headers=newHeaders)
print("Status code: ", response.status_code)
