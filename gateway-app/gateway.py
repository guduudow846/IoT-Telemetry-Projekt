#!/usr/bin/env python3
"""Gateway: MQTT -> Azure IoT Hub."""

import json
import os
import signal
import sys
import time

import paho.mqtt.client as mqtt
from azure.iot.device import IoTHubDeviceClient, Message
from azure.iot.device.exceptions import ClientError

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")

MQTT_TOPICS = [
    "telemetry/sensor-01/#",
    "telemetry/sensor-02/#",
]

AZURE_CONNECTION_STRING = os.getenv("AZURE_IOT_CONNECTION_STRING", "")

azure_client = None
running = True

def azure_connect():
    client = IoTHubDeviceClient.create_from_connection_string(
        AZURE_CONNECTION_STRING
    )
    print("Ansluten till Azure IoT Hub.")
    return client

def azure_send(payload):
    global azure_client
    if azure_client is None:
        azure_client = azure_connect()

    try:
        azure_client.send_message(Message(payload))
    except ClientError as e:
        print(f"Azure-sändning misslyckades: {e}. Försöker återansluta...")
        try:
            azure_client.shutdown()
        except Exception:
            pass
        time.sleep(2)
        azure_client = azure_connect()
        azure_client.send_message(Message(payload))

def on_mqtt_connect(client, userdata, flags, rc):
    if rc != 0:
        print(f"MQTT-anslutning misslyckades: rc={rc}")
        return
    print("Ansluten till MQTT-brokern.")
    for topic in MQTT_TOPICS:
        client.subscribe(topic)
        print(f"Prenumererar på {topic}")

def on_mqtt_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"Ogiltigt meddelande på {msg.topic}: {e}")
        return

    required = ("deviceId", "value", "unit")
    if not isinstance(data, dict) or not all(k in data for k in required):
        print(f"Telemetri saknar fält på {msg.topic}: {payload}")
        return

    print(f"\nMQTT {msg.topic}: {payload}")
    try:
        azure_send(payload)
        print("Vidarebefordrat till Azure IoT Hub.")
    except Exception as e:
        print(f"Kunde inte skicka till Azure: {e}")

def shutdown_handler(signum, frame):
    global running
    print("\nAvslutar gatewayen...")
    running = False

def main():
    global azure_client

    if not AZURE_CONNECTION_STRING:
        print("Sätt AZURE_IOT_CONNECTION_STRING innan start.")
        return 1

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        azure_client = azure_connect()
    except Exception as e:
        print(f"Kunde inte ansluta till Azure: {e}")
        return 1

    mqtt_client = mqtt.Client(client_id="rpi-gateway")
    if MQTT_USER:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message

    print(f"Ansluter till MQTT {MQTT_BROKER}:{MQTT_PORT}...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    print("Gatewayen kör. Avsluta med Ctrl+C.")
    try:
        while running:
            signal.pause()
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        if azure_client is not None:
            try:
                azure_client.shutdown()
            except Exception:
                pass
        print("Gatewayen stoppad.")

    return 0

if __name__ == "__main__":
    sys.exit(main())