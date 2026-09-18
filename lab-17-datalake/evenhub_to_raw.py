import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

from azure.eventhub import EventHubConsumerClient
from azure.storage.filedatalake import DataLakeServiceClient


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

STORAGE_CONNECTION_STRING = os.getenv(
    "STORAGE_CONNECTION_STRING"
)

STORAGE_FILE_SYSTEM = os.getenv(
    "STORAGE_FILE_SYSTEM",
    "taxidatalake"
)


# ============================================================
# CONFIGURATION
# ============================================================

CONSUMER_GROUP = "$Default"

RAW_DIRECTORY = "raw"

BATCH_SIZE = 20

FLUSH_INTERVAL_SECONDS = 60


# ============================================================
# VALIDATE ENVIRONMENT VARIABLES
# ============================================================

required_variables = {
    "EVENT_HUB_CONNECTION_STRING": EVENT_HUB_CONNECTION_STRING,
    "EVENT_HUB_NAME": EVENT_HUB_NAME,
    "STORAGE_CONNECTION_STRING": STORAGE_CONNECTION_STRING,
    "STORAGE_FILE_SYSTEM": STORAGE_FILE_SYSTEM,
}

missing_variables = [
    name
    for name, value in required_variables.items()
    if not value
]

if missing_variables:
    raise ValueError(
        "Missing environment variables: "
        + ", ".join(missing_variables)
    )


# ============================================================
# GLOBAL STATE
# ============================================================

# One buffer for each Event Hub partition.
#
# Example:
#
# buffers = {
#     "0": [event1, event2, ...],
#     "1": [event1, event2, ...]
# }
#
buffers = {}


# Protects access to the buffers.
buffer_lock = threading.Lock()


# Prevents two threads from uploading to ADLS
# at the same time.
upload_lock = threading.Lock()


# Used to stop the timer thread.
stop_timer = threading.Event()


# ============================================================
# ADLS CONNECTION
# ============================================================

print()
print("=" * 70)
print("CONNECTING TO AZURE DATA LAKE")
print("=" * 70)

service_client = DataLakeServiceClient.from_connection_string(
    STORAGE_CONNECTION_STRING
)

file_system_client = service_client.get_file_system_client(
    file_system=STORAGE_FILE_SYSTEM
)


# ============================================================
# VERIFY FILESYSTEM
# ============================================================

try:

    file_system_client.get_file_system_properties()

    print(
        f"✓ Filesystem exists: "
        f"{STORAGE_FILE_SYSTEM}"
    )

except Exception as e:

    print("✗ Cannot access ADLS filesystem")

    raise e


# ============================================================
# VERIFY / CREATE RAW DIRECTORY
# ============================================================

try:

    directory_client = (
        file_system_client.get_directory_client(
            RAW_DIRECTORY
        )
    )

    directory_client.get_directory_properties()

    print(
        f"✓ Directory exists: "
        f"{RAW_DIRECTORY}/"
    )

except Exception:

    print(
        f"Directory {RAW_DIRECTORY}/ does not exist."
    )

    print("Creating directory...")

    file_system_client.create_directory(
        RAW_DIRECTORY
    )

    print(
        f"✓ Directory created: "
        f"{RAW_DIRECTORY}/"
    )


print("=" * 70)
print("✓ ADLS READY")
print("=" * 70)


# ============================================================
# SAVE BATCH TO ADLS RAW
# ============================================================

def save_batch_to_raw(
    partition_id,
    events
):

    if not events:
        return False


    # --------------------------------------------------------
    # Convert events to JSON
    # --------------------------------------------------------

    json_data = json.dumps(
        events,
        ensure_ascii=False,
        indent=2
    )

    data = json_data.encode("utf-8")

    data_size = len(data)


    # --------------------------------------------------------
    # Generate unique filename
    # --------------------------------------------------------

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    file_name = (
        f"taxi_events_"
        f"{timestamp}_"
        f"partition_{partition_id}_"
        f"{uuid.uuid4().hex[:8]}.json"
    )

    file_path = (
        f"{RAW_DIRECTORY}/{file_name}"
    )


    print()
    print("-" * 70)

    print(
        f"FLUSHING PARTITION {partition_id}"
    )

    print(
        f"Events : {len(events)}"
    )

    print(
        f"Size   : {data_size:,} bytes"
    )

    print(
        f"File   : {file_path}"
    )

    print("-" * 70)


    # --------------------------------------------------------
    # Only one ADLS upload at a time
    # --------------------------------------------------------

    with upload_lock:

        file_client = (
            file_system_client.get_file_client(
                file_path
            )
        )

        try:

            # ==================================================
            # STEP 1 — CREATE FILE
            # ==================================================

            print(
                "1. Creating file..."
            )

            file_client.create_file()

            print(
                "   ✓ File created"
            )


            # ==================================================
            # STEP 2 — APPEND DATA
            # ==================================================

            print(
                "2. Appending data..."
            )

            file_client.append_data(
                data=data,
                offset=0,
                length=data_size
            )

            print(
                "   ✓ Data appended"
            )


            # ==================================================
            # STEP 3 — FLUSH DATA
            # ==================================================

            print(
                "3. Flushing data..."
            )

            # IMPORTANT:
            #
            # Your installed Azure SDK expects:
            #
            #     flush_data(offset)
            #
            # Therefore:
            #
            #     flush_data(data_size)
            #
            # NOT:
            #
            #     flush_data(position=data_size)

            file_client.flush_data(
                data_size
            )

            print(
                "   ✓ Data flushed"
            )


            # ==================================================
            # SUCCESS
            # ==================================================

            print()
            print(
                f"✓ SUCCESS: "
                f"{len(events)} events saved"
            )

            print(
                f"  ADLS path: {file_path}"
            )

            print("-" * 70)

            return True


        except Exception as e:

            print()
            print(
                "✗ ADLS UPLOAD FAILED"
            )

            print(
                f"Partition : {partition_id}"
            )

            print(
                f"File      : {file_path}"
            )

            print(
                f"Events    : {len(events)}"
            )

            print(
                f"Size      : {data_size:,} bytes"
            )

            print(
                f"Error     : {e}"
            )

            print(
                f"Error type: {type(e).__name__}"
            )

            print("-" * 70)

            # ------------------------------------------------
            # Try to delete partially-created file
            # ------------------------------------------------

            try:

                file_client.delete_file()

                print(
                    "✓ Partial file deleted"
                )

            except Exception:

                pass


            return False


# ============================================================
# FLUSH ONE PARTITION
# ============================================================

def flush_partition(
    partition_id
):

    # --------------------------------------------------------
    # Take events from the buffer
    # --------------------------------------------------------

    with buffer_lock:

        events = buffers.get(
            partition_id,
            []
        )

        if not events:
            return


        # IMPORTANT:
        #
        # Remove the events from the buffer BEFORE uploading.
        #
        # If upload fails, we put them back.
        #

        buffers[partition_id] = []


    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    success = save_batch_to_raw(
        partition_id,
        events
    )


    # --------------------------------------------------------
    # If upload failed, restore events
    # --------------------------------------------------------

    if not success:

        with buffer_lock:

            # Put failed events back at the beginning
            # so they are not lost.

            buffers.setdefault(
                partition_id,
                []
            )

            buffers[partition_id] = (
                events
                + buffers[partition_id]
            )

        print(
            f"⚠ {len(events)} events "
            f"returned to partition "
            f"{partition_id} buffer"
        )


# ============================================================
# TIMER WORKER
# ============================================================

def timer_worker():

    print(
        "✓ Timer worker started"
    )

    while not stop_timer.wait(
        FLUSH_INTERVAL_SECONDS
    ):

        print()
        print(
            "=" * 70
        )

        print(
            "⏰ 60-SECOND FLUSH"
        )

        print(
            "=" * 70
        )


        # ----------------------------------------------------
        # Get partition IDs
        # ----------------------------------------------------

        with buffer_lock:

            partition_ids = list(
                buffers.keys()
            )


        # ----------------------------------------------------
        # Flush every partition
        # ----------------------------------------------------

        for partition_id in partition_ids:

            flush_partition(
                partition_id
            )


# ============================================================
# EVENT HUB CALLBACK
# ============================================================

def on_event(
    partition_context,
    event
):

    partition_id = (
        partition_context.partition_id
    )


    try:

        # ====================================================
        # GET EVENT BODY
        # ====================================================

        event_body = event.body_as_str(
            encoding="UTF-8"
        )


        # ====================================================
        # PARSE JSON
        # ====================================================

        data = json.loads(
            event_body
        )


        # ====================================================
        # ADD INGESTION METADATA
        # ====================================================

        data["ingested_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        data["eventhub_partition"] = (
            partition_id
        )

        data["eventhub_offset"] = str(
            event.offset
        )


        # ====================================================
        # ADD TO PARTITION BUFFER
        # ====================================================

        should_flush = False

        with buffer_lock:

            if partition_id not in buffers:

                buffers[partition_id] = []


            buffers[partition_id].append(
                data
            )


            buffer_size = len(
                buffers[partition_id]
            )


            if buffer_size >= BATCH_SIZE:

                should_flush = True


        # ====================================================
        # DISPLAY EVENT
        # ====================================================

        print(
            f"Event received | "
            f"partition={partition_id} | "
            f"buffer={buffer_size}/{BATCH_SIZE}"
        )


        # ====================================================
        # FLUSH WHEN BATCH SIZE REACHED
        # ====================================================

        if should_flush:

            flush_partition(
                partition_id
            )


    except json.JSONDecodeError as e:

        print()
        print(
            "✗ Invalid JSON event"
        )

        print(
            f"Partition: {partition_id}"
        )

        print(
            f"Error: {e}"
        )


    except Exception as e:

        print()
        print(
            "✗ Error processing event"
        )

        print(
            f"Partition: {partition_id}"
        )

        print(
            f"Error: {e}"
        )


# ============================================================
# ERROR CALLBACK
# ============================================================

def on_error(
    partition_context,
    error
):

    if partition_context:

        print()
        print(
            f"✗ Event Hub error "
            f"on partition "
            f"{partition_context.partition_id}"
        )

    else:

        print()
        print(
            "✗ Event Hub consumer error"
        )

    print(
        f"Error: {error}"
    )


# ============================================================
# PARTITION INITIALIZATION
# ============================================================

def on_partition_initialize(
    partition_context
):

    partition_id = (
        partition_context.partition_id
    )

    print()
    print(
        f"✓ Partition initialized: "
        f"{partition_id}"
    )

    with buffer_lock:

        if partition_id not in buffers:

            buffers[partition_id] = []


# ============================================================
# PARTITION CLOSE
# ============================================================

def on_partition_close(
    partition_context,
    reason
):

    partition_id = (
        partition_context.partition_id
    )

    print()
    print(
        f"Partition closed: "
        f"{partition_id}"
    )

    print(
        f"Reason: {reason}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("AZURE EVENT HUB → ADLS GEN2 RAW CONSUMER")
    print("=" * 70)

    print(
        f"Event Hub       : {EVENT_HUB_NAME}"
    )

    print(
        f"Consumer Group  : {CONSUMER_GROUP}"
    )

    print(
        f"ADLS Filesystem : {STORAGE_FILE_SYSTEM}"
    )

    print(
        f"Raw Directory   : {RAW_DIRECTORY}/"
    )

    print(
        f"Batch Size      : {BATCH_SIZE}"
    )

    print(
        f"Flush Interval  : {FLUSH_INTERVAL_SECONDS}s"
    )

    print("=" * 70)


    # ========================================================
    # START TIMER
    # ========================================================

    timer_thread = threading.Thread(
        target=timer_worker,
        daemon=True
    )

    timer_thread.start()


    # ========================================================
    # CREATE EVENT HUB CLIENT
    # ========================================================

    consumer = EventHubConsumerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STRING,
        consumer_group=CONSUMER_GROUP,
        eventhub_name=EVENT_HUB_NAME
    )


    print()
    print(
        "✓ Event Hub consumer created"
    )

    print(
        "✓ Waiting for events..."
    )

    print(
        "Press Ctrl+C to stop."
    )

    print()


    # ========================================================
    # START CONSUMING
    # ========================================================

    try:

        with consumer:

            consumer.receive(
                on_event=on_event,
                on_error=on_error,
                on_partition_initialize=(
                    on_partition_initialize
                ),
                on_partition_close=(
                    on_partition_close
                ),

                # Start from the earliest available event.
                starting_position="-1"
            )


    except KeyboardInterrupt:

        print()
        print()
        print(
            "=" * 70
        )

        print(
            "STOPPING CONSUMER..."
        )

        print(
            "=" * 70
        )


    finally:

        # ====================================================
        # STOP TIMER
        # ====================================================

        stop_timer.set()

        timer_thread.join(
            timeout=5
        )


        # ====================================================
        # FLUSH REMAINING EVENTS
        # ====================================================

        print()
        print(
            "Flushing remaining buffered events..."
        )


        with buffer_lock:

            partition_ids = list(
                buffers.keys()
            )


        for partition_id in partition_ids:

            flush_partition(
                partition_id
            )


        # ====================================================
        # FINAL STATUS
        # ====================================================

        print()
        print(
            "=" * 70
        )

        print(
            "CONSUMER STOPPED"
        )

        print(
            "=" * 70
        )


        with buffer_lock:

            for partition_id, events in buffers.items():

                print(
                    f"Partition {partition_id}: "
                    f"{len(events)} events remaining"
                )

        print(
            "=" * 70
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()