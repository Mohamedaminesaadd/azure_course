Absolutely. **Lab 20 — Real-Time Event Streaming with Azure Event Hubs** starts now.

The goal is not just to create an Event Hub. We will understand **how real-time streaming works**, then build it with Python.

# 🚀 Lab 20 — Azure Event Hubs

According to your roadmap, this lab is the entry point into **Data Engineering / real-time streaming**:

> **IoT / Applications → Event Hubs → Consumers**

We will eventually build:

```text
┌──────────────────┐
│ Event Producer   │
│ Python / IoT     │
└────────┬─────────┘
         │
         │ Events
         ▼
┌──────────────────────────────┐
│ Azure Event Hubs Namespace   │
│                              │
│   ┌──────────────────────┐   │
│   │ Event Hub            │   │
│   │                      │   │
│   │ Partition 0          │   │
│   │ Partition 1          │   │
│   │ Partition 2          │   │
│   └──────────────────────┘   │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│ Consumer 1  │  │ Consumer 2  │
│ Python      │  │ Analytics   │
└─────────────┘  └─────────────┘
```

Azure describes Event Hubs as a scalable publish-subscribe streaming service designed to ingest very large volumes of events from applications and connected devices. ([Microsoft Learn][1])

---

# 1. First: What exactly is an "event"?

An **event** is a piece of information saying that something happened.

For example:

```json
{
    "device_id": "ESP32-001",
    "temperature": 27.4,
    "heart_rate": 78,
    "timestamp": "2026-09-17T18:30:00"
}
```

This is one event.

Another:

```json
{
    "device_id": "ESP32-001",
    "temperature": 27.6,
    "heart_rate": 80,
    "timestamp": "2026-09-17T18:30:01"
}
```

And another:

```json
{
    "device_id": "ESP32-001",
    "temperature": 27.7,
    "heart_rate": 81,
    "timestamp": "2026-09-17T18:30:02"
}
```

Together:

```text
Event 1
Event 2
Event 3
Event 4
Event 5
...
```

form an **event stream**.

---

# 2. Event stream vs normal database

This distinction is extremely important.

### Traditional database

You might have:

```text
Application
     │
     ▼
 Azure SQL
     │
     ▼
Customers table
Orders table
Products table
```

The database stores the **current state**.

For example:

```text
Customer 42
Balance = 150 €
```

---

### Event streaming

With Event Hubs:

```text
Application
     │
     ▼
Event Hub
     │
     ├── Event 1
     ├── Event 2
     ├── Event 3
     ├── Event 4
     └── Event 5
```

The system is interested in the **continuous flow of events**.

For example:

```text
18:00:01 → temperature = 27.1
18:00:02 → temperature = 27.2
18:00:03 → temperature = 27.3
18:00:04 → temperature = 27.4
```

This is why Event Hubs is useful for:

* IoT
* telemetry
* application events
* logs
* clickstreams
* real-time analytics
* monitoring
* financial/event data
* sensor systems

---

# 3. The 7 concepts you MUST understand

Before touching Azure Portal, I want you to understand these:

```text
Event
   ↓
Producer
   ↓
Event Hub
   ↓
Partition
   ↓
Consumer Group
   ↓
Consumer
   ↓
Offset / Checkpoint
```

These are the vocabulary of the lab.

---

## ① Producer

The **producer** creates and sends events.

Example:

```python
producer.send(event)
```

Architecture:

```text
Python application
       │
       │ send event
       ▼
Azure Event Hubs
```

A producer could be:

* Python application
* Java application
* IoT device
* web application
* backend API
* Kafka producer

---

# 4. ② Event Hub

An **Event Hub** is where the stream of events is collected.

Think:

```text
Producer
   │
   │
   ▼
┌─────────────────┐
│   Event Hub     │
│                 │
│ E1              │
│ E2              │
│ E3              │
│ E4              │
│ E5              │
└─────────────────┘
```

Important:

### Namespace ≠ Event Hub

A **namespace** is the larger management container.

```text
Azure
 │
 ▼
Event Hubs Namespace
 │
 ├── Event Hub: sensors
 │
 ├── Event Hub: orders
 │
 └── Event Hub: logs
```

Microsoft describes the namespace as the management container for one or more event hubs. ([Microsoft Learn][2])

For our lab:

```text
Resource Group
     │
     ▼
Event Hubs Namespace
     │
     ▼
event-hub
```

---

# 5. ③ Partitions — VERY IMPORTANT

This is probably the most important concept in Event Hubs.

Imagine one huge highway:

```text
=============================
        ONE LANE
=============================
```

If millions of cars use it, there is a bottleneck.

Instead:

```text
=============================
 Lane 0
=============================
 Lane 1
=============================
 Lane 2
=============================
 Lane 3
=============================
```

These are **partitions**.

An Event Hub contains one or more partitions, which allow events to be processed in parallel. ([Microsoft Learn][2])

For example:

```text
Event Hub
│
├── Partition 0
│     ├── E1
│     ├── E4
│     └── E7
│
├── Partition 1
│     ├── E2
│     ├── E5
│     └── E8
│
└── Partition 2
      ├── E3
      ├── E6
      └── E9
```

### Why partitions?

Because consumers can process them in parallel.

```text
Partition 0 ──► Consumer A
Partition 1 ──► Consumer B
Partition 2 ──► Consumer C
```

This is a fundamental scalability mechanism in Event Hubs. ([Microsoft Learn][3])

---

# 6. Ordering

There is an important rule:

> **Ordering is maintained within a partition.**

Suppose:

```text
Partition 0

E1
E2
E3
E4
```

The consumer reads:

```text
E1 → E2 → E3 → E4
```

But don't think of the entire Event Hub as one globally ordered list.

Instead:

```text
Partition 0: E1 → E2 → E3

Partition 1: A1 → A2 → A3

Partition 2: B1 → B2 → B3
```

Each partition has its own ordered sequence.

If you need related events to stay together, a **partition key** can be used so events with the same key are sent to the same partition. ([Microsoft Learn][4])

For example:

```text
device_id = ESP32-001
```

could be used as the partition key.

Then:

```text
ESP32-001 → Partition 0
ESP32-001 → Partition 0
ESP32-001 → Partition 0
```

This helps preserve ordering for that device.

---

# 7. ④ Consumer

A **consumer** reads events.

For example:

```text
Event Hub
    │
    │
    ▼
Python Consumer
    │
    ▼
print(event)
```

But you can also have:

```text
                    ┌──► Python analytics
                    │
Event Hub ──────────┼──► Data Lake
                    │
                    └──► Real-time dashboard
```

This is where Event Hubs becomes powerful.

---

# 8. ⑤ Consumer Group

This is another extremely important concept.

Imagine one Event Hub:

```text
Event Hub
    │
    ├── Consumer Group A
    │       └── Analytics application
    │
    └── Consumer Group B
            └── Storage application
```

Both applications can independently read the same stream.

Microsoft describes a consumer group as a logical view of an event hub that allows different consumer applications to read the same stream independently, each maintaining its own position. ([Microsoft Learn][2])

Think of it like:

```text
                 Event Hub
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    Consumer Group A       Consumer Group B
          │                     │
          ▼                     ▼
    Real-time AI            Data Lake
```

They don't have to consume the events at exactly the same speed.

---

# 9. ⑥ Offset

Suppose the partition contains:

```text
E1
E2
E3
E4
E5
E6
E7
```

Your consumer processed:

```text
E1
E2
E3
E4
```

It needs to know:

> "Where did I stop?"

That's the purpose of the **offset**.

Conceptually:

```text
E1
E2
E3
E4  ← last processed
E5  ← next
E6
E7
```

The offset identifies a position in the event stream within a partition. ([Microsoft Learn][5])

---

# 10. ⑦ Checkpoint

A checkpoint is the persisted record of the consumer's progress.

Imagine:

```text
Consumer
   │
   ├── E1 ✓
   ├── E2 ✓
   ├── E3 ✓
   ├── E4 ✓
   └── checkpoint
          ↓
       "E4"
```

Then your application crashes.

When it restarts:

```text
checkpoint
     ↓
     E4
     │
     ▼
continue from E5
```

Checkpointing provides resilience and allows consumers to resume processing from a known position. ([Microsoft Learn][5])

For more advanced labs, we'll use **Azure Blob Storage as the checkpoint store**. Microsoft recommends the Event Hubs checkpoint-store library for this scenario. ([Microsoft Learn][6])

---

# 11. Complete mental model

Put everything together:

```text
                    PRODUCER
                       │
                       │ Events
                       ▼
              ┌──────────────────┐
              │ Event Hub        │
              │                  │
              │ ┌──────────────┐ │
              │ │ Partition 0  │ │
              │ ├──────────────┤ │
              │ │ Partition 1  │ │
              │ ├──────────────┤ │
              │ │ Partition 2  │ │
              │ └──────────────┘ │
              └────────┬─────────┘
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
       Consumer Group A    Consumer Group B
             │                   │
             ▼                   ▼
       Application A        Application B
             │                   │
             ▼                   ▼
        Analytics            Data Lake
```

That architecture is the foundation for Labs **21–23**.

---

# 12. Event Hubs vs Kafka

Since you already worked with Kafka, this is particularly useful.

### Kafka

```text
Producer
   ↓
Kafka Cluster
   ↓
Topic
   ↓
Partitions
   ↓
Consumer Groups
   ↓
Consumers
```

### Azure Event Hubs

```text
Producer
   ↓
Event Hubs Namespace
   ↓
Event Hub
   ↓
Partitions
   ↓
Consumer Groups
   ↓
Consumers
```

The concepts are deliberately very similar.

Azure Event Hubs also provides a Kafka-compatible endpoint, so Kafka clients can communicate with Event Hubs without requiring you to operate your own Kafka cluster. ([Microsoft Learn][7])

**But don't conclude that Event Hubs and Kafka are identical products.**

For this lab, think:

> **Kafka = streaming platform you can operate yourself.**
> **Event Hubs = Azure-managed streaming ingestion service.**

---

# 13. Our practical lab

We will build this:

```text
                 YOUR UBUNTU PC
                      │
                      │ Python Producer
                      │
                      ▼
             ┌──────────────────┐
             │ Azure Event Hubs │
             │                  │
             │  sensor-events   │
             │                  │
             │ ┌────┐ ┌────┐   │
             │ │ P0 │ │ P1 │   │
             │ └────┘ └────┘   │
             └────────┬─────────┘
                      │
                      ▼
              Python Consumer
                      │
                      ▼
               Terminal output
```

Then we'll progressively improve it:

### Stage 1 — Azure infrastructure

```text
Resource Group
      ↓
Event Hubs Namespace
      ↓
Event Hub
```

### Stage 2 — Producer

```text
Python
  ↓
generate JSON events
  ↓
Event Hubs
```

### Stage 3 — Consumer

```text
Event Hubs
   ↓
Python
   ↓
read events
```

### Stage 4 — Partitions

We'll deliberately generate enough events to understand:

```text
P0
P1
P2
```

and how consumers interact with them.

### Stage 5 — Consumer groups

We'll create independent consumers:

```text
                 Event Hub
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      Group A              Group B
          │                   │
     Analytics            Storage
```

### Stage 6 — Checkpointing

We'll introduce:

```text
Event Hub
    ↓
Consumer
    ↓
Blob Storage
    ↓
Checkpoint
```

### Stage 7 — Real architecture

Eventually:

```text
IoT / Python
      │
      ▼
 Event Hubs
      │
      ├──────────────► Real-Time Processing
      │
      └──────────────► Data Lake
                           │
                           ▼
                     Batch Processing
                           │
                           ▼
                       Power BI
```

That's where Labs **20 → 21 → 22 → 23** connect together.

---

# 14. Azure configuration for our lab

We'll keep this lab deliberately small.

Microsoft currently lists **Basic** as intended for simple, low-volume streaming with a single consumer group and short retention, while **Standard** adds capabilities such as multiple consumer groups and Kafka support. ([Microsoft Learn][8])

For learning, we should **not create unnecessary capacity**.

We'll first check what tiers your subscription exposes in the Portal before choosing.

### Target resources

```text
Resource Group:
amine_saad

Region:
South Africa North

Namespace:
eh-amine-lab20

Event Hub:
sensor-events
```

And initially:

```text
Partitions: small number
Retention: short
```

The exact available settings depend on the tier and current Azure Portal interface.

---

# 15. First practical step — create the Namespace

Open:

[Azure Portal](https://portal.azure.com/?utm_source=chatgpt.com)

Search:

**Event Hubs**

Then:

**Create → Event Hubs namespace**

Use approximately:

| Setting        | Value                                           |
| -------------- | ----------------------------------------------- |
| Subscription   | Your Azure subscription                         |
| Resource group | `amine_saad`                                    |
| Namespace      | `eh-amine-lab20`                                |
| Region         | `South Africa North`                            |
| Pricing tier   | We'll choose the lowest suitable tier available |
| Other settings | Keep defaults initially                         |

Microsoft's current portal workflow is **Create namespace → create Event Hub inside the namespace**. ([Microsoft Learn][7])

### ⚠️ Important

Don't create it yet if you see a **pricing/cost warning you don't understand**.

Send me a screenshot of the **Basics / Pricing tier** page if the options differ from what I described.

We'll verify the configuration before deployment.

---

## 🧠 Lab 20 checkpoint

Before we start clicking around, make sure these relationships are clear:

```text
Namespace
   │
   └── Event Hub
          │
          ├── Partition 0
          ├── Partition 1
          └── Partition 2
                  │
                  ▼
             Consumer Group
                  │
                  ▼
               Consumer
                  │
                  ▼
               Offset
                  │
                  ▼
             Checkpoint
```

**Next practical step:** create the **Event Hubs Namespace**, then we'll create `sensor-events` and immediately test our first event with Python.

[1]: https://learn.microsoft.com/en-us/azure/event-hubs/?utm_source=chatgpt.com "Azure Event Hubs documentation | Microsoft Learn"
[2]: https://learn.microsoft.com/en-in/azure/event-hubs/event-hubs-about?utm_source=chatgpt.com "What is Azure Event Hubs - Real-time data streaming platform - Azure Event Hubs | Microsoft Learn"
[3]: https://learn.microsoft.com/en-us/azure/event-hubs/event-processor-balance-partition-load?utm_source=chatgpt.com "Partition load balancing for event processing - Azure Event Hubs | Microsoft Learn"
[4]: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-availability-and-consistency?utm_source=chatgpt.com "Availability and consistency - Azure Event Hubs - Azure Event Hubs | Microsoft Learn"
[5]: https://learn.microsoft.com/en-us/python/api/overview/azure/eventhub-checkpointstoreblob-readme?view=azure-python&utm_source=chatgpt.com "Azure EventHubs Checkpoint Store using Storage Blobs client library for Python | Microsoft Learn"
[6]: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-python-get-started-send?utm_source=chatgpt.com "Send and Receive Events from Azure Event Hubs Using Python - Azure Event Hubs | Microsoft Learn"
[7]: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-create?utm_source=chatgpt.com "Create Azure Event Hubs instance Using Portal - Azure Event Hubs | Microsoft Learn"
[8]: https://learn.microsoft.com/en-us/azure/event-hubs/compare-tiers?utm_source=chatgpt.com "Compare Azure Event Hubs tiers - Azure Event Hubs | Microsoft Learn"
