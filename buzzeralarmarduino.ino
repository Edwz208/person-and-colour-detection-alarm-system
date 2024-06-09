#include <WiFi.h>

#define NOTE_C4  262
#define NOTE_G3  196
#define NOTE_B3  247
#define NOTE_A3  220

// Replace with your network credentials
const char* ssid = "";
const char* password = "";

const int pirPin = 5;
const int ledPin = 16;
const int buzzerPin = 19;


int pirState = LOW; 
int val = 0;      
unsigned long lastDetectionTime = 0;
unsigned long lastMelodyTime = 0;  
const unsigned long cooldownTime = 8000; 

WiFiServer server(80);
WiFiClient client;

int melody[] = {
  NOTE_C4, NOTE_G3, NOTE_G3, NOTE_A3, NOTE_G3, 0, NOTE_B3, NOTE_C4
};

int noteDurations[] = {
  4, 8, 8, 4, 4, 4, 4, 4
};

bool playMelodyFlag = false;

void setup() {
  Serial.begin(115200);
  
  pinMode(pirPin, INPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);

  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  // Print local IP address and start web server
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
}

void loop() {
  val = digitalRead(pirPin);
  unsigned long currentTime = millis();

  if (val == HIGH && (currentTime - lastDetectionTime > cooldownTime)) {
    if (pirState == LOW) {    
      Serial.println("Motion detected!");
      pirState = HIGH;    
      digitalWrite(ledPin, HIGH); 
      lastDetectionTime = currentTime;
    }
  } else if (val == LOW) {
    if (pirState == HIGH && (currentTime - lastDetectionTime > cooldownTime)) { 
      Serial.println("Motion ended!");
      pirState = LOW; 
      digitalWrite(ledPin, LOW); 
      noTone(buzzerPin); 
    }
  }

  if (!client || !client.connected()) {
    client = server.available();
  } else {
    while (client.available()) {
      char c = client.read();
      if (c == '1' && (currentTime - lastMelodyTime >= cooldownTime)) {
        Serial.println("Signal received! ");
        playMelodyFlag = true;
        lastMelodyTime = currentTime; 
      }
    }
  }
  if (playMelodyFlag) {
    playMelody();
  }
}

void playMelody() {
  for (int thisNote = 0; thisNote < 8; thisNote++) {
    int noteDuration = 1000 / noteDurations[thisNote];
    tone(buzzerPin, melody[thisNote], noteDuration);
    delay(noteDuration * 1.30);
    noTone(buzzerPin);
  }
}
