Before **event-driven architecture**, systems mainly used **request/response communication** and **direct service-to-service communication**. Later, systems also relied heavily on **batch processing**.

A simple evolution is:

```text
1. Batch processing
       ↓
2. Request / Response
       ↓
3. Message queues
       ↓
4. Event-driven architecture / Event streaming
```

### 1. Batch processing — the old approach

A system collected data and processed it periodically.

For example, a bank might collect transactions:

```text
09:00 ─┐
10:00 ─┤
11:00 ─┤
12:00 ─┤
       ↓
   Database
       ↓
Nightly batch job
       ↓
Process all transactions
```

Instead of reacting immediately, the system might process everything every hour or every night.

---

### 2. Request/Response — very common before event-driven systems

This is the classic:

```text
Client
  │
  │ HTTP Request
  ▼
Server
  │
  │ Response
  ▼
Client
```

For example:

```http
POST /orders
```

The server processes the request and responds:

```json
{
  "status": "success"
}
```

In a microservice architecture, this could become:

```text
Order Service
      │
      │ HTTP/REST
      ▼
Payment Service
      │
      │ HTTP/REST
      ▼
Inventory Service
```

The services are directly connected.

---

### 3. The problem with direct communication

Imagine:

```text
Order Service
 ├────→ Payment
 ├────→ Inventory
 ├────→ Email
 ├────→ Analytics
 └────→ Recommendation
```

Now suppose **Analytics is down**.

Depending on how the system is designed, the Order Service may have to deal with that failure.

And as the system grows:

```text
A → B
A → C
A → D

B → C
B → D

C → D
...
```

The architecture becomes increasingly coupled.

---

### 4. Then came message queues

A major step was introducing **messaging systems**.

Instead of:

```text
Service A ─────────→ Service B
```

you get:

```text
Service A
    │
    ▼
 Message Queue
    │
    ▼
Service B
```

Examples include:

* RabbitMQ
* IBM MQ
* ActiveMQ

This allows asynchronous communication.

---

### 5. Then event-driven architecture / event streaming

Modern event streaming takes the idea further:

```text
                    ┌→ Consumer A
                    │
Producer → Event Bus ├→ Consumer B
                    │
                    └→ Consumer C
```

For your Azure lab:

```text
Producer
   │
   ▼
Azure Event Hubs
   │
   ├── Partition 0
   ├── Partition 1
   │
   ▼
Consumer Group
   │
   ▼
Consumer
```

And with your checkpoint lab:

```text
Consumer
    │
    │ checkpoint
    ▼
Azure Blob Storage
```

### The key difference

**Old request/response:**

> "I need something from you, so I'm asking you now."

**Event-driven:**

> "Something happened. Whoever is interested can react."

For example:

```text
OLD:

Order Service → Payment Service
              "Process order 123"


EVENT:

Order Service → Event Hubs
                "OrderCreated: 123"
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          Payment  Inventory  Analytics
```

So **event-driven architecture didn't completely replace the old technologies**. In real systems today, REST APIs, databases, queues, and event streaming are often used **together**, each for a different purpose.
