### this error make me crazy for 5 hours, and I found the solution:
Yes — **the Event Hub connection itself is working**, because your consumer is successfully receiving events from partitions 0 and 1.

However, **the ADLS file-write operation is NOT passing**.

Your log clearly shows:

* ✅ Events are received from Event Hub.
* ✅ Partition 0 and 1 are being consumed.
* ✅ The buffer is working.
* ✅ The batch flush is triggered.
* ❌ Upload to ADLS fails with `PathNotFound`.
* ❌ Therefore, the events remain in memory and are **not being saved to `raw/`**.

For example, the consumer reaches:

```text
FLUSHING PARTITION 1
Reason : batch size reached
Events : 62

Uploading partition 1...
File : raw/taxi_events_...json
```

but ADLS responds:

```text
❌ ERROR SAVING PARTITION 1
The specified path does not exist.
ErrorCode:PathNotFound
```



### So the situation is

```text
                 ✅
Producer
   │
   ▼
Event Hub
   │
   │  ✅ Events received
   ▼
Consumer
   │
   │  ✅ Buffer
   ▼
Batch of 20+
   │
   │  ❌
   ▼
ADLS Gen2
   raw/
   │
   └── PathNotFound
```

### Important

This means **your Python/Event Hub part is good**. The problem is specifically on the **ADLS path/filesystem configuration**.

Your code is trying to write:

```text
<filesystem>/raw/taxi_events_....json
```

So we need to verify that:

```text
Storage Account
    └── Container / File System
          └── raw/
```

actually exists **in the same storage account/container referenced by your `.env`**.

Also, your log shows the consumer continuing to receive events while uploads fail, so the buffer keeps growing: 62 → 63 → 64 → 65 → ... 

**Don't continue sending events yet**, because the buffer can grow indefinitely while ADLS is unavailable.

If you show me your `.env` **with the connection string/password hidden**, specifically these three values:

```env
STORAGE_CONNECTION_STRING=...
STORAGE_FILE_SYSTEM=...
```

I can tell you exactly why `raw/` is returning `PathNotFound`.


Yes. I see a **very likely cause**, and we can fix it without changing your Event Hub architecture.

Your new log confirms the same issue: Event Hub consumption works, but every ADLS upload returns `PathNotFound`. 

### The most likely problem

Your code assumes that the ADLS directory:

```text
raw/
```

exists inside the filesystem/container:

```text
STORAGE_FILE_SYSTEM
```

But there is an important distinction:

```text
Storage Account
      │
      └── ADLS Gen2 filesystem/container
                │
                └── raw/
```

Your `STORAGE_FILE_SYSTEM` must be the **filesystem/container name**, not the storage-account name.

For example, if Azure Storage Explorer looks like:

```text
aminestorages
└── taxi-data
    ├── raw
    ├── processed
    └── analytics
```

then your `.env` must contain:

```env
STORAGE_FILE_SYSTEM=taxi-data
```

NOT:

```env
STORAGE_FILE_SYSTEM=aminestorages
```

---

## 1. First, don't run the consumer

Stop it for now:

```bash
Ctrl+C
```

Otherwise it will continue accumulating events in memory because the ADLS writes are failing.

Your log shows exactly this behavior: the buffer keeps the events after a failed upload. 

---

## 2. Check your Azure filesystem

Run:

```bash
az storage fs list \
  --account-name YOUR_STORAGE_ACCOUNT \
  --auth-mode login \
  -o table
```

You should see something like:

```text
Name
----------------
taxi-data
```

or:

```text
Name
----------------
lab-files
```

Whatever appears under `Name` is the value that should go into:

```env
STORAGE_FILE_SYSTEM=...
```

---

## 3. Check whether `raw` exists

Then run:

```bash
az storage fs directory list \
  --account-name YOUR_STORAGE_ACCOUNT \
  --file-system YOUR_FILE_SYSTEM \
  --auth-mode login \
  -o table
```

You should see:

```text
Name
----
raw
```

If `raw` doesn't exist, create it:

```bash
az storage fs directory create \
  --account-name YOUR_STORAGE_ACCOUNT \
  --file-system YOUR_FILE_SYSTEM \
  --name raw \
  --auth-mode login
```

Then verify:

```bash
az storage fs directory show \
  --account-name YOUR_STORAGE_ACCOUNT \
  --file-system YOUR_FILE_SYSTEM \
  --name raw \
  --auth-mode login
```

---

## 4. I would also modify your Python startup test

This is important.

Your current program apparently verifies the **filesystem**, but your actual failure is specifically at:

```text
raw/<filename>
```

So let's make the program test **the exact `raw/` directory before Event Hub starts**.

Add this after creating `directory_client`:

```python
# ============================================================
# VERIFY RAW DIRECTORY
# ============================================================

print()
print("Checking raw directory...")

directory_client = file_system_client.get_directory_client(
    RAW_DIRECTORY
)

try:
    directory_client.get_directory_properties()

    print(
        f"✓ Raw directory exists: "
        f"{STORAGE_FILE_SYSTEM}/{RAW_DIRECTORY}/"
    )

except Exception as error:
    print()
    print("❌ RAW DIRECTORY NOT FOUND")
    print("-" * 65)
    print(
        f"Filesystem : {STORAGE_FILE_SYSTEM}"
    )
    print(
        f"Directory  : {RAW_DIRECTORY}"
    )
    print("-" * 65)
    print(error)
    print("-" * 65)

    raise
```

Then your application will fail **immediately** if `raw/` is wrong instead of waiting until 20+ events arrive.

---

# 5. Even better: test the exact upload

I recommend making a small separate test.

Create:

```text
test_adls.py
```

with:

```python
import json
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

STORAGE_CONNECTION_STRING = os.getenv(
    "STORAGE_CONNECTION_STRING"
)

STORAGE_FILE_SYSTEM = os.getenv(
    "STORAGE_FILE_SYSTEM"
)

RAW_DIRECTORY = "raw"


# ============================================================
# VALIDATION
# ============================================================

if not STORAGE_CONNECTION_STRING:
    raise ValueError(
        "STORAGE_CONNECTION_STRING is missing"
    )

if not STORAGE_FILE_SYSTEM:
    raise ValueError(
        "STORAGE_FILE_SYSTEM is missing"
    )


# ============================================================
# CONNECT
# ============================================================

print()
print("=" * 65)
print("                 ADLS GEN2 TEST")
print("=" * 65)

print(
    f"Filesystem : {STORAGE_FILE_SYSTEM}"
)

print(
    f"Directory  : {RAW_DIRECTORY}/"
)

service_client = (
    DataLakeServiceClient.from_connection_string(
        STORAGE_CONNECTION_STRING
    )
)

filesystem_client = (
    service_client.get_file_system_client(
        STORAGE_FILE_SYSTEM
    )
)


# ============================================================
# TEST FILESYSTEM
# ============================================================

print()
print("1. Testing filesystem...")

filesystem_client.get_file_system_properties()

print("✓ Filesystem exists")


# ============================================================
# TEST RAW DIRECTORY
# ============================================================

print()
print("2. Testing raw directory...")

directory_client = (
    filesystem_client.get_directory_client(
        RAW_DIRECTORY
    )
)

directory_client.get_directory_properties()

print(
    f"✓ Directory exists: "
    f"{RAW_DIRECTORY}/"
)


# ============================================================
# TEST FILE UPLOAD
# ============================================================

print()
print("3. Testing file upload...")

filename = (
    f"_test_{uuid.uuid4().hex[:8]}.json"
)

file_client = (
    directory_client.get_file_client(
        filename
    )
)

test_data = {
    "test": True,
    "message": "ADLS connection test",
    "created_at": datetime.now(
        timezone.utc
    ).isoformat(),
}

file_client.upload_data(
    json.dumps(test_data, indent=2).encode(
        "utf-8"
    ),
    overwrite=False,
)

print(
    f"✓ File uploaded successfully:"
    f" {RAW_DIRECTORY}/{filename}"
)


# ============================================================
# DELETE TEST FILE
# ============================================================

print()
print("4. Cleaning up test file...")

file_client.delete_file()

print("✓ Test file deleted")


# ============================================================
# SUCCESS
# ============================================================

print()
print("=" * 65)
print("             ✓ ALL ADLS TESTS PASSED")
print("=" * 65)
print()
```

Run:

```bash
python test_adls.py
```

### We want to see:

```text
=================================================================
                 ADLS GEN2 TEST
=================================================================

Filesystem : taxi-data
Directory  : raw/

1. Testing filesystem...
✓ Filesystem exists

2. Testing raw directory...
✓ Directory exists: raw/

3. Testing file upload...
✓ File uploaded successfully: raw/_test_a81f32c1.json

4. Cleaning up test file...
✓ Test file deleted

=================================================================
             ✓ ALL ADLS TESTS PASSED
=================================================================
```

**Only after this test passes should you start `eventhub_to_raw.py`.**

---

### One more important observation

Your shutdown is working correctly up to the ADLS upload. When you press `Ctrl+C`, the application attempts to flush the remaining events, but that upload also fails with `PathNotFound`. 

So I **would not rewrite your Event Hub consumer**. The Event Hub side is doing its job.

The troubleshooting order should be:

```text
.env
  ↓
Storage account
  ↓
Filesystem/container name
  ↓
raw/ directory
  ↓
Python ADLS test
  ↓
Event Hub → ADLS consumer
```

If you run **`test_adls.py`** and send me its output, we can identify the exact problem immediately.
 
 --------------------------------------------------------

 Yes. I see a **very likely cause**, and we can fix it without changing your Event Hub architecture.

Your new log confirms the same issue: Event Hub consumption works, but every ADLS upload returns `PathNotFound`. 

### The most likely problem

Your code assumes that the ADLS directory:

```text
raw/
```

exists inside the filesystem/container:

```text
STORAGE_FILE_SYSTEM
```

But there is an important distinction:

```text
Storage Account
      │
      └── ADLS Gen2 filesystem/container
                │
                └── raw/
```

Your `STORAGE_FILE_SYSTEM` must be the **filesystem/container name**, not the storage-account name.

For example, if Azure Storage Explorer looks like:

```text
aminestorages
└── taxi-data
    ├── raw
    ├── processed
    └── analytics
```

then your `.env` must contain:

```env
STORAGE_FILE_SYSTEM=taxi-data
```

NOT:

```env
STORAGE_FILE_SYSTEM=aminestorages
```

---

## 1. First, don't run the consumer

Stop it for now:

```bash
Ctrl+C
```

Otherwise it will continue accumulating events in memory because the ADLS writes are failing.

Your log shows exactly this behavior: the buffer keeps the events after a failed upload. 

---

## 2. Check your Azure filesystem

Run:

```bash
az storage fs list \
  --account-name YOUR_STORAGE_ACCOUNT \
  --auth-mode login \
  -o table
```

You should see something like:

```text
Name
----------------
taxi-data
```

or:

```text
Name
----------------
lab-files
```

Whatever appears under `Name` is the value that should go into:

```env
STORAGE_FILE_SYSTEM=...
```

---

## 3. Check whether `raw` exists

Then run:

```bash
az storage fs directory list \
  --account-name YOUR_STORAGE_ACCOUNT \
  --file-system YOUR_FILE_SYSTEM \
  --auth-mode login \
  -o table
```

You should see:

```text
Name
----
raw
```

If `raw` doesn't exist, create it:

```bash
az storage fs directory create \
  --account-name YOUR_STORAGE_ACCOUNT \
  --file-system YOUR_FILE_SYSTEM \
  --name raw \
  --auth-mode login
```

Then verify:

```bash
az storage fs directory show \
  --account-name YOUR_STORAGE_ACCOUNT \
  --file-system YOUR_FILE_SYSTEM \
  --name raw \
  --auth-mode login
```

---

## 4. I would also modify your Python startup test

This is important.

Your current program apparently verifies the **filesystem**, but your actual failure is specifically at:

```text
raw/<filename>
```

So let's make the program test **the exact `raw/` directory before Event Hub starts**.

Add this after creating `directory_client`:

```python
# ============================================================
# VERIFY RAW DIRECTORY
# ============================================================

print()
print("Checking raw directory...")

directory_client = file_system_client.get_directory_client(
    RAW_DIRECTORY
)

try:
    directory_client.get_directory_properties()

    print(
        f"✓ Raw directory exists: "
        f"{STORAGE_FILE_SYSTEM}/{RAW_DIRECTORY}/"
    )

except Exception as error:
    print()
    print("❌ RAW DIRECTORY NOT FOUND")
    print("-" * 65)
    print(
        f"Filesystem : {STORAGE_FILE_SYSTEM}"
    )
    print(
        f"Directory  : {RAW_DIRECTORY}"
    )
    print("-" * 65)
    print(error)
    print("-" * 65)

    raise
```

Then your application will fail **immediately** if `raw/` is wrong instead of waiting until 20+ events arrive.

---

# 5. Even better: test the exact upload

I recommend making a small separate test.

Create:

```text
test_adls.py
```

with:

```python
import json
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

STORAGE_CONNECTION_STRING = os.getenv(
    "STORAGE_CONNECTION_STRING"
)

STORAGE_FILE_SYSTEM = os.getenv(
    "STORAGE_FILE_SYSTEM"
)

RAW_DIRECTORY = "raw"


# ============================================================
# VALIDATION
# ============================================================

if not STORAGE_CONNECTION_STRING:
    raise ValueError(
        "STORAGE_CONNECTION_STRING is missing"
    )

if not STORAGE_FILE_SYSTEM:
    raise ValueError(
        "STORAGE_FILE_SYSTEM is missing"
    )


# ============================================================
# CONNECT
# ============================================================

print()
print("=" * 65)
print("                 ADLS GEN2 TEST")
print("=" * 65)

print(
    f"Filesystem : {STORAGE_FILE_SYSTEM}"
)

print(
    f"Directory  : {RAW_DIRECTORY}/"
)

service_client = (
    DataLakeServiceClient.from_connection_string(
        STORAGE_CONNECTION_STRING
    )
)

filesystem_client = (
    service_client.get_file_system_client(
        STORAGE_FILE_SYSTEM
    )
)


# ============================================================
# TEST FILESYSTEM
# ============================================================

print()
print("1. Testing filesystem...")

filesystem_client.get_file_system_properties()

print("✓ Filesystem exists")


# ============================================================
# TEST RAW DIRECTORY
# ============================================================

print()
print("2. Testing raw directory...")

directory_client = (
    filesystem_client.get_directory_client(
        RAW_DIRECTORY
    )
)

directory_client.get_directory_properties()

print(
    f"✓ Directory exists: "
    f"{RAW_DIRECTORY}/"
)


# ============================================================
# TEST FILE UPLOAD
# ============================================================

print()
print("3. Testing file upload...")

filename = (
    f"_test_{uuid.uuid4().hex[:8]}.json"
)

file_client = (
    directory_client.get_file_client(
        filename
    )
)

test_data = {
    "test": True,
    "message": "ADLS connection test",
    "created_at": datetime.now(
        timezone.utc
    ).isoformat(),
}

file_client.upload_data(
    json.dumps(test_data, indent=2).encode(
        "utf-8"
    ),
    overwrite=False,
)

print(
    f"✓ File uploaded successfully:"
    f" {RAW_DIRECTORY}/{filename}"
)


# ============================================================
# DELETE TEST FILE
# ============================================================

print()
print("4. Cleaning up test file...")

file_client.delete_file()

print("✓ Test file deleted")


# ============================================================
# SUCCESS
# ============================================================

print()
print("=" * 65)
print("             ✓ ALL ADLS TESTS PASSED")
print("=" * 65)
print()
```

Run:

```bash
python test_adls.py
```

### We want to see:

```text
=================================================================
                 ADLS GEN2 TEST
=================================================================

Filesystem : taxi-data
Directory  : raw/

1. Testing filesystem...
✓ Filesystem exists

2. Testing raw directory...
✓ Directory exists: raw/

3. Testing file upload...
✓ File uploaded successfully: raw/_test_a81f32c1.json

4. Cleaning up test file...
✓ Test file deleted

=================================================================
             ✓ ALL ADLS TESTS PASSED
=================================================================
```

**Only after this test passes should you start `eventhub_to_raw.py`.**

---

### One more important observation

Your shutdown is working correctly up to the ADLS upload. When you press `Ctrl+C`, the application attempts to flush the remaining events, but that upload also fails with `PathNotFound`. 

So I **would not rewrite your Event Hub consumer**. The Event Hub side is doing its job.

The troubleshooting order should be:

```text
.env
  ↓
Storage account
  ↓
Filesystem/container name
  ↓
raw/ directory
  ↓
Python ADLS test
  ↓
Event Hub → ADLS consumer
```

If you run **`test_adls.py`** and send me its output, we can identify the exact problem immediately.
 

 also  i remove the `the container` and i create a new one with the name `taxidatalake` and i put it in the `.env` file and now it works fine.


 Ah, **that explains the situation very well**. Your screenshot shows that your new ADLS Gen2 filesystem/container is:

```text
taxidatalake
├── curated/
├── processed/
└── raw/
```

So your architecture is actually correct. The important thing now is to make sure your Python `.env` points to **`taxidatalake`**, not the old deleted container.

### 1. Change your `.env`

You should have:

```env
STORAGE_FILE_SYSTEM=taxidatalake
```

Not:

```env
STORAGE_FILE_SYSTEM=datalake
```

and not the storage-account name.

Your structure should be:

```text
Storage Account
      │
      └── taxidatalake
            ├── raw
            ├── processed
            └── curated
```

### 2. Test it directly

Before running your Event Hub consumer, run this:

```bash
python test_adls.py
```

If you don't have the test file yet, you can use this **very small test**:

```python
import os
from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient

load_dotenv()

connection_string = os.getenv("STORAGE_CONNECTION_STRING")
filesystem_name = os.getenv("STORAGE_FILE_SYSTEM")

print("=" * 60)
print("ADLS CONNECTION TEST")
print("=" * 60)

print(f"Filesystem: {filesystem_name}")

service_client = DataLakeServiceClient.from_connection_string(
    connection_string
)

filesystem_client = service_client.get_file_system_client(
    filesystem_name
)

# Test filesystem
filesystem_client.get_file_system_properties()
print("✓ Filesystem exists")

# Test raw directory
directory_client = filesystem_client.get_directory_client("raw")

directory_client.get_directory_properties()
print("✓ raw/ directory exists")

print("=" * 60)
print("✓ ADLS TEST PASSED")
print("=" * 60)
```

Then:

```bash
python test_adls.py
```

You want:

```text
============================================================
ADLS CONNECTION TEST
============================================================
Filesystem: taxidatalake
✓ Filesystem exists
✓ raw/ directory exists
============================================================
✓ ADLS TEST PASSED
============================================================
```

### 3. Then test an actual file upload

This is the **most important test**, because your previous error happened specifically during `upload_data()`.

Add:

```python
file_client = directory_client.get_file_client(
    "test.json"
)

file_client.upload_data(
    b'{"test": true}',
    overwrite=True
)

print("✓ File upload successful")
```

Then check Azure Storage Explorer:

```text
taxidatalake
└── raw
      └── test.json
```

If that works, **your ADLS problem is solved**.

---

### 4. Then start your Event Hub consumer

After the test succeeds:

```bash
python evenhub_to_raw.py
```

You should then get something like:

```text
EVENT RECEIVED
Partition : 0
Offset    : ...
Event ID  : evt_xxxxx
Buffer    : 20

FLUSHING PARTITION 0
Reason : batch size reached
Events : 20

Uploading partition 0...
Events : 20
File : raw/taxi_events_....json

=============================================================
✓ BATCH SAVED TO ADLS
=============================================================
Partition : 0
Events    : 20
File      : raw/taxi_events_....json
=============================================================
```

And in Azure:

```text
taxidatalake
│
├── curated/
│
├── processed/
│
└── raw/
      ├── taxi_events_20260918_....json
      ├── taxi_events_20260918_....json
      └── ...
```

### ⚠️ One thing I want you to check

Because you **deleted the old filesystem and created a new one**, your old `STORAGE_CONNECTION_STRING` may still point to the **same storage account**—which is fine. A connection string identifies the storage account, **not the filesystem**.

So the critical `.env` combination is:

```env
STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=...
STORAGE_FILE_SYSTEM=taxidatalake
```

The screenshot confirms `taxidatalake` and `raw/` exist, so **I would first change/check `STORAGE_FILE_SYSTEM=taxidatalake` and run the direct test before changing your consumer code.**


Exactly. Since your test now shows:

```text
Filesystem: taxidatalake
✓ Filesystem exists
✓ raw/ directory exists
✓ ADLS TEST PASSED
```

the ADLS side is working. The important correction is that your consumer must use:

```env
STORAGE_FILE_SYSTEM=taxidatalake
```

Your Event Hub → ADLS consumer can now be used. I also kept the **batch = 20**, **timer = 60 seconds**, **partition buffers**, and **final flush** logic from your uploaded code. 

## `eventhub_to_raw.py`

```python
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
# CONFIGURATION
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

# IMPORTANT:
# This is the ADLS Gen2 filesystem/container name.
STORAGE_FILE_SYSTEM = os.getenv(
    "STORAGE_FILE_SYSTEM"
)

CONSUMER_GROUP = "$Default"

RAW_DIRECTORY = "raw"

# Save when a partition reaches 20 events
BATCH_SIZE = 20

# Save when events have been waiting for 60 seconds
FLUSH_INTERVAL_SECONDS = 60

# Timer checks every second
TIMER_CHECK_INTERVAL = 1


# ============================================================
# VALIDATE ENVIRONMENT
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

# Example:
#
# {
#     "0": [event1, event2, ...],
#     "1": [event1, event2, ...]
# }
#
event_buffers = {}


# Time when the first event entered each partition buffer
last_flush_times = {}


# Protect shared state
buffer_lock = threading.Lock()


# Partitions currently being flushed
flushing_partitions = set()


# Used to stop timer thread
stop_timer_event = threading.Event()


# ============================================================
# CONNECT TO ADLS GEN2
# ============================================================

print()
print("=" * 65)
print("          EVENT HUB → ADLS GEN2 RAW")
print("=" * 65)

print()
print("Connecting to ADLS Gen2...")

try:

    service_client = (
        DataLakeServiceClient.from_connection_string(
            STORAGE_CONNECTION_STRING
        )
    )

    file_system_client = (
        service_client.get_file_system_client(
            STORAGE_FILE_SYSTEM
        )
    )

    # Verify filesystem
    file_system_client.get_file_system_properties()

    print(
        f"✓ Filesystem connected: "
        f"{STORAGE_FILE_SYSTEM}"
    )

except Exception as error:

    print()
    print("❌ ADLS CONNECTION FAILED")
    print("-" * 65)
    print(error)
    print("-" * 65)

    raise


# ============================================================
# VERIFY / CREATE RAW DIRECTORY
# ============================================================

print()
print("Checking raw directory...")

directory_client = (
    file_system_client.get_directory_client(
        RAW_DIRECTORY
    )
)

try:

    directory_client.get_directory_properties()

    print(
        f"✓ Raw directory exists: "
        f"{RAW_DIRECTORY}/"
    )

except Exception:

    print(
        f"Raw directory does not exist."
    )

    print(
        f"Creating {RAW_DIRECTORY}/ ..."
    )

    directory_client.create_directory()

    print(
        f"✓ Raw directory created: "
        f"{RAW_DIRECTORY}/"
    )


# ============================================================
# TEST ADLS WRITE
# ============================================================

print()
print("Testing ADLS write...")

test_filename = (
    f"_consumer_test_"
    f"{uuid.uuid4().hex[:8]}.json"
)

try:

    test_file_client = (
        directory_client.get_file_client(
            test_filename
        )
    )

    test_data = {
        "test": True,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    test_file_client.upload_data(
        json.dumps(test_data).encode("utf-8"),
        overwrite=True,
    )

    test_file_client.delete_file()

    print("✓ ADLS write test passed")

except Exception as error:

    print()
    print("❌ ADLS WRITE TEST FAILED")
    print("-" * 65)
    print(error)
    print("-" * 65)

    raise


# ============================================================
# SAVE BATCH TO ADLS
# ============================================================

def save_batch_to_raw(events, partition_id):

    if not events:
        return False

    try:

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        # ----------------------------------------------------
        # Unique ID
        # ----------------------------------------------------

        unique_id = uuid.uuid4().hex[:8]

        # ----------------------------------------------------
        # Filename
        # ----------------------------------------------------

        file_name = (
            f"taxi_events_"
            f"{timestamp}_"
            f"partition_{partition_id}_"
            f"{unique_id}.json"
        )

        # ----------------------------------------------------
        # Get raw directory
        # ----------------------------------------------------

        directory_client = (
            file_system_client.get_directory_client(
                RAW_DIRECTORY
            )
        )

        # ----------------------------------------------------
        # Create file client
        # ----------------------------------------------------

        file_client = (
            directory_client.get_file_client(
                file_name
            )
        )

        # ----------------------------------------------------
        # Convert events to JSON
        # ----------------------------------------------------

        json_data = json.dumps(
            events,
            indent=2
        )

        # ----------------------------------------------------
        # Upload
        # ----------------------------------------------------

        print()
        print("-" * 65)
        print("UPLOADING BATCH")
        print("-" * 65)

        print(
            f"Partition : {partition_id}"
        )

        print(
            f"Events    : {len(events)}"
        )

        print(
            f"File      : "
            f"{RAW_DIRECTORY}/{file_name}"
        )

        file_client.upload_data(
            json_data.encode("utf-8"),
            overwrite=False,
        )

        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        print()
        print("=" * 65)
        print("✓ BATCH SAVED TO ADLS")
        print("=" * 65)

        print(
            f"Partition : {partition_id}"
        )

        print(
            f"Events    : {len(events)}"
        )

        print(
            f"Location  : "
            f"{RAW_DIRECTORY}/{file_name}"
        )

        print("=" * 65)

        return True

    except Exception as error:

        print()
        print("=" * 65)
        print(
            f"❌ ADLS UPLOAD FAILED"
        )
        print("=" * 65)

        print(
            f"Partition : {partition_id}"
        )

        print(
            f"Events    : {len(events)}"
        )

        print(
            f"Error     : {error}"
        )

        print("=" * 65)

        return False


# ============================================================
# FLUSH PARTITION
# ============================================================

def flush_partition(partition_id, reason):

    # --------------------------------------------------------
    # Get events safely
    # --------------------------------------------------------

    with buffer_lock:

        if partition_id not in event_buffers:
            return

        if not event_buffers[partition_id]:
            return

        # Prevent duplicate flush
        if partition_id in flushing_partitions:

            print(
                f"Partition {partition_id} "
                f"is already being flushed."
            )

            return

        # Mark as flushing
        flushing_partitions.add(
            partition_id
        )

        # Copy current events
        events_to_save = (
            event_buffers[
                partition_id
            ].copy()
        )

    # --------------------------------------------------------
    # Upload outside the lock
    # --------------------------------------------------------

    print()
    print("-" * 65)
    print(
        f"FLUSHING PARTITION "
        f"{partition_id}"
    )
    print(
        f"Reason : {reason}"
    )
    print(
        f"Events : {len(events_to_save)}"
    )
    print("-" * 65)

    success = save_batch_to_raw(
        events_to_save,
        partition_id
    )

    # --------------------------------------------------------
    # Process result
    # --------------------------------------------------------

    with buffer_lock:

        if success:

            current_buffer = (
                event_buffers[
                    partition_id
                ]
            )

            number_saved = len(
                events_to_save
            )

            # Remove only events that were uploaded
            del current_buffer[
                :number_saved
            ]

            # Reset timer
            if current_buffer:

                last_flush_times[
                    partition_id
                ] = time.time()

            else:

                last_flush_times.pop(
                    partition_id,
                    None
                )

            print(
                f"✓ Partition "
                f"{partition_id} "
                f"flushed successfully."
            )

        else:

            print(
                f"❌ Partition "
                f"{partition_id} "
                f"was NOT flushed."
            )

            print(
                "Events remain in buffer."
            )

        # Release flushing flag
        flushing_partitions.discard(
            partition_id
        )


# ============================================================
# TIMER WORKER
# ============================================================

def timer_flush_worker():

    print()
    print("✓ Timer worker started.")

    print(
        f"  Check interval : "
        f"{TIMER_CHECK_INTERVAL}s"
    )

    print(
        f"  Flush interval : "
        f"{FLUSH_INTERVAL_SECONDS}s"
    )

    while not stop_timer_event.is_set():

        # Wait one second
        stop_timer_event.wait(
            TIMER_CHECK_INTERVAL
        )

        if stop_timer_event.is_set():
            break

        current_time = time.time()

        partitions_to_flush = []

        # ----------------------------------------------------
        # Find partitions requiring flush
        # ----------------------------------------------------

        with buffer_lock:

            for partition_id in list(
                event_buffers.keys()
            ):

                buffer = (
                    event_buffers[
                        partition_id
                    ]
                )

                if not buffer:
                    continue

                if (
                    partition_id
                    in flushing_partitions
                ):
                    continue

                last_flush = (
                    last_flush_times.get(
                        partition_id,
                        current_time
                    )
                )

                elapsed = (
                    current_time
                    - last_flush
                )

                if (
                    elapsed
                    >= FLUSH_INTERVAL_SECONDS
                ):

                    partitions_to_flush.append(
                        partition_id
                    )

        # ----------------------------------------------------
        # Flush outside lock
        # ----------------------------------------------------

        for partition_id in (
            partitions_to_flush
        ):

            flush_partition(
                partition_id,
                "60-second timer"
            )

    print(
        "✓ Timer worker stopped."
    )


# ============================================================
# EVENT CALLBACK
# ============================================================

def on_event(
    partition_context,
    event
):

    if event is None:
        return

    partition_id = (
        partition_context.partition_id
    )

    try:

        # ----------------------------------------------------
        # Initialize partition buffer
        # ----------------------------------------------------

        with buffer_lock:

            if (
                partition_id
                not in event_buffers
            ):

                event_buffers[
                    partition_id
                ] = []

                last_flush_times[
                    partition_id
                ] = time.time()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        event_data = json.loads(
            event.body_as_str()
        )

        # ----------------------------------------------------
        # Add ingestion metadata
        # ----------------------------------------------------

        event_data[
            "ingested_at"
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        event_data[
            "eventhub_partition"
        ] = partition_id

        event_data[
            "eventhub_offset"
        ] = event.offset

        # ----------------------------------------------------
        # Add to buffer
        # ----------------------------------------------------

        with buffer_lock:

            event_buffers[
                partition_id
            ].append(
                event_data
            )

            buffer_size = len(
                event_buffers[
                    partition_id
                ]
            )

        # ----------------------------------------------------
        # Display event
        # ----------------------------------------------------

        print()
        print("-" * 65)
        print("EVENT RECEIVED")
        print("-" * 65)

        print(
            f"Partition : {partition_id}"
        )

        print(
            f"Offset    : {event.offset}"
        )

        print(
            f"Event ID  : "
            f"{event_data.get('event_id')}"
        )

        print(
            f"Buffer    : {buffer_size}"
        )

        print("-" * 65)

        # ----------------------------------------------------
        # Batch flush
        # ----------------------------------------------------

        if buffer_size >= BATCH_SIZE:

            flush_partition(
                partition_id,
                "batch size reached"
            )

    except json.JSONDecodeError as error:

        print(
            f"❌ Invalid JSON: {error}"
        )

    except Exception as error:

        print(
            f"❌ Error processing event: "
            f"{error}"
        )


# ============================================================
# ERROR CALLBACK
# ============================================================

def on_error(
    partition_context,
    error
):

    if partition_context:

        print(
            f"❌ Consumer error "
            f"(partition "
            f"{partition_context.partition_id}): "
            f"{error}"
        )

    else:

        print(
            f"❌ Consumer error: "
            f"{error}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Startup information
    # --------------------------------------------------------

    print()
    print("=" * 65)
    print("       EVENT HUB → ADLS GEN2 RAW CONSUMER")
    print("=" * 65)

    print(
        f"Event Hub       : "
        f"{EVENT_HUB_NAME}"
    )

    print(
        f"Consumer Group  : "
        f"{CONSUMER_GROUP}"
    )

    print(
        f"Filesystem      : "
        f"{STORAGE_FILE_SYSTEM}"
    )

    print(
        f"Directory       : "
        f"{RAW_DIRECTORY}/"
    )

    print(
        f"Batch Size      : "
        f"{BATCH_SIZE}"
    )

    print(
        f"Flush Interval  : "
        f"{FLUSH_INTERVAL_SECONDS}s"
    )

    print("=" * 65)

    # --------------------------------------------------------
    # Start timer
    # --------------------------------------------------------

    timer_thread = threading.Thread(
        target=timer_flush_worker,
        daemon=True
    )

    timer_thread.start()

    # --------------------------------------------------------
    # Create Event Hub consumer
    # --------------------------------------------------------

    consumer = (
        EventHubConsumerClient
        .from_connection_string(
            conn_str=EVENT_HUB_CONNECTION_STRING,
            consumer_group=CONSUMER_GROUP,
            eventhub_name=EVENT_HUB_NAME,
        )
    )

    # --------------------------------------------------------
    # Start consumer
    # --------------------------------------------------------

    try:

        with consumer:

            print()
            print("✓ Consumer started.")
            print("✓ Waiting for events...")
            print()

            consumer.receive(
                on_event=on_event,
                on_error=on_error,

                # Read from the earliest available
                # Event Hub position.
                starting_position="-1",
            )

    except KeyboardInterrupt:

        print()
        print("=" * 65)
        print("              CONSUMER STOPPED")
        print("=" * 65)

    finally:

        # ----------------------------------------------------
        # Stop timer
        # ----------------------------------------------------

        stop_timer_event.set()

        timer_thread.join(
            timeout=5
        )

        # ----------------------------------------------------
        # Final flush
        # ----------------------------------------------------

        with buffer_lock:

            remaining_partitions = [
                partition_id
                for partition_id, events
                in event_buffers.items()
                if events
            ]

        for partition_id in (
            remaining_partitions
        ):

            flush_partition(
                partition_id,
                "consumer shutdown"
            )

        print()
        print(
            "✓ Consumer connection closed."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
```

### Your `.env` must now contain

```env
EVENT_HUB_CONNECTION_STRING=your_event_hub_connection_string
EVENT_HUB_NAME=your_event_hub_name

STORAGE_CONNECTION_STRING=your_storage_connection_string
STORAGE_FILE_SYSTEM=taxidatalake
```

### Then run

```bash
python eventhub_to_raw.py
```

You should see:

```text
=================================================================
       EVENT HUB → ADLS GEN2 RAW CONSUMER
=================================================================
Event Hub       : ...
Consumer Group  : $Default
Filesystem      : taxidatalake
Directory       : raw/
Batch Size      : 20
Flush Interval  : 60s
=================================================================

✓ Timer worker started.
✓ Consumer started.
✓ Waiting for events...
```

Then when 20 events arrive:

```text
FLUSHING PARTITION 0
Reason : batch size reached
Events : 20

UPLOADING BATCH
Partition : 0
Events    : 20
File      : raw/taxi_events_...json

=================================================================
✓ BATCH SAVED TO ADLS
=================================================================
```

And Azure should show:

```text
taxidatalake
├── curated/
├── processed/
└── raw/
    ├── taxi_events_....json
    ├── taxi_events_....json
    └── ...
```

**One important note:** this version still uses `starting_position="-1"`, as your current code does.  That means if you restart the consumer without checkpointing, Event Hub can replay the available events from the beginning rather than only continuing from the last successfully processed event. For your next step, I recommend adding **Blob Checkpoint Store**, so your RAW ingestion becomes a proper production-style pipeline:

```text
Producer
   ↓
Event Hub
   ↓
Consumer
   ↓
Checkpoint Store
   ↓
ADLS Gen2 / raw/
```


### still the same error 

Good — **this test is very useful**. It tells us something important:

* `create_file()` ✅ works
* `append_data()` ✅ works
* The failure is only because your installed Azure SDK expects an `offset` argument for `flush_data()`.
* So this is **not an ADLS path problem** anymore.

Microsoft's current Python example uses `file.flush_data(len(data))`, i.e. the final file position as the required offset. ([Microsoft Learn][1])

### Fix `t.py`

You currently have something like:

```python
file_client.flush_data(
    position=data_size
)
```

Change it to:

```python
file_client.flush_data(data_size)
```

So the complete upload sequence should be:

```python
print("\n1. Creating file...")
file_client.create_file()
print("✓ File created")

print("\n2. Appending data...")
file_client.append_data(
    data=data,
    offset=0,
    length=data_size
)
print("✓ Data appended")

print("\n3. Flushing data...")
file_client.flush_data(data_size)
print("✓ Data flushed")
```

The official Microsoft example follows exactly this pattern:

```python
file.create_file()
file.append_data(data, offset=0, length=len(data))
file.flush_data(len(data))
```

([Microsoft Learn][1])

### What this means for our investigation

Your test has now narrowed the problem considerably:

```text
ADLS filesystem       ✅
raw/ directory        ✅
create_file()         ✅
append_data()         ✅
flush_data()          ❌ only because of Python argument syntax
```

So **20,512 bytes / 70 events is not failing at append**. That's actually very good news.

Run:

```bash
python t.py
```

again after changing:

```python
file_client.flush_data(data_size)
```

If you get:

```text
✓ File created
✓ Data appended
✓ Data flushed

=================================================================
✓ REALISTIC BATCH TEST PASSED
=================================================================
```

then we have essentially proven that **ADLS can successfully store a realistic 70-event batch**.

At that point, the next thing to fix is your consumer's `save_batch_to_raw()` function, because the consumer currently uses:

```python
file_client.upload_data(...)
```

instead of the explicit:

```text
create_file()
      ↓
append_data()
      ↓
flush_data()
```

The explicit method is also the pattern documented by Microsoft for Data Lake file uploads. ([Microsoft Learn][1])

**Run the corrected `t.py` first and send me the output.** Then we can determine the actual remaining cause without guessing.

[1]: https://learn.microsoft.com/en-us/python/api/overview/azure/storage-file-datalake-readme?view=azure-python&utm_source=chatgpt.com "Azure DataLake service client library for Python | Microsoft Learn"


Yes. Replace your `t.py` completely with this corrected version:

```python
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
```

Then run:

```bash
python t.py
```

### The important correction

Your previous code had:

```python
file_client.flush_data(
    position=data_size
)
```

Your installed Azure SDK expects:

```python
file_client.flush_data(data_size)
```

So the complete ADLS operation is now:

```text
create_file()
      ↓
append_data(...)
      ↓
flush_data(data_size)
      ↓
JSON file completed in ADLS
```

If this test passes, **do not modify anything else yet**. Send me the output. Then we'll fix your Event Hub consumer using this exact upload mechanism and investigate why the original `upload_data()` was producing `PathNotFound`.


Exactly. Your `t.py` test **returns a successful result**. It proves that ADLS can handle a realistic batch.

### What `t.py` proved

Your test uploaded:

```text
70 events
24,233 bytes
```

And every operation succeeded:

```text
1. create_file()    ✓
2. append_data()    ✓
3. flush_data()     ✓
```

So we can now eliminate these as the cause:

| Component                 | Result    |
| ------------------------- | --------- |
| Storage connection        | ✅ Working |
| `taxidatalake` filesystem | ✅ Working |
| `raw/` directory          | ✅ Working |
| File creation             | ✅ Working |
| 24 KB batch upload        | ✅ Working |
| `append_data()`           | ✅ Working |
| `flush_data()`            | ✅ Working |

### So where is the hidden problem?

The important difference is:

**Your test:**

```text
create_file()
      ↓
append_data()
      ↓
flush_data()
```

**Your Event Hub consumer:**

```text
file_client.upload_data(...)
```

And your consumer was getting:

```text
PathNotFound
```

while trying to upload the batch.

Therefore, the next step should **not** be changing your Azure Storage configuration.

We should change the consumer's `save_batch_to_raw()` to use the exact method that we just proved works:

```python
file_client.create_file()

file_client.append_data(
    data=data,
    offset=0,
    length=len(data)
)

file_client.flush_data(len(data))
```

There is also a second thing I want to check: **two Event Hub partitions can flush simultaneously**. So we'll make the ADLS upload operation safe when partition 0 and partition 1 flush at the same time.

### Your architecture will become

```text
                 Azure Event Hubs
                       │
              ┌────────┴────────┐
              │                 │
         Partition 0       Partition 1
              │                 │
              └────────┬────────┘
                       │
                  Python Consumer
                       │
                    Buffer
                       │
                 20 events OR
                 60 seconds
                       │
                       ▼
                 create_file()
                       │
                       ▼
                 append_data()
                       │
                       ▼
                 flush_data()
                       │
                       ▼
              ADLS Gen2 / raw/
```

**The good news:** your Azure infrastructure is working. We now have a reproducible upload method that succeeds with 70 events / 24 KB.

If you want, I can now give you the **complete corrected Event Hub consumer `.py`**, replacing the problematic `upload_data()` with this proven method and handling both partitions safely.


Yes. Since the realistic ADLS test passed, here is the **corrected consumer** using the proven `create_file → append_data → flush_data` method.

It also:

* consumes from Event Hubs
* keeps a separate buffer for each partition
* flushes at **20 events**
* flushes after **60 seconds**
* adds ingestion metadata
* writes JSON batches to `raw/`
* safely handles simultaneous partition flushes
* keeps failed events in the buffer so they are not silently lost
* flushes remaining events when you stop with `Ctrl+C`

```python
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
```

### `.env`

Make sure your `.env` contains these four variables:

```env
EVENT_HUB_CONNECTION_STRING=your_event_hub_connection_string
EVENT_HUB_NAME=your_event_hub_name

STORAGE_CONNECTION_STRING=your_storage_connection_string
STORAGE_FILE_SYSTEM=taxidatalake
```

Don't send me the actual connection strings.

### What changed from your old consumer

The important change is this:

```python
file_client.create_file()

file_client.append_data(
    data=data,
    offset=0,
    length=data_size
)

file_client.flush_data(
    data_size
)
```

instead of:

```python
file_client.upload_data(
    data,
    overwrite=False
)
```

And because your test proved this exact sequence works with **70 events / 24 KB**, we now have a solid basis for testing the real consumer.

Run:

```bash
python consumer.py
```

Then send me the output from the **first batch upload**. We should see something like:

```text
Event received | partition=0 | buffer=20/20

----------------------------------------------------------------------
FLUSHING PARTITION 0
Events : 20
Size   : xxxx bytes
File   : raw/taxi_events_...
----------------------------------------------------------------------

1. Creating file...
   ✓ File created
2. Appending data...
   ✓ Data appended
3. Flushing data...
   ✓ Data flushed

✓ SUCCESS: 20 events saved
```

That will let us verify the complete **Event Hub → Python Consumer → ADLS RAW** pipeline.

Yes — **the pipeline is working now.** 🎉

The problem was specifically the way the consumer was writing batches to ADLS.

### What was happening before

Your original consumer used:

```text
Event Hub
   ↓
Consumer
   ↓
Buffer
   ↓
upload_data()
   ↓
❌ PathNotFound
```

Even though:

* `taxidatalake` existed ✅
* `raw/` existed ✅
* connection worked ✅
* small ADLS test worked ✅

The `upload_data()` operation was failing during its internal file upload process.

### What we changed

We replaced:

```python
file_client.upload_data(...)
```

with the explicit ADLS operations:

```python
file_client.create_file()

file_client.append_data(
    data=data,
    offset=0,
    length=data_size
)

file_client.flush_data(data_size)
```

And your independent test proved that this works with:

```text
70 events
24,233 bytes
✓ create
✓ append
✓ flush
```

Then the real consumer also worked.

### So your current architecture is

```text
              TAXI PRODUCER
                    │
                    ▼
             Azure Event Hubs
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     Partition 0         Partition 1
          │                   │
          └─────────┬─────────┘
                    ▼
             Python Consumer
                    │
              JSON parsing
                    │
           Add ingestion metadata
                    │
                Buffer
                    │
            ┌───────┴───────┐
            │               │
       20 events         60 seconds
            │               │
            └───────┬───────┘
                    ▼
             create_file()
                    ↓
             append_data()
                    ↓
             flush_data()
                    ↓
              ADLS Gen2
                    │
                    ▼
              taxidatalake
                    │
                    ▼
                  raw/
```

### One important point

The old error:

```text
PathNotFound
```

was **not because your `raw/` directory was missing**. We proved that because your direct test and the new consumer can successfully create files there.

The exact underlying reason why `upload_data()` produced that error in your particular environment isn't fully established. What we **did establish experimentally** is that the explicit `create → append → flush` path works reliably, so that's the implementation we're using.

You now have the **RAW ingestion layer** working. The natural next step is:

```text
RAW
 ↓
Python processing
 ↓
PROCESSED
 ↓
ANALYTICS
 ↓
Power BI / analysis
```

So your Event Hub → ADLS RAW part is now ready.


