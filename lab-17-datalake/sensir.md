Yes — **this is a better approach for your Lab 21**, because it connects directly to your previous **Azure Event Hubs Lab 20** and creates a realistic data-engineering pipeline.

The architecture becomes:

```text
                    LAB 20
ESP32 / Application
        │
        ▼
 Azure Event Hubs
        │
        │ Python Consumer
        ▼
 ┌─────────────────────┐
 │ ADLS Gen2           │
 │ raw/                │
 │ sensor_events.json  │
 └─────────────────────┘
        │
        │ Python Processing App
        ▼
 ┌─────────────────────┐
 │ processed/          │
 │ cleaned_events.json │
 └─────────────────────┘
        │
        │ Python Analysis App
        ▼
 ┌─────────────────────┐
 │ curated/            │
 │ device_summary.json │
 └─────────────────────┘
```

This gives you a complete **Raw → Processed → Curated** architecture.

### What each Python application does

| Stage                   | Application          | Role                                        |
| ----------------------- | -------------------- | ------------------------------------------- |
| **Event Hubs → Raw**    | `eventhub_to_raw.py` | Consume events and save them in ADLS `raw/` |
| **Raw → Processed**     | `process_data.py`    | Clean and validate sensor data              |
| **Processed → Curated** | `analyze_data.py`    | Aggregate/analyze data by device            |
| **Curated**             | ADLS Gen2            | Store business-ready results                |

For example:

```text
datalake/
│
├── raw/
│   └── sensor_events.json
│
├── processed/
│   └── processed_events.json
│
└── curated/
    └── device_summary.json
```

This is also conceptually aligned with how ADLS Gen2 provides filesystem/directory organization, while Python can perform the processing before you later automate the workflow with Data Factory.

## The important part

We should **not redo everything from zero**.

We'll reuse your Lab 20:

```text
azure-eventhub-lab20/
│
├── producer.py
├── consumer.py
├── checkpoint_consumer.py
├── consumer_b.py
├── .env
└── .venv/
```

Then extend it for Lab 21:

```text
azure-eventhub-lab20/
│
├── producer.py
├── consumer.py
│
├── eventhub_to_raw.py       ← NEW
├── process_data.py          ← NEW
├── analyze_data.py          ← NEW
│
├── .env
├── .gitignore
└── .venv/
```

### The final real pipeline

```text
1. producer.py
       ↓
2. Azure Event Hubs
       ↓
3. eventhub_to_raw.py
       ↓
4. ADLS Gen2 /raw
       ↓
5. process_data.py
       ↓
6. ADLS Gen2 /processed
       ↓
7. analyze_data.py
       ↓
8. ADLS Gen2 /curated
```

And this is useful for your HPIS project too:

```text
ESP32
  ↓
Event Hubs
  ↓
Raw sensor data
  ↓
Cleaning
  ↓
Processed physiological data
  ↓
Aggregation / analysis
  ↓
Curated data
  ↓
BI / ML / Analytics
```

So let's do it **one step at a time**.

### Step 1 — Event Hubs → ADLS `raw/`

We'll modify the consumer you already have so that instead of simply doing:

```text
Event Hubs
    ↓
print(event)
```

it does:

```text
Event Hubs
    ↓
Python Consumer
    ↓
ADLS Gen2
    ↓
raw/sensor_events.json
```

**Do not modify `process_data.py` yet.** First we'll make sure the Event Hubs → Raw part works correctly.


Exactly. You caught an important missing piece. **The Event Hub consumer does not automatically know about your Data Lake.** The consumer needs credentials and the address of the ADLS Gen2 filesystem/directory where it should write the data.

Your architecture has **two separate connections**:

```text
                 CONNECTION 1
Producer ───────► Event Hubs
                    │
                    │ Consumer
                    ▼
                 CONNECTION 2
              ADLS Gen2 Storage
                    │
                    ▼
              datalake/raw/
```

### What we need for ADLS

Your storage account is:

```text
amineadlslab21
```

and your filesystem/container is:

```text
datalake
```

and the destination directory is:

```text
raw/
```

The ADLS Gen2 endpoint follows the storage-account pattern:

```text
https://<storage-account>.dfs.core.windows.net
```

So yours is:

```text
https://amineadlslab21.dfs.core.windows.net
```

The Python SDK can use `DataLakeServiceClient` to connect to this endpoint and work with files/directories.

### But we need authentication too

Instead of putting a storage account key directly into your code, I recommend using your **Azure CLI login**:

```bash
az login
```

and Python's:

```python
from azure.identity import AzureCliCredential
```

Then:

```text
Python Consumer
      │
      │ AzureCliCredential
      ▼
Azure
      │
      ▼
amineadlslab21
      │
      ▼
datalake/raw/
```

You will also need an Azure RBAC role allowing your user to write blob data, typically **Storage Blob Data Contributor**, on the storage account.

### So our consumer will actually be

```text
Event Hubs
    │
    │ EventHubConsumerClient
    ▼
Python
    │
    ├── AzureCliCredential
    │
    ▼
DataLakeServiceClient
    │
    ▼
amineadlslab21
    │
    ▼
datalake
    │
    ▼
raw/
    │
    ▼
sensor_events.json
```

So **yes, we should configure the ADLS connection before writing `eventhub_to_raw.py`**.

I suggest we do it in this order:

**Step 1:** Give your Azure account `Storage Blob Data Contributor` on `amineadlslab21`
**Step 2:** Test Python → ADLS connection
**Step 3:** Write `eventhub_to_raw.py`
**Step 4:** Run producer → Event Hubs → consumer → `raw/`
**Step 5:** Verify the file in Azure Portal.

Let's do **Step 1** first so we don't write code that cannot access your Data Lake.


You can get it directly from the Azure Portal.

### Step 1 — Open your storage account

In Azure Portal, go to:

**Storage accounts → `amineadlslab21`**

### Step 2 — Open Access keys

In the left menu, find:

**Security + networking → Access keys**

You should see:

```text
Storage account name: amineadlslab21

key1
  Key
  Connection string

key2
  Key
  Connection string
```

### Step 3 — Copy the connection string

Under **key1**, click **Show** next to the connection string, then copy the entire value.

It looks approximately like:

```text
DefaultEndpointsProtocol=https;AccountName=amineadlslab21;AccountKey=XXXXXXXXXXXXXXXX;EndpointSuffix=core.windows.net
```

**Do not send that value to me**, because it contains your storage account key.

### Step 4 — Put it in `.env`

In your project:

```bash
nano .env
```

Add:

```env
EVENT_HUB_CONNECTION_STRING=your_event_hub_connection_string
EVENT_HUB_NAME=sensor-events

STORAGE_CONNECTION_STRING=your_storage_connection_string
STORAGE_FILE_SYSTEM=datalake
```

For example:

```env
STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=amineadlslab21;AccountKey=XXXXXX;EndpointSuffix=core.windows.net
STORAGE_FILE_SYSTEM=datalake
```

Make sure `.env` is in `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
```

### Then our Python application can do

```text
Event Hubs
     ↓
Consumer
     ↓
STORAGE_CONNECTION_STRING
     ↓
amineadlslab21
     ↓
datalake
     ↓
raw/
```

Once you've added the connection string to `.env`, **don't paste it here**. Just tell me **"done"**, and I'll give you the complete `eventhub_to_raw.py`.
