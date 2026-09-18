
import os
import json
import time
import uuid
import random
from datetime import datetime, timezone

from dotenv import load_dotenv
from azure.eventhub import EventHubProducerClient, EventData


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

EVENT_HUB_CONNECTION_STRING = os.getenv(
    "EVENT_HUB_CONNECTION_STRING"
)

EVENT_HUB_NAME = os.getenv(
    "EVENT_HUB_NAME"
)


# ============================================================
# CONFIGURATION
# ============================================================

# Get the operating system process ID
PROCESS_ID = os.getpid()

# Generate unique IDs based on the process ID
DRIVER_ID = f"driver_{PROCESS_ID}"
RIDE_ID = f"ride_{PROCESS_ID}"

# Initial driver position
INITIAL_LATITUDE = 35.8225
INITIAL_LONGITUDE = 10.6342

# Send every 10 seconds
INTERVAL_SECONDS = 10

# Run for 10 minutes
DURATION_SECONDS = 10 * 60


# ============================================================
# CREATE TAXI LOCATION EVENT
# ============================================================

def create_driver_location_event(
    driver_id,
    ride_id,
    latitude,
    longitude,
    speed_kmh,
    heading
):

    return {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",

        "event_type": "driver.location_updated",

        "event_version": "1.0",

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "driver": {
            "driver_id": driver_id
        },

        "ride": {
            "ride_id": ride_id
        },

        "location": {
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "speed_kmh": round(speed_kmh, 2),
            "heading": heading
        }
    }


# ============================================================
# MAIN
# ============================================================

def main():

    producer = EventHubProducerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STRING,
        eventhub_name=EVENT_HUB_NAME
    )

    latitude = INITIAL_LATITUDE
    longitude = INITIAL_LONGITUDE

    start_time = time.time()

    event_count = 0

    try:

        print("=" * 60)
        print("TAXI LOCATION EVENT PRODUCER")
        print("=" * 60)

        print(f"Process ID   : {PROCESS_ID}")
        print(f"Driver       : {DRIVER_ID}")
        print(f"Ride         : {RIDE_ID}")
        print(f"Interval     : {INTERVAL_SECONDS} seconds")
        print(f"Duration     : {DURATION_SECONDS / 60} minutes")
        print("=" * 60)

        while time.time() - start_time < DURATION_SECONDS:

            # ------------------------------------------------
            # Generate different values
            # ------------------------------------------------

            speed = random.uniform(20, 60)

            heading = random.randint(0, 359)

            # Small GPS movement
            latitude += random.uniform(-0.0005, 0.0005)
            longitude += random.uniform(-0.0005, 0.0005)

            # ------------------------------------------------
            # Create event
            # ------------------------------------------------

            event = create_driver_location_event(
                driver_id=DRIVER_ID,
                ride_id=RIDE_ID,
                latitude=latitude,
                longitude=longitude,
                speed_kmh=speed,
                heading=heading
            )

            # ------------------------------------------------
            # Convert to JSON
            # ------------------------------------------------

            event_json = json.dumps(event)

            # ------------------------------------------------
            # Create Event Hub batch
            # ------------------------------------------------

            event_batch = producer.create_batch()

            event_batch.add(
                EventData(event_json)
            )

            # ------------------------------------------------
            # Send event
            # ------------------------------------------------

            producer.send_batch(event_batch)

            event_count += 1

            print()
            print(f"Event #{event_count} sent")
            print(json.dumps(event, indent=2))

            # ------------------------------------------------
            # Wait
            # ------------------------------------------------

            time.sleep(INTERVAL_SECONDS)

        print()
        print("=" * 60)
        print("PRODUCER FINISHED")
        print("=" * 60)

        print(f"Total events sent: {event_count}")

    finally:

        producer.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()