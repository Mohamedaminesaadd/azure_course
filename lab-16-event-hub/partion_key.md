Great. We've completed the basic producer/consumer and verified the events in Azure Portal. **The next step is partition keys**, because this is where the partition concept becomes practical.

# Lab 20 — Step 5: Partition Keys

Right now, your producer sends events without specifying a key:

```text
Producer
   │
   ├── Event 1
   ├── Event 2
   ├── Event 3
   └── ...
          │
          ▼
     Azure Event Hubs
       ┌───────┬───────┐
       │ P0    │ P1    │
       └───────┴───────┘
```

When you specify a **partition key**, Event Hubs hashes the key and routes events with the same key to the same partition. This is useful when you need related events to remain ordered. ([Microsoft Learn][1])

---

## 1. Why do we need a partition key?

Imagine you have two ESP32 devices:

```text
ESP32-001
ESP32-002
```

Each sends measurements:

```text
ESP32-001 → HR 70
ESP32-001 → HR 72
ESP32-001 → HR 75

ESP32-002 → HR 80
ESP32-002 → HR 81
ESP32-002 → HR 79
```

We want the events belonging to the **same device** to stay in the same partition.

For example:

```text
Partition 0
├── ESP32-001 → HR 70
├── ESP32-001 → HR 72
└── ESP32-001 → HR 75

Partition 1
├── ESP32-002 → HR 80
├── ESP32-002 → HR 81
└── ESP32-002 → HR 79
```

The exact partition chosen for a key is determined by Event Hubs; **you don't manually decide that `ESP32-001` must be Partition 0**. ([Microsoft Learn][2])

---

# 2. Modify your producer

Open:

```bash
cd ~/azure-eventhub-lab20
nano producer.py
```

The important line is:

```python
batch = producer.create_batch(
    partition_key=device_id
)
```

The Python SDK supports specifying a `partition_key` when creating the batch. ([Microsoft Learn][2])

---

# 3. Run the producer

Keep your consumer running in Terminal 1.

In Terminal 2:

```bash
cd ~/azure-eventhub-lab20
source .venv/bin/activate
python producer.py
```

You should get:

```text
ESP32-001 → event 1
ESP32-001 → event 2
ESP32-001 → event 3
ESP32-001 → event 4
ESP32-001 → event 5
Sent 5 events for ESP32-001

ESP32-002 → event 1
ESP32-002 → event 2
ESP32-002 → event 3
ESP32-002 → event 4
ESP32-002 → event 5
Sent 5 events for ESP32-002
```

---

# 4. Look at your consumer

Your consumer should show events similar to:

```text
EVENT RECEIVED
Partition: 0
Event: {"device_id": "ESP32-001", ...}

EVENT RECEIVED
Partition: 0
Event: {"device_id": "ESP32-001", ...}

...

EVENT RECEIVED
Partition: 1
Event: {"device_id": "ESP32-002", ...}
```

The actual partition numbers may be the opposite:

```text
ESP32-001 → Partition 1
ESP32-002 → Partition 0
```

That's completely normal.

**The important property is consistency for the same key**, not which numerical partition it gets.

---

# 5. Verify it in Azure Portal

Go to:

**Event Hubs → `eh-amine-lab20` → `sensor-events` → Data Explorer → View events**

Choose:

```text
Partition ID:
All partition IDs

Consumer Group:
$Default

Event position:
Oldest position
```

Then **View events**.

You should find your JSON:

```json
{
    "device_id": "ESP32-001",
    "heart_rate": 70,
    "temperature": 25.0,
    ...
}
```

and:

```json
{
    "device_id": "ESP32-002",
    "heart_rate": 80,
    "temperature": 25.0,
    ...
}
```

Data Explorer supports viewing events by partition, consumer group, and event position. ([Microsoft Learn][3])

---

# 6. The key idea

This is the concept I want you to remember:

### Without partition key

```text
Events
   │
   ▼
Event Hubs
   │
   ├── P0
   └── P1
```

The service can distribute events across partitions.

### With partition key

```text
device_id = ESP32-001
              │
              ▼
         hash(key)
              │
              ▼
         Partition X

device_id = ESP32-001
              │
              ▼
         hash(key)
              │
              ▼
         Partition X
```

Therefore:

```text
Same key
   ↓
Same partition
   ↓
Ordered within that partition
```

Microsoft specifically documents that events sharing a partition key are stored together and delivered in order of arrival. ([Microsoft Learn][2])

---

# 7. Why this matters for your HPIS project

This is directly relevant to your wearable architecture.

You could use:

```text
partition_key = device_id
```

For example:

```text
ESP32-001 ──┐
            │
            ▼
       Event Hubs
            │
            ├── Partition 0
            │
ESP32-002 ──┤
            │
            └── Partition 1
```

Then the stream becomes:

```text
ESP32
  ↓
Sensor data
  ↓
Event Hubs
  ↓
Partitions
  ↓
Real-time processing
  ↓
Stress / ECG / activity analysis
```

This is exactly the type of architecture we'll build toward in **Lab 23**.

---
