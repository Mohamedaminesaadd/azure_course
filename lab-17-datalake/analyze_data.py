import os
import json
import math
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

STORAGE_CONNECTION_STRING = os.getenv(
    "STORAGE_CONNECTION_STRING"
)

STORAGE_FILE_SYSTEM = os.getenv(
    "STORAGE_FILE_SYSTEM"
)


# ============================================================
# 2. CONFIGURATION
# ============================================================

PROCESSED_DIRECTORY = "processed"

CURATED_DIRECTORY = "curated"

ANALYTICS_FILE = "taxi_driver_summary.json"


# ============================================================
# 3. VALIDATE CONFIGURATION
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
# 4. CONNECT TO ADLS GEN2
# ============================================================

service_client = DataLakeServiceClient.from_connection_string(
    STORAGE_CONNECTION_STRING
)

file_system_client = service_client.get_file_system_client(
    STORAGE_FILE_SYSTEM
)


# ============================================================
# 5. READ PROCESSED DATA
# ============================================================

def read_processed_data():

    print()
    print("=" * 60)
    print("READING PROCESSED DATA")
    print("=" * 60)

    events = []

    try:

        paths = file_system_client.get_paths(
            path=PROCESSED_DIRECTORY
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
            # Download file
            # ------------------------------------------------

            file_client = (
                file_system_client.get_file_client(
                    path.name
                )
            )

            data = (
                file_client
                .download_file()
                .readall()
            )

            parsed_data = json.loads(
                data.decode("utf-8")
            )

            # =================================================
            # JSON ARRAY
            # =================================================

            if isinstance(parsed_data, list):

                events.extend(
                    parsed_data
                )

                print(
                    f"  → {len(parsed_data)} events"
                )

            # =================================================
            # SINGLE EVENT
            # =================================================

            elif isinstance(parsed_data, dict):

                events.append(
                    parsed_data
                )

                print(
                    "  → 1 event"
                )

            else:

                print(
                    f"Skipping {path.name}: "
                    f"invalid JSON structure"
                )

        print()
        print(
            f"Total processed events: "
            f"{len(events)}"
        )

        return events

    except Exception as error:

        print(
            f"Error reading processed data: "
            f"{error}"
        )

        return []


# ============================================================
# 6. HAVERSINE DISTANCE
# ============================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# ============================================================
# 7. ANALYZE TAXI DATA
# ============================================================

def analyze_data(events):

    # --------------------------------------------------------
    # Group events by driver
    # --------------------------------------------------------

    drivers = defaultdict(list)

    for event in events:

        try:

            driver_id = event[
                "driver_id"
            ]

            drivers[
                driver_id
            ].append(event)

        except KeyError:

            print(
                f"Skipping event without "
                f"driver_id: {event}"
            )


    results = []


    # ========================================================
    # ANALYZE EACH DRIVER
    # ========================================================

    for driver_id, driver_events in drivers.items():

        if not driver_events:
            continue

        # ----------------------------------------------------
        # Sort events chronologically
        # ----------------------------------------------------

        driver_events.sort(
            key=lambda event: event[
                "timestamp"
            ]
        )

        # ----------------------------------------------------
        # Extract values
        # ----------------------------------------------------

        speeds = []

        latitudes = []

        longitudes = []

        rides = set()

        headings = []

        for event in driver_events:

            try:

                speeds.append(
                    float(
                        event["speed_kmh"]
                    )
                )

                latitudes.append(
                    float(
                        event["latitude"]
                    )
                )

                longitudes.append(
                    float(
                        event["longitude"]
                    )
                )

                headings.append(
                    float(
                        event["heading"]
                    )
                )

                rides.add(
                    event["ride_id"]
                )

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                print(
                    f"Invalid event skipped: "
                    f"{event}"
                )


        # ----------------------------------------------------
        # Calculate total distance
        # ----------------------------------------------------

        total_distance = 0.0

        for i in range(
            1,
            len(driver_events)
        ):

            try:

                lat1 = float(
                    driver_events[i - 1][
                        "latitude"
                    ]
                )

                lon1 = float(
                    driver_events[i - 1][
                        "longitude"
                    ]
                )

                lat2 = float(
                    driver_events[i][
                        "latitude"
                    ]
                )

                lon2 = float(
                    driver_events[i][
                        "longitude"
                    ]
                )

                distance = calculate_distance(
                    lat1,
                    lon1,
                    lat2,
                    lon2
                )

                total_distance += distance

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                continue


        # ----------------------------------------------------
        # Calculate ride duration
        # ----------------------------------------------------

        duration_minutes = None

        try:

            first_timestamp = datetime.fromisoformat(
                driver_events[0][
                    "timestamp"
                ].replace(
                    "Z",
                    "+00:00"
                )
            )

            last_timestamp = datetime.fromisoformat(
                driver_events[-1][
                    "timestamp"
                ].replace(
                    "Z",
                    "+00:00"
                )
            )

            duration_seconds = (
                last_timestamp
                - first_timestamp
            ).total_seconds()

            duration_minutes = round(
                duration_seconds / 60,
                2
            )

        except Exception:

            duration_minutes = None


        # ====================================================
        # CREATE DRIVER SUMMARY
        # ====================================================

        summary = {

            "driver_id": driver_id,

            "event_count": len(
                driver_events
            ),

            "ride_count": len(
                rides
            ),

            "average_speed_kmh": (
                round(
                    sum(speeds)
                    / len(speeds),
                    2
                )
                if speeds
                else None
            ),

            "minimum_speed_kmh": (
                round(
                    min(speeds),
                    2
                )
                if speeds
                else None
            ),

            "maximum_speed_kmh": (
                round(
                    max(speeds),
                    2
                )
                if speeds
                else None
            ),

            "total_distance_km": round(
                total_distance,
                3
            ),

            "average_heading": (
                round(
                    sum(headings)
                    / len(headings),
                    2
                )
                if headings
                else None
            ),

            "start_latitude": (
                latitudes[0]
                if latitudes
                else None
            ),

            "start_longitude": (
                longitudes[0]
                if longitudes
                else None
            ),

            "end_latitude": (
                latitudes[-1]
                if latitudes
                else None
            ),

            "end_longitude": (
                longitudes[-1]
                if longitudes
                else None
            ),

            "tracking_duration_minutes":
                duration_minutes
        }

        results.append(
            summary
        )

    return results


# ============================================================
# 8. CREATE CURATED DIRECTORY
# ============================================================

def create_curated_directory():

    try:

        file_system_client.create_directory(
            CURATED_DIRECTORY
        )

        print(
            f"Created directory: "
            f"{CURATED_DIRECTORY}/"
        )

    except Exception:

        # Directory already exists
        pass


# ============================================================
# 9. SAVE ANALYTICS
# ============================================================

def save_analytics(results):

    create_curated_directory()

    directory_client = (
        file_system_client.get_directory_client(
            CURATED_DIRECTORY
        )
    )

    file_client = (
        directory_client.get_file_client(
            ANALYTICS_FILE
        )
    )

    json_data = json.dumps(
        results,
        indent=2
    )

    file_client.upload_data(
        json_data.encode("utf-8"),
        overwrite=True
    )

    print()
    print("=" * 60)
    print("ANALYTICS SAVED")
    print("=" * 60)

    print(
        f"Location: "
        f"{CURATED_DIRECTORY}/"
        f"{ANALYTICS_FILE}"
    )

    print(
        f"Drivers analyzed: "
        f"{len(results)}"
    )

    print("=" * 60)


# ============================================================
# 10. MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("PROCESSED → ANALYTICS")
    print("=" * 60)


    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    events = read_processed_data()

    if not events:

        print(
            "No processed events found."
        )

        return


    # --------------------------------------------------------
    # TRANSFORM
    # --------------------------------------------------------

    results = analyze_data(
        events
    )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("TAXI ANALYTICS RESULTS")
    print("=" * 60)

    for result in results:

        print()

        print(
            f"Driver: "
            f"{result['driver_id']}"
        )

        print(
            f"Events: "
            f"{result['event_count']}"
        )

        print(
            f"Rides: "
            f"{result['ride_count']}"
        )

        print(
            f"Average speed: "
            f"{result['average_speed_kmh']} km/h"
        )

        print(
            f"Minimum speed: "
            f"{result['minimum_speed_kmh']} km/h"
        )

        print(
            f"Maximum speed: "
            f"{result['maximum_speed_kmh']} km/h"
        )

        print(
            f"Total distance: "
            f"{result['total_distance_km']} km"
        )

        print(
            f"Average heading: "
            f"{result['average_heading']}°"
        )

        print(
            f"Tracking duration: "
            f"{result['tracking_duration_minutes']} minutes"
        )

        print(
            f"Start position: "
            f"({result['start_latitude']}, "
            f"{result['start_longitude']})"
        )

        print(
            f"End position: "
            f"({result['end_latitude']}, "
            f"{result['end_longitude']})"
        )


    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    save_analytics(
        results
    )


    print()
    print("=" * 60)
    print("ANALYTICS PROCESSING COMPLETED")
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()