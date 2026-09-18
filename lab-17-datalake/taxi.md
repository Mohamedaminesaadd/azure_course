If you mean an **event schema for a real-time taxi/ride-hailing application** using something like **Azure Event Hubs, Kafka, or another event-streaming system**, I would structure it around the lifecycle of a ride.

### 1. Core taxi event schema

A common envelope for **every event**:

```json
{
  "event_id": "evt_8f92a1",
  "event_type": "ride.requested",
  "event_version": "1.0",
  "timestamp": "2026-09-18T10:30:15.250Z",

  "source": {
    "service": "ride-service",
    "instance": "ride-service-01"
  },

  "ride": {
    "ride_id": "ride_12345",
    "passenger_id": "user_789",
    "driver_id": null
  },

  "location": {
    "latitude": 35.8256,
    "longitude": 10.63699
  },

  "data": {}
}
```

The important idea is that **`event_type` tells you what happened**, while **`data` contains the information specific to that event**.

---

## 2. Taxi application events

A complete ride lifecycle could look like:

```text
ride.requested
      ↓
driver.searching
      ↓
driver.assigned
      ↓
driver.arriving
      ↓
ride.started
      ↓
ride.location_updated
      ↓
ride.completed
      ↓
payment.completed
      ↓
ride.rated
```

You can also have:

```text
ride.cancelled
payment.failed
driver.cancelled
driver.offline
driver.online
```

---

## 3. `ride.requested`

When the passenger requests a taxi:

```json
{
  "event_id": "evt_001",
  "event_type": "ride.requested",
  "event_version": "1.0",
  "timestamp": "2026-09-18T10:30:15.250Z",

  "ride": {
    "ride_id": "ride_12345",
    "passenger_id": "user_789",
    "driver_id": null
  },

  "pickup": {
    "latitude": 35.8256,
    "longitude": 10.6369
  },

  "destination": {
    "latitude": 35.7643,
    "longitude": 10.8113
  },

  "ride_type": "standard",
  "estimated_distance_km": 8.5,
  "estimated_fare": 18.5
}
```

---

## 4. `driver.assigned`

When a driver accepts the ride:

```json
{
  "event_id": "evt_002",
  "event_type": "driver.assigned",
  "event_version": "1.0",
  "timestamp": "2026-09-18T10:31:02.100Z",

  "ride": {
    "ride_id": "ride_12345",
    "passenger_id": "user_789",
    "driver_id": "driver_456"
  },

  "driver": {
    "driver_id": "driver_456",
    "vehicle_id": "vehicle_123",
    "vehicle_type": "sedan"
  },

  "location": {
    "latitude": 35.8211,
    "longitude": 10.6321
  }
}
```

---

## 5. `driver.location_updated`

This is one of the most important **high-frequency events**.

For example, the driver's phone sends GPS data every few seconds:

```json
{
  "event_id": "evt_003",
  "event_type": "driver.location_updated",
  "event_version": "1.0",
  "timestamp": "2026-09-18T10:31:15.500Z",

  "driver": {
    "driver_id": "driver_456"
  },

  "ride": {
    "ride_id": "ride_12345"
  },

  "location": {
    "latitude": 35.8225,
    "longitude": 10.6342,
    "speed_kmh": 32.5,
    "heading": 145
  }
}
```

This event can be sent to:

```text
Taxi App
   ↓
Event Hubs / Kafka
   ↓
Stream Processing
   ↓
 ┌───────────────┬──────────────┬───────────────┐
 ↓               ↓              ↓
Live Map       Analytics      ETA calculation
```

---

## 6. `ride.started`

When the passenger gets into the taxi:

```json
{
  "event_id": "evt_004",
  "event_type": "ride.started",
  "event_version": "1.0",
  "timestamp": "2026-09-18T10:40:00Z",

  "ride": {
    "ride_id": "ride_12345",
    "passenger_id": "user_789",
    "driver_id": "driver_456"
  },

  "location": {
    "latitude": 35.8250,
    "longitude": 10.6375
  },

  "meter": {
    "start_distance_km": 0,
    "start_fare": 2.0
  }
}
```

---

## 7. `ride.completed`

When the passenger reaches the destination:

```json
{
  "event_id": "evt_005",
  "event_type": "ride.completed",
  "event_version": "1.0",
  "timestamp": "2026-09-18T11:02:35Z",

  "ride": {
    "ride_id": "ride_12345",
    "passenger_id": "user_789",
    "driver_id": "driver_456"
  },

  "trip": {
    "distance_km": 9.2,
    "duration_seconds": 1355,
    "fare": 21.5
  },

  "pickup": {
    "latitude": 35.8256,
    "longitude": 10.6369
  },

  "destination": {
    "latitude": 35.7643,
    "longitude": 10.8113
  }
}
```

---

## 8. `payment.completed`

```json
{
  "event_id": "evt_006",
  "event_type": "payment.completed",
  "event_version": "1.0",
  "timestamp": "2026-09-18T11:02:40Z",

  "ride": {
    "ride_id": "ride_12345",
    "passenger_id": "user_789",
    "driver_id": "driver_456"
  },

  "payment": {
    "payment_id": "payment_987",
    "amount": 21.5,
    "currency": "TND",
    "method": "card",
    "status": "completed"
  }
}
```

---

# 9. `ride.cancelled`

```json
{
  "event_id": "evt_007",
  "event_type": "ride.cancelled",
  "event_version": "1.0",
  "timestamp": "2026-09-18T11:05:00Z",

  "ride": {
    "ride_id": "ride_12345",
    "passenger_id": "user_789",
    "driver_id": "driver_456"
  },

  "cancellation": {
    "cancelled_by": "passenger",
    "reason": "changed_plan"
  }
}
```

---

# 10. `ride.rated`

After the ride:

```json
{
  "event_id": "evt_008",
  "event_type": "ride.rated",
  "event_version": "1.0",
  "timestamp": "2026-09-18T11:10:00Z",

  "ride": {
    "ride_id": "ride_12345",
    "passenger_id": "user_789",
    "driver_id": "driver_456"
  },

  "rating": {
    "score": 5,
    "comment": "Good driver"
  }
}
```

---

# 11. Driver availability events

You also need events that aren't necessarily associated with a ride.

### Driver online

```json
{
  "event_id": "evt_100",
  "event_type": "driver.online",
  "timestamp": "2026-09-18T09:00:00Z",

  "driver": {
    "driver_id": "driver_456"
  },

  "location": {
    "latitude": 35.8256,
    "longitude": 10.6369
  }
}
```

### Driver offline

```json
{
  "event_id": "evt_101",
  "event_type": "driver.offline",
  "timestamp": "2026-09-18T18:00:00Z",

  "driver": {
    "driver_id": "driver_456"
  }
}
```

---

# 12. Recommended Event Hub architecture

Since you're currently working with **Azure Event Hubs**, you can use this architecture:

```text
                   ┌─────────────────┐
                   │   Passenger App │
                   └────────┬────────┘
                            │
                     ride.requested
                            │
                            ▼
                  ┌───────────────────┐
                  │   Azure Event Hub │
                  │     taxi-events   │
                  └─────────┬─────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        Consumer 1      Consumer 2      Consumer 3
        Ride Service    Analytics       Monitoring
             │              │              │
             ▼              ▼              ▼
          Database      Data Lake       Dashboard
```

For higher volume, I'd separate the events into logical streams:

```text
taxi-rides
taxi-driver-location
taxi-payments
taxi-driver-status
taxi-ratings
```

For example:

```text
taxi-driver-location
```

could receive thousands of events per second:

```json
{
  "event_type": "driver.location_updated",
  "driver_id": "D123",
  "timestamp": "2026-09-18T10:31:15.500Z",
  "latitude": 35.8256,
  "longitude": 10.6369,
  "speed_kmh": 35.2
}
```

while:

```text
taxi-rides
```

contains lower-frequency business events such as:

```text
ride.requested
driver.assigned
ride.started
ride.completed
ride.cancelled
```

### The key concept

Don't design your schema around **tables** first. For an event-driven taxi application, think:

**Something happened → produce an event → multiple consumers react to it.**

For your Azure lab, this is a very realistic example because you can then take:

**Taxi App → Event Hubs → Raw Data Lake → Python Processing → Analytics Data → Power BI**

which is essentially the same **raw → processed → analytical** pipeline you've been building.


Yes. Since your taxi app needs to send a **`driver.location_updated` event every 10 seconds for 10 minutes**, the producer should:

* run for **10 minutes**
* send **1 event every 10 seconds**
* generate a new `event_id`
* update the timestamp automatically
* generate different GPS coordinates
* vary speed and heading
* keep the same driver/ride IDs, unless you want multiple drivers/rides

Here is the modified producer:



### What this will do

Your producer will generate approximately:

```text
10 minutes
   ↓
600 seconds
   ↓
1 event / 10 seconds
   ↓
≈ 60 events
```

The events will look like this:

**Event 1**

```json
{
  "event_id": "evt_a31f82c1",
  "event_type": "driver.location_updated",
  "event_version": "1.0",
  "timestamp": "2026-09-18T10:31:15.500000+00:00",
  "driver": {
    "driver_id": "driver_456"
  },
  "ride": {
    "ride_id": "ride_12345"
  },
  "location": {
    "latitude": 35.822731,
    "longitude": 10.634011,
    "speed_kmh": 42.31,
    "heading": 145
  }
}
```

10 seconds later:

```json
{
  "event_id": "evt_71bc92fa",
  "event_type": "driver.location_updated",
  "event_version": "1.0",
  "timestamp": "2026-09-18T10:31:25.500000+00:00",
  "driver": {
    "driver_id": "driver_456"
  },
  "ride": {
    "ride_id": "ride_12345"
  },
  "location": {
    "latitude": 35.823102,
    "longitude": 10.634422,
    "speed_kmh": 37.84,
    "heading": 161
  }
}
```

Then another event 10 seconds later, etc.

### Your complete pipeline

This fits directly into the Azure architecture you're building:

```text
                 TAXI APPLICATION
                       │
                       │ GPS event
                       ▼
              ┌──────────────────┐
              │ Python Producer  │
              │                  │
              │ Every 10 seconds │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Azure Event Hubs │
              │                  │
              │ taxi-events      │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Python Consumer  │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Raw Data Lake    │
              │                  │
              │ /raw/taxi/...    │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Python Processing│
              │                  │
              │ /processed/...   │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Analytics Data   │
              │                  │
              │ /analytics/...   │
              └────────┬─────────┘
                       │
                       ▼
                  Power BI
```

One important change from your old sensor producer is that **you no longer need hardcoded events**. The producer continuously creates realistic taxi-location events, which is much closer to how a real GPS-based application would behave.

Yes — for your architecture, **one JSON file containing all raw events for a processing batch** makes more sense than creating one file per event.

Your current code creates:

```text
raw/
├── event_20260918_103115_partition_0_offset_123.json
├── event_20260918_103125_partition_0_offset_124.json
├── event_20260918_103135_partition_0_offset_125.json
└── ...
```

For your taxi simulation (≈60 events / 10 minutes), I recommend instead:

```text
raw/
└── taxi_events_20260918_103000.json
```

containing:

```json
[
  {
    "event_id": "evt_abc123",
    "event_type": "driver.location_updated",
    "event_version": "1.0",
    "timestamp": "2026-09-18T10:30:00Z",
    "driver": {
      "driver_id": "driver_456"
    },
    "ride": {
      "ride_id": "ride_12345"
    },
    "location": {
      "latitude": 35.8225,
      "longitude": 10.6342,
      "speed_kmh": 32.5,
      "heading": 145
    },
    "ingested_at": "2026-09-18T10:30:01Z",
    "eventhub_partition": "0",
    "eventhub_offset": 123
  },
  {
    "event_id": "evt_def456",
    "event_type": "driver.location_updated",
    "event_version": "1.0",
    "timestamp": "2026-09-18T10:30:10Z",
    "driver": {
      "driver_id": "driver_456"
    },
    "ride": {
      "ride_id": "ride_12345"
    },
    "location": {
      "latitude": 35.8228,
      "longitude": 10.6345,
      "speed_kmh": 38.2,
      "heading": 151
    }
  }
]
```

### Important point

Don't wait for exactly 10 minutes inside the consumer. The **producer** generates data every 10 seconds, while the consumer should normally run continuously.

A practical raw-ingestion strategy is:

```text
Event Hub
    │
    │ event every 10 sec
    ▼
Consumer
    │
    │ accumulate events
    ▼
100 events OR 5 minutes
    │
    ▼
JSON file
    │
    ▼
ADLS /raw/
```

For your current lab, however, you can simply create **one file per driver/ride batch**.

Here is the corrected version of your consumer:


### One issue with this exact version

Because your producer sends **60 events in 10 minutes**, `BATCH_SIZE = 60` works nicely for your current lab:

```text
Producer
   │
   ├── Event 1   t=0s
   ├── Event 2   t=10s
   ├── Event 3   t=20s
   │     ...
   └── Event 60  t=590s
                 │
                 ▼
           Consumer buffer
                 │
                 ▼
          60 events collected
                 │
                 ▼
       taxi_events_xxx.json
                 │
                 ▼
             ADLS /raw
```

Then your **next application** can read:

```text
/raw/taxi_events_20260918_103000.json
```

and transform it into your **processed layer**, for example:

```text
RAW
[
  event1,
  event2,
  event3,
  ...
]

        ↓ Python processing

PROCESSED
[
  {
    "driver_id": "driver_456",
    "ride_id": "ride_12345",
    "timestamp": "...",
    "latitude": 35.8225,
    "longitude": 10.6342,
    "speed_kmh": 32.5,
    "heading": 145
  }
]
```

**One thing I'd change for your next step:** for a real Data Lake pipeline, I'd use **JSON Lines (`.jsonl`) or Parquet** rather than a giant JSON array. JSONL is much easier for your Python processing and Spark/Databricks later.



### question if i run the consumer.py in to 2 process will the traffic distrubted and the saving into the datalake is happen with no fault
Yes — **if you run two instances of the consumer with the same Event Hub and the same consumer group (`$Default`)**, Event Hubs will distribute partitions between them.

But there is an important detail: **your current code is not completely safe for two consumers when both are writing to the same raw file/buffer strategy.**

### What happens with 2 consumers?

Suppose your Event Hub has **4 partitions**:

```text
                    Azure Event Hub
                  taxi-events
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Partition 0  Partition 1  Partition 2  Partition 3
          │            │            │            │
          └───────┬────┘            └───────┬────┘
                  ▼                         ▼
             Consumer 1                Consumer 2
```

Event Hubs uses the **consumer group** to coordinate ownership of partitions.

For example:

```text
Consumer 1 → P0 + P1
Consumer 2 → P2 + P3
```

If one consumer stops:

```text
Consumer 1 → P0 + P1 + P2 + P3
Consumer 2 → stopped
```

The remaining consumer can take ownership of the other partitions.

So yes, **the traffic can be distributed.**

---

### But your Data Lake writes need attention

Your current code has:

```python
file_name = f"taxi_events_{timestamp}.json"
```

Imagine both consumers receive events at approximately the same time:

```text
Consumer 1
    │
    └── taxi_events_20260918_104000.json

Consumer 2
    │
    └── taxi_events_20260918_104000.json
```

They could potentially generate the **same filename**.

Because you use:

```python
overwrite=True
```

one consumer could overwrite the other's file.

That's a problem.

### Better filename

Include the partition ID and a unique identifier:

```python
file_name = (
    f"taxi_events_"
    f"{timestamp}_"
    f"partition_{partition_id}_"
    f"{uuid.uuid4().hex[:8]}.json"
)
```

Then you'll get:

```text
raw/
├── taxi_events_20260918_104000_partition_0_a81f32c1.json
├── taxi_events_20260918_104000_partition_1_82fa91de.json
├── taxi_events_20260918_104000_partition_2_b92ac421.json
└── taxi_events_20260918_104000_partition_3_c81e721a.json
```

Now the consumers can write independently.

---

## Another important issue: checkpointing

You currently do:

```python
save_batch_to_raw(event_buffer.copy())

event_buffer.clear()

partition_context.update_checkpoint(event)
```

This ordering is actually good.

You should **save successfully first, then checkpoint**.

Why?

Imagine:

```text
Receive event
     ↓
Save to ADLS ❌
     ↓
Checkpoint
```

If you checkpoint after a failed save, Event Hubs considers the event processed, and you could lose it from your pipeline.

Your desired order is:

```text
Event Hub
   ↓
Receive event
   ↓
Save to ADLS
   ↓
SUCCESS
   ↓
Checkpoint
```

That gives you much better delivery guarantees.

---

## But there is one more problem with `BATCH_SIZE = 60`

Suppose:

```text
Event Hub = 4 partitions
Consumers = 2
```

The 60 events might be distributed:

```text
Consumer 1:
P0 → 15 events
P1 → 15 events

Consumer 2:
P2 → 15 events
P3 → 15 events
```

Each consumer has its **own Python memory**:

```text
Consumer 1
event_buffer = [30 events]

Consumer 2
event_buffer = [30 events]
```

Neither reaches:

```python
len(event_buffer) >= 60
```

So after your producer stops, the consumers may still have unsaved events until you stop them with `Ctrl+C`.

For a real pipeline, I'd use a **time-based flush as well as a size-based flush**.

For example:

```text
100 events OR 60 seconds
```

whichever happens first.

That gives you:

```text
Event Hub
   │
   ├── Consumer 1
   │      └── Partition 0,1
   │
   └── Consumer 2
          └── Partition 2,3
                  │
                  ▼
             ADLS Raw
```

And:

```text
Consumer
   │
   ├── collect events
   │
   ├── 100 events?
   │       YES → save
   │
   └── 60 seconds?
           YES → save
```

### So the answer is:

| Question                                     | Answer                                          |
| -------------------------------------------- | ----------------------------------------------- |
| Can 2 consumers share the traffic?           | **Yes**                                         |
| Same consumer group?                         | **Yes, that's what you want**                   |
| Events duplicated between them?              | Normally **no**, within the same consumer group |
| Partitions distributed?                      | **Yes**                                         |
| Can both write to ADLS?                      | **Yes**                                         |
| Is your current filename strategy safe?      | **Not completely**                              |
| Should you include partition ID in filename? | **Yes**                                         |
| Checkpoint after successful ADLS write?      | **Yes**                                         |
| Should you use time-based flushing?          | **Yes**                                         |

One subtle point: Event Hubs consumers are generally **at-least-once**, so under failures/restarts, duplicate processing can occur. Your raw storage design should therefore tolerate duplicates, typically by retaining `event_id` and using it later for deduplication.

For your lab, I recommend we make the **production-style `eventhub_to_raw.py`** with **2 consumers + partition distribution + checkpointing + 60-second flush + unique ADLS files**, then you can run two terminals and actually observe the load balancing.



Yes. The clean solution is to change your consumer so that **each consumer writes its own batch file**, identified by the Event Hub partition, and uses **both a batch-size and time-based flush**.

For your lab, I recommend this architecture:

```text
                    Azure Event Hub
                         │
              ┌──────────┴──────────┐
              │  Consumer Group      │
              │      $Default        │
              └──────────┬──────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Consumer #1            Consumer #2
        Partition 0,1          Partition 2,3
              │                     │
              └──────────┬──────────┘
                         ▼
                    ADLS Gen2
                       /raw
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       P0 batch        P1 batch        P2 batch
       P3 batch        ...
```


## 2. Now run TWO consumers

Open terminal 1:

```bash
source /home/mohamed-amine/Documents/cloud_azure/.venv/bin/activate

python eventhub_to_raw.py
```

Open terminal 2:

```bash
source /home/mohamed-amine/Documents/cloud_azure/.venv/bin/activate

python eventhub_to_raw.py
```

Both must use:

```python
CONSUMER_GROUP = "$Default"
```

**Do not create a different consumer group for the second process.**

### Same group

```text
Consumer 1 ──┐
              ├── $Default ── Event Hub
Consumer 2 ──┘
```

This means they cooperate.

### Different groups

```text
Consumer 1 → $Default
Consumer 2 → taxi-analytics
```

Now both groups receive their own copy of the events. That's useful when you want **two independent applications** to process the same stream, but not for load balancing.

---

## 3. What you should see

Suppose your Event Hub has 4 partitions.

Terminal 1:

```text
EVENT RECEIVED
Partition : 0
Offset    : 100

EVENT RECEIVED
Partition : 1
Offset    : 205
```

Terminal 2:

```text
EVENT RECEIVED
Partition : 2
Offset    : 301

EVENT RECEIVED
Partition : 3
Offset    : 410
```

The exact distribution is controlled by Event Hubs and can change when consumers join/leave.

Then ADLS might contain:

```text
raw/
│
├── taxi_events_20260918_104001_partition_0_a81f32c1.json
├── taxi_events_20260918_104002_partition_1_82fa91de.json
├── taxi_events_20260918_104003_partition_2_b92ac421.json
└── taxi_events_20260918_104004_partition_3_c81e721a.json
```

No two consumers should overwrite each other's files because every filename contains:

```text
partition_ID
+
UUID
```

---

## 4. One correction to understand

There is a subtle issue with the previous code I gave you.

If you checkpoint **every event immediately**, you can checkpoint an event that hasn't actually been written to ADLS yet.

The safer pattern is:

```text
Receive event
     ↓
Add to buffer
     ↓
Buffer full / timeout
     ↓
Write batch to ADLS
     ↓
       ├── FAILED → don't checkpoint
       │
       └── SUCCESS → checkpoint
```

That's what the new code implements.

However, for a **production-grade system**, I would go one step further and use the Event Hubs checkpoint store in **Azure Blob Storage** rather than relying only on the default local/in-memory behavior. That makes partition ownership and checkpoints much more robust when you have multiple consumer processes or restart them.

For your current Azure lab, though, the immediate next test is simple:

```text
1. Start Consumer #1
2. Start Consumer #2
3. Start Producer
4. Let it generate 60 events
5. Check both consumer terminals
6. Check ADLS /raw/
```

You should then be able to see **which partitions each consumer owns and the resulting JSON batch files in the Data Lake**.
