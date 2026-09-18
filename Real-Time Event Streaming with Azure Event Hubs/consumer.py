import os
import json
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from azure.eventhub import EventHubProducerClient, EventData


load_dotenv()

CONNECTION_STRING = os.getenv("EVENT_HUB_CONNECTION_STRING")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")


def send_device_events(producer, device_id, start_hr):

    # Create a batch associated with this device
    batch = producer.create_batch(
        partition_key=device_id
    )

    for i in range(5):

        event = {
            "device_id": device_id,
            "heart_rate": start_hr + i,
            "temperature": 25.0 + i * 0.1,
            "event_number": i + 1,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        event_json = json.dumps(event)

        batch.add(EventData(event_json))

        print(
            f"{device_id} → event {i + 1}"
        )

    producer.send_batch(batch)

    print(f"Sent 5 events for {device_id}\n")


def main():

    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STRING,
        eventhub_name=EVENT_HUB_NAME
    )

    with producer:

        send_device_events(
            producer,
            "ESP32-001",
            70
        )

        send_device_events(
            producer,
            "ESP32-002",
            80
        )


if __name__ == "__main__":
    main()