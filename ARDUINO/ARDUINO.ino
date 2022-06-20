#include <SoftwareSerial.h>
#include <String.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

//BLUETOOTH PINS
#define PIN_TX_BT D4
#define PIN_RX_BT D3
//RFID PINS
#define PIN_RST D0
#define PIN_SDA  D8
// https://www.aranacorp.com/es/uso-de-un-modulo-rfid-con-un-esp8266/
// SCK => D5
// MISO => D6
// MOSI => D7

#define PIN_LED D2
#define PIN_BUZZER D1


// CONSTANTES DE LA ESTACION
#define ID_STATION "urn:ngsi-ld:Station:MyStationJesus"
#define NAME_STATION "MyStationJesus"
#define LATITUDE 36.721182
#define LONGITUDE -4.474272
// VARIABLES DE LA ESTACION
String state = "LIBRE";
String id_bike = "None";
String id_user = "None";
int lastUpdate = 0;
int timeUpdate = 1000*5;


// Bluetooth variables
SoftwareSerial BT1(PIN_TX_BT, PIN_RX_BT); // TX, RX
String command;
String bleUsername;
String blePassword;
String bleIdUser;
String bleIdBikeUser;
String bleIdStationUser;
String bleStateUser;
String bleAutenticationState = "DISCONNECTED";


// Led and Buzzer variables
int ledState = LOW; //led starts off
bool buzzerActive = false;
int maxTimeBuzzer = 1000*2;
int buzzerState = LOW;
int buzzerActiveInterval = 700; 
int buzzerInactiveInterval = 500;
int buzzerTime = 0;
int buzzerStartTime = 0;

// RFID variables
byte nuidMyCard[4] = {0xC5, 0xD2, 0xDC, 0x73};
int lastLectureCard = 0;
int maxTimeLecture = 1000*5; // 5 seconds
MFRC522 rfid(PIN_SDA, PIN_RST); // Instance of the class
MFRC522::MIFARE_Key key;
byte nuidPICC[4];

//WIFI variables
const char* ssid = "DIGIPONCHO";
const char* password = "3BEtD7btmVQHDmgc";
//API REQUESTS
String serverName = "http://192.168.1.139:5000";

void setup() {
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_LED, ledState);
  
  Serial.begin(9600);

  //BLUETOOTH
  BT1.begin(9600);
  //BT1.print("AT+NAMEJesusIsmaelBLEDevice\n");
  //BT1.print("AT+PIN1234\n");

  //RFID
  SPI.begin(); // Init SPI bus
  rfid.PCD_Init(); // Init MFRC522
  Serial.print(F("Reader :"));
   rfid.PCD_DumpVersionToSerial();
   for (byte i = 0; i < 6; i++) {
     key.keyByte[i] = 0xFF;
   }

   //WIFI
   Serial.printf("\nConnecting to %s:\n", ssid);
   WiFi.mode(WIFI_STA);
   WiFi.begin(ssid, password);
   while (WiFi.status() != WL_CONNECTED) {
    delay(200);
    Serial.print(".");
   }
   Serial.printf("\nWiFi connected, IP address: %s\n", WiFi.localIP().toString().c_str());

   POST_create_entity_station();

   
}

void loop() {
  unsigned long now = millis();
  if(now > lastUpdate + timeUpdate){
    lastUpdate = now;
    GET_info_station();
  }
  sound_buzzer(now);
  listen_card_RFID(now);
  listen_commands_bluetooth(now);
}


void sound_buzzer(int now){
  if (buzzerActive) {
    if(now - buzzerStartTime >= maxTimeBuzzer){
      Serial.write("Buzzer deactivated!");
      buzzerActive = false;
      digitalWrite(PIN_BUZZER, LOW);
      digitalWrite(PIN_LED, LOW);
    }else{
      if(buzzerState == LOW){
        if(now - buzzerTime >= buzzerInactiveInterval){
          buzzerTime = now;
          buzzerState = HIGH;
        }
      }else if(buzzerState == HIGH){
        if(now - buzzerTime >= buzzerActiveInterval){
          buzzerTime = now;
          buzzerState = LOW;
        }
      }
      digitalWrite(PIN_BUZZER, buzzerState);
    }
  }
}

void listen_card_RFID(int now){
 // Reset the loop if no new card present on the sensor/reader. This saves the entire process when idle.
 if ( ! rfid.PICC_IsNewCardPresent())
   return;
   
 // Verify if the NUID has been readed
 if ( ! rfid.PICC_ReadCardSerial())
   return;
   
 Serial.print(F("PICC type: "));
 MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
 Serial.println(rfid.PICC_GetTypeName(piccType));
 
 // Check is the PICC of Classic MIFARE type
 if (piccType != MFRC522::PICC_TYPE_MIFARE_MINI &&
     piccType != MFRC522::PICC_TYPE_MIFARE_1K &&
     piccType != MFRC522::PICC_TYPE_MIFARE_4K) {
   Serial.println(F("Your tag is not of type MIFARE Classic."));
   return;
 }
 
 if (now - lastLectureCard > maxTimeLecture) {
   Serial.println(F("A new card has been detected."));
   // Store NUID into nuidPICC array
   for (byte i = 0; i < 4; i++) {
     nuidPICC[i] = rfid.uid.uidByte[i];
   }
   
   Serial.println(F("The NUID tag is:"));
   Serial.print(F("In hex: "));
   printHex(rfid.uid.uidByte, rfid.uid.size);
   Serial.println();
   Serial.print(F("In dec: "));
   printDec(rfid.uid.uidByte, rfid.uid.size);
   Serial.println();

   if (rfid.uid.uidByte[0] == nuidMyCard[0] &&
     rfid.uid.uidByte[1] == nuidMyCard[1] &&
     rfid.uid.uidByte[2] == nuidMyCard[2] &&
     rfid.uid.uidByte[3] == nuidMyCard[3] ) {
       Serial.write("COMMNAD: ACTIVATE!\n");
       buzzerActive = true;
       buzzerTime = now;
       buzzerStartTime = now;
       ledState = HIGH;
       digitalWrite(PIN_LED, HIGH);
     }
   lastLectureCard = now;
 }
 else Serial.println(F("Too early to read another card!"));
 
 // Halt PICC
 rfid.PICC_HaltA();
 // Stop encryption on PCD
 rfid.PCD_StopCrypto1();
  
}


void listen_commands_bluetooth(int now){
  //Read commands from BT1
  
  if (BT1.available() > 0){
    if(bleAutenticationState.equals("DISCONNECTED")){
      BT1.print("INTRODUCE TU USERNAME: ");
      bleAutenticationState = "WAIT_USERNAME";
      BT1.flush();
      return;
    }
    
    command = BT1.readString();
    command.trim();
    Serial.write("Received command: ");
    Serial.write(command.c_str());
    Serial.write("\n");

    if(bleAutenticationState.equals("WAIT_USERNAME")){
      bleUsername = command;
      BT1.print("INTRODUCE LA PASSWORD: ");
      bleAutenticationState = "WAIT_PASSWORD";
      BT1.flush();
      return;
    }

    if(bleAutenticationState.equals("WAIT_PASSWORD")){
      blePassword = command;
      BT1.print("Comprobando las credenciales\n");
      bleAutenticationState = "WAIT_AUTENTICATION";
      POST_autentication_User_BLE();
      BT1.flush();
      return;
    }

    if(bleAutenticationState.equals("AUTENTICATED")){
      if(command == "LED"){
        Serial.write("COMMNAD: ACTIVATE LED!\n");
        ledState = HIGH;
        digitalWrite(PIN_LED, ledState);
  
      }else if(command == "BUZZER"){
         Serial.write("COMMNAD: ACTIVATE BUZZER!\n");
         buzzerActive = true;
         buzzerTime = now;
         buzzerStartTime = now;

      }else if(command == "DESBLOQUEAR"){
        POST_unlock_BLE();
        
      }else if(command == "BLOQUEAR"){
        POST_lock_BLE();

      }else if(command == "RESERVAR"){
        POST_book_BLE();
        
      }else if(command == "INFO"){
        GET_info_station();
        GET_info_user_BLE();
        
        BT1.print("********** ESTACIÓN *******\n");
        BT1.print("* ID: ");
        BT1.print(ID_STATION);
        BT1.print("\n");
        BT1.print("* Name: ");
        BT1.print(NAME_STATION);
        BT1.print("\n");
        BT1.print("* Longitude: ");
        BT1.print(LONGITUDE);
        BT1.print(", Latitude: ");
        BT1.print(LATITUDE);
        BT1.print("\n");
        BT1.print("*** Estado: ");
        BT1.print(state);
        BT1.print("\n");
        BT1.print("*** Id Bicicleta: ");
        BT1.print(id_bike);
        BT1.print("\n");
        BT1.print("*** Id Usuario: ");
        BT1.print(id_user);
        BT1.print("\n");
        BT1.print("********** USUARIO *******\n");
        BT1.print("* Id Usuario: ");
        BT1.print(bleIdUser);
        BT1.print("\n");
        BT1.print("* Username: ");
        BT1.print(bleUsername);
        BT1.print("\n");
        BT1.print("*** Estado: ");
        BT1.print(bleStateUser);
        BT1.print("\n");
        BT1.print("*** Id Estacion: ");
        BT1.print(bleIdStationUser);
        BT1.print("\n");
        BT1.print("*** Id Bicicleta: ");
        BT1.print(bleIdBikeUser);
        BT1.print("\n");
        
      }else{
        BT1.print("Bad Command: ");
        BT1.print(command.c_str());
        BT1.print("\n");
      }
      BT1.flush();
    }
  }
}

void POST_create_entity_station(){
  //Check WiFi connection status
    if(WiFi.status()== WL_CONNECTED){
      WiFiClient client;
      HTTPClient http;
      http.begin(client, serverName + "/api/entities/station");
      http.addHeader("Content-Type", "application/json");
      
      // Data to send with HTTP POST
      StaticJsonDocument<400> data;
      data["id"] = ID_STATION;
      data["name"] = NAME_STATION;
      data["latitude"] = LATITUDE;
      data["longitude"] = LONGITUDE;
      String requestBody;
      serializeJson(data, requestBody);
      
      int httpResponseCode = http.POST(requestBody);
      String payload = http.getString();
      StaticJsonDocument<200> response;
      deserializeJson(response, payload);
      String status_response = response["status"];
      String msg_response = response["msg"];
      Serial.print("HTTP Response code: ");
      Serial.println(status_response);
      Serial.println(msg_response);
        
      // Free resources
      http.end();
    }
    else {
      Serial.println("WiFi Disconnected");
    }
}

void POST_autentication_User_BLE(){
  //Check WiFi connection status
    if(WiFi.status()== WL_CONNECTED){
      WiFiClient client;
      HTTPClient http;
      http.begin(client, serverName + "/api/autenticate");
      http.addHeader("Content-Type", "application/json");
      
      // Data to send with HTTP POST
      StaticJsonDocument<400> data;
      data["username"] = bleUsername;
      data["password"] = blePassword;
      String requestBody;
      serializeJson(data, requestBody);
      
      int httpResponseCode = http.POST(requestBody);
      String payload = http.getString();
      StaticJsonDocument<1000> response;
      deserializeJson(response, payload);
      String status_response = response["status"];
      if(status_response.equals("200")){
        BT1.print("USUARIO AUTENTICADO!\n");
        BT1.print("Puedes usar los siguientes comandos:!\n");
        BT1.print("INFO - (Obtener información del estado de la estación y del usuario)\n");
        BT1.print("RESERVAR - (Reservar la bicicleta, en caso de que el estado de la estación y el usuario sea DISPONIBLE. También se puede realizar via WEB)\n");
        BT1.print("DESBLOQUEAR - (Desbloquear la bicicleta, en caso de que el usuario haya RESERVADO dicha estación previamente)\n");
        BT1.print("BLOQUEAR - (Bloquear una bicicleta, en caso de que la estación esté LIBRE y el usuario OCUPADO)\n");
        bleIdUser = (const char*) response["data"]["id"];
        bleStateUser = (const char*) response["data"]["state"]["value"];
        bleIdBikeUser = (const char*) response["data"]["id_bike"]["value"];
        bleIdStationUser = (const char*) response["data"]["id_station"]["value"];
        bleAutenticationState = "AUTENTICATED";
      }else{
        BT1.print("CREDENCIALES INCORRECTAS!\n");
        BT1.print("INTRODUCE TU USERNAME: ");
        bleAutenticationState = "WAIT_USERNAME";
      }
        
      // Free resources
      http.end();
    }
    else {
      Serial.println("WiFi Disconnected");
    }
}

void POST_book_BLE(){
  //Check WiFi connection status
    if(WiFi.status()== WL_CONNECTED){
      WiFiClient client;
      HTTPClient http;
      http.begin(client, serverName + "/user_book_station");
      http.addHeader("Content-Type", "application/json");
      
      // Data to send with HTTP POST
      StaticJsonDocument<400> data;
      data["id_user"] = bleIdUser;
      data["id_station"] = ID_STATION;
      String requestBody;
      serializeJson(data, requestBody);
      
      int httpResponseCode = http.POST(requestBody);
      String payload = http.getString();
      StaticJsonDocument<1000> response;
      deserializeJson(response, payload);
      String status_response = response["status"];
      String msg = response["msg"];
      if(status_response.equals("200")){
        BT1.print("SE HA RESERVADO LA ESTACIÓN CON ÉXITO!\n");
        //GET_info_user_BLE();
        //GET_info_station();
        activate_Led_Buzzer();
      }else{
        BT1.print("ERROR: No se ha podido reservar correctamente la bicicleta.");
        BT1.print(msg);
        BT1.print("\n");
      }
      // Free resources
      http.end();
    }
    else {
      Serial.println("WiFi Disconnected");
    }
}

void POST_lock_BLE(){
  //Check WiFi connection status
    if(WiFi.status()== WL_CONNECTED){
      WiFiClient client;
      HTTPClient http;
      http.begin(client, serverName + "/user_lock_station");
      http.addHeader("Content-Type", "application/json");
      
      // Data to send with HTTP POST
      StaticJsonDocument<400> data;
      data["id_user"] = bleIdUser;
      data["id_station"] = ID_STATION;
      String requestBody;
      serializeJson(data, requestBody);
      
      int httpResponseCode = http.POST(requestBody);
      String payload = http.getString();
      StaticJsonDocument<1000> response;
      deserializeJson(response, payload);
      String status_response = response["status"];
      String msg = response["msg"];
      if(status_response.equals("200")){
        BT1.print("SE HA BLOQUEADO LA BICICLETA CON ÉXITO!\n");
        //GET_info_user_BLE();
        //GET_info_station();
        activate_Led_Buzzer();
      }else{
        BT1.print("ERROR: No se ha podido bloquear correctamente la bicicleta.");
        BT1.print(msg);
        BT1.print("\n");
      }
      // Free resources
      http.end();
    }
    else {
      Serial.println("WiFi Disconnected");
    }
}

void POST_unlock_BLE(){
  //Check WiFi connection status
    if(WiFi.status()== WL_CONNECTED){
      WiFiClient client;
      HTTPClient http;
      http.begin(client, serverName + "/user_unlock_station");
      http.addHeader("Content-Type", "application/json");
      
      // Data to send with HTTP POST
      StaticJsonDocument<400> data;
      data["id_user"] = bleIdUser;
      data["id_station"] = ID_STATION;
      String requestBody;
      serializeJson(data, requestBody);
      
      int httpResponseCode = http.POST(requestBody);
      String payload = http.getString();
      StaticJsonDocument<1000> response;
      deserializeJson(response, payload);
      String status_response = response["status"];
      String msg = response["msg"];
      if(status_response.equals("200")){
        BT1.print("SE HA DESBLOQUEADO LA BICICLETA CON ÉXITO!\n");
        //GET_info_user_BLE();
        //GET_info_station();
        activate_Led_Buzzer();
      }else{
        BT1.print("ERROR: No se ha podido desbloquear correctamente la bicicleta.");
        BT1.print(msg);
        BT1.print("\n");
      }
      // Free resources
      http.end();
    }
    else {
      Serial.println("WiFi Disconnected");
    }
}

void GET_info_station(){
  //Check WiFi connection status
    if(WiFi.status()== WL_CONNECTED){
      WiFiClient client;
      HTTPClient http;

      Serial.println("GET INFO STATION");
      http.begin(client, serverName + "/api/entities/station/info/" + ID_STATION);
      int httpResponseCode = http.GET();
      
      String payload = http.getString();
      StaticJsonDocument<1000> response;
      deserializeJson(response, payload);
      String status_response = response["status"];
      if(status_response.equals("200")){
        
        state = (const char*) response["data"]["state"]["value"];
        id_user = (const char*) response["data"]["id_user"]["value"];
        id_bike = (const char*) response["data"]["id_bike"]["value"];
      }else{
        String msg_response = response["data"];
        Serial.print("HTTP Response code: ");
        Serial.println(status_response);
        Serial.println(msg_response);
      }
        
      // Free resources
      http.end();
    }
    else {
      Serial.println("WiFi Disconnected");
    }
}


void GET_info_user_BLE(){
  //Check WiFi connection status
    if(WiFi.status()== WL_CONNECTED){
      WiFiClient client;
      HTTPClient http;

      Serial.println("GET INFO User");
      http.begin(client, serverName + "/api/entities/user/info/" + bleUsername);
      int httpResponseCode = http.GET();
      
      String payload = http.getString();
      StaticJsonDocument<1000> response;
      deserializeJson(response, payload);
      String status_response = response["status"];
      if(status_response.equals("200")){
        bleIdUser = (const char*) response["data"]["id"];
        bleStateUser = (const char*) response["data"]["state"]["value"];
        bleIdBikeUser = (const char*) response["data"]["id_bike"]["value"];
        bleIdStationUser = (const char*) response["data"]["id_station"]["value"];
      }else{
        String msg_response = response["data"];
        Serial.print("HTTP Response code: ");
        Serial.println(status_response);
        Serial.println(msg_response);
      }
        
      // Free resources
      http.end();
    }
    else {
      Serial.println("WiFi Disconnected");
    }
}

void activate_Led_Buzzer(){
    digitalWrite(PIN_LED, HIGH);
     buzzerActive = true;
     buzzerTime = millis();
     buzzerStartTime = millis();
}

/**
   Helper routine to dump a byte array as hex values to Serial.
*/
void printHex(byte *buffer, byte bufferSize) {
 for (byte i = 0; i < bufferSize; i++) {
   Serial.print(buffer[i] < 0x10 ? " 0" : " ");
   Serial.print(buffer[i], HEX);
 }
}

/**
   Helper routine to dump a byte array as dec values to Serial.
*/
void printDec(byte *buffer, byte bufferSize) {
 for (byte i = 0; i < bufferSize; i++) {
   Serial.print(buffer[i] < 0x10 ? " 0" : " ");
   Serial.print(buffer[i], DEC);
 }
}
