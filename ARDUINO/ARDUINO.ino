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
#define ID_STATION "urn:ngsi-ld:Station:MyStationJesus2"
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

// Led and Buzzer variables
int ledState = LOW; //led starts off
bool buzzerActive = false;
int maxTimeBuzzer = 1000*10;
int buzzerState = LOW;
int buzzerActiveInterval = 750; 
int buzzerInactiveInterval = 1000;
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
const char* ssid = "FTE-9480";
const char* password = "REYES2020";
//API REQUESTS
String serverName = "http://192.168.1.138:5000";

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
  GET_info_station(now);
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
    command = BT1.readString();
    command.trim();
    Serial.write("Received command: ");
    Serial.write(command.c_str());
    Serial.write("\n");
   
    if(command == "LED"){
      Serial.write("COMMNAD: ACTIVATE LED!\n");
      ledState = !ledState;
      digitalWrite(PIN_LED, ledState);

    }else if(command == "BUZZER"){
       Serial.write("COMMNAD: ACTIVATE BUZZER!\n");
       buzzerActive = true;
       buzzerTime = now;
       buzzerStartTime = now;

    }else if(command == "INFO"){
      Serial.write("COMMNAD: STATE OF THE HOUSE!\n");
      BT1.print("LED: ");
      BT1.print(ledState);
      BT1.print("\n");
      BT1.print("BUZZER: ");
      BT1.print(buzzerActive);
      BT1.print("\n");
      
    }else{
      Serial.write("Bad Command: ");
      Serial.write(command.c_str());
      Serial.write("\n");
    }
    BT1.flush();
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

void GET_info_station(int now){
  if(now > lastUpdate + timeUpdate){
    lastUpdate = now;
    
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
        if(status_response == "200"){
          
          state = (const char*) response["data"]["state"]["value"];
          Serial.print("State: ");
          Serial.println(state);
          id_user = (const char*) response["data"]["id_user"]["value"];
          Serial.print("Id User: ");
          Serial.println(id_user);
          id_bike = (const char*) response["data"]["id_bike"]["value"];
          Serial.print("Id Bike: ");
          Serial.println(id_bike);
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
