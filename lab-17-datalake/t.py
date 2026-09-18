import os
import json
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
STORAGE_FILE_SYSTEM = os.getenv("STORAGE_FILE_SYSTEM", "taxidatalake")


# ============================================================
# CONFIGURATION
# ============================================================

DIRECTORY_NAME = "raw"
NUMBER_OF_EVENTS = 70


# ============================================================
# VALIDATION
# ============================================================

if not STORAGE_CONNECTION_STRING:
    raise ValueError(
        "STORAGE_CONNECTION_STRING is missing from .env"
    )


# ============================================================
# CREATE ADLS CLIENT
# ============================================================

service_client = DataLakeServiceClient.from_connection_string(
    STORAGE_CONNECTION_STRING
)

file_system_client = service_client.get_file_system_client(
    file_system=STORAGE_FILE_SYSTEM
)


# ============================================================
# GENERATE REALISTIC TAXI EVENTS
# ============================================================

events = []

for i in range(NUMBER_OF_EVENTS):

    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "driver_location",
        "timestamp": datetime.now(timezone.utc).isoformat(),

        "driver": {
            "driver_id": f"driver_{(i % 5) + 1}",
            "vehicle_id": f"taxi_{(i % 10) + 1}"
        },

        "location": {
            "latitude": 35.819055 + (i * 0.00001),
            "longitude": 10.633141 + (i * 0.00001),
            "speed_kmh": 40.26 + (i % 10),
            "heading": 249
        }
    }

    events.append(event)


# ============================================================
# CONVERT EVENTS TO JSON
# ============================================================

json_data = json.dumps(
    events,
    ensure_ascii=False,
    indent=2
)

data = json_data.encode("utf-8")
data_size = len(data)


# ============================================================
# FILE NAME
# ============================================================

timestamp = datetime.now(timezone.utc).strftime(
    "%Y%m%d_%H%M%S_%f"
)

file_name = (
    f"taxi_events_"
    f"{timestamp}_"
    f"batch_test_"
    f"{uuid.uuid4().hex[:8]}.json"
)

file_path = f"{DIRECTORY_NAME}/{file_name}"


# ============================================================
# DISPLAY TEST INFORMATION
# ============================================================

print()
print("=" * 65)
print("REALISTIC ADLS BATCH TEST")
print("=" * 65)

print(f"Filesystem : {STORAGE_FILE_SYSTEM}")
print(f"Directory  : {DIRECTORY_NAME}/")
print(f"Events     : {NUMBER_OF_EVENTS}")
print(f"Size       : {data_size:,} bytes")
print(f"File       : {file_path}")

print("=" * 65)


# ============================================================
# GET FILE CLIENT
# ============================================================

file_client = file_system_client.get_file_client(
    file_path
)


# ============================================================
# 1. CREATE FILE
# ============================================================

try:

    print()
    print("1. Creating file...")

    file_client.create_file()

    print("✓ File created")


    # ========================================================
    # 2. APPEND DATA
    # ========================================================

    print()
    print("2. Appending data...")

    file_client.append_data(
        data=data,
        offset=0,
        length=data_size
    )

    print("✓ Data appended")


    # ========================================================
    # 3. FLUSH DATA
    # ========================================================

    print()
    print("3. Flushing data...")

    # IMPORTANT:
    # Your installed Azure SDK expects the offset
    # as the first positional argument.
    #
    # Therefore:
    #     flush_data(data_size)
    #
    # NOT:
    #     flush_data(position=data_size)

    file_client.flush_data(data_size)

    print("✓ Data flushed")


    # ========================================================
    # SUCCESS
    # ========================================================

    print()
    print("=" * 65)
    print("✓ REALISTIC BATCH TEST PASSED")
    print("=" * 65)

    print()
    print(f"ADLS file created successfully:")
    print(f"  {file_path}")

    print()
    print(f"Uploaded:")
    print(f"  {NUMBER_OF_EVENTS} events")
    print(f"  {data_size:,} bytes")

    print("=" * 65)


except Exception as e:

    print()
    print("=" * 65)
    print("✗ REALISTIC BATCH TEST FAILED")
    print("=" * 65)

    print()
    print("Error:")
    print(e)

    print()
    print("Error type:")
    print(type(e).__name__)

    print("=" * 65)

    raise