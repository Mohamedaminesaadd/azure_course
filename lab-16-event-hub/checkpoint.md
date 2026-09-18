Next is **checkpointing**. This is the step that turns our simple consumer into something closer to a production consumer.

# Lab 20 — Step 7: Checkpointing

So far:

```text
Producer
   ↓
Event Hubs
   ↓
Consumer
```

But our consumer currently keeps its position **only in memory**. If the program stops, that position disappears. Microsoft recommends a persistent checkpoint store when you want consumers to resume from their previous position and support load balancing/failover. ([Microsoft Learn][1])

The architecture becomes:

```text
                  Event Hubs
                      │
                      ▼
                  Consumer
                      │
              process event
                      │
                      ▼
               Blob Storage
                      │
                 checkpoint
                      │
                      ▼
              "I processed E250"
```

---

## 1. What exactly is a checkpoint?

Suppose Partition 0 contains:

```text
E1 → E2 → E3 → E4 → E5 → E6 → E7 → E8
```

Your consumer processes:

```text
E1 ✓
E2 ✓
E3 ✓
E4 ✓
E5 ✓
```

Then it saves:

```text
Checkpoint:
Partition 0 → E5
```

If the application crashes:

```text
Consumer crashes
       ↓
Restart
       ↓
Read checkpoint
       ↓
Partition 0 → E5
       ↓
Continue processing
```

The checkpoint is associated with the **consumer group and partition**. ([Microsoft Learn][1])

---

# 2. Why Azure Blob Storage?

Event Hubs doesn't simply store your application's checkpoint for you.

We use an external checkpoint store.

For Python, Microsoft provides:

```text
azure-eventhub-checkpointstoreblob
```

which uses **Azure Blob Storage** to persist checkpoints and partition ownership information. ([Microsoft Learn][1])

So:

```text
Event Hubs
   │
   │ events
   ▼
Python Consumer
   │
   │ checkpoint
   ▼
Azure Blob Storage
```

This is also a nice connection with the **Storage Account lab you already completed**.

---

# 3. Create a Blob container

You already have the storage account:

```text
aminestorages
```

We can create a dedicated container for this lab.

Go to:

**Azure Portal → Storage accounts → `aminestorages`**

Then:

**Data storage → Containers → + Container**

Create:

```text
eventhub-checkpoints
```

Use:

```text
Public access level:
Private
```

Do **not** make it public.

Your structure becomes:

```text
aminestorages
    │
    └── eventhub-checkpoints
```

Microsoft recommends using a dedicated container for each consumer group when using Blob Storage as an Event Hubs checkpoint store. ([Microsoft Learn][2])

---

# 4. Get the Storage connection string

Go to:

**Storage account → Security + networking → Access keys**

You'll see:

```text
KEY1
  Storage account name
  Key
  Connection string

KEY2
  ...
```

Copy the **Connection string**.

⚠️ Don't send it to me. It's a secret.

---

# 5. Add it to `.env`

Your `.env` currently has:

```text id="m28b8w"
EVENT_HUB_CONNECTION_STRING="..."
EVENT_HUB_NAME="sensor-events"
```

Add:

```text id="qu1ygr"
BLOB_STORAGE_CONNECTION_STRING="..."
BLOB_CONTAINER_NAME="eventhub-checkpoints"
```

So:

```text id="k3o4vw"
EVENT_HUB_CONNECTION_STRING="..."
EVENT_HUB_NAME="sensor-events"

BLOB_STORAGE_CONNECTION_STRING="..."
BLOB_CONTAINER_NAME="eventhub-checkpoints"
```

Your `.env` now contains **two credentials**:

```text
Event Hubs credential
        +
Storage credential
```

Keep `.env` in `.gitignore`.

---

# 6. Install the checkpoint package

Inside your virtual environment:

```bash
cd ~/azure-eventhub-lab20
source .venv/bin/activate
```

Then:

```bash
pip install azure-eventhub-checkpointstoreblob
```

Microsoft's current Python SDK documentation lists this package for persistent Blob checkpoints. ([Microsoft Learn][3])

---

# 7. Create the checkpoint consumer

Let's create a new file instead of destroying your original consumer:


# 8. Run it

```bash
python checkpoint_consumer.py
```

You should see:

```text
Checkpoint consumer started.
Consumer group: analytics
Waiting for events...
```

Then when events arrive:

```text
==============================
EVENT RECEIVED
==============================
Consumer Group: analytics
Partition: 0
Event: {"device_id":"ESP32-001", ...}
Checkpoint saved.
```

---

# 9. Look inside Azure Blob Storage

Now go back to:

**Storage Account → `aminestorages` → Containers → `eventhub-checkpoints`**

Initially:

```text
eventhub-checkpoints
        │
        └── blobs...
```

After the consumer processes events, you'll see checkpoint/ownership data created by the library.

Conceptually:

```text
Blob Storage
│
└── eventhub-checkpoints
       │
       ├── checkpoint information
       └── partition ownership information
```

The library uses Blob Storage for both checkpoint persistence and partition ownership. ([Microsoft Learn][1])

---

# 10. Now perform the important experiment

This is the part I want you to **actually test**.

### Step A — Start the consumer

```bash
python checkpoint_consumer.py
```

### Step B — Send events

In another terminal:

```bash
python producer.py
```

Let the consumer process them.

You'll see:

```text
Event 1
Checkpoint saved.

Event 2
Checkpoint saved.

Event 3
Checkpoint saved.
```

### Step C — Stop the consumer

Press:

```text
CTRL + C
```

Suppose it stopped after:

```text
E1 ✓
E2 ✓
E3 ✓
E4 ✓
E5 ✓
```

The checkpoint represents the processed position.

### Step D — Restart

```bash
python checkpoint_consumer.py
```

Now the consumer can use the persisted checkpoint rather than relying only on its previous in-memory state.

That's the whole reason checkpointing exists. ([Microsoft Learn][1])

---

# 11. Offset vs checkpoint

Don't confuse these:

### Offset

A position of an event within a partition.

```text
Partition 0:

E1
E2
E3
E4  ← offset identifies a position
E5
```

### Checkpoint

The consumer's **saved progress**.

```text
Consumer Group: analytics

Partition 0
Checkpoint → E4
```

Microsoft describes offsets/sequence numbers as positions within a partition, while checkpointing records the consumer's progress so it can resume later. ([Microsoft Learn][1])

Think:

```text
OFFSET
   ↓
Where is the event?

CHECKPOINT
   ↓
Where did MY APPLICATION successfully get to?
```

---

# Lab 20 architecture now

```text
                    PRODUCER
                       │
                       ▼
              ┌────────────────┐
              │  Event Hubs    │
              │                │
              │ P0    P1       │
              └───────┬────────┘
                      │
                      ▼
              Consumer Group
                "analytics"
                      │
                      ▼
              Python Consumer
                      │
                 process
                      │
                      ▼
              Blob Checkpoint
                      │
                      ▼
              saved position
```

We have now covered:



**After this checkpoint test, the next step is load balancing with multiple consumers**—we'll run two consumer instances in the **same consumer group** and observe how your two partitions are distributed between them.



The error is **not in your Python consumer logic**. Your code is reaching `BlobCheckpointStore`, but the **Blob Storage connection string that your program receives is invalid or empty**.

### 1. What the error means

The important part is:

```text
KeyError: 'ACCOUNTNAME'
```

followed by:

```text
ValueError: Connection string missing required connection details.
```

This happens here:

```python
BlobCheckpointStore.from_connection_string(
    BLOB_STORAGE_CONNECTION_STRING,
    BLOB_CONTAINER_NAME
)
```

The Azure SDK expects `BLOB_STORAGE_CONNECTION_STRING` to contain something like:

```text
DefaultEndpointsProtocol=https;
AccountName=aminestorages;
AccountKey=YOUR_SECRET_KEY;
EndpointSuffix=core.windows.net
```

But the value loaded into:

```python
BLOB_STORAGE_CONNECTION_STRING
```

doesn't contain the required `AccountName` information.

Your lab specifically expects a **Storage Account connection string** in `BLOB_STORAGE_CONNECTION_STRING`. 

---

# 2. First check what your `.env` contains

From your project directory:

```bash
cd ~/Documents/cloud_azure/"Real-Time Event Streaming with Azure Event Hubs"
```

Run:

```bash
cat .env
```

You should have something structurally like:

```env
EVENT_HUB_CONNECTION_STRING="Endpoint=sb://...."
EVENT_HUB_NAME="sensor-events"

BLOB_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=aminestorages;AccountKey=...;EndpointSuffix=core.windows.net"
BLOB_CONTAINER_NAME="eventhub-checkpoints"
```

⚠️ **Don't send me the actual connection string**, because it contains your Storage Account key.

---

# 3. Most likely problem

I suspect you may have put one of these instead:

### ❌ Wrong: Storage account name only

```env
BLOB_STORAGE_CONNECTION_STRING="aminestorages"
```

This will produce your error.

### ❌ Wrong: SAS URL

For example:

```env
BLOB_STORAGE_CONNECTION_STRING="https://aminestorages.blob.core.windows.net/?sv=..."
```

This is also **not what your current code expects**.

### ❌ Wrong: SAS token only

```env
BLOB_STORAGE_CONNECTION_STRING="sv=2025-..."
```

Also wrong for:

```python
BlobCheckpointStore.from_connection_string(...)
```

### ✅ Correct

You need the **Storage Account connection string**:

```env
BLOB_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=aminestorages;AccountKey=XXXXXXXX;EndpointSuffix=core.windows.net"
```

---

# 4. Get the correct connection string from Azure

Go to:

**Azure Portal → Storage accounts → `aminestorages`**

Then:

**Security + networking → Access keys**

You should see:

```text
KEY 1

Storage account name
aminestorages

Key
***************

Connection string
DefaultEndpointsProtocol=https;AccountName=aminestorages;AccountKey=...
```

Copy the **Connection string**, not the key alone.

Your lab also explicitly tells you to copy the **Connection string** from Access keys. 

Put it into:

```env
BLOB_STORAGE_CONNECTION_STRING="PASTE_CONNECTION_STRING_HERE"
```

---

# 5. Check that Python is actually loading it

Before creating the `BlobCheckpointStore`, temporarily add:

```python
print("Blob connection string loaded:", bool(BLOB_STORAGE_CONNECTION_STRING))
print("Blob container:", BLOB_CONTAINER_NAME)
```

So:

```python
def main():

    print("Blob connection string loaded:", bool(BLOB_STORAGE_CONNECTION_STRING))
    print("Blob container:", BLOB_CONTAINER_NAME)

    checkpoint_store = (
        BlobCheckpointStore.from_connection_string(
            BLOB_STORAGE_CONNECTION_STRING,
            BLOB_CONTAINER_NAME
        )
    )
```

Run:

```bash
python checkpoint_consumer.py
```

You want:

```text
Blob connection string loaded: True
Blob container: eventhub-checkpoints
```

Don't print the actual connection string.

---

# 6. If it says `False`

If you get:

```text
Blob connection string loaded: False
```

then Python isn't loading your `.env`.

Check that the file exists:

```bash
ls -la
```

You should see:

```text
.env
checkpoint_consumer.py
...
```

And check:

```bash
pwd
```

You should be in:

```text
/home/mohamed-amine/Documents/cloud_azure/Real-Time Event Streaming with Azure Event Hubs
```

Since you're using:

```python
load_dotenv()
```

Python normally searches for `.env` in the current/appropriate project context.

---

# 7. Check your environment variables safely

Run this:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('BLOB:', bool(os.getenv('BLOB_STORAGE_CONNECTION_STRING'))); print('CONTAINER:', os.getenv('BLOB_CONTAINER_NAME')); print('EVENT HUB:', bool(os.getenv('EVENT_HUB_CONNECTION_STRING'))); print('EVENT NAME:', os.getenv('EVENT_HUB_NAME'))"
```

Expected:

```text
BLOB: True
CONTAINER: eventhub-checkpoints
EVENT HUB: True
EVENT NAME: sensor-events
```

---

# 8. Also verify the container exists

In Azure Portal:

**Storage accounts → aminestorages → Data storage → Containers**

You should have:

```text
eventhub-checkpoints
```

Your lab uses this exact container name. 

If it doesn't exist, create it:

```text
Name: eventhub-checkpoints
Public access: Private
```

---

## 9. Your Python code itself is basically correct

This part:

```python
checkpoint_store = (
    BlobCheckpointStore.from_connection_string(
        BLOB_STORAGE_CONNECTION_STRING,
        BLOB_CONTAINER_NAME
    )
)
```

is correct for the connection-string approach described in your lab. 

And this:

```python
partition_context.update_checkpoint(event)
```

is what saves the consumer's progress after processing the event. 

So **don't change the consumer architecture yet**.

### Do this now

Run:

```bash
cat .env
```

Look specifically at:

```env
BLOB_STORAGE_CONNECTION_STRING=...
BLOB_CONTAINER_NAME=...
```

If you want, paste **only these two lines with the secret replaced**, like:

```env
BLOB_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=aminestorages;AccountKey=HIDDEN;EndpointSuffix=core.windows.net"
BLOB_CONTAINER_NAME="eventhub-checkpoints"
```

and I can tell you immediately whether the format is correct.


Yes, **checkpointing can be used on both sides conceptually, but in Azure Event Hubs the checkpoint you are working with belongs to the *consumer*, not the producer.**

### In your architecture

```text
Producer
   │
   │ sends events
   ▼
Event Hubs
   │
   │ reads events
   ▼
Consumer
   │
   │ saves checkpoint
   ▼
Blob Storage
```

### 1. Producer → normally NO checkpoint

The producer sends events:

```python
producer.send_batch(event_data)
```

Its responsibility is basically:

```text
Create event
     ↓
Send event
     ↓
Event Hubs
```

It doesn't need to remember **"I consumed event #50"**, because the producer isn't consuming anything.

---

### 2. Consumer → YES checkpoint

The consumer reads events:

```text
E1 → E2 → E3 → E4 → E5
```

After successfully processing E5:

```text
Checkpoint = E5
```

The checkpoint is persisted in Blob Storage.

If the consumer crashes:

```text
Consumer
   ↓
CRASH
   ↓
Restart
   ↓
Read checkpoint
   ↓
Continue from saved position
```

That's exactly what your current code does:

```python
partition_context.update_checkpoint(event)
```

Your lab describes the checkpoint as the consumer's saved progress and uses Blob Storage to persist it. 

### Important distinction

There are **two different reliability problems**:

| Component  | What it needs to remember              | Typical mechanism                                         |
| ---------- | -------------------------------------- | --------------------------------------------------------- |
| Producer   | Whether an event was successfully sent | Producer-side retry / acknowledgement / application logic |
| Consumer   | Which events it successfully processed | **Checkpoint**                                            |
| Event Hubs | Events and their positions             | Partitions + offsets/sequence numbers                     |

So when you're learning **Azure Event Hubs checkpointing**, focus on the **consumer side**.

In your project, the flow is:

```text
ESP32 / Producer
       ↓
   Event Hubs
       ↓
    Consumer
       ↓
  Process event
       ↓
update_checkpoint()
       ↓
  Blob Storage
```

And that's why the Blob Storage connection you were fixing earlier is needed **by the consumer**, not by the producer.


