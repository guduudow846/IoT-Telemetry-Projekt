# IoT Telemetry Solution – ESP32, MQTT och Azure IoT Hub

En komplett IoT-lösning där en ESP32-enhet med DHT11-sensor skickar telemetri via MQTT till en lokal Mosquitto-broker på en Raspberry Pi. En gateway-applikation på Pi:n vidarebefordrar datan till Azure IoT Hub, och två konsumenter (lokal MQTT + Azure Event Hub) visar telemetrin i realtid.

## Arkitektur

```mermaid
graph TD
    ESP32[ESP32 <br> DHT11-sensor] -->|WiFi / MQTT| Mosquitto[Mosquitto <br> Raspberry Pi]
    Mosquitto -->|MQTT| Gateway[Gateway <br> Python]
    Gateway -->|AMQP| Azure[Azure IoT Hub]
    Azure -->|Event Hub| AzureConsumer[Azure-konsument <br> consumer.py]
    Mosquitto -->|MQTT| LocalConsumer[Lokal konsument <br> local_consumer.py]