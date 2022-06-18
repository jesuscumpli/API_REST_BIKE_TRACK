#include <SoftwareSerial.h>
#include <String.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>

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
const char* ssid = "vodafone07B0";
const char* password = "H8QCKYATYR4CKK";

void setup() {
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_LED, ledState);
  
  Serial.begin(9600);

  //BLUETOOTH
  BT1.begin(9600);
  BT1.print("AT+NAMEJesusIsmaelBLEDevice\n");
  BT1.print("AT+PIN1234\n");

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
}

void loop() {
  unsigned long now = millis();
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
