import os

from dotenv import load_dotenv

from azure.eventhub import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblob import BlobCheckpointStore


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

BLOB_STORAGE_CONNECTION_STRING = os.getenv(
    "BLOB_STORAGE_CONNECTION_STRING"
)

BLOB_CONTAINER_NAME = os.getenv(
    "BLOB_CONTAINER_NAME"
)


# ============================================================
# CONSUMER GROUP
# ============================================================

# Azure Event Hubs default consumer group
CONSUMER_GROUP = "$Default"


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not EVENT_HUB_CONNECTION_STRING:
    raise ValueError(
        "EVENT_HUB_CONNECTION_STRING is not configured"
    )

if not EVENT_HUB_NAME:
    raise ValueError(
        "EVENT_HUB_NAME is not configured"
    )

if not BLOB_STORAGE_CONNECTION_STRING:
    raise ValueError(
        "BLOB_STORAGE_CONNECTION_STRING is not configured"
    )

if not BLOB_CONTAINER_NAME:
    raise ValueError(
        "BLOB_CONTAINER_NAME is not configured"
    )


# ============================================================
# EVENT HANDLER
# ============================================================

def on_event(partition_context, event):

    print("\n" + "=" * 50)
    print("EVENT RECEIVED")
    print("=" * 50)

    print(
        "Consumer Group:",
        CONSUMER_GROUP
    )

    print(
        "Partition:",
        partition_context.partition_id
    )

    print(
        "Sequence Number:",
        event.sequence_number
    )

    print(
        "Offset:",
        event.offset
    )

    print(
        "Event:",
        event.body_as_str(encoding="UTF-8")
    )

    # Save checkpoint to Azure Blob Storage
    partition_context.update_checkpoint(event)

    print("Checkpoint saved.")


# ============================================================
# ERROR HANDLER
# ============================================================

def on_error(partition_context, error):

    print("\n" + "=" * 50)
    print("CONSUMER ERROR")
    print("=" * 50)

    print(error)


# ============================================================
# MAIN
# ============================================================

def main():

    # Create Blob checkpoint store
    checkpoint_store = BlobCheckpointStore.from_connection_string(
        BLOB_STORAGE_CONNECTION_STRING,
        BLOB_CONTAINER_NAME
    )

    # Create Event Hub consumer
    client = EventHubConsumerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STRING,
        consumer_group=CONSUMER_GROUP,
        eventhub_name=EVENT_HUB_NAME,
        checkpoint_store=checkpoint_store
    )

    print("\n" + "=" * 50)
    print("AZURE EVENT HUB CONSUMER")
    print("=" * 50)

    print("Event Hub:", EVENT_HUB_NAME)
    print("Consumer Group:", CONSUMER_GROUP)
    print("Waiting for events...")
    print("Press CTRL+C to stop.")

    # Start receiving
    with client:

        client.receive(
            on_event=on_event,
            on_error=on_error,
            starting_position="-1"
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()