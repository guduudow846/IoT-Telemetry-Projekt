
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ================= WIFI =================
const char* WIFI_SSID = "iPhone";
const char* WIFI_PASSWORD = "Hassan10";

// ================ MQTT ==================
// Ange Raspberry Pi:ns IP-adress.
const char* MQTT_SERVER = "172.20.10.3";
const int MQTT_PORT = 1883;

// Lämna tomma om Mosquitto inte kräver inloggning.
const char* MQTT_USER = "";
const char* MQTT_PASS = "";

// =============== ENHET =================
const char* DEVICE_ID = "sensor-01";
const char* MQTT_TOPIC = "telemetry/sensor-01";

// =============== SENSOR ================
#define DHTPIN 2

#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// =============== MQTT ==================
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

// =============== TID ===================
unsigned long lastWiFiAttempt = 0;
unsigned long lastMqttAttempt = 0;
unsigned long lastPublish = 0;

const unsigned long WIFI_RETRY = 10000;
const unsigned long MQTT_RETRY = 5000;
const unsigned long PUBLISH_INTERVAL = 5000;

// ============ WIFI ANSLUTNING ===========
void connectWiFi() {
  Serial.print("Ansluter till Wi-Fi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

// ============ MQTT ANSLUTNING ===========
void connectMQTT() {
  if (WiFi.status() != WL_CONNECTED || mqtt.connected()) {
    return;
  }

  Serial.print("Ansluter till MQTT... ");

  String clientId = String("esp32-") + DEVICE_ID;

  bool connected;

  if (strlen(MQTT_USER) > 0) {
    connected = mqtt.connect(
      clientId.c_str(),
      MQTT_USER,
      MQTT_PASS
    );
  } else {
    connected = mqtt.connect(clientId.c_str());
  }

  if (connected) {
    Serial.println("OK!");
  } else {
    Serial.print("Misslyckades. MQTT state: ");
    Serial.println(mqtt.state());
  }
}

// ============ PUBLICERA DATA ============
void publishTelemetry(
  const char* measurement,
  float value,
  const char* unit
) {
  if (!mqtt.connected()) {
    Serial.println("MQTT ej ansluten. Data skickas inte.");
    return;
  }

  JsonDocument doc;

  doc["deviceId"] = DEVICE_ID;
  doc["value"] = value;
  doc["unit"] = unit;

  char payload[192];
  serializeJson(doc, payload, sizeof(payload));

  char topic[128];
  snprintf(
    topic,
    sizeof(topic),
    "%s/%s",
    MQTT_TOPIC,
    measurement
  );

  if (mqtt.publish(topic, payload)) {
    Serial.print("Topic: ");
    Serial.println(topic);

    Serial.print("JSON: ");
    Serial.println(payload);
  } else {
    Serial.println("Fel: MQTT-publicering misslyckades.");
  }
}

// ================= SETUP ================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("Arduino Nano ESP32 startar...");
  Serial.println("Sensor: DHT11");

  dht.begin();

  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setBufferSize(256);
  mqtt.setKeepAlive(30);

  connectWiFi();
}

// ================= LOOP =================
void loop() {
  unsigned long now = millis();

  // Kontrollera Wi-Fi.
  if (WiFi.status() != WL_CONNECTED) {
    if (now - lastWiFiAttempt >= WIFI_RETRY) {
      lastWiFiAttempt = now;
      Serial.println("Wi-Fi frånkopplat. Försöker igen...");
      WiFi.reconnect();
    }

    delay(10);
    return;
  }

  // Visa IP-adressen när Wi-Fi ansluter.
  static bool ipPrinted = false;

  if (!ipPrinted) {
    Serial.print("Wi-Fi anslutet! IP: ");
    Serial.println(WiFi.localIP());
    ipPrinted = true;
  }

  // Återanslut till MQTT vid behov.
  if (!mqtt.connected()) {
    if (now - lastMqttAttempt >= MQTT_RETRY) {
      lastMqttAttempt = now;
      connectMQTT();
    }
  } else {
    mqtt.loop();
  }

  // Läs och skicka sensordata var femte sekund.
  if (mqtt.connected() &&
      now - lastPublish >= PUBLISH_INTERVAL) {

    lastPublish = now;

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Fel vid läsning av DHT11.");
      return;
    }

    publishTelemetry("temperature", temperature, "C");
    publishTelemetry("humidity", humidity, "%");
  }

  delay(2);
}
