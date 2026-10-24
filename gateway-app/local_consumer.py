#!/usr/bin/env python3
"""Lokal MQTT-konsument: visar telemetri från ESP32 i realtid."""

import json
import os

import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = "telemetry/#"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Ansluten till MQTT-brokern.")
        client.subscribe(MQTT_TOPIC)
        print(f"Prenumererar på {MQTT_TOPIC}")
    else:
        print(f"Anslutning misslyckades: rc={rc}")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        print(f"\n{msg.topic}")
        print(f"  Device ID: {data.get('deviceId', 'Okänd')}")
        print(f"  Värde: {data.get('value', 'N/A')} {data.get('unit', '')}")
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"Ogiltigt meddelande: {e}")


def main():
    client = mqtt.Client(client_id="local-consumer")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    print("Lokal konsument kör. Avsluta med Ctrl+C.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nAvslutar.")
        client.disconnect()


if __name__ == "__main__":
    main()