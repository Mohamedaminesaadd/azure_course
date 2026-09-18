import os
import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient


# ============================================================
# LOAD CONFIGURATION
# ============================================================

load_dotenv()

STORAGE_CONNECTION_STRING = os.getenv(
    "STORAGE_CONNECTION_STRING"
)

STORAGE_FILE_SYSTEM = os.getenv(
    "STORAGE_FILE_SYSTEM"
)

RAW_DIRECTORY = "raw"

PROCESSED_DIRECTORY = "processed"

PROCESSED_FILE = "processed_events.json"


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not STORAGE_CONNECTION_STRING:
    raise ValueError(
        "STORAGE_CONNECTION_STRING is missing from .env"
    )

if not STORAGE_FILE_SYSTEM:
    raise ValueError(
        "STORAGE_FILE_SYSTEM is missing from .env"
    )


# ============================================================
# CONNECT TO ADLS GEN2
# ============================================================

service_client = DataLakeServiceClient.from_connection_string(
    STORAGE_CONNECTION_STRING
)

file_system_client = service_client.get_file_system_client(
    STORAGE_FILE_SYSTEM
)


# ============================================================
# READ RAW DATA
# ============================================================

def read_raw_data():

    print()
    print("=" * 60)
    print("READING RAW DATA")
    print("=" * 60)

    events = []

    try:

        paths = file_system_client.get_paths(
            path=RAW_DIRECTORY
        )

        for path in paths:

            # ------------------------------------------------
            # Ignore directories
            # ------------------------------------------------

            if path.is_directory:
                continue

            # ------------------------------------------------
            # Only JSON files
            # ------------------------------------------------

            if not path.name.endswith(".json"):
                continue

            print(
                f"Reading: {path.name}"
            )

            # ------------------------------------------------
            # Get file
            # ------------------------------------------------

            file_client = (
                file_system_client.get_file_client(
                    path.name
                )
            )

            # ------------------------------------------------
            # Download
            # ------------------------------------------------

            downloaded_data = (
                file_client
                .download_file()
                .readall()
            )

            # ------------------------------------------------
            # JSON → Python
            # ------------------------------------------------

            data = json.loads(
                downloaded_data.decode("utf-8")
            )

            # =================================================
            # CASE 1:
            # JSON file contains a list of events
            # =================================================

            if isinstance(data, list):

                events.extend(data)

                print(
                    f"  → {len(data)} events"
                )

            # =================================================
            # CASE 2:
            # JSON file contains one event
            # =================================================

            elif isinstance(data, dict):

                events.append(data)

                print(
                    "  → 1 event"
                )

            else:

                print(
                    "  → Invalid JSON structure"
                )

        print()
        print(
            f"Total raw events loaded: "
            f"{len(events)}"
        )

        return events

    except Exception as error:

        print(
            f"Error reading raw data: {error}"
        )

        return []


# ============================================================
# VALIDATE TAXI EVENT
# ============================================================

def is_valid(event):

    try:

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        required_fields = [
            "event_id",
            "event_type",
            "event_version",
            "timestamp",
            "driver",
            "ride",
            "location"
        ]

        for field in required_fields:

            if field not in event:
                return False

        # ----------------------------------------------------
        # Event type
        # ----------------------------------------------------

        if event["event_type"] != (
            "driver.location_updated"
        ):
            return False

        # ----------------------------------------------------
        # Driver
        # ----------------------------------------------------

        driver_id = (
            event["driver"]["driver_id"]
        )

        if not driver_id:
            return False

        # ----------------------------------------------------
        # Ride
        # ----------------------------------------------------

        ride_id = (
            event["ride"]["ride_id"]
        )

        if not ride_id:
            return False

        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        location = event["location"]

        latitude = float(
            location["latitude"]
        )

        longitude = float(
            location["longitude"]
        )

        speed = float(
            location["speed_kmh"]
        )

        heading = float(
            location["heading"]
        )

        # ----------------------------------------------------
        # Validate latitude
        # ----------------------------------------------------

        if not -90 <= latitude <= 90:
            return False

        # ----------------------------------------------------
        # Validate longitude
        # ----------------------------------------------------

        if not -180 <= longitude <= 180:
            return False

        # ----------------------------------------------------
        # Validate speed
        # ----------------------------------------------------

        if not 0 <= speed <= 200:
            return False

        # ----------------------------------------------------
        # Validate heading
        # ----------------------------------------------------

        if not 0 <= heading <= 360:
            return False

        return True

    except (
        KeyError,
        TypeError,
        ValueError
    ):

        return False


# ============================================================
# CLEAN / TRANSFORM TAXI EVENTS
# ============================================================

def process_data(events):

    processed_events = []

    print()
    print("=" * 60)
    print("PROCESSING EVENTS")
    print("=" * 60)

    for event in events:

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        if not is_valid(event):

            print(
                "Invalid event removed:"
            )

            print(
                json.dumps(
                    event,
                    indent=2
                )
            )

            continue

        # ----------------------------------------------------
        # Extract nested values
        # ----------------------------------------------------

        driver_id = (
            event["driver"]["driver_id"]
        )

        ride_id = (
            event["ride"]["ride_id"]
        )

        location = event["location"]

        # ----------------------------------------------------
        # Create clean event
        # ----------------------------------------------------

        clean_event = {

            "event_id": event["event_id"],

            "event_type": event["event_type"],

            "event_version": event["event_version"],

            "timestamp": event["timestamp"],

            "driver_id": driver_id,

            "ride_id": ride_id,

            "latitude": float(
                location["latitude"]
            ),

            "longitude": float(
                location["longitude"]
            ),

            "speed_kmh": float(
                location["speed_kmh"]
            ),

            "heading": float(
                location["heading"]
            )
        }

        # ----------------------------------------------------
        # Keep ingestion metadata
        # ----------------------------------------------------

        if "ingested_at" in event:

            clean_event["ingested_at"] = (
                event["ingested_at"]
            )

        if "eventhub_partition" in event:

            clean_event["eventhub_partition"] = (
                event["eventhub_partition"]
            )

        if "eventhub_offset" in event:

            clean_event["eventhub_offset"] = (
                event["eventhub_offset"]
            )

        # ----------------------------------------------------
        # Add processed timestamp
        # ----------------------------------------------------

        clean_event["processed_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        # ----------------------------------------------------
        # Add to processed list
        # ----------------------------------------------------

        processed_events.append(
            clean_event
        )

    return processed_events


# ============================================================
# SAVE PROCESSED DATA
# ============================================================

def save_processed_data(events):

    if not events:

        print(
            "No processed events to save."
        )

        return

    try:

        # ----------------------------------------------------
        # Create processed directory
        # ----------------------------------------------------

        try:

            file_system_client.create_directory(
                PROCESSED_DIRECTORY
            )

            print(
                f"Created directory: "
                f"{PROCESSED_DIRECTORY}/"
            )

        except Exception:

            # Directory already exists
            pass

        # ----------------------------------------------------
        # Directory client
        # ----------------------------------------------------

        directory_client = (
            file_system_client.get_directory_client(
                PROCESSED_DIRECTORY
            )
        )

        # ----------------------------------------------------
        # File client
        # ----------------------------------------------------

        file_client = (
            directory_client.get_file_client(
                PROCESSED_FILE
            )
        )

        # ----------------------------------------------------
        # Convert to JSON
        # ----------------------------------------------------

        json_data = json.dumps(
            events,
            indent=2
        )

        # ----------------------------------------------------
        # Upload
        # ----------------------------------------------------

        file_client.upload_data(
            json_data.encode("utf-8"),
            overwrite=True
        )

        print()
        print("=" * 60)
        print("PROCESSED DATA SAVED")
        print("=" * 60)

        print(
            f"File: "
            f"{PROCESSED_DIRECTORY}/"
            f"{PROCESSED_FILE}"
        )

        print(
            f"Events: {len(events)}"
        )

        print("=" * 60)

    except Exception as error:

        print(
            f"Error saving processed data: "
            f"{error}"
        )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print()
    print("=" * 60)
    print("RAW → PROCESSING → PROCESSED")
    print("=" * 60)

    # ========================================================
    # EXTRACT
    # ========================================================

    raw_events = read_raw_data()

    if not raw_events:

        print(
            "No raw events found."
        )

        return

    # ========================================================
    # TRANSFORM
    # ========================================================

    processed_events = process_data(
        raw_events
    )

    # ========================================================
    # LOAD
    # ========================================================

    save_processed_data(
        processed_events
    )

    # ========================================================
    # STATISTICS
    # ========================================================

    print()
    print("=" * 60)
    print("PROCESSING STATISTICS")
    print("=" * 60)

    print(
        f"Raw events       : "
        f"{len(raw_events)}"
    )

    print(
        f"Valid events     : "
        f"{len(processed_events)}"
    )

    print(
        f"Removed events   : "
        f"{len(raw_events) - len(processed_events)}"
    )

    print("=" * 60)

    print(
        "PROCESSING COMPLETED"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()