#!/usr/bin/env python3
"""Azure-konsument: läser telemetri från Azure IoT Hub."""

import json
import os
import sys

from azure.eventhub import EventHubConsumerClient

CONNECTION_STR = os.getenv("AZURE_EVENTHUB_CONNECTION_STRING", "")
CONSUMER_GROUP = "$Default"


def on_event(partition_context, event):
    if event is None:
        return
    try:
        payload = event.body_as_str(encoding="UTF-8")
        data = json.loads(payload)
        print("\nMottog telemetri från Azure IoT Hub")
        print(f"Device ID: {data.get('deviceId', 'Okänd')}")
        print(f"Värde: {data.get('value', 'N/A')} {data.get('unit', '')}")
        print(f"JSON: {payload}")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Kunde inte tolka meddelandet: {e}")

    # Markera som läst så vi inte får det igen vid omstart
    partition_context.update_checkpoint(event)


def main() -> int:
    if not CONNECTION_STR:
        print("Sätt AZURE_EVENTHUB_CONNECTION_STRING innan start.")
        return 1

    client = EventHubConsumerClient.from_connection_string(
        conn_str=CONNECTION_STR,
        consumer_group=CONSUMER_GROUP,
    )

    print("Lyssnar på telemetri från Azure... (Ctrl+C för att avsluta)")
    try:
        with client:
            client.receive(
                on_event=on_event,
                starting_position="-1",  # från början av streamen
            )
    except KeyboardInterrupt:
        print("\nAzure-konsumenten avslutas.")
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())