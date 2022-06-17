import hashlib

from flask import Flask, request, jsonify, redirect, session, flash, render_template
import requests
import json
import os
import queries

ORION_HOST = os.getenv('ORION_HOST', 'localhost')
app = Flask(__name__)
app.secret_key = '6ee9a71761572d9f91dc2067da170889'


# VIEWS

def is_logged():
    username = session.get("username")
    if username is None:
        return False
    return True

@app.route('/')
def index():
    if not is_logged():
        return redirect("/login")
    return redirect("/home")

@app.route('/logout', methods=["GET"])
def logout():
    session["username"] = None
    return redirect("/login")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form = request.form
        username = form.get("username")
        password = form.get("password")
        # Check data
        if username is None:
            flash("Nombre de usuario no definido")
        elif password is None:
            flash("Contraseña no definida")
        elif not queries.user_exists(username):
            flash("Usuario no existe")
        else:
            password_hashed = hashlib.sha256(password.encode()).hexdigest()
            real_password = queries.get_password_user(username)
            if password_hashed == real_password:
                # Starts session
                session["username"] = username
                return redirect("/home")
            else:
                flash("Los datos introducidos son incorrectos.")
    return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        form = request.form
        username = form.get("username")
        password1 = form.get("password1")
        password2 = form.get("password2")
        tag_rfid = form.get("tag_rfid")

        # Check data
        if username is None:
            flash("Nombre de usuario no definido")
        elif password1 is None or password2 is None:
            flash("Contraseña no definida")
        elif password1 != password2:
            flash("Las contraseñas no coinciden")
        elif tag_rfid is None:
            flash("TAG RFID no definido")
        elif queries.user_exists(username):
            flash("Usuario ya existe")
        else:
            # Create user
            password_hashed = hashlib.sha256(password1.encode()).hexdigest()
            json_user = {
                "id": "urn:ngsi-ld:User:" + username,
                "type": "User",
                "username": {"type": "Text", "value": username},
                "password": {"type": "Text", "value": password_hashed},
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

            # Register Success
            session["username"] = username
            return redirect("/home")
    return render_template("register.html")

@app.route('/home', methods=["GET"])
def home():
    if not is_logged():
        return redirect("/login")
    data_user = queries.get_info_user(session["username"])
    station_user = None
    if "id_station" in data_user and data_user["id_station"]:
        station_user = queries.get_info_station(data_user["id_station"])
    station_entities = queries.get_all_stations()
    bikes_entities = queries.get_all_bikes()
    return render_template("home.html", user_data=data_user, station_user=station_user, station_entities=station_entities, bikes_entities=bikes_entities)

@app.route('/stations', methods=["GET"])
def stations():
    if not is_logged():
        return redirect("/login")
    data_user = queries.get_info_user(session["username"])
    station_user = None
    if "id_station" in data_user and data_user["id_station"]["value"]:
        station_user = queries.get_info_station(data_user["id_station"]["value"])
    station_entities = queries.get_all_stations()
    bikes_entities = queries.get_all_bikes()
    return render_template("stations.html", user_data=data_user, station_user=station_user, station_entities=station_entities, bikes_entities=bikes_entities)


# API REQUESTS

@app.route('/api/entities/user', methods=["POST"])
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

        response = {"status": 200, "msg": "User created"}
        return jsonify(response)
    except Exception as e:
        response = {'status': 400, "msg": str(e)}
        return jsonify(response)


@app.route('/api/entities/station', methods=["POST"])
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

        return jsonify({"status": 200, "msg": "Station created!"})
    except Exception as e:
        response = {'status': 400, "msg": str(e)}
        return jsonify(response)


@app.route('/api/entities/bike', methods=["POST"])
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
        response = requests.post(
            'http://' + ORION_HOST + ':1026/v2/entities/' + id_station + '/attrs',
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

        return jsonify({"status": 200, "msg": "Bike created!"})
    except Exception as e:
        response = {'status': 400, "msg": str(e)}
        return jsonify(response)


@app.route('/user_lock_station', methods=["POST"])
def user_lock_station():
    try:
        data = request.get_json()
        id_user = data["id_user"]
        id_station = data["id_station"]

        # Check user is OCUPADO
        state_user = queries.get_state_user_by_id(id_user)
        if state_user != "OCUPADO":
            raise Exception("Usuario no esta Ocupado!")
        # Check station is LIBRE
        state_station = queries.get_state_station(id_station)
        if state_station != "LIBRE":
            raise Exception("La estacion no esta Libre!")

        # Get id_bike
        id_bike = queries.get_bike_from_user_by_id(id_user)

        response = lock_user(id_user)
        if int(response.status_code) >= 400:
            raise Exception(response.text)
        response = lock_station(id_station, id_bike)
        if int(response.status_code) >= 400:
            raise Exception(response.text)
        response = lock_bike(id_bike, id_station)
        if int(response.status_code) >= 400:
            raise Exception(response.text)

        return jsonify({"status": "200", "msg": "Bloqueado con éxito!"})
    except Exception as e:
        response = {'status': 400, "msg": str(e)}
        return jsonify(response)


@app.route('/user_book_station', methods=["POST"])
def user_book_station():
    try:
        data = request.get_json()
        id_user = data["id_user"]
        id_station = data["id_station"]

        # Check user is DISPONIBLE
        state_user = queries.get_state_user_by_id(id_user)
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

        return jsonify({"status": "200", "msg": "Reservado con éxito!"})
    except Exception as e:
        response = {'status': 400, "msg": str(e)}
        return jsonify(response)


@app.route('/user_unlock_station', methods=["POST"])
def user_unlock_station():
    try:
        data = request.get_json()
        id_user = data["id_user"]
        id_station = data["id_station"]

        # Check user is RESERVADO
        state_user = queries.get_state_user_by_id(id_user)
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

        return jsonify({"status": "200", "msg": "Desbloqueado con éxito!"})
    except Exception as e:
        response = {'status': 400, "msg": str(e)}
        return jsonify(response)


# METODOS PRIVADOS
##########################################################################


def lock_station(id_station, id_bike):
    json_station_update = {
        "state": {"value": "DISPONIBLE"},
        "id_bike": {"value": id_bike},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/' + id_station + '/attrs',
                             data=json.dumps(json_station_update), headers=newHeaders)
    return response


def lock_bike(id_bike, id_station):
    json_bike_update = {
        "state": {"value": "DISPONIBLE"},
        "id_station": {"value": id_station},
        "id_user": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/' + id_bike + '/attrs',
                             data=json.dumps(json_bike_update), headers=newHeaders)
    return response


def lock_user(id_user):
    json_user_update = {
        "state": {"value": "DISPONIBLE"},
        "id_bike": {"value": None},
        "id_station": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/' + id_user + '/attrs',
                             data=json.dumps(json_user_update), headers=newHeaders)
    return response


def book_station(id_station, id_user):
    json_station_update = {
        "state": {"value": "RESERVADO"},
        "id_user": {"value": id_user},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/' + id_station + '/attrs',
                             data=json.dumps(json_station_update), headers=newHeaders)
    return response


def book_bike(id_bike, id_user):
    json_bike_update = {
        "state": {"value": "RESERVADO"},
        "id_user": {"value": id_user},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/' + id_bike + '/attrs',
                             data=json.dumps(json_bike_update), headers=newHeaders)
    return response


def book_user(id_user, id_station, id_bike):
    json_user_update = {
        "state": {"value": "RESERVADO"},
        "id_station": {"value": id_station},
        "id_bike": {"value": id_bike},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/' + id_user + '/attrs',
                             data=json.dumps(json_user_update), headers=newHeaders)
    return response


def unlock_station(id_station):
    json_station_update = {
        "state": {"value": "LIBRE"},
        "id_bike": {"value": None},
        "id_user": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/' + id_station + '/attrs',
                             data=json.dumps(json_station_update), headers=newHeaders)
    return response


def unlock_bike(id_bike):
    json_bike_update = {
        "state": {"value": "OCUPADO"},
        "id_station": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/' + id_bike + '/attrs',
                             data=json.dumps(json_bike_update), headers=newHeaders)
    return response


def unlock_user(id_user):
    json_user_update = {
        "state": {"value": "OCUPADO"},
        "id_station": {"value": None},
    }
    newHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post('http://' + ORION_HOST + ':1026/v2/entities/' + id_user + '/attrs',
                             data=json.dumps(json_user_update), headers=newHeaders)
    return response


if __name__ == '__main__':
    app.run()
