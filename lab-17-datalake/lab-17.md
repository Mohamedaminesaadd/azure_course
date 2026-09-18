Exactly. **Lab 20 is finished conceptually**, so now we move to **Lab 21 — Azure Data Lake Storage Gen2 (ADLS Gen2)**.

This lab is very important because it connects directly to the Event Hubs work we just did:

```text
Lab 20
IoT / Applications
       ↓
   Event Hubs
       ↓
   Real-time events

              ↓ Lab 21

       Azure Data Lake
       ┌───────────────┐
       │ raw/          │
       │ processed/    │
       │ curated/      │
       └───────────────┘
```

Azure Data Lake Storage Gen2 is built on Azure Blob Storage with **hierarchical namespace enabled**, which gives you directory/file-system semantics useful for analytics workloads. ([Microsoft Learn][1])

# 🏞️ Lab 21 — Build a Cloud Data Lake

## 1. First: What is a Data Lake?

A **Data Lake** is a centralized place where you can store large amounts of data in its original or processed form.

Unlike a traditional database, you don't have to force every incoming dataset into a predefined relational schema.

For example:

```text
Data Lake
│
├── JSON
├── CSV
├── Parquet
├── images
├── logs
├── sensor data
├── IoT data
└── application events
```

Microsoft describes ADLS Gen2 as a centralized repository capable of storing structured and unstructured data, commonly in files/blobs. ([Microsoft Learn][2])

---

# 2. Why do we need a Data Lake?

Look at our Event Hubs lab.

Suppose your ESP32 generates:

```text
10 events/second
```

Then:

```text
10 × 60 × 60
= 36,000 events/hour
```

And:

```text
36,000 × 24
= 864,000 events/day
```

You don't necessarily want all of that sitting inside a transactional SQL database.

Instead:

```text
ESP32
  ↓
Event Hubs
  ↓
Data Lake
  ↓
Long-term storage
  ↓
Data Engineering / AI / Power BI
```

That's the architecture we're beginning to build.

---

# 3. ADLS Gen2 vs Blob Storage

This is an important distinction because you've already worked with Azure Storage.

### Normal Blob Storage

Conceptually:

```text
Storage Account
      │
      └── Container
             │
             ├── file1.json
             ├── file2.csv
             └── file3.parquet
```

### ADLS Gen2

With **Hierarchical Namespace (HNS)**:

```text
Storage Account
      │
      └── File System / Container
              │
              ├── raw/
              │    ├── sensors/
              │    └── events/
              │
              ├── processed/
              │    ├── sensors/
              │    └── events/
              │
              └── curated/
                   ├── analytics/
                   └── reports/
```

The hierarchical namespace organizes objects/files into directories and nested directories, similar to a normal filesystem. ([Microsoft Learn][1])

---

# 4. The most important feature: Hierarchical Namespace

This is what turns an Azure Storage account into an ADLS Gen2-capable account.

```text
Azure Storage Account
        │
        │ HNS = Enabled
        ▼
ADLS Gen2 capabilities
```

Microsoft's current documentation says you enable **Hierarchical namespace** during storage-account creation, under the **Advanced** tab. ([Microsoft Learn][3])

Without HNS:

```text
Storage
 └── container
       └── blobs
```

With HNS:

```text
Storage
 └── filesystem/container
       ├── directory
       │    └── subdirectory
       │          └── file
       └── directory
```

This is especially useful for analytics workloads because directories have actual filesystem semantics, including atomic directory operations. ([Microsoft Learn][1])

---

# 5. Our Data Lake architecture

We're going to build exactly the architecture from your roadmap:

```text
                    DATA LAKE
                       │
       ┌───────────────┼───────────────┐
       ↓               ↓               ↓
     raw/          processed/       curated/
       │               │               │
       ↓               ↓               ↓
Original data     Clean data       Analytics data
```

### `raw/`

The original data.

Example:

```text
raw/
└── sensors/
    ├── 2026-09-18/
    │   ├── events-01.json
    │   └── events-02.json
```

Don't modify the raw data unnecessarily.

Think:

> **What did the source actually send?**

---

### `processed/`

Cleaned/transformed data.

Example:

```text
processed/
└── sensors/
    └── 2026-09-18/
        └── cleaned-events.parquet
```

Think:

> **What did our data pipeline clean and transform?**

---

### `curated/`

Data prepared specifically for analytics or applications.

Example:

```text
curated/
└── health/
    └── daily-summary/
        └── 2026-09-18.parquet
```

Think:

> **What data is ready for consumers such as analytics, BI, or ML?**

---

# 6. Now let's build it

## Step 1 — Create a NEW Storage Account

I recommend a new account for this lab instead of modifying your existing `aminestorages`.

Why?

Because you want to understand the difference between:

```text
Blob Storage
```

and:

```text
ADLS Gen2
```

from a clean architecture.

Go to:

**Azure Portal → Storage accounts → Create**

---

## Step 2 — Basics

Use:

| Setting              | Value                        |
| -------------------- | ---------------------------- |
| Subscription         | Azure subscription 1         |
| Resource group       | `amine_saad`                 |
| Storage account name | `amineadlslab21`*            |
| Region               | South Africa North           |
| Performance          | Standard                     |
| Redundancy           | Lowest suitable/local option |

* Storage account names must be globally unique and contain only lowercase letters and numbers. If `amineadlslab21` is unavailable, add a few digits.

For ADLS Gen2, Microsoft currently supports **Standard general-purpose v2** and **Premium block blob** accounts. For our learning lab, Standard is appropriate. ([Microsoft Learn][3])

---

# 7. Advanced — THIS IS THE IMPORTANT PART

Open:

**Advanced**

Find:

### Hierarchical namespace

Set:

```text
Enable hierarchical namespace
        ↓
       YES
```

This is the critical setting.

Your configuration should look conceptually like:

```text
Advanced

Hierarchical namespace
        ● Enabled
```

Microsoft's current documentation confirms that enabling HNS unlocks the Data Lake Storage capabilities. ([Microsoft Learn][3])

---

# 8. Why we're creating a new account

You might wonder:

> "Why don't we just enable HNS on `aminestorages`?"

Technically, an existing Blob Storage account can be upgraded in certain cases, but Microsoft's documentation warns that the upgrade to hierarchical namespace is **one-way**. ([Microsoft Learn][4])

For a learning environment:

```text
aminestorages
      ↓
Your previous Blob Storage labs

amineadlslab21
      ↓
Our ADLS Gen2 Lab 21
```

This is cleaner.

---

# 9. Networking

For this lab, keep the networking configuration simple.

Use the default public endpoint configuration unless Azure shows a subscription-specific restriction.

We are learning:

```text
Data Lake
HNS
Containers
Directories
Files
```

We don't need private endpoints yet.

Those concepts will become more important in your later **security/network architecture labs**.

---

# 10. Data protection

For a small learning lab:

Keep the default/basic settings unless Azure presents a required configuration.

We don't need:

```text
Geo-redundancy
advanced replication
versioning
immutability
```

for this exercise.

The goal is to understand the **data-lake architecture**, not build production disaster recovery yet.

---

# 11. Create

Go:

**Review + create**

Wait for validation.

Then:

**Create**

---

# 12. After deployment

Open:

```text
Storage accounts
      ↓
amineadlslab21
```

You should see the storage account overview.

The important thing we want to verify is:

```text
Hierarchical namespace:
Enabled
```

You can also inspect the account's **Data storage** area.

---

# 13. Create our first filesystem/container

Now go to:

**Data storage → Containers**

Click:

### `+ Container`

Create:

```text
datalake
```

Keep it private.

Our structure now becomes:

```text
amineadlslab21
       │
       └── datalake
```

In ADLS Gen2 terminology, the container is commonly used as the **file system** boundary for hierarchical data. Microsoft documentation also refers to creating a container/filesystem before creating directories and files. ([Microsoft Learn][5])

---

# 14. Now create the three layers

Inside:

```text
datalake
```

create:

```text
raw
processed
curated
```

So:

```text
datalake/
│
├── raw/
│
├── processed/
│
└── curated/
```

This is the first important Data Lake architecture you're building.

---

# 15. Then create subdirectories

Inside `raw`:

```text
raw/
└── sensors/
```

Inside `processed`:

```text
processed/
└── sensors/
```

Inside `curated`:

```text
curated/
└── analytics/
```

Final structure:

```text
datalake/
│
├── raw/
│   └── sensors/
│
├── processed/
│   └── sensors/
│
└── curated/
    └── analytics/
```

This is exactly why **hierarchical namespace** matters: you can work with actual directory structures rather than merely simulating paths in object names. ([Microsoft Learn][1])

---

# 16. Our next experiment

Once those directories exist, we're going to create actual files:

```text
raw/
└── sensors/
    └── sensor_data.json
```

For example:

```json
{
    "device_id": "ESP32-001",
    "temperature": 27.4,
    "heart_rate": 78,
    "timestamp": "2026-09-18T08:30:00Z"
}
```

Then we'll transform it:

```text
raw
 │
 │ transformation
 ▼
processed
```

and eventually:

```text
processed
 │
 │ analytics transformation
 ▼
curated
```

That will give you the fundamental **Raw → Processed → Curated** data-engineering pattern.

---

# 🧠 Lab 21 mental model

Remember this:

```text
                Azure Storage Account
                         │
                 HNS = ENABLED
                         │
                         ▼
                    ADLS Gen2
                         │
                    datalake/
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
      raw/          processed/         curated/
        │                │                │
   source data       clean data      analytics data
```

And now connect Lab 20 and Lab 21:

```text
                  ESP32 / Application
                         │
                         ▼
                    Event Hubs
                  [Lab 20]
                         │
                         │ events
                         ▼
                 ┌───────────────┐
                 │   ADLS Gen2   │
                 │   [Lab 21]    │
                 │               │
                 │ raw/          │
                 │ processed/    │
                 │ curated/      │
                 └───────────────┘
```

**Start by creating the new Storage Account with `Hierarchical namespace = Enabled`.** Once it is deployed, tell me the **storage account name + whether HNS shows Enabled**, and we'll create the `datalake → raw/processed/curated` structure and upload our first real data file.

[1]: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-namespace?utm_source=chatgpt.com "Azure Data Lake Storage hierarchical namespace - Azure Storage | Microsoft Learn"
[2]: https://learn.microsoft.com/en-us/azure/architecture/data-guide/technology-choices/data-storage?utm_source=chatgpt.com "Choose a data storage technology - Azure Architecture Center | Microsoft Learn"
[3]: https://learn.microsoft.com/en-us/azure/storage/blobs/create-data-lake-storage-account?utm_source=chatgpt.com "Create a storage account for Data Lake Storage - Azure Storage | Microsoft Learn"
[4]: https://learn.microsoft.com/en-us/azure/storage/blobs/upgrade-to-data-lake-storage-gen2-how-to?utm_source=chatgpt.com "Upgrade Azure Blob Storage with Azure Data Lake Storage capabilities | Microsoft Learn"
[5]: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-directory-file-acl-powershell?utm_source=chatgpt.com "Manage Files and Directories With PowerShell in Data Lake - Azure Storage | Microsoft Learn"


## Step 3 — Create the Data Lake directories

Now we have:

```text
amineadlslab21
└── datalake
```

We're going to create the three layers:

```text
datalake/
├── raw/
├── processed/
└── curated/
```

ADLS Gen2 supports actual directories because we enabled **Hierarchical Namespace**. ([Microsoft Learn][1])

### 3.1 Open the filesystem

In Azure Portal:

**Storage accounts → `amineadlslab21` → Containers**

Click:

```text
datalake
```

You should see the contents of the filesystem.

---

### 3.2 Create `raw`

Click:

**+ Add directory**

Enter:

```text
raw
```

Click **Save/Create**.

You should now have:

```text
datalake/
└── raw/
```

---

### 3.3 Create `processed`

Go back to the `datalake` root.

Click:

**+ Add directory**

Enter:

```text
processed
```

Now:

```text
datalake/
├── raw/
└── processed/
```

---

### 3.4 Create `curated`

Again, at the `datalake` root:

**+ Add directory**

Enter:

```text
curated
```

Final structure:

```text
datalake/
├── raw/
├── processed/
└── curated/
```

---

## 🧠 What these three directories mean

### `raw/`

Original data — **don't transform it**.

```text
raw/
└── sensors/
    └── events.json
```

### `processed/`

Cleaned/transformed data.

```text
processed/
└── sensors/
    └── clean-events.parquet
```

### `curated/`

Data prepared for analytics/business/ML.

```text
curated/
└── analytics/
    └── daily-summary.parquet
```

Think:

```text
             SOURCE
                │
                ▼
              raw/
                │
          cleaning/
          transformation
                │
                ▼
           processed/
                │
          aggregation
                │
                ▼
            curated/
```

This **Raw → Processed → Curated** pattern will become very important when we build your Data Factory pipeline in **Lab 22**.

---

### Stop here ⛔

Don't create the subdirectories yet.

Once you have:

```text
datalake/
├── raw/
├── processed/
└── curated/
```

say **next** and we'll do **Step 4: put real sensor/event data into `raw/`**.

[1]: https://learn.microsoft.com/en-us/cli/azure/storage/fs/directory?view=azure-cli-latest&utm_source=chatgpt.com "az storage fs directory | Microsoft Learn"
